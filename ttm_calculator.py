#!/usr/bin/env python3
"""
TTM Revenue Calculator - Calculate trailing twelve months growth
"""
import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'market_data.db')

def get_ttm_growth(symbol):
    """
    Calculate TTM revenue growth vs prior year TTM
    Returns: (current_ttm_growth, prior_ttm_growth) or (None, None)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get last 8 quarters of revenue
        c.execute('''
            SELECT year, quarter, revenue FROM quarterly_revenue
            WHERE symbol = ? AND revenue IS NOT NULL
            ORDER BY year DESC, quarter DESC
            LIMIT 8
        ''', (symbol,))
        rows = c.fetchall()
        conn.close()
        
        if len(rows) < 8:
            return None, None
        
        # rows[0:4] = most recent 4 quarters (current TTM)
        # rows[4:8] = prior 4 quarters (prior TTM)
        
        ttm_current = sum(r[2] for r in rows[0:4])
        ttm_prior = sum(r[2] for r in rows[4:8])
        
        if ttm_prior <= 0:
            return None, None
        
        growth_current = (ttm_current - ttm_prior) / ttm_prior
        
        # For prior TTM growth, we'd need 12 quarters... 
        # For now, return current growth only
        # Prior year comparison is already handled by the 4-quarter gap
        
        return growth_current, None
        
    except Exception as e:
        return None, None

def get_ttm_growth_strict(symbol):
    """
    Strict TTM: Current TTM vs 1-year-ago TTM
    Both must be >= 10% to pass
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Get last 8 quarters
        c.execute('''
            SELECT year, quarter, revenue FROM quarterly_revenue
            WHERE symbol = ? AND revenue IS NOT NULL
            ORDER BY year DESC, quarter DESC
            LIMIT 8
        ''', (symbol,))
        rows = c.fetchall()
        conn.close()
        
        if len(rows) < 8:
            return None, None  # Not enough data
        
        # TTM Current = sum of most recent 4 quarters
        ttm_current = sum(r[2] for r in rows[0:4])
        
        # TTM Prior Year = sum of quarters 5-8 (4 quarters ago)
        ttm_prior_year = sum(r[2] for r in rows[4:8])
        
        if ttm_prior_year <= 0:
            return None, None
        
        growth_current = (ttm_current - ttm_prior_year) / ttm_prior_year
        
        # For "prior year" check, we'd need TTM from 2 years ago...
        # Let's also calculate TTM 1 year before prior
        # That requires 12 quarters total
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            SELECT year, quarter, revenue FROM quarterly_revenue
            WHERE symbol = ? AND revenue IS NOT NULL
            ORDER BY year DESC, quarter DESC
            LIMIT 12
        ''', (symbol,))
        all_rows = c.fetchall()
        conn.close()
        
        if len(all_rows) >= 12:
            # TTM from 2 years ago = quarters 9-12
            ttm_2years_ago = sum(r[2] for r in all_rows[8:12])
            if ttm_2years_ago > 0:
                growth_prior = (ttm_prior_year - ttm_2years_ago) / ttm_2years_ago
                return growth_current, growth_prior
        
        return growth_current, None
        
    except Exception as e:
        return None, None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
        current, prior = get_ttm_growth_strict(ticker)
        print(f"{ticker}:")
        print(f"  Current TTM Growth: {current*100:.1f}%" if current else "  Current: N/A")
        print(f"  Prior TTM Growth: {prior*100:.1f}%" if prior else "  Prior: N/A")
    else:
        print("Usage: python ttm_calculator.py TICKER")
