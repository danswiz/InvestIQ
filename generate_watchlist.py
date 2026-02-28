#!/usr/bin/env python3
"""
Generate watchlist.json for InvestIQ portfolio holdings.
Reads all scores and fundamentals from all_stocks.json (database).
Only fetches live price for daily % change via yfinance bulk download.
"""
import json
import yfinance as yf
from datetime import datetime
from config import (
    TRADING_ACCOUNT, CORE_ETFS,
    GRID_TO_CHIP, DEFENSE_AEROSPACE, AI_SEMIS, BIOTECH
)
from utils.logger import get_logger

logger = get_logger('watchlist')

BASKETS = {
    "Trading Account": TRADING_ACCOUNT,
    "IRA Core ETFs": CORE_ETFS,
    "Grid-to-Chip": GRID_TO_CHIP,
    "Defense & Aerospace": DEFENSE_AEROSPACE,
    "AI Semis": AI_SEMIS,
    "Biotech": BIOTECH
}


def load_stock_db():
    """Load all stock data from all_stocks.json"""
    try:
        with open('all_stocks.json', 'r') as f:
            data = json.load(f)
            stocks = data.get('stocks', {})
            if isinstance(stocks, dict):
                logger.info(f"Loaded {len(stocks)} stocks from database")
                return stocks
            # Handle list format (convert to dict)
            return {s['ticker']: s for s in stocks if 'ticker' in s}
    except Exception as e:
        logger.warning(f"Could not load all_stocks.json: {e}")
        return {}


def fetch_live_prices(tickers):
    """Bulk fetch live prices + previous close for daily % change"""
    live = {}
    try:
        # yfinance bulk download — single API call for all tickers
        data = yf.download(tickers, period="2d", group_by="ticker", progress=False, threads=True)
        for t in tickers:
            try:
                if len(tickers) == 1:
                    closes = data['Close'].dropna()
                else:
                    closes = data[t]['Close'].dropna()
                if len(closes) >= 2:
                    prev = float(closes.iloc[-2])
                    curr = float(closes.iloc[-1])
                    live[t] = {
                        'price': round(curr, 2),
                        'previous_close': round(prev, 2),
                        'daily_change': round((curr - prev) / prev * 100, 2)
                    }
                elif len(closes) == 1:
                    live[t] = {
                        'price': round(float(closes.iloc[-1]), 2),
                        'previous_close': None,
                        'daily_change': None
                    }
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Bulk price fetch failed: {e}")
    return live


def build_stock_entry(ticker, basket_name, db, live_prices):
    """Build a watchlist entry from DB + live price data"""
    stock = db.get(ticker, {})
    live = live_prices.get(ticker, {})

    # Extract revenue/earnings growth from criteria if available
    revenue_growth = None
    earnings_growth = None
    for c in stock.get('criteria', []):
        if c.get('name') == 'Sales Growth (2yr)' and c.get('value'):
            # Parse "Cur: 22.7%, Prior: 16.7%"
            try:
                parts = c['value'].split(',')
                cur = parts[0].split(':')[1].strip().replace('%', '')
                revenue_growth = float(cur)
            except:
                pass
        if c.get('name') == 'Earnings Acceleration' and c.get('value'):
            try:
                val = c['value']
                if 'accelerating' in val.lower():
                    earnings_growth = 'Accelerating'
                elif 'positive' in val.lower():
                    earnings_growth = 'Positive'
                elif 'decelerating' in val.lower():
                    earnings_growth = 'Decelerating'
            except:
                pass

    return {
        "ticker": ticker,
        "name": stock.get('name', ticker),
        "sector": stock.get('sector', ''),
        "industry": stock.get('industry', ''),
        "price": live.get('price') or stock.get('current_price'),
        "previous_close": live.get('previous_close'),
        "daily_change": live.get('daily_change'),
        "trailing_pe": round(stock['trailing_pe'], 2) if stock.get('trailing_pe') else None,
        "forward_pe": round(stock['forward_pe'], 2) if stock.get('forward_pe') else None,
        "revenue_growth": revenue_growth,
        "earnings_growth": earnings_growth,
        "peg_ratio": round(stock['peg_ratio'], 2) if stock.get('peg_ratio') else None,
        "market_cap": stock.get('market_cap'),
        # Rater v5.0 scores (from DB)
        "score": stock.get('score', 0),
        "grade": stock.get('grade', 'N/A'),
        "technical_score": stock.get('technical_score', 0),
        "growth_score": stock.get('growth_score', 0),
        "quality_score": stock.get('quality_score', 0),
        "context_score": stock.get('context_score', 0),
        "moonshot_score": stock.get('moonshot_score', 0),
        # Rotation Catcher scores (from DB)
        "rotation_score": stock.get('rotation_score', 0),
        "rotation_signal": stock.get('rotation_signal', 'N/A'),
        # Analyst data
        "recommendation": stock.get('recommendation'),
        "target_mean": round(stock['target_mean'], 2) if stock.get('target_mean') else None,
        "analyst_count": stock.get('analyst_count', 0),
        # Basket
        "basket": basket_name,
    }


def generate_watchlist():
    """Generate watchlist.json from database + live prices"""
    logger.info("Starting watchlist generation...")

    # Load DB
    db = load_stock_db()

    # Collect all tickers
    all_tickers = []
    for tickers in BASKETS.values():
        all_tickers.extend(tickers)
    all_tickers = list(set(all_tickers))

    # Bulk fetch live prices (single API call)
    logger.info(f"Fetching live prices for {len(all_tickers)} tickers...")
    live_prices = fetch_live_prices(all_tickers)
    logger.info(f"Got live prices for {len(live_prices)} tickers")

    # Build watchlist
    watchlist_data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M EST"),
        "baskets": {},
        "all": []
    }

    for basket_name, tickers in BASKETS.items():
        logger.info(f"Processing basket: {basket_name} ({len(tickers)} holdings)")
        basket_stocks = []

        for ticker in tickers:
            entry = build_stock_entry(ticker, basket_name, db, live_prices)
            basket_stocks.append(entry)
            watchlist_data['all'].append(entry)

        watchlist_data['baskets'][basket_name] = basket_stocks

    # Write
    with open('watchlist.json', 'w') as f:
        json.dump(watchlist_data, f, indent=2)

    logger.info(f"✓ Watchlist generated: watchlist.json")
    logger.info(f"  Total holdings: {len(watchlist_data['all'])}")
    logger.info(f"  Baskets: {len(watchlist_data['baskets'])}")

    return watchlist_data


if __name__ == "__main__":
    result = generate_watchlist()
    print(f"\n✓ Generated watchlist with {len(result['all'])} holdings")
    print(f"Last updated: {result['last_updated']}")
