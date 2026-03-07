#!/usr/bin/env python3
"""
EWROS — Exponential Weighted Relative Outperformance Score

For each stock over the last 63 trading days (~3 months):
  1. daily_alpha = stock_daily_return - SPY_daily_return
  2. weight = e^(-λ × days_ago)   (λ = 0.03, ~33 day half-life)
  3. EWROS_raw = Σ(daily_alpha × weight)
  4. Rank all stocks → percentile 1-99

Saves ewros_score (1-99) and ewros_raw into all_stocks.json.
"""
import json
import math
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE, 'data')
ALL_STOCKS_FILE = os.path.join(DATA_DIR, 'all_stocks.json')

LOOKBACK_DAYS = 63  # ~3 months of trading days
TREND_OFFSET = 21   # ~1 month back for trend comparison
LAMBDA = 0.03       # decay factor, ~33 day half-life
MAX_WORKERS = 10


def fetch_daily_closes(ticker, period='6mo'):
    """Fetch daily closes from Yahoo Finance chart API."""
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={period}&interval=1d'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        result = data.get('chart', {}).get('result', [{}])[0]
        closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
        return [c for c in closes if c is not None]
    except Exception:
        return []


def compute_daily_returns(closes):
    """Convert closes to daily % returns."""
    if len(closes) < 2:
        return []
    returns = []
    for i in range(1, len(closes)):
        if closes[i-1] > 0:
            returns.append((closes[i] - closes[i-1]) / closes[i-1])
        else:
            returns.append(0.0)
    return returns


def compute_ewros_raw(stock_returns, spy_returns, end_offset=0):
    """
    Compute EWROS raw score.
    end_offset: how many days back from the end to compute
                (0 = current, 21 = one month ago)
    """
    if end_offset > 0:
        s_rets = stock_returns[:-end_offset] if end_offset < len(stock_returns) else []
        b_rets = spy_returns[:-end_offset] if end_offset < len(spy_returns) else []
    else:
        s_rets = stock_returns
        b_rets = spy_returns

    n = min(len(s_rets), len(b_rets), LOOKBACK_DAYS)
    if n < 20:
        return None

    s_ret = s_rets[-n:]
    b_ret = b_rets[-n:]

    ewros = 0.0
    for i in range(n):
        days_ago = n - 1 - i
        alpha = s_ret[i] - b_ret[i]
        weight = math.exp(-LAMBDA * days_ago)
        ewros += alpha * weight

    return ewros


