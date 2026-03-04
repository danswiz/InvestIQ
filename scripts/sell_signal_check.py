#!/usr/bin/env python3
"""
Sell Signal Check — runs nightly after market close.

Evaluates all watchlist tickers against 3-tier sell signal framework:
  🔴 SELL  — hard stop (-8% from entry) OR rotation score < 35
  🟡 WATCH — rotation dropped 15+ pts from entry OR 3+ distribution signals OR price < 50d MA
  🟢 HOLD  — thesis intact

Saves daily snapshots to data/rotation_snapshots.json
Sends Telegram alerts for SELL and new WATCH signals.
"""

import sys, os, json, urllib.request
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SUPABASE_URL = 'https://jvgxgfbthfsdqtvzeuqz.supabase.co'
SNAPSHOT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'rotation_snapshots.json')
DIST_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'distribution_signals.json')


def get_supabase_key():
    key = os.environ.get('SUPABASE_KEY', '')
    if not key:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        try:
            with open(env_path) as f:
                for line in f:
                    if line.startswith('SUPABASE_KEY='):
                        key = line.strip().split('=', 1)[1]
        except FileNotFoundError:
            pass
    return key


def sb_get(path, key):
    headers = {'apikey': key, 'Authorization': f'Bearer {key}'}
    req = urllib.request.Request(f'{SUPABASE_URL}{path}', headers=headers)
    return json.loads(urllib.request.urlopen(req).read())


def get_watchlist_items():
    key = get_supabase_key()
    items = sb_get('/rest/v1/watchlist_items?select=ticker,entry_price,added_date,snapshot', key)
    return items


def get_current_price(ticker):
    """Get current price using Yahoo spark endpoint."""
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/spark?symbols={ticker}&range=1d&interval=1m'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read())
        closes = data.get(ticker, {}).get('close', [])
        prev = data.get(ticker, {}).get('chartPreviousClose')
        curr = closes[-1] if closes else None
        return curr, prev
    except Exception:
        return None, None


def get_50d_ma(ticker):
    """Get 50-day moving average."""
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=3mo'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read())
        closes = data['chart']['result'][0]['indicators']['quote'][0].get('close', [])
        closes = [c for c in closes if c is not None]
        if len(closes) >= 50:
            return sum(closes[-50:]) / 50
        elif closes:
            return sum(closes) / len(closes)
    except Exception:
        pass
    return None


def get_rotation_score(ticker):
    """Get current rotation score from all_stocks.json cache (updated by daily scan)."""
    try:
        ws_dir = os.path.dirname(os.path.dirname(__file__))
        with open(os.path.join(ws_dir, 'data', 'all_stocks.json')) as f:
            data = json.load(f)
        stocks = data.get('stocks', data)
        return stocks.get(ticker, {}).get('rotation_score', 0) or 0
    except Exception:
        pass
    return 0


def get_distribution_count(ticker):
    """Get recent distribution signal count from distribution_signals.json or all_stocks."""
    try:
        if os.path.exists(DIST_FILE):
            with open(DIST_FILE) as f:
                dist_data = json.load(f)
            return dist_data.get(ticker, {}).get('signal_count', 0)
    except Exception:
        pass
    return 0


