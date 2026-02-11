#!/usr/bin/env python3
"""
Verified Market Pulse Report Generator
Fetches data, verifies it, then generates report only if accurate
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from verify_data import verify_portfolio
import yfinance as yf
from datetime import datetime

def fetch_and_verify(holdings):
    """
    Fetch current prices and verify them
    holdings: list of tickers
    Returns: (verified_prices dict, verification_report)
    """
    # First pass: fetch all prices
    fetched = {}
    for ticker in holdings:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            price = info.get('regularMarketPrice') or info.get('currentPrice')
            if not price:
                hist = t.history(period="1d")
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
            if price:
                fetched[ticker] = price
        except Exception as e:
            print(f"Failed to fetch {ticker}: {e}")
            continue
    
    # Second pass: verify (fetch again to check consistency)
    print(f"[Verifier] Checking {len(fetched)} prices for consistency...")
    verification = verify_portfolio(fetched, tolerance=0.015)  # 1.5% tolerance
    
    if verification["should_send_report"]:
        print(f"[Verifier] ✓ {verification['verified_count']}/{verification['total_checked']} prices verified")
        return fetched, verification
    else:
        print(f"[Verifier] ✗ Too many discrepancies: {verification['failed_count']} failed")
        for fail in verification["failed_tickers"]:
            print(f"  - {fail['ticker']}: expected {fail.get('expected')}, got {fail.get('actual', 'N/A')}")
        return None, verification

def main():
    # Dan's core holdings
    holdings = ["SPY", "QQQ", "IWM", "VIX", "GLD", "COPX", "NLR", "VOO", "XLI", "ITA"]
    
    prices, verification = fetch_and_verify(holdings)
    
    if prices:
        print(f"[Verified] Data confirmed at {datetime.now().strftime('%H:%M:%S')}")
        # Return prices for report generation
        return prices
    else:
        print("[FAILED] Data verification failed. Report NOT generated.")
        return None

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
