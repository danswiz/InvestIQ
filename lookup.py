#!/usr/bin/env python3
"""
InvestIQ Lookup Utility
Reduces token costs by querying local JSON files instead of the bot reading them.
"""
import json
import sys
import os

def lookup_ticker(ticker):
    ticker = ticker.upper()
    try:
        # Try all_stocks first (contains full details)
        if os.path.exists('all_stocks.json'):
            with open('all_stocks.json', 'r') as f:
                data = json.load(f)
                stock = data['stocks'].get(ticker)
                if stock:
                    return stock
        
        # Fallback to top_stocks
        if os.path.exists('top_stocks.json'):
            with open('top_stocks.json', 'r') as f:
                data = json.load(f)
                stocks = data.get('stocks', [])
                for s in stocks:
                    if s['ticker'] == ticker:
                        return s
        return None
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 lookup.py TICKER")
        sys.exit(1)
    
    result = lookup_ticker(sys.argv[1])
    if result:
        print(json.dumps(result, indent=2))
    else:
        print(f"Ticker {sys.argv[1]} not found in local cache.")
