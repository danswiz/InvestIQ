#!/usr/bin/env python3
"""
Portfolio Loader - Loads Dan's actual holdings from MY_PORTFOLIO.md
Usage: python3 load_portfolio.py [basket_name]
       python3 load_portfolio.py all  # Loads all individual stocks
"""

import re
import sys

def load_portfolio(basket_filter=None):
    """Load portfolio holdings from MY_PORTFOLIO.md"""
    
    with open("/Users/dansmacmini/.openclaw/workspace/MY_PORTFOLIO.md", "r") as f:
        content = f.read()
    
    portfolios = {}
    current_basket = None
    
    for line in content.split('\n'):
        # Check for basket header
        if line.startswith('## BASKET'):
            match = re.search(r'## BASKET \d+: ([^(]+)', line)
            if match:
                current_basket = match.group(1).strip()
                portfolios[current_basket] = []
        # Check for ticker (simple uppercase letters, 1-5 chars)
        elif current_basket and line.strip() and not line.startswith('#'):
            ticker = line.strip().upper()
            if re.match(r'^[A-Z\-]{1,6}$', ticker):
                portfolios[current_basket].append(ticker)
    
    if basket_filter and basket_filter.lower() != 'all':
        # Find matching basket
        for basket_name, tickers in portfolios.items():
            if basket_filter.lower() in basket_name.lower():
                return {basket_name: tickers}
        return {}
    
    return portfolios

def get_all_stocks():
    """Get all individual stock holdings (no ETFs)"""
    portfolios = load_portfolio()
    
    # Combine Defense, Grid-to-Chip, and TopVOO holdings
    all_stocks = []
    for basket, tickers in portfolios.items():
        if 'ETF' not in basket and 'Scan' not in basket:
            all_stocks.extend(tickers)
    
    # Remove duplicates and sort
    return sorted(list(set(all_stocks)))

def main():
    if len(sys.argv) > 1:
        basket = sys.argv[1]
    else:
        basket = 'all'
    
    if basket.lower() == 'all':
        print("Loading all individual stock holdings...")
        stocks = get_all_stocks()
        print(f"Found {len(stocks)} unique stocks:")
        print(' '.join(stocks))
    else:
        portfolios = load_portfolio(basket)
        for name, tickers in portfolios.items():
            print(f"{name}: {' '.join(tickers)}")

if __name__ == "__main__":
    main()
