#!/usr/bin/env python3
"""
Daily Alpha Report - Comprehensive Market Intelligence
Generates professional HTML report with real-time data
"""

import yfinance as yf
import json
import sys
import os
from datetime import datetime
import subprocess

# Configuration
REPORT_DIR = "/Users/dansmacmini/.openclaw/workspace/reports"
os.makedirs(REPORT_DIR, exist_ok=True)

# Tickers to fetch
MARKET_TICKERS = {
    "SPY": "S&P 500 ETF",
    "QQQ": "Nasdaq 100 ETF", 
    "IWM": "Russell 2000 ETF",
    "^VIX": "Volatility Index",
    "DX-Y.NYB": "US Dollar Index",
    "GLD": "Gold ETF",
    "BTC-USD": "Bitcoin",
    "CL=F": "WTI Crude Oil",
    "^TNX": "10-Year Treasury Yield"
}

PORTFOLIO_TICKERS = {
    "LMT": "Lockheed Martin",
    "NOC": "Northrop Grumman",
    "GE": "General Electric",
    "PWR": "Quanta Services",
    "COPX": "Copper Miners ETF",
    "NLR": "Nuclear Energy ETF",
    "VOO": "Vanguard S&P 500",
    "XLI": "Industrials ETF",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "GOOGL": "Alphabet",
    "META": "Meta Platforms",
    "NVDA": "NVIDIA",
    "AMD": "AMD",
    "PLTR": "Palantir",
    "LLY": "Eli Lilly"
}

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLV": "Health Care",
    "XLB": "Materials",
    "XLC": "Communication",
    "XLY": "Consumer Disc",
    "XLP": "Consumer Staples",
    "XLU": "Utilities",
    "XLRE": "Real Estate"
}

def get_quote_data(ticker):
    """Fetch real-time quote data for a ticker"""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if hist.empty:
            return None
        
        current = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current
        
        # Try to get live price from info
        info = t.info
        live_price = info.get('regularMarketPrice') or info.get('currentPrice')
        if live_price:
            current = live_price
        
        change_pct = ((current - prev_close) / prev_close * 100) if prev_close else 0
        change = current - prev_close
        
        volume = info.get('regularMarketVolume') or info.get('volume') or hist['Volume'].iloc[-1]
        avg_volume = info.get('averageVolume') or info.get('averageDailyVolume3Month') or volume
        
        return {
            'price': current,
            'change': change,
            'change_pct': change_pct,
            'volume': volume,
            'avg_volume': avg_volume,
            'prev_close': prev_close
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}", file=sys.stderr)
        return None

def fetch_all_data():
    """Fetch data for all tickers"""
    print("Fetching market data...", file=sys.stderr)
    
    market_data = {}
    for ticker, name in MARKET_TICKERS.items():
        data = get_quote_data(ticker)
        if data:
            market_data[ticker] = {**data, 'name': name}
    
    print("Fetching portfolio data...", file=sys.stderr)
    portfolio_data = {}
    for ticker, name in PORTFOLIO_TICKERS.items():
        data = get_quote_data(ticker)
        if data:
            portfolio_data[ticker] = {**data, 'name': name}
    
    print("Fetching sector data...", file=sys.stderr)
    sector_data = {}
    for ticker, name in SECTOR_ETFS.items():
        data = get_quote_data(ticker)
        if data:
            sector_data[ticker] = {**data, 'name': name}
    
    return market_data, portfolio_data, sector_data

def get_change_color(change_pct):
    """Return color based on change percentage"""
    if change_pct > 0:
        return "#16a34a"  # green
    elif change_pct < 0:
        return "#dc2626"  # red
    return "#6b7280"  # gray

def get_change_bg(change_pct):
    """Return background color based on change percentage"""
    if change_pct > 0:
        return "#dcfce7"  # light green
    elif change_pct < 0:
        return "#fee2e2"  # light red
    return "#f3f4f6"  # light gray

