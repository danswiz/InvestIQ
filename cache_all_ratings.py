#!/usr/bin/env python3
"""
Calculate ratings for ALL stocks and cache to DB
Run after nightly cache refresh
"""
import sqlite3
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rater import BreakoutRater

DB_PATH = os.path.join(os.getcwd(), 'market_data.db')

def cache_all_ratings():
    print(f"🚀 Calculating ratings for all stocks... {datetime.now().strftime('%H:%M:%S')}")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all tickers with price data
    c.execute('SELECT DISTINCT symbol FROM prices')
    tickers = [row[0] for row in c.fetchall()]
    
    print(f"Found {len(tickers)} tickers")
    
    # Create ratings table if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS stock_ratings (
            symbol TEXT PRIMARY KEY,
            name TEXT,
            sector TEXT,
            industry TEXT,
            score INTEGER,
            grade TEXT,
            technical_score INTEGER,
            growth_score INTEGER,
            quality_score INTEGER,
            context_score INTEGER,
            market_cap REAL,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    rater = BreakoutRater()
    success = 0
    failed = []
    
    for i, ticker in enumerate(tickers, 1):
        try:
            result = rater.rate_stock(ticker)
            
            if result and 'error' not in result:
                c.execute('''
                    INSERT OR REPLACE INTO stock_ratings 
                    (symbol, name, sector, industry, score, grade, 
                     technical_score, growth_score, quality_score, context_score, 
                     market_cap, calculated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    result['ticker'],
                    result['name'],
                    result['sector'],
                    result.get('industry', 'N/A'),
                    result['score'],
                    result['grade'],
                    result.get('technical_score', 0),
                    result.get('growth_score', 0),
                    result.get('quality_score', 0),
                    result.get('context_score', 0),
                    result.get('market_cap', 0)
                ))
                success += 1
            else:
                failed.append(ticker)
                
        except Exception as e:
            failed.append(ticker)
        
        if i % 50 == 0:
            print(f"  [{i}/{len(tickers)}] {success} rated, {len(failed)} failed")
            try:
                conn.commit()
            except:
                pass
    
    try:
        conn.commit()
    except:
        pass
    conn.close()
    
    print(f"\n✅ Rating cache complete!")
    print(f"   Success: {success}/{len(tickers)}")
    print(f"   Failed: {len(failed)}")
    if failed[:5]:
        print(f"   Sample failures: {', '.join(failed[:5])}")

if __name__ == '__main__':
    cache_all_ratings()
