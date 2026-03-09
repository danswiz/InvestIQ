#!/usr/bin/env python3
"""
IQ Edge Score — Predict breakout probability for all current stocks.

Uses the trained XGBoost model to score every stock in all_stocks.json.
Adds `iq_edge` (0-99 percentile) and `iq_edge_raw` (probability) to each stock.

Usage:
    python3 scripts/iq_edge_predict.py
    python3 scripts/iq_edge_predict.py --ticker NVDA   # Score single stock
"""
import argparse
import json
import os
import pickle
import sys
import time

import numpy as np
import pandas as pd
import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
STOCKS_FILE = os.path.join(DATA_DIR, 'all_stocks.json')
MODEL_FILE = os.path.join(MODEL_DIR, 'breakout_xgb_prod.pkl')  # trained 2016-2024, OOS AUC 0.835

# Must match training features exactly
FEATURE_COLS = [
    'close_to_ma20', 'close_to_ma50', 'close_to_ma200',
    'trend_aligned', 'atr_14', 'vol_dryup_ratio', 'vol_compression',
    'proximity_52w', 'return_3mo', 'up_days_pct', 'vol_trend_in_base',
    'base_length', 'base_range', 'breakout_vol_ratio'
]

# Parameters (match labeler)
BASE_MIN_DAYS = 20
BASE_MAX_DRIFT = 0.15
VOLUME_THRESHOLD = 1.0  # Lower threshold for scoring (not just confirmed breakouts)


def load_model():
    with open(MODEL_FILE, 'rb') as f:
        return pickle.load(f)