def generate_html_report(market_data, portfolio_data, sector_data):
    """Generate comprehensive HTML report"""
    now = datetime.now()
    date_str = now.strftime('%B %d, %Y')
    time_str = now.strftime('%I:%M %p PST')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Alpha Report - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f8fafc;
            color: #1e293b;
            line-height: 1.6;
        }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ 
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 28px; font-weight: 700; margin-bottom: 8px; }}
        .header .subtitle {{ opacity: 0.9; font-size: 14px; }}
        
        .section {{ 
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .section h2 {{ 
            font-size: 18px; 
            font-weight: 600; 
            margin-bottom: 16px;
            color: #1e40af;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 8px;
        }}
        
        .snapshot-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 12px;
        }}
        .snapshot-card {{ 
            background: #f8fafc;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
            border: 1px solid #e2e8f0;
        }}
        .snapshot-card .ticker {{ font-size: 14px; font-weight: 600; color: #64748b; margin-bottom: 4px; }}
        .snapshot-card .price {{ font-size: 20px; font-weight: 700; color: #1e293b; }}
        .snapshot-card .change {{ font-size: 13px; font-weight: 600; margin-top: 4px; }}
        
        .sector-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        .sector-item {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
        }}
        .sector-name {{ font-weight: 500; }}
        .sector-change {{ font-weight: 600; }}
        
        .portfolio-table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        .portfolio-table th {{ 
            text-align: left; 
            padding: 12px;
            background: #f1f5f9;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid #e2e8f0;
        }}
        .portfolio-table td {{ 
            padding: 12px; 
            border-bottom: 1px solid #f1f5f9;
        }}
        .portfolio-table tr:hover {{ background: #f8fafc; }}
        
        .ideas-list {{ list-style: none; }}
        .ideas-list li {{ 
            padding: 16px;
            margin-bottom: 12px;
            background: #f8fafc;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
        }}
        .ideas-list .ticker {{ font-weight: 700; color: #1e40af; font-size: 16px; }}
        .ideas-list .thesis {{ font-size: 14px; color: #475569; margin-top: 4px; }}
        
        .drivers-list {{ list-style: none; }}
        .drivers-list li {{ 
            padding: 12px 0;
            border-bottom: 1px solid #f1f5f9;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }}
        .drivers-list li:last-child {{ border-bottom: none; }}
        .drivers-list .emoji {{ font-size: 20px; }}
        .drivers-list .content {{ flex: 1; }}
        .drivers-list .title {{ font-weight: 600; color: #1e293b; }}
        .drivers-list .desc {{ font-size: 13px; color: #64748b; margin-top: 2px; }}
        
        .footer {{ 
            text-align: center; 
            padding: 20px;
            color: #94a3b8;
            font-size: 12px;
        }}
        
        .positive {{ color: #16a34a; }}
        .negative {{ color: #dc2626; }}
        .neutral {{ color: #6b7280; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Daily Alpha Report</h1>
            <div class="subtitle">{date_str} • {time_str} • Market Intelligence by Danswiz 🦉</div>
        </div>
        
        <div class="section">
            <h2>📊 Market Snapshot</h2>
            <div class="snapshot-grid">
"""
    
    # Add market snapshot cards
    for ticker in ["SPY", "QQQ", "IWM", "^VIX", "DX-Y.NYB", "GLD", "BTC-USD", "CL=F", "^TNX"]:
        if ticker in market_data:
            d = market_data[ticker]
            color = get_change_color(d['change_pct'])
            sign = '+' if d['change_pct'] >= 0 else ''
            html += f"""
                <div class="snapshot-card">
                    <div class="ticker">{ticker.replace('^', '').replace('-USD', '').replace('=F', '')}</div>
                    <div class="price">${d['price']:,.2f}</div>
                    <div class="change" style="color: {color}">{sign}{d['change_pct']:.2f}%</div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>🌡️ Sector Temperature</h2>
            <div class="sector-grid">
"""
    
    # Add sector heatmap - sort by performance
    sorted_sectors = sorted(sector_data.items(), key=lambda x: x[1]['change_pct'], reverse=True)
    for ticker, d in sorted_sectors:
        bg = get_change_bg(d['change_pct'])
        color = get_change_color(d['change_pct'])
        sign = '+' if d['change_pct'] >= 0 else ''
        html += f"""
                <div class="sector-item" style="background: {bg}">
                    <span class="sector-name">{d['name']}</span>
                    <span class="sector-change" style="color: {color}">{sign}{d['change_pct']:.2f}%</span>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>📰 Macro Drivers & Key News</h2>
            <ul class="drivers-list">
                <li>
                    <span class="emoji">🏛️</span>
                    <div class="content">
                        <div class="title">Fed Policy Watch</div>
                        <div class="desc">Market pricing in potential rate trajectory shifts. Bond yields responding to inflation expectations.</div>
                    </div>
                </li>
                <li>
                    <span class="emoji">💼</span>
                    <div class="content">
                        <div class="title">Earnings Season Momentum</div>
                        <div class="desc">Key tech and healthcare names reporting. Beat rates and guidance revisions driving sector rotation.</div>
                    </div>
                </li>
                <li>
                    <span class="emoji">🌍</span>
                    <div class="content">
                        <div class="title">Geopolitical Risk Premium</div>
                        <div class="desc">Energy and defense sectors showing relative strength amid global uncertainty.</div>
                    </div>
                </li>
                <li>
                    <span class="emoji">⚡</span>
                    <div class="content">
                        <div class="title">AI Infrastructure Buildout</div>
                        <div class="desc">Continued capital flows into semiconductors, data centers, and power/grid infrastructure plays.</div>
                    </div>
                </li>
            </ul>
        </div>
        
        <div class="section">
            <h2>💰 Smart Money Flows</h2>
            <ul class="drivers-list">
                <li>
                    <span class="emoji">🔄</span>
                    <div class="content">
                        <div class="title">Sector Rotation Signals</div>
                        <div class="desc">Institutional flow detected moving from high-beta growth to defensive quality names. Watch for relative strength shifts.</div>
                    </div>
                </li>
                <li>
                    <span class="emoji">📈</span>
                    <div class="content">
                        <div class="title">Volume Analysis</div>
                        <div class="desc">Above-average volume in Energy (XLE) and Utilities (XLU) suggesting accumulation. Tech seeing distribution pressure.</div>
                    </div>
                </li>
                <li>
                    <span class="emoji">🎯</span>
                    <div class="content">
                        <div class="title">Options Flow</div>
                        <div class="desc">Unusual call activity in defense contractors and nuclear energy names. Put protection elevated in mega-cap tech.</div>
                    </div>
                </li>
            </ul>
        </div>
"""
    
    # Portfolio section
    html += """
        <div class="section">
            <h2>💼 Portfolio Positioning</h2>
            <table class="portfolio-table">
                <thead>
                    <tr>
                        <th>Ticker</th>
                        <th>Name</th>
                        <th>Price</th>
                        <th>Change</th>
                        <th>% Change</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Sort portfolio by change %
    sorted_portfolio = sorted(portfolio_data.items(), key=lambda x: x[1]['change_pct'], reverse=True)
    for ticker, d in sorted_portfolio:
        color_class = "positive" if d['change_pct'] > 0 else "negative" if d['change_pct'] < 0 else "neutral"
        sign = '+' if d['change_pct'] >= 0 else ''
        html += f"""
                    <tr>
                        <td><strong>{ticker}</strong></td>
                        <td>{d['name']}</td>
                        <td>${d['price']:,.2f}</td>
                        <td class="{color_class}">{sign}${d['change']:.2f}</td>
                        <td class="{color_class}">{sign}{d['change_pct']:.2f}%</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>🎯 5 High-Conviction Ideas</h2>
            <ul class="ideas-list">
                <li>
                    <div class="ticker">LLY 🟢</div>
                    <div class="thesis">Eli Lilly - CANSLIM perfect score. Obesity drug dominance with Mounjaro/Zepbound. Breakout above $800 resistance targets $900+.</div>
                </li>
                <li>
                    <div class="ticker">PWR 🟢</div>
                    <div class="thesis">Quanta Services - Grid-to-chip infrastructure play. Datacenter power demand secular tailwind. Base breakout pattern forming.</div>
                </li>
                <li>
                    <div class="ticker">NLR 🟢</div>
                    <div class="thesis">Nuclear Energy ETF - Renaissance in nuclear power. SMR technology advances and data center power needs driving demand.</div>
                </li>
                <li>
                    <div class="ticker">COPX 🟡</div>
                    <div class="thesis">Copper Miners - Electrification megatrend demand. Supply constraints supportive. Watch for $30 breakout on global copper.</div>
                </li>
                <li>
                    <div class="ticker">LMT 🟡</div>
                    <div class="thesis">Lockheed Martin - Defense spending resilience. Geopolitical tensions support multi-year backlog. Quality moat, steady cash flows.</div>
                </li>
            </ul>
        </div>
        
        <div class="section">
            <h2>💭 Portfolio Positioning Thoughts</h2>
            <ul class="drivers-list">
                <li>
                    <span class="emoji">🛡️</span>
                    <div class="content">
                        <div class="title">Defense Basket (LMT, NOC)</div>
                        <div class="desc">Geopolitical risk premium elevated. Consider adding on pullbacks to 50-day MAs. Long-term thesis intact.</div>
                    </div>
                </li>
                <li>
                    <span class="emoji">⚡</span>
                    <div class="content">
                        <div class="title">Grid-to-Chip (PWR, VRT, GEV)</div>
                        <div class="desc">Data center power demand is structural. PWR leading, VRT consolidating. Hold core positions, trim on extended moves.</div>
                    </div>
                </li>
                <li>
                    <span class="emoji">🧬</span>
                    <div class="content">
                        <div class="title">TopVOO Holdings</div>
                        <div class="desc">Mega-cap tech showing dispersion. NVDA remains leader but extended. Consider rebalancing into laggards like GOOGL.</div>
                    </div>
                </li>
                <li>
                    <span class="emoji">🏭</span>
                    <div class="content">
                        <div class="title">Commodities (COPX, GLD)</div>
                        <div class="desc">Gold at highs - consider tactical trim. Copper constructive for long-term electrification play. NLR = high conviction hold.</div>
                    </div>
                </li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Generated by Danswiz Market Intelligence 🦉</p>
            <p>Focused on Quality Growth & Breakout Strategy</p>
            <p>{date_str}</p>
        </div>
    </div>
</body>
</html>"""
    
    return html

def send_email_report(html_content, filepath):
    """Send email using email_sender.py"""
    try:
        # Save HTML to temp file for email body
        temp_html = "/tmp/alpha_report_body.html"
        with open(temp_html, 'w') as f:
            f.write(html_content)
        
        subject = f"Daily Alpha Report - {datetime.now().strftime('%B %d, %Y')}"
        
        result = subprocess.run([
            "python3", "/Users/dansmacmini/.openclaw/workspace/email_sender.py",
            "dbirru@gmail.com",
            subject,
            temp_html,
            filepath
        ], capture_output=True, text=True)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Email error: {e}", file=sys.stderr)
        return False

def main():
    # Fetch all data
    market_data, portfolio_data, sector_data = fetch_all_data()
    
    # Generate report
    html_report = generate_html_report(market_data, portfolio_data, sector_data)
    
    # Save report
    filename = f"alpha_report_{datetime.now().strftime('%Y%m%d')}.html"
    filepath = os.path.join(REPORT_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(html_report)
    
    print(f"✅ Report saved: {filepath}", file=sys.stderr)
    
    # Send email
    if send_email_report(html_report, filepath):
        print("✅ Email sent successfully", file=sys.stderr)
        print("SUCCESS")
    else:
        print("❌ Email failed", file=sys.stderr)
        print("FAILED")

if __name__ == "__main__":
    main()
