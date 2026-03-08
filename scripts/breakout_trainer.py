#!/usr/bin/env python3
"""
Breakout ML — Step 3: Train XGBoost + CNN hybrid model.

Model 1: XGBoost on tabular features (fast, interpretable)
Model 2: 1D CNN on raw OHLCV time series (captures patterns)
Model 3: Ensemble (combine both)

Target: Binary — "double" (100%+ gain) vs everything else.
Also trains a multi-class model for graded predictions.

Usage:
    python3 scripts/breakout_trainer.py
    python3 scripts/breakout_trainer.py --target big_win  # 50%+ gain target
"""
import argparse
import json
import os
import pickle
import sys
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import (classification_report, precision_score, 
                             recall_score, roc_auc_score, confusion_matrix)
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
EVENTS_FILE = os.path.join(DATA_DIR, 'breakout_events.parquet')
TIMESERIES_FILE = os.path.join(DATA_DIR, 'breakout_timeseries.npz')

os.makedirs(MODEL_DIR, exist_ok=True)

# Feature columns for XGBoost
FEATURE_COLS = [
    'close_to_ma20', 'close_to_ma50', 'close_to_ma200',
    'trend_aligned', 'atr_14', 'vol_dryup_ratio', 'vol_compression',
    'proximity_52w', 'return_3mo', 'up_days_pct', 'vol_trend_in_base',
    'base_length', 'base_range', 'breakout_vol_ratio'
]


def load_data(target='double'):
    """Load and prepare data with time-based train/val/test split."""
    df = pd.read_parquet(EVENTS_FILE)
    ts_data = np.load(TIMESERIES_FILE)['timeseries']
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Binary target
    if target == 'double':
        df['target'] = (df['label'] == 'double').astype(int)
    elif target == 'big_win':
        df['target'] = df['label'].isin(['double', 'big_win']).astype(int)
    elif target == 'winner':
        df['target'] = df['label'].isin(['double', 'big_win', 'win']).astype(int)
    
    # Multi-class target
    label_map = {'fail': 0, 'win': 1, 'big_win': 2, 'double': 3}
    df['target_multi'] = df['label'].map(label_map)
    
    # Time-based split: train (2021-2024), val (2025 H1), test (2025 H2+)
    train_end = pd.Timestamp('2025-01-01')
    val_end = pd.Timestamp('2025-07-01')
    
    train_mask = df['date'] < train_end
    val_mask = (df['date'] >= train_end) & (df['date'] < val_end)
    test_mask = df['date'] >= val_end
    
    print(f'📊 Dataset: {len(df)} events')
    print(f'   Train: {train_mask.sum()} (before {train_end.strftime("%Y-%m-%d")})')
    print(f'   Val:   {val_mask.sum()} ({train_end.strftime("%Y-%m-%d")} - {val_end.strftime("%Y-%m-%d")})')
    print(f'   Test:  {test_mask.sum()} (after {val_end.strftime("%Y-%m-%d")})')
    print(f'   Target ({target}): {df["target"].sum()} positives ({df["target"].mean()*100:.1f}%)')
    
    return df, ts_data, train_mask, val_mask, test_mask