def compute_features_for_ticker(ticker, hist_df=None):
    """Compute breakout features for a single ticker using recent data."""
    try:
        if hist_df is None:
            t = yf.Ticker(ticker)
            hist_df = t.history(period='1y', interval='1d')
        
        if len(hist_df) < 100:
            return None
        
        prices = hist_df['Close'].values
        volumes = hist_df['Volume'].values
        idx = len(prices) - 1  # Current day
        close = prices[idx]
        
        # Moving averages
        ma_20 = np.mean(prices[max(0, idx-20):idx]) if idx >= 20 else close
        ma_50 = np.mean(prices[max(0, idx-50):idx]) if idx >= 50 else close
        ma_200 = np.mean(prices[max(0, idx-200):idx]) if idx >= 200 else close
        
        # Trend alignment
        trend_aligned = 1 if close > ma_50 > ma_200 else 0
        
        # ATR (normalized)
        if idx >= 15:
            atr_14 = np.mean(np.abs(np.diff(prices[idx-15:idx]))) / close
        else:
            atr_14 = 0
        
        # 50-day avg volume
        vol_50d = np.mean(volumes[max(0, idx-50):idx])
        
        # Look for consolidation base
        base_length = BASE_MIN_DAYS
        base_range = 0
        breakout_vol_ratio = volumes[idx] / vol_50d if vol_50d > 0 else 1
        vol_dryup = 1.0
        vol_trend = 1.0
        up_days_pct = 0.5
        
        for bl in range(BASE_MIN_DAYS, min(120, idx - 10) + 1, 5):
            base_start = idx - bl
            base_prices = prices[base_start:idx]
            ceiling = np.max(base_prices)
            floor = np.min(base_prices)
            br = (ceiling - floor) / floor if floor > 0 else 0
            
            if br <= BASE_MAX_DRIFT:
                base_length = bl
                base_range = br
                
                # Volume dry-up
                if bl >= 20:
                    recent_vol = np.mean(volumes[idx-10:idx])
                    earlier_vol = np.mean(volumes[base_start:base_start+10])
                    vol_dryup = recent_vol / earlier_vol if earlier_vol > 0 else 1.0
                    
                    vol_first = np.mean(volumes[base_start:base_start+bl//2])
                    vol_second = np.mean(volumes[base_start+bl//2:idx])
                    vol_trend = vol_second / vol_first if vol_first > 0 else 1.0
                
                base_returns = np.diff(prices[base_start:idx]) / prices[base_start:idx-1]
                up_days_pct = np.sum(base_returns > 0) / len(base_returns) if len(base_returns) > 0 else 0.5
                break
        
        # 52W proximity
        if idx >= 252:
            high_52w = np.max(prices[idx-252:idx])
        else:
            high_52w = np.max(prices[:idx])
        proximity_52w = close / high_52w if high_52w > 0 else 1.0
        
        # 3-month return
        if idx >= 63:
            return_3mo = (close / prices[idx-63]) - 1
        else:
            return_3mo = 0
        
        # Volatility compression
        if idx >= 50:
            recent_atr = np.mean(np.abs(np.diff(prices[idx-10:idx])))
            longer_atr = np.mean(np.abs(np.diff(prices[idx-50:idx])))
            vol_compression = recent_atr / longer_atr if longer_atr > 0 else 1.0
        else:
            vol_compression = 1.0
        
        return {
            'close_to_ma20': close / ma_20 if ma_20 > 0 else 1,
            'close_to_ma50': close / ma_50 if ma_50 > 0 else 1,
            'close_to_ma200': close / ma_200 if ma_200 > 0 else 1,
            'trend_aligned': trend_aligned,
            'atr_14': atr_14,
            'vol_dryup_ratio': vol_dryup,
            'vol_compression': vol_compression,
            'proximity_52w': proximity_52w,
            'return_3mo': return_3mo,
            'up_days_pct': up_days_pct,
            'vol_trend_in_base': vol_trend,
            'base_length': base_length,
            'base_range': base_range,
            'breakout_vol_ratio': breakout_vol_ratio,
        }
    except Exception as e:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ticker', help='Score single ticker')
    args = parser.parse_args()
    
    print('🧠 IQ Edge Score — Loading model...')
    model = load_model()
    
    if args.ticker:
        # Single ticker mode
        ticker = args.ticker.upper()
        features = compute_features_for_ticker(ticker)
        if features:
            X = np.array([[features[c] for c in FEATURE_COLS]])
            prob = model.predict_proba(X)[0][1]
            print(f'\n{ticker}: IQ Edge Raw = {prob:.4f} ({prob*100:.1f}%)')
            print(f'Features: {json.dumps({k: round(v, 4) for k, v in features.items()}, indent=2)}')
        else:
            print(f'Could not compute features for {ticker}')
        return
    
    # Batch mode: score all stocks
    with open(STOCKS_FILE) as f:
        data = json.load(f)
    
    stocks = data.get('stocks', {})
    tickers = sorted(stocks.keys())
    print(f'   Scoring {len(tickers)} stocks...')
    
    # Download data in batches for speed
    all_features = {}
    batch_size = 50
    
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        pct = i / len(tickers) * 100
        print(f'[{pct:5.1f}%] Downloading batch {i//batch_size + 1}...')
        
        try:
            batch_str = ' '.join(batch)
            df = yf.download(batch_str, period='1y', interval='1d',
                           group_by='ticker', auto_adjust=True,
                           threads=True, progress=False)
            
            for ticker in batch:
                try:
                    if len(batch) == 1:
                        tdf = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                    else:
                        if ticker not in df.columns.get_level_values(0):
                            continue
                        tdf = df[ticker][['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                    
                    tdf = tdf.dropna(subset=['Close'])
                    if len(tdf) >= 100:
                        features = compute_features_for_ticker(ticker, tdf)
                        if features:
                            all_features[ticker] = features
                except:
                    pass
        except Exception as e:
            print(f'  Batch error: {e}')
        
        time.sleep(0.5)
    
    print(f'\n   Computed features for {len(all_features)} stocks')
    
    # Score all
    scored_tickers = sorted(all_features.keys())
    X = np.array([[all_features[t][c] for c in FEATURE_COLS] for t in scored_tickers])
    probs = model.predict_proba(X)[:, 1]
    
    # Convert to percentile (1-99)
    from scipy.stats import rankdata
    ranks = rankdata(probs)
    percentiles = np.clip(np.round(ranks / len(ranks) * 99), 1, 99).astype(int)
    
    # Update all_stocks.json
    for i, ticker in enumerate(scored_tickers):
        stocks[ticker]['iq_edge'] = int(percentiles[i])
        stocks[ticker]['iq_edge_raw'] = round(float(probs[i]), 6)
    
    # Stats
    top_20 = sorted(zip(scored_tickers, probs, percentiles), key=lambda x: -x[1])[:20]
    
    data['stocks'] = stocks
    data['iq_edge_updated'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
    
    with open(STOCKS_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f'\n🏆 Top 20 IQ Edge Scores:')
    for ticker, prob, pct in top_20:
        sector = stocks[ticker].get('sector', '')
        ewros = stocks[ticker].get('ewros_score', '?')
        print(f'   {ticker:6s}  IQ Edge: {pct:2d}  (prob: {prob:.4f})  EWROS: {ewros}  {sector}')
    
    print(f'\n✅ Updated {len(scored_tickers)} stocks with IQ Edge Score')
    print(f'   Saved to {STOCKS_FILE}')


if __name__ == '__main__':
    main()