def main():
    print("📊 EWROS — Exponential Weighted Relative Outperformance Score")
    print(f"   Lookback: {LOOKBACK_DAYS} days | λ: {LAMBDA} | Half-life: {int(math.log(2)/LAMBDA)} days")
    print("=" * 60)

    # Load all stocks
    with open(ALL_STOCKS_FILE) as f:
        data = json.load(f)

    stocks = data.get('stocks', data)
    tickers = list(stocks.keys())
    print(f"📈 Scoring {len(tickers)} stocks...")

    # Fetch SPY benchmark first
    print("   Fetching SPY benchmark...")
    spy_closes = fetch_daily_closes('SPY')
    spy_returns = compute_daily_returns(spy_closes)
    if len(spy_returns) < LOOKBACK_DAYS:
        print(f"❌ SPY data insufficient ({len(spy_returns)} days). Aborting.")
        sys.exit(1)
    print(f"   SPY: {len(spy_returns)} daily returns ✓")

    # Fetch all stock data in parallel — compute current + prior EWROS
    raw_scores = {}
    prior_scores = {}
    failed = 0
    completed = 0

    def process_ticker(ticker):
        closes = fetch_daily_closes(ticker)
        returns = compute_daily_returns(closes)
        current = compute_ewros_raw(returns, spy_returns, end_offset=0)
        prior = compute_ewros_raw(returns, spy_returns, end_offset=TREND_OFFSET)
        return ticker, current, prior

    print(f"   Fetching {len(tickers)} stocks ({MAX_WORKERS} threads)...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_ticker, t): t for t in tickers}
        for f in as_completed(futures):
            completed += 1
            ticker, current, prior = f.result()
            if current is not None:
                raw_scores[ticker] = current
            else:
                failed += 1
            if prior is not None:
                prior_scores[ticker] = prior
            if completed % 100 == 0:
                print(f"   ... {completed}/{len(tickers)} done")

    print(f"\n✅ Scored {len(raw_scores)} stocks ({failed} failed)")

    # Rank current → percentile 1-99
    sorted_tickers = sorted(raw_scores.keys(), key=lambda t: raw_scores[t])
    total = len(sorted_tickers)

    percentiles = {}
    for rank, ticker in enumerate(sorted_tickers):
        pct = int(((rank + 1) / total) * 99)
        pct = max(1, min(99, pct))
        percentiles[ticker] = pct

    # Rank prior → percentile 1-99
    prior_sorted = sorted(prior_scores.keys(), key=lambda t: prior_scores[t])
    prior_total = len(prior_sorted)
    prior_percentiles = {}
    for rank, ticker in enumerate(prior_sorted):
        pct = int(((rank + 1) / prior_total) * 99)
        pct = max(1, min(99, pct))
        prior_percentiles[ticker] = pct

    # Save back into all_stocks.json
    for ticker in stocks:
        if ticker in percentiles:
            stocks[ticker]['ewros_score'] = percentiles[ticker]
            stocks[ticker]['ewros_raw'] = round(raw_scores[ticker] * 10000, 2)
            prior_pct = prior_percentiles.get(ticker)
            if prior_pct is not None:
                stocks[ticker]['ewros_trend'] = percentiles[ticker] - prior_pct  # positive = improving
            else:
                stocks[ticker]['ewros_trend'] = None
        else:
            stocks[ticker]['ewros_score'] = None
            stocks[ticker]['ewros_raw'] = None
            stocks[ticker]['ewros_trend'] = None

    with open(ALL_STOCKS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

    # Print top/bottom
    print(f"\n🏆 TOP 10 EWROS:")
    for ticker in sorted_tickers[-10:][::-1]:
        trend = stocks[ticker].get('ewros_trend', 0) or 0
        arrow = '▲' if trend > 0 else '▼' if trend < 0 else '='
        print(f"   {ticker:6s}  RS {percentiles[ticker]:2d}  {arrow}{abs(trend):+d}  raw={raw_scores[ticker]*10000:+.1f}bps")

    print(f"\n📉 BOTTOM 10 EWROS:")
    for ticker in sorted_tickers[:10]:
        trend = stocks[ticker].get('ewros_trend', 0) or 0
        arrow = '▲' if trend > 0 else '▼' if trend < 0 else '='
        print(f"   {ticker:6s}  RS {percentiles[ticker]:2d}  {arrow}{abs(trend):+d}  raw={raw_scores[ticker]*10000:+.1f}bps")

    # Portfolio highlights
    print(f"\n💼 Portfolio EWROS:")
    portfolio_file = os.path.join(DATA_DIR, 'watchlist.json')
    if os.path.exists(portfolio_file):
        with open(portfolio_file) as f:
            wl = json.load(f)
        holdings = [h['ticker'] for h in wl.get('all', [])]
        for t in sorted(holdings):
            if t in percentiles:
                indicator = '🟢' if percentiles[t] >= 70 else '🟡' if percentiles[t] >= 40 else '🔴'
                trend = stocks[t].get('ewros_trend', 0) or 0
                arrow = '▲' if trend > 0 else '▼' if trend < 0 else '='
                print(f"   {indicator} {t:6s}  RS {percentiles[t]:2d}  {arrow}{trend:+d}")

    print(f"\n💾 Saved to {ALL_STOCKS_FILE}")


if __name__ == '__main__':
    main()