def train_xgboost(df, train_mask, val_mask, test_mask, target_col='target'):
    """Train XGBoost on tabular features."""
    try:
        import xgboost as xgb
    except ImportError:
        print('Installing xgboost...')
        os.system(f'{sys.executable} -m pip install xgboost --quiet')
        import xgboost as xgb
    
    X_train = df.loc[train_mask, FEATURE_COLS].values
    y_train = df.loc[train_mask, target_col].values
    X_val = df.loc[val_mask, FEATURE_COLS].values
    y_val = df.loc[val_mask, target_col].values
    X_test = df.loc[test_mask, FEATURE_COLS].values
    y_test = df.loc[test_mask, target_col].values
    
    # Handle class imbalance
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    scale_pos_weight = neg_count / pos_count if pos_count > 0 else 1
    
    print(f'\n🌲 Training XGBoost (scale_pos_weight={scale_pos_weight:.1f})...')
    
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        eval_metric='aucpr',
        early_stopping_rounds=50,
        random_state=42,
        use_label_encoder=False
    )
    
    model.fit(X_train, y_train, 
              eval_set=[(X_val, y_val)], 
              verbose=False)
    
    # Evaluate
    print(f'   Best iteration: {model.best_iteration}')
    
    for name, X, y in [('Val', X_val, y_val), ('Test', X_test, y_test)]:
        if len(y) == 0:
            continue
        probs = model.predict_proba(X)[:, 1]
        preds = (probs >= 0.5).astype(int)
        
        auc = roc_auc_score(y, probs) if len(np.unique(y)) > 1 else 0
        prec = precision_score(y, preds, zero_division=0)
        rec = recall_score(y, preds, zero_division=0)
        
        # Top-decile precision (when model is most confident)
        top_n = max(1, len(probs) // 10)
        top_idx = np.argsort(probs)[-top_n:]
        top_prec = y[top_idx].mean() if len(top_idx) > 0 else 0
        
        print(f'\n   {name} Results:')
        print(f'   AUC: {auc:.3f}  Precision: {prec:.3f}  Recall: {rec:.3f}')
        print(f'   Top-10% Precision: {top_prec:.3f} ({y[top_idx].sum()}/{len(top_idx)} hits)')
    
    # Feature importance
    importance = dict(zip(FEATURE_COLS, model.feature_importances_))
    sorted_imp = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    print(f'\n   📊 Feature Importance:')
    for feat, imp in sorted_imp:
        bar = '█' * int(imp * 50)
        print(f'   {feat:25s} {imp:.3f} {bar}')
    
    return model


def train_cnn(df, ts_data, train_mask, val_mask, test_mask, target_col='target'):
    """Train 1D CNN on raw OHLCV time series."""
    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError:
        print('\n⚠️  PyTorch not installed. Skipping CNN model.')
        print('   Install: pip install torch')
        return None
    
    # Prepare data
    X_train_ts = ts_data[train_mask.values]
    y_train = df.loc[train_mask, target_col].values
    X_val_ts = ts_data[val_mask.values]
    y_val = df.loc[val_mask, target_col].values
    X_test_ts = ts_data[test_mask.values]
    y_test = df.loc[test_mask, target_col].values
    
    # Convert to tensors: (N, 91, 5) → (N, 5, 91) for Conv1d
    X_train_t = torch.FloatTensor(X_train_ts).permute(0, 2, 1)
    y_train_t = torch.FloatTensor(y_train)
    X_val_t = torch.FloatTensor(X_val_ts).permute(0, 2, 1)
    y_val_t = torch.FloatTensor(y_val)
    X_test_t = torch.FloatTensor(X_test_ts).permute(0, 2, 1)
    y_test_t = torch.FloatTensor(y_test)
    
    # Class weight
    pos_weight = torch.tensor([(len(y_train) - y_train.sum()) / max(y_train.sum(), 1)])
    
    class BreakoutCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv1d(5, 32, kernel_size=5, padding=2)
            self.conv2 = nn.Conv1d(32, 64, kernel_size=5, padding=2)
            self.conv3 = nn.Conv1d(64, 128, kernel_size=3, padding=1)
            self.pool = nn.AdaptiveAvgPool1d(1)
            self.dropout = nn.Dropout(0.3)
            self.fc1 = nn.Linear(128, 64)
            self.fc2 = nn.Linear(64, 1)
            self.relu = nn.ReLU()
            self.bn1 = nn.BatchNorm1d(32)
            self.bn2 = nn.BatchNorm1d(64)
            self.bn3 = nn.BatchNorm1d(128)
        
        def forward(self, x):
            x = self.relu(self.bn1(self.conv1(x)))
            x = self.relu(self.bn2(self.conv2(x)))
            x = self.relu(self.bn3(self.conv3(x)))
            x = self.pool(x).squeeze(-1)
            x = self.dropout(x)
            x = self.relu(self.fc1(x))
            x = self.fc2(x)
            return x.squeeze(-1)
    
    model = BreakoutCNN()
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    
    train_ds = TensorDataset(X_train_t, y_train_t)
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    
    print(f'\n🧠 Training 1D CNN ({sum(p.numel() for p in model.parameters()):,} params)...')
    
    best_val_auc = 0
    best_model_state = None
    patience = 20
    patience_counter = 0
    
    for epoch in range(150):
        model.train()
        epoch_loss = 0
        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            out = model(X_batch)
            loss = criterion(out, y_batch)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        
        # Validate
        model.eval()
        with torch.no_grad():
            val_logits = model(X_val_t)
            val_probs = torch.sigmoid(val_logits).numpy()
            val_loss = criterion(val_logits, y_val_t).item()
        
        if len(np.unique(y_val)) > 1:
            val_auc = roc_auc_score(y_val, val_probs)
        else:
            val_auc = 0
        
        scheduler.step(val_loss)
        
        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_model_state = {k: v.clone() for k, v in model.state_dict().items()}
            patience_counter = 0
        else:
            patience_counter += 1
        
        if patience_counter >= patience:
            print(f'   Early stop at epoch {epoch+1}')
            break
        
        if (epoch + 1) % 25 == 0:
            print(f'   Epoch {epoch+1}: loss={epoch_loss/len(train_loader):.4f}, val_auc={val_auc:.3f}')
    
    # Load best model
    if best_model_state:
        model.load_state_dict(best_model_state)
    
    # Evaluate
    model.eval()
    with torch.no_grad():
        for name, X_t, y in [('Val', X_val_t, y_val), ('Test', X_test_t, y_test)]:
            if len(y) == 0:
                continue
            probs = torch.sigmoid(model(X_t)).numpy()
            preds = (probs >= 0.5).astype(int)
            
            auc = roc_auc_score(y, probs) if len(np.unique(y)) > 1 else 0
            prec = precision_score(y, preds, zero_division=0)
            
            top_n = max(1, len(probs) // 10)
            top_idx = np.argsort(probs)[-top_n:]
            top_prec = y[top_idx].mean()
            
            print(f'\n   CNN {name}: AUC={auc:.3f}, Precision={prec:.3f}, Top-10%={top_prec:.3f}')
    
    return model


def train_ensemble(df, ts_data, xgb_model, cnn_model, train_mask, val_mask, test_mask, target_col='target'):
    """Combine XGBoost + CNN predictions."""
    import torch
    
    X_tab = df[FEATURE_COLS].values
    
    # XGBoost predictions
    xgb_probs = xgb_model.predict_proba(X_tab)[:, 1]
    
    # CNN predictions
    cnn_model.eval()
    with torch.no_grad():
        X_ts = torch.FloatTensor(ts_data).permute(0, 2, 1)
        cnn_probs = torch.sigmoid(cnn_model(X_ts)).numpy()
    
    # Simple average ensemble
    ensemble_probs = 0.5 * xgb_probs + 0.5 * cnn_probs
    
    for name, mask in [('Val', val_mask), ('Test', test_mask)]:
        y = df.loc[mask, target_col].values
        probs = ensemble_probs[mask.values]
        
        if len(y) == 0 or len(np.unique(y)) < 2:
            continue
        
        auc = roc_auc_score(y, probs)
        top_n = max(1, len(probs) // 10)
        top_idx = np.argsort(probs)[-top_n:]
        top_prec = y[top_idx].mean()
        
        print(f'\n   Ensemble {name}: AUC={auc:.3f}, Top-10% Precision={top_prec:.3f}')
    
    return ensemble_probs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', default='double', choices=['double', 'big_win', 'winner'])
    args = parser.parse_args()
    
    print(f'🚀 Breakout Prediction Model Training')
    print(f'   Target: {args.target}')
    print(f'   Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    df, ts_data, train_mask, val_mask, test_mask = load_data(args.target)
    
    # Model 1: XGBoost
    xgb_model = train_xgboost(df, train_mask, val_mask, test_mask)
    
    # Save XGBoost model
    xgb_path = os.path.join(MODEL_DIR, f'breakout_xgb_{args.target}.pkl')
    with open(xgb_path, 'wb') as f:
        pickle.dump(xgb_model, f)
    print(f'\n   💾 XGBoost saved: {xgb_path}')
    
    # Model 2: CNN (if PyTorch available)
    cnn_model = train_cnn(df, ts_data, train_mask, val_mask, test_mask)
    
    if cnn_model:
        import torch
        cnn_path = os.path.join(MODEL_DIR, f'breakout_cnn_{args.target}.pt')
        torch.save(cnn_model.state_dict(), cnn_path)
        print(f'   💾 CNN saved: {cnn_path}')
        
        # Model 3: Ensemble
        print(f'\n🤝 Ensemble (XGBoost + CNN):')
        train_ensemble(df, ts_data, xgb_model, cnn_model, train_mask, val_mask, test_mask)
    
    # Save metadata
    meta = {
        'target': args.target,
        'features': FEATURE_COLS,
        'train_events': int(train_mask.sum()),
        'val_events': int(val_mask.sum()),
        'test_events': int(test_mask.sum()),
        'positive_rate': float(df['target'].mean()),
        'trained_at': datetime.now().isoformat(),
        'has_cnn': cnn_model is not None
    }
    with open(os.path.join(MODEL_DIR, 'breakout_meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    
    print(f'\n✅ Training complete!')


if __name__ == '__main__':
    main()