def load_snapshots():
    try:
        with open(SNAPSHOT_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_snapshots(snapshots):
    os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
    with open(SNAPSHOT_FILE, 'w') as f:
        json.dump(snapshots, f, indent=2)


def evaluate_sell_signal(ticker, entry_price, current_price, rotation_score,
                          entry_rotation, ma50, dist_count):
    """Evaluate sell signal tier."""
    reasons = []
    tier = 'HOLD'

    if not current_price or not entry_price:
        return 'HOLD', []

    pct_from_entry = (current_price - entry_price) / entry_price * 100

    # --- Tier 1: SELL signals (hard) ---
    if pct_from_entry <= -8.0:
        tier = 'SELL'
        reasons.append(f'Hard stop: {pct_from_entry:.1f}% from entry')

    if rotation_score < 35:
        tier = 'SELL'
        reasons.append(f'Rotation collapsed: {rotation_score:.1f} (buy threshold was ≥60)')

    # --- Tier 2: WATCH signals ---
    if tier == 'HOLD':
        rotation_drop = (entry_rotation or 0) - rotation_score
        if rotation_drop >= 15:
            tier = 'WATCH'
            reasons.append(f'Rotation dropped {rotation_drop:.1f} pts (entry: {entry_rotation:.1f} → now: {rotation_score:.1f})')

        if dist_count >= 3:
            tier = 'WATCH'
            reasons.append(f'{dist_count} distribution signals in last 25 days')

        if ma50 and current_price < ma50:
            tier = 'WATCH'
            reasons.append(f'Price ${current_price:.2f} below 50-day MA ${ma50:.2f}')

        if pct_from_entry <= -5.0:
            tier = 'WATCH'
            reasons.append(f'Down {pct_from_entry:.1f}% from entry (approaching stop)')

    return tier, reasons


def send_telegram(message):
    """Send Telegram message via OpenClaw gateway."""
    try:
        payload = json.dumps({
            'channel': 'telegram',
            'to': '690660528',
            'message': message
        }).encode()
        req = urllib.request.Request(
            'http://localhost:18790/api/message/send',
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f'Telegram send failed: {e}')


def main():
    today = date.today().isoformat()
    print(f'\n=== Sell Signal Check — {today} ===\n')

    items = get_watchlist_items()
    if not items:
        print('No watchlist items found.')
        return

    snapshots = load_snapshots()
    alerts_sell = []
    alerts_watch = []
    results = []

    for item in items:
        ticker = item['ticker']
        entry_price = item.get('entry_price')
        if not entry_price:
            continue

        entry_snapshot = item.get('snapshot') or {}
        entry_rotation = entry_snapshot.get('rotation_score', 0) or 0

        print(f'Checking {ticker}...')
        current_price, prev_close = get_current_price(ticker)
        rotation_score = get_rotation_score(ticker)
        ma50 = get_50d_ma(ticker)
        dist_count = get_distribution_count(ticker)

        tier, reasons = evaluate_sell_signal(
            ticker, entry_price, current_price, rotation_score,
            entry_rotation, ma50, dist_count
        )

        pct = ((current_price - entry_price) / entry_price * 100) if current_price else None

        result = {
            'ticker': ticker,
            'tier': tier,
            'reasons': reasons,
            'current_price': round(current_price, 2) if current_price else None,
            'entry_price': entry_price,
            'pct_from_entry': round(pct, 2) if pct is not None else None,
            'rotation_score': round(rotation_score, 1),
            'entry_rotation': round(entry_rotation, 1),
            'ma50': round(ma50, 2) if ma50 else None,
            'dist_count': dist_count,
            'date': today
        }
        results.append(result)

        # Save daily snapshot
        if ticker not in snapshots:
            snapshots[ticker] = {}
        snapshots[ticker][today] = {
            'price': current_price,
            'rotation_score': rotation_score,
            'tier': tier
        }

        # Track previous tier to detect new WATCH signals
        prev_tier = None
        dates = sorted(snapshots[ticker].keys())
        if len(dates) >= 2:
            prev_tier = snapshots[ticker][dates[-2]].get('tier')

        print(f'  {tier:5s} | Price ${current_price:.2f} ({pct:+.1f}%) | Rot {rotation_score:.1f} | {", ".join(reasons) if reasons else "thesis intact"}')

        if tier == 'SELL':
            alerts_sell.append(result)
        elif tier == 'WATCH' and prev_tier in (None, 'HOLD'):
            alerts_watch.append(result)  # New WATCH (wasn't WATCH yesterday)

    save_snapshots(snapshots)

    # --- Print summary ---
    print(f'\n{"─"*50}')
    print(f'SELL:  {sum(1 for r in results if r["tier"] == "SELL")}')
    print(f'WATCH: {sum(1 for r in results if r["tier"] == "WATCH")}')
    print(f'HOLD:  {sum(1 for r in results if r["tier"] == "HOLD")}')

    # --- Send Telegram alerts ---
    if alerts_sell or alerts_watch:
        lines = ['🚨 *InvestIQ Sell Signal Alert*\n']

        if alerts_sell:
            lines.append('🔴 *SELL SIGNALS:*')
            for r in alerts_sell:
                lines.append(f'  {r["ticker"]} ${r["current_price"]} ({r["pct_from_entry"]:+.1f}%)')
                for reason in r['reasons']:
                    lines.append(f'    • {reason}')

        if alerts_watch:
            lines.append('\n🟡 *NEW WATCH:*')
            for r in alerts_watch:
                lines.append(f'  {r["ticker"]} ${r["current_price"]} ({r["pct_from_entry"]:+.1f}%)')
                for reason in r['reasons']:
                    lines.append(f'    • {reason}')

        msg = '\n'.join(lines)
        print(f'\n{msg}')
        send_telegram(msg)
    else:
        print('\nNo new alerts. All positions healthy.')

    # Save results for API
    ws_dir = os.path.dirname(os.path.dirname(__file__))
    out_path = os.path.join(ws_dir, 'data', 'sell_signals.json')
    with open(out_path, 'w') as f:
        json.dump({'date': today, 'signals': results}, f, indent=2)
    print(f'\nResults saved to {out_path}')


if __name__ == '__main__':
    main()
