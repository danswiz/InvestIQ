#!/usr/bin/env python3
"""
InvestIQ Website Scan - Uses BreakoutRater for consistent scoring
Updates top_stocks.json for website display
"""
import json
import os
import sqlite3
import sys
from datetime import datetime

# Import the actual rater
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rater import BreakoutRater, CriterionResult

DB_PATH = os.path.join(os.getcwd(), 'market_data.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def rate_stock_consistent(symbol, rater, conn):
    """Rate stock using BreakoutRater with DB data"""
    try:
        import pandas as pd
        
        # Get price history from DB
        prices = pd.read_sql_query(
            f"SELECT * FROM prices WHERE symbol = '{symbol}' ORDER BY date",
            conn
        )
        if len(prices) < 130:
            return None
        
        # Get fundamentals from DB
        fund_df = pd.read_sql_query(
            f"SELECT data FROM fundamentals WHERE symbol = '{symbol}'",
            conn
        )
        info = json.loads(fund_df.iloc[0]['data']) if not fund_df.empty else {}
        
        # Build mock hist DataFrame like yfinance
        hist = prices.set_index('date')
        hist.index = pd.to_datetime(hist.index)
        
        # Build mock info dict
        mock_info = {
            'sector': info.get('sector', 'Unknown'),
            'shortName': info.get('shortName', symbol),
            'revenueGrowth': info.get('revenueGrowth'),
            'earningsGrowth': info.get('earningsGrowth'),
            'operatingMargins': info.get('operatingMargins'),
            'freeCashflow': info.get('freeCashflow'),
            'totalDebt': info.get('totalDebt'),
            'totalCash': info.get('totalCash'),
            'marketCap': info.get('marketCap', 0)
        }
        
        # Use BreakoutRater logic with DB data - HIGH POTENTIAL REWEIGHTING
        close = hist['close']
        sma50 = close.rolling(50).mean().iloc[-1]
        sma200 = close.rolling(200).mean().iloc[-1]
        current_price = close.iloc[-1]
        
        results = []
        
        # 1. Breakout Pattern (25 pts) - CORE TIMING SIGNAL
        window = hist.iloc[-130:-5]
        high_1 = window.iloc[:65]['high'].max()
        high_2 = window.iloc[65:]['high'].max()
        drift = (high_2 - high_1) / high_1
        base_ceiling = max(high_1, high_2)
        dist = (base_ceiling - current_price) / base_ceiling
        passed_bo = bool((drift < 0.10) and (dist < 0.05))
        results.append(CriterionResult("Breakout Pattern", "Breakout", passed_bo, "", "", 25 if passed_bo else 0))
        
        # 2. Consolidation (12 pts) - BASE QUALITY
        depth = (window['high'].max() - window['low'].min()) / window['high'].max()
        passed_con = bool(depth < 0.45)
        results.append(CriterionResult("Consolidation", "Breakout", passed_con, "", "", 12 if passed_con else 0))
        
        # 3. Volume Dry-up (10 pts) - INSTITUTIONAL ACCUMULATION
        v5 = hist['volume'].tail(5).mean()
        v50 = hist['volume'].tail(50).mean()
        passed_vol = bool(v5 < (v50 * 1.2))
        results.append(CriterionResult("Volume Dry-up", "Breakout", passed_vol, "", "", 10 if passed_vol else 0))
        
        # 4. Trend Alignment (8 pts) - DIRECTION CONFIRMATION
        price_above_50 = bool(current_price > sma50)
        if pd.notna(sma200):
            passed_trend = bool(price_above_50 and (sma50 > sma200))
        else:
            sma50_prev = close.rolling(50).mean().iloc[-5]
            passed_trend = bool(price_above_50 and sma50 > sma50_prev)
        results.append(CriterionResult("Trend Alignment", "Momentum", passed_trend, "", "", 8 if passed_trend else 0))
        
        # 5. Industry Strength (8 pts) - SECTOR TAILWIND
        sector = mock_info.get('sector', '')
        strong_sectors = ['Technology', 'Healthcare', 'Communication Services']
        passed_industry = sector in strong_sectors
        results.append(CriterionResult("Industry Strength", "Context", passed_industry, "", "", 8 if passed_industry else 0))
        
        # 6. Sales Growth (5 pts) - GROWTH ENGINE
        rev_g = mock_info.get('revenueGrowth')
        passed_rev = bool(rev_g is not None and rev_g > 0.1)
        results.append(CriterionResult("Sales Growth", "Growth", passed_rev, "", "", 5 if passed_rev else 0))
        
        # 7. Operating Margin (5 pts) - QUALITY (reduced)
        margin = mock_info.get('operatingMargins')
        passed_margin = bool(margin is not None and margin > 0.10)
        results.append(CriterionResult("Operating Margin", "Quality", passed_margin, "", "", 5 if passed_margin else 0))
        
        # 8. FCF Quality (3 pts) - SAFETY (reduced)
        fcf = mock_info.get('freeCashflow')
        passed_fcf = bool(fcf is not None and fcf > 0)
        results.append(CriterionResult("FCF Quality", "Quality", passed_fcf, "", "", 3 if passed_fcf else 0))
        
        # 9. Earnings Growth (2 pts) - LAGGING (reduced)
        earn_g = mock_info.get('earningsGrowth')
        passed_earn = bool(earn_g is not None and earn_g > 0.15)
        results.append(CriterionResult("Earnings Growth", "Growth", passed_earn, "", "", 2 if passed_earn else 0))
        
        # 10. Debt Safety (2 pts) - SAFETY (reduced)
        debt = mock_info.get('totalDebt', 0)
        cash = mock_info.get('totalCash', 0)
        passed_debt = bool(cash > debt * 0.5)
        results.append(CriterionResult("Debt Safety", "Safety", passed_debt, "", "", 2 if passed_debt else 0))
        
        # Calculate total
        total = sum(r.points for r in results)
        
        # Grade (matching rater.py - TIGHTER scale)
        # A=60+ (75% of max), B=45-59, C=30-44, D=15-29, F=<15
        if total >= 60: grade = 'A'
        elif total >= 45: grade = 'B'
        elif total >= 30: grade = 'C'
        elif total >= 15: grade = 'D'
        else: grade = 'F'
        
        return {
            'ticker': symbol,
            'name': mock_info.get('shortName', symbol)[:35],
            'sector': sector,
            'score': total,
            'grade': grade,
            'total': total
        }
        
    except Exception as e:
        return None

def run_scan():
    print("🚀 Starting InvestIQ Website Scan (Consistent Scoring)...")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get all tickers
    c.execute('SELECT DISTINCT symbol FROM prices')
    tickers = [row[0] for row in c.fetchall()]
    
    print(f"Found {len(tickers)} tickers in database")
    
    results = []
    for i, ticker in enumerate(tickers, 1):
        data = rate_stock_consistent(ticker, None, conn)
        if data:
            results.append(data)
        
        if i % 100 == 0:
            print(f"  Processed {i}/{len(tickers)}...")
    
    conn.close()
    
    # Sort by score
    results.sort(key=lambda x: x['total'], reverse=True)
    
    # Save
    output = {
        'last_scan': datetime.now().strftime('%Y-%m-%d %H:%M PST'),
        'stocks': results[:50]
    }
    
    with open('top_stocks.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved {len(results[:50])} stocks to top_stocks.json")
    print(f"   Top 5: {', '.join([s['ticker'] + ' ' + s['grade'] for s in results[:5]])}")

if __name__ == '__main__':
    run_scan()
