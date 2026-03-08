#!/usr/bin/env python3
"""
Breakout ML — Step 2: Identify breakout events and label outcomes.

A breakout is detected when:
  1. Price crosses above the ceiling of a consolidation base (20-60 day range)
  2. Volume on breakout day is >= 1.5x the 50-day average

Labels:
  - "double": stock gained >= 100% within 12 months of breakout
  - "big_win": gained >= 50% within 12 months
  - "win": gained >= 25% within 12 months  
  - "fail": didn't gain 25% or pulled back > 15% from breakout

Features captured at breakout moment:
  - 90 days of OHLCV (raw time series for CNN/LSTM)
  - Derived technical features (for XGBoost)
  - Industry/sector context

Usage:
    python3 scripts/breakout_labeler.py
    python3 scripts/breakout_labeler.py --limit 50   # test
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
OHLCV_FILE = os.path.join(DATA_DIR, 'historical_ohlcv.parquet')
STOCKS_FILE = os.path.join(DATA_DIR, 'all_stocks.json')
OUTPUT_FILE = os.path.join(DATA_DIR, 'breakout_events.parquet')
TIMESERIES_FILE = os.path.join(DATA_DIR, 'breakout_timeseries.npz')

# Parameters
BASE_MIN_DAYS = 20          # Minimum consolidation length
BASE_MAX_DAYS = 120         # Maximum consolidation length  
BASE_MAX_DRIFT = 0.15       # Max price range in base (15%)
VOLUME_THRESHOLD = 1.5      # Breakout volume must be >= 1.5x 50d avg
LOOKBACK_DAYS = 90          # Days of OHLCV to capture before breakout
FORWARD_DAYS = 252          # 12 months forward to measure outcome
MIN_HISTORY = 150           # Need at least 150 days before breakout

# Outcome thresholds
DOUBLE_THRESHOLD = 1.00     # 100% gain
BIG_WIN_THRESHOLD = 0.50    # 50% gain
WIN_THRESHOLD = 0.25        # 25% gain
MAX_DRAWDOWN = 0.15         # 15% max pullback before recovery


def detect_consolidation(prices, volumes, idx, vol_50d):
    """Check if there's a consolidation base ending at idx."""
    if idx < BASE_MIN_DAYS + 10:
        return None
    
    # Look back for a flat base
    for base_len in range(BASE_MIN_DAYS, min(BASE_MAX_DAYS, idx - 10) + 1, 5):
        base_start = idx - base_len
        base_prices = prices[base_start:idx]
        
        if len(base_prices) < BASE_MIN_DAYS:
            continue
        
        ceiling = np.max(base_prices)
        floor = np.min(base_prices)
        base_range = (ceiling - floor) / floor
        
        # Base must be relatively flat
        if base_range > BASE_MAX_DRIFT:
            continue
        
        # Current price must be near/above ceiling
        current = prices[idx]
        if current < ceiling * 0.98:  # Within 2% of ceiling
            continue
        
        # Volume on breakout day should be elevated
        current_vol = volumes[idx]
        if vol_50d > 0 and current_vol >= VOLUME_THRESHOLD * vol_50d:
            return {
                'base_length': base_len,
                'base_range': base_range,
                'ceiling': ceiling,
                'floor': floor,
                'breakout_volume_ratio': current_vol / vol_50d if vol_50d > 0 else 0
            }
    
    return None


