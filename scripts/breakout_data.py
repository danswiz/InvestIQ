#!/usr/bin/env python3
"""
Breakout ML — Step 1: Download 5 years of daily OHLCV for all stocks.
Saves to data/historical_ohlcv.parquet (~50-100MB)

Usage:
    python3 scripts/breakout_data.py              # Full download
    python3 scripts/breakout_data.py --limit 50   # Test with 50 stocks
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime

import pandas as pd
import yfinance as yf

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
STOCKS_FILE = os.path.join(DATA_DIR, 'all_stocks.json')
OUTPUT_FILE = os.path.join(DATA_DIR, 'historical_ohlcv.parquet')

def get_tickers():
    """Get all tickers from all_stocks.json"""
    with open(STOCKS_FILE) as f:
        data = json.load(f)
    return sorted(data.get('stocks', {}).keys())

def download_batch(tickers, batch_size=50):
    """Download OHLCV in batches using yfinance batch download"""
    all_data = []
    total = len(tickers)
    
    for i in range(0, total, batch_size):
        batch = tickers[i:i+batch_size]
        batch_str = ' '.join(batch)
        pct = (i / total) * 100
        print(f'[{pct:5.1f}%] Downloading batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size} ({len(batch)} tickers)...')
        
        try:
            df = yf.download(batch_str, period='5y', interval='1d', 
                           group_by='ticker', auto_adjust=True, 
                           threads=True, progress=False)
            
            if len(batch) == 1:
                # Single ticker returns flat columns
                ticker = batch[0]
                if not df.empty:
                    df_copy = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                    df_copy['Ticker'] = ticker
                    df_copy = df_copy.reset_index()
                    all_data.append(df_copy)
            else:
                # Multiple tickers returns multi-level columns
                for ticker in batch:
                    try:
                        if ticker in df.columns.get_level_values(0):
                            tdf = df[ticker][['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                            tdf = tdf.dropna(subset=['Close'])
                            if len(tdf) >= 200:  # Need at least 200 days
                                tdf['Ticker'] = ticker
                                tdf = tdf.reset_index()
                                all_data.append(tdf)
                    except Exception as e:
                        print(f'  Warning: {ticker} — {e}')
        except Exception as e:
            print(f'  Batch error: {e}')
        
        time.sleep(1)  # Rate limit respect
    
    return all_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, help='Limit number of tickers')
    args = parser.parse_args()
    
    tickers = get_tickers()
    if args.limit:
        tickers = tickers[:args.limit]
    
    print(f'📊 Downloading 5yr daily OHLCV for {len(tickers)} stocks...')
    start = time.time()
    
    all_data = download_batch(tickers)
    
    if not all_data:
        print('❌ No data downloaded')
        sys.exit(1)
    
    # Combine into single DataFrame
    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.rename(columns={'Date': 'date', 'Open': 'open', 'High': 'high', 
                                         'Low': 'low', 'Close': 'close', 'Volume': 'volume',
                                         'Ticker': 'ticker'})
    
    # Sort by ticker and date
    combined = combined.sort_values(['ticker', 'date']).reset_index(drop=True)
    
    # Save as parquet (much smaller than CSV)
    combined.to_parquet(OUTPUT_FILE, index=False)
    
    elapsed = time.time() - start
    unique_tickers = combined['ticker'].nunique()
    total_rows = len(combined)
    file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    
    print(f'\n✅ Done in {elapsed:.0f}s')
    print(f'   Tickers: {unique_tickers}')
    print(f'   Total rows: {total_rows:,}')
    print(f'   Date range: {combined["date"].min()} → {combined["date"].max()}')
    print(f'   File: {OUTPUT_FILE} ({file_size:.1f} MB)')

if __name__ == '__main__':
    main()
