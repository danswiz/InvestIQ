#!/usr/bin/env python3
"""
Market Data Verifier - Cross-checks prices before sending reports
Usage: python verify_data.py <ticker> <expected_price>
Returns: {"verified": bool, "actual": float, "discrepancy": float}
"""
import yfinance as yf
import sys
import json

def verify_price(ticker, expected_price, tolerance=0.02):
    """
    Verify a stock price against live data
    tolerance: 0.02 = 2% allowed variance
    """
    try:
        t = yf.Ticker(ticker)
        
        # Try to get real-time price first
        info = t.info
        live_price = info.get('regularMarketPrice') or info.get('currentPrice')
        
        # Fallback to recent history
        if not live_price:
            hist = t.history(period="1d")
            if not hist.empty:
                live_price = hist['Close'].iloc[-1]
        
        if not live_price:
            return {"verified": False, "error": "Could not fetch live price", "ticker": ticker}
        
        discrepancy = abs(live_price - expected_price) / expected_price
        
        return {
            "ticker": ticker,
            "expected": expected_price,
            "actual": round(live_price, 2),
            "discrepancy": round(discrepancy * 100, 2),
            "verified": discrepancy <= tolerance,
            "timestamp": str(yf.Ticker(ticker).info.get('regularMarketTime', 'N/A'))
        }
    except Exception as e:
        return {"verified": False, "error": str(e), "ticker": ticker}

def verify_portfolio(holdings_dict, tolerance=0.02):
    """
    Verify multiple holdings
    holdings_dict: {"TICKER": expected_price, ...}
    Returns: summary report
    """
    results = []
    failed = []
    
    for ticker, expected in holdings_dict.items():
        result = verify_price(ticker, expected, tolerance)
        results.append(result)
        if not result.get("verified"):
            failed.append(result)
    
    return {
        "total_checked": len(results),
        "verified_count": len([r for r in results if r.get("verified")]),
        "failed_count": len(failed),
        "failed_tickers": failed,
        "all_results": results,
        "should_send_report": len(failed) <= len(results) * 0.2  # Allow 20% failure rate
    }

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        ticker = sys.argv[1]
        expected = float(sys.argv[2])
        result = verify_price(ticker, expected)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python verify_data.py TICKER EXPECTED_PRICE")
        print("Example: python verify_data.py SPY 450.00")