def compute_features(prices, volumes, idx, base_info, sector_data=None):
    """Compute derived features at the breakout moment."""
    close = prices[idx]
    
    # Moving averages
    ma_20 = np.mean(prices[max(0, idx-20):idx]) if idx >= 20 else close
    ma_50 = np.mean(prices[max(0, idx-50):idx]) if idx >= 50 else close
    ma_200 = np.mean(prices[max(0, idx-200):idx]) if idx >= 200 else close
    
    # Trend alignment
    trend_aligned = 1 if close > ma_50 > ma_200 else 0
    
    # ATR (14-day)
    if idx >= 15:
        highs = prices[idx-14:idx]  # Simplified - using close only
        atr_14 = np.mean(np.abs(np.diff(prices[idx-15:idx])))
    else:
        atr_14 = 0
    
    # Volume dry-up: ratio of recent volume to earlier volume in base
    base_start = idx - base_info['base_length']
    if base_info['base_length'] >= 20:
        recent_vol = np.mean(volumes[idx-10:idx]) if idx >= 10 else volumes[idx]
        earlier_vol = np.mean(volumes[base_start:base_start+10])
        vol_dryup = recent_vol / earlier_vol if earlier_vol > 0 else 1.0
    else:
        vol_dryup = 1.0
    
    # 52-week high proximity
    if idx >= 252:
        high_52w = np.max(prices[idx-252:idx])
        proximity_52w = close / high_52w
    else:
        high_52w = np.max(prices[:idx])
        proximity_52w = close / high_52w if high_52w > 0 else 1.0
    
    # Price momentum (3-month return)
    if idx >= 63:
        return_3mo = (close / prices[idx-63]) - 1
    else:
        return_3mo = 0
    
    # Volatility compression: recent ATR vs longer-term ATR
    if idx >= 50:
        recent_atr = np.mean(np.abs(np.diff(prices[idx-10:idx])))
        longer_atr = np.mean(np.abs(np.diff(prices[idx-50:idx])))
        vol_compression = recent_atr / longer_atr if longer_atr > 0 else 1.0
    else:
        vol_compression = 1.0
    
    # Up days vs down days in base
    base_returns = np.diff(prices[base_start:idx]) / prices[base_start:idx-1]
    up_days_pct = np.sum(base_returns > 0) / len(base_returns) if len(base_returns) > 0 else 0.5
    
    # Volume trend in base (is volume declining? good sign)
    if base_info['base_length'] >= 20:
        vol_first_half = np.mean(volumes[base_start:base_start + base_info['base_length']//2])
        vol_second_half = np.mean(volumes[base_start + base_info['base_length']//2:idx])
        vol_trend = vol_second_half / vol_first_half if vol_first_half > 0 else 1.0
    else:
        vol_trend = 1.0
    
    return {
        'close_to_ma20': close / ma_20 if ma_20 > 0 else 1,
        'close_to_ma50': close / ma_50 if ma_50 > 0 else 1,
        'close_to_ma200': close / ma_200 if ma_200 > 0 else 1,
        'trend_aligned': trend_aligned,
        'atr_14': atr_14 / close if close > 0 else 0,  # Normalized
        'vol_dryup_ratio': vol_dryup,
        'vol_compression': vol_compression,
        'proximity_52w': proximity_52w,
        'return_3mo': return_3mo,
        'up_days_pct': up_days_pct,
        'vol_trend_in_base': vol_trend,
        'base_length': base_info['base_length'],
        'base_range': base_info['base_range'],
        'breakout_vol_ratio': base_info['breakout_volume_ratio'],
    }


def label_outcome(prices, idx, breakout_price):
    """Label the outcome of a breakout: double, big_win, win, or fail."""
    forward = prices[idx+1:idx+1+FORWARD_DAYS]
    if len(forward) < 20:
        return 'unknown', 0, 0  # Not enough forward data
    
    max_gain = (np.max(forward) / breakout_price) - 1
    max_drawdown = (breakout_price - np.min(forward[:60])) / breakout_price  # Drawdown in first 60 days
    
    # Check for early failure (pulled back >15% in first 60 days before any big gain)
    early_min = np.min(forward[:min(60, len(forward))])
    early_drawdown = (breakout_price - early_min) / breakout_price
    
    if max_gain >= DOUBLE_THRESHOLD:
        label = 'double'
    elif max_gain >= BIG_WIN_THRESHOLD:
        label = 'big_win'
    elif max_gain >= WIN_THRESHOLD:
        label = 'win'
    else:
        label = 'fail'
    
    # If early drawdown was severe, might still be a fail even with later recovery
    if early_drawdown > MAX_DRAWDOWN and max_gain < BIG_WIN_THRESHOLD:
        label = 'fail'
    
    return label, max_gain, max_drawdown


def get_sector_data():
    """Load sector/industry info from all_stocks.json"""
    try:
        with open(STOCKS_FILE) as f:
            data = json.load(f)
        return {t: {'sector': s.get('sector', ''), 'industry': s.get('industry', '')} 
                for t, s in data.get('stocks', {}).items()}
    except:
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, help='Limit tickers to process')
    args = parser.parse_args()
    
    print('📊 Loading historical OHLCV data...')
    df = pd.read_parquet(OHLCV_FILE)
    
    sector_data = get_sector_data()
    tickers = sorted(df['ticker'].unique())
    if args.limit:
        tickers = tickers[:args.limit]
    
    print(f'   {len(tickers)} tickers, {len(df):,} total rows')
    print(f'   Looking for breakout events...\n')
    
    events = []
    timeseries_list = []
    
    for ti, ticker in enumerate(tickers):
        if ti % 100 == 0:
            print(f'[{ti/len(tickers)*100:5.1f}%] Processing {ticker}... ({len(events)} events found so far)')
        
        tdf = df[df['ticker'] == ticker].sort_values('date').reset_index(drop=True)
        
        if len(tdf) < MIN_HISTORY + FORWARD_DAYS:
            continue
        
        prices = tdf['close'].values
        volumes = tdf['volume'].values
        dates = tdf['date'].values
        
        # Skip through the data looking for breakouts
        last_breakout_idx = -60  # Prevent overlapping breakouts
        
        for idx in range(MIN_HISTORY, len(tdf) - 20):  # Need some forward data
            # Skip if too close to last breakout
            if idx - last_breakout_idx < 60:
                continue
            
            # Compute 50-day average volume
            vol_50d = np.mean(volumes[max(0, idx-50):idx])
            
            # Detect consolidation base
            base_info = detect_consolidation(prices, volumes, idx, vol_50d)
            if base_info is None:
                continue
            
            # Found a breakout! Compute features
            features = compute_features(prices, volumes, idx, base_info)
            
            # Label outcome
            label, max_gain, max_dd = label_outcome(prices, idx, prices[idx])
            
            # Sector/industry
            sec = sector_data.get(ticker, {})
            
            # Capture 90-day OHLCV time series (normalized)
            ts_start = max(0, idx - LOOKBACK_DAYS)
            ts_prices = prices[ts_start:idx+1]
            ts_volumes = volumes[ts_start:idx+1]
            
            # Normalize: prices as % of breakout price, volume as multiple of 50d avg
            breakout_price = prices[idx]
            norm_prices = ts_prices / breakout_price
            norm_volumes = ts_volumes / vol_50d if vol_50d > 0 else ts_volumes
            
            # Pad to exactly LOOKBACK_DAYS+1 if shorter
            target_len = LOOKBACK_DAYS + 1
            if len(norm_prices) < target_len:
                pad_len = target_len - len(norm_prices)
                norm_prices = np.pad(norm_prices, (pad_len, 0), mode='edge')
                norm_volumes = np.pad(norm_volumes, (pad_len, 0), mode='edge')
            
            # OHLCV time series: [open, high, low, close, volume] × 91 days
            # We only have close+volume in normalized form; use close for OHLC proxy
            ts_open = prices[ts_start:idx+1] / breakout_price
            ts_high = prices[ts_start:idx+1] / breakout_price  # Simplified
            ts_low = prices[ts_start:idx+1] / breakout_price
            ts_close = norm_prices
            ts_vol = norm_volumes
            
            # Actually get real OHLC
            real_open = tdf['open'].values[ts_start:idx+1] / breakout_price
            real_high = tdf['high'].values[ts_start:idx+1] / breakout_price
            real_low = tdf['low'].values[ts_start:idx+1] / breakout_price
            
            # Pad
            if len(real_open) < target_len:
                pad_len = target_len - len(real_open)
                real_open = np.pad(real_open, (pad_len, 0), mode='edge')
                real_high = np.pad(real_high, (pad_len, 0), mode='edge')
                real_low = np.pad(real_low, (pad_len, 0), mode='edge')
                ts_close = np.pad(ts_close, (pad_len, 0), mode='edge') if len(ts_close) < target_len else ts_close
                ts_vol = np.pad(ts_vol, (pad_len, 0), mode='edge') if len(ts_vol) < target_len else ts_vol
            
            # Stack: shape (91, 5) — OHLCV
            ts_array = np.stack([real_open[:target_len], real_high[:target_len], 
                                  real_low[:target_len], ts_close[:target_len], 
                                  ts_vol[:target_len]], axis=1)
            timeseries_list.append(ts_array)
            
            event = {
                'ticker': ticker,
                'date': pd.Timestamp(dates[idx]),
                'breakout_price': breakout_price,
                'label': label,
                'max_gain_pct': round(max_gain * 100, 1),
                'max_drawdown_pct': round(max_dd * 100, 1),
                'sector': sec.get('sector', ''),
                'industry': sec.get('industry', ''),
                **features
            }
            events.append(event)
            last_breakout_idx = idx
    
    print(f'\n✅ Found {len(events)} breakout events')
    
    if not events:
        print('❌ No breakout events found')
        sys.exit(1)
    
    # Save events (tabular features)
    events_df = pd.DataFrame(events)
    events_df.to_parquet(OUTPUT_FILE, index=False)
    
    # Save time series
    ts_array = np.array(timeseries_list)  # Shape: (N, 91, 5)
    np.savez_compressed(TIMESERIES_FILE, timeseries=ts_array)
    
    # Print summary
    labels = events_df['label'].value_counts()
    print(f'\n📊 Label Distribution:')
    for label, count in labels.items():
        pct = count / len(events_df) * 100
        print(f'   {label:10s}: {count:5d} ({pct:.1f}%)')
    
    print(f'\n📊 Top sectors for doubles:')
    doubles = events_df[events_df['label'] == 'double']
    if len(doubles) > 0:
        sector_counts = doubles['sector'].value_counts().head(5)
        for sec, count in sector_counts.items():
            print(f'   {sec}: {count}')
    
    print(f'\n📁 Files saved:')
    print(f'   {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE)/1024:.0f} KB)')
    print(f'   {TIMESERIES_FILE} ({os.path.getsize(TIMESERIES_FILE)/(1024*1024):.1f} MB)')
    
    # Feature stats for doubles vs fails
    print(f'\n📊 Feature Comparison (Doubles vs Fails):')
    fails = events_df[events_df['label'] == 'fail']
    feature_cols = ['breakout_vol_ratio', 'base_length', 'base_range', 'vol_dryup_ratio',
                    'trend_aligned', 'proximity_52w', 'return_3mo', 'vol_compression']
    for col in feature_cols:
        d_mean = doubles[col].mean() if len(doubles) > 0 else 0
        f_mean = fails[col].mean() if len(fails) > 0 else 0
        print(f'   {col:25s}  doubles={d_mean:7.3f}  fails={f_mean:7.3f}')


if __name__ == '__main__':
    main()
