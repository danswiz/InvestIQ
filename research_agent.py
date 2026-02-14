#!/usr/bin/env python3
"""
InvestIQ Research Agent
Generates comprehensive investment analysis for any stock ticker.
Usage: python3 research_agent.py <TICKER>
"""

import yfinance as yf
import sys
import json
from datetime import datetime, timedelta
import numpy as np

def calculate_rsi(prices, window=14):
    """Calculate RSI technical indicator"""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[:window])
    avg_loss = np.mean(losses[:window])
    
    for i in range(window, len(gains)):
        avg_gain = (avg_gain * (window - 1) + gains[i]) / window
        avg_loss = (avg_loss * (window - 1) + losses[i]) / window
    
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_sma(prices, window):
    """Calculate simple moving average"""
    return np.mean(prices[-window:])

def get_stock_data(ticker):
    """Fetch comprehensive stock data"""
    print(f"🔍 Researching {ticker}...", file=sys.stderr)
    
    try:
        stock = yf.Ticker(ticker)
        
        # Price history
        hist = stock.history(period="1y")
        if hist.empty:
            return None, f"No data found for {ticker}"
        
        # Current price data
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0
        
        # 52-week range
        high_52w = hist['High'].max()
        low_52w = hist['Low'].min()
        position_52w = ((current_price - low_52w) / (high_52w - low_52w)) * 100
        
        # Moving averages
        ma_20 = calculate_sma(hist['Close'].values, 20)
        ma_50 = calculate_sma(hist['Close'].values, 50)
        ma_200 = calculate_sma(hist['Close'].values, 200)
        
        # RSI
        rsi = calculate_rsi(hist['Close'].values)
        
        # Volume analysis
        avg_volume = hist['Volume'].mean()
        recent_volume = hist['Volume'].iloc[-5:].mean()
        volume_trend = "Above average" if recent_volume > avg_volume * 1.2 else "Below average" if recent_volume < avg_volume * 0.8 else "Normal"
        
        # Fundamentals
        info = stock.info
        fundamentals = {
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', info.get('forwardPE', None)),
            'forward_pe': info.get('forwardPE', None),
            'peg_ratio': info.get('pegRatio', None),
            'price_to_book': info.get('priceToBook', None),
            'price_to_sales': info.get('priceToSalesTrailing12Months', None),
            'profit_margin': info.get('profitMargins', None),
            'revenue_growth': info.get('revenueGrowth', None),
            'earnings_growth': info.get('earningsGrowth', None),
            'debt_to_equity': info.get('debtToEquity', None),
            'return_on_equity': info.get('returnOnEquity', None),
            'current_ratio': info.get('currentRatio', None),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', None),
            'target_price': info.get('targetMeanPrice', None),
            'recommendation': info.get('recommendationKey', 'none'),
            'short_ratio': info.get('shortRatio', None),
            'shares_short_pct': info.get('shortPercentOfFloat', None)
        }
        
        return {
            'ticker': ticker,
            'current_price': round(current_price, 2),
            'change': round(change, 2),
            'change_pct': round(change_pct, 2),
            'high_52w': round(high_52w, 2),
            'low_52w': round(low_52w, 2),
            'position_52w': round(position_52w, 1),
            'ma_20': round(ma_20, 2),
            'ma_50': round(ma_50, 2),
            'ma_200': round(ma_200, 2),
            'rsi': round(rsi, 1),
            'volume_trend': volume_trend,
            'fundamentals': fundamentals
        }, None
        
    except Exception as e:
        return None, str(e)

def analyze_technicals(data):
    """Generate technical analysis"""
    price = data['current_price']
    ma_20 = data['ma_20']
    ma_50 = data['ma_50']
    ma_200 = data['ma_200']
    rsi = data['rsi']
    position = data['position_52w']
    
    # Trend determination
    if price > ma_20 > ma_50 > ma_200:
        trend = "Strong Uptrend"
        trend_score = 3
    elif price > ma_50 > ma_200:
        trend = "Uptrend"
        trend_score = 2
    elif price > ma_200:
        trend = "Weak Uptrend"
        trend_score = 1
    elif price < ma_20 < ma_50 < ma_200:
        trend = "Strong Downtrend"
        trend_score = -3
    elif price < ma_50 < ma_200:
        trend = "Downtrend"
        trend_score = -2
    else:
        trend = "Mixed/Consolidating"
        trend_score = 0
    
    # RSI interpretation
    if rsi > 70:
        rsi_signal = "Overbought"
        rsi_score = -1
    elif rsi < 30:
        rsi_signal = "Oversold"
        rsi_score = 1
    else:
        rsi_signal = "Neutral"
        rsi_score = 0
    
    # Position in 52w range
    if position > 80:
        range_signal = "Near 52w high"
        range_score = -1
    elif position < 20:
        range_signal = "Near 52w low"
        range_score = 2
    elif position < 40:
        range_signal = "Lower range - potential value"
        range_score = 1
    else:
        range_signal = "Mid to upper range"
        range_score = 0
    
    technical_score = trend_score + rsi_score + range_score
    
    return {
        'trend': trend,
        'rsi_signal': rsi_signal,
        'range_signal': range_signal,
        'technical_score': technical_score,
        'ma_alignment': f"20: ${ma_20} | 50: ${ma_50} | 200: ${ma_200}"
    }

def analyze_fundamentals(fund):
    """Generate fundamental analysis"""
    score = 0
    signals = []
    
    # P/E Analysis
    pe = fund.get('pe_ratio')
    if pe:
        if pe < 15:
            signals.append("Attractive P/E (value)")
            score += 2
        elif pe < 25:
            signals.append("Reasonable P/E")
            score += 1
        elif pe > 40:
            signals.append("High P/E (growth expectations)")
            score -= 1
    
    # PEG Ratio
    peg = fund.get('peg_ratio')
    if peg:
        if peg < 1:
            signals.append("Excellent PEG (<1) - undervalued growth")
            score += 3
        elif peg < 1.5:
            signals.append("Good PEG ratio")
            score += 1
        elif peg > 2:
            signals.append("Expensive PEG (>2)")
            score -= 2
    
    # Profit Margin
    margin = fund.get('profit_margin')
    if margin:
        if margin > 0.20:
            signals.append("Strong profit margins (>20%)")
            score += 2
        elif margin > 0.10:
            signals.append("Healthy margins")
            score += 1
        elif margin < 0:
            signals.append("Negative margins - unprofitable")
            score -= 2
    
    # Revenue Growth
    growth = fund.get('revenue_growth')
    if growth:
        if growth > 0.20:
            signals.append("High revenue growth (>20%)")
            score += 2
        elif growth > 0.10:
            signals.append("Solid revenue growth")
            score += 1
        elif growth < 0:
            signals.append("Declining revenue")
            score -= 2
    
    # ROE
    roe = fund.get('return_on_equity')
    if roe:
        if roe > 0.20:
            signals.append("Excellent ROE (>20%)")
            score += 2
        elif roe > 0.15:
            signals.append("Good ROE")
            score += 1
        elif roe < 0.10:
            signals.append("Low ROE")
            score -= 1
    
    # Debt
    debt = fund.get('debt_to_equity')
    if debt:
        if debt < 50:
            signals.append("Low debt")
            score += 1
        elif debt > 100:
            signals.append("High debt levels")
            score -= 1
    
    # Beta
    beta = fund.get('beta')
    if beta:
        if beta < 1:
            signals.append("Lower volatility than market")
            score += 1
        elif beta > 1.5:
            signals.append("High volatility (beta > 1.5)")
            score -= 1
    
    return {
        'fundamental_score': score,
        'signals': signals,
        'summary': "Strong fundamentals" if score >= 5 else "Solid fundamentals" if score >= 2 else "Mixed fundamentals" if score >= -1 else "Weak fundamentals"
    }

def generate_recommendation(technical, fundamental, data):
    """Generate final recommendation"""
    total_score = technical['technical_score'] + fundamental['fundamental_score']
    
    # Adjust for analyst target
    fund = data['fundamentals']
    target = fund.get('target_price')
    current = data['current_price']
    
    if target and target > current * 1.15:
        total_score += 1
    elif target and target < current * 0.85:
        total_score -= 1
    
    # Generate recommendation
    if total_score >= 6:
        rec = "STRONG BUY"
        conviction = 9
    elif total_score >= 4:
        rec = "BUY"
        conviction = 7
    elif total_score >= 2:
        rec = "SPECULATIVE BUY"
        conviction = 5
    elif total_score >= 0:
        rec = "HOLD"
        conviction = 4
    elif total_score >= -2:
        rec = "REDUCE"
        conviction = 5
    else:
        rec = "SELL"
        conviction = 7
    
    return {
        'recommendation': rec,
        'conviction': conviction,
        'total_score': total_score
    }

def format_report(data, technical, fundamental, recommendation):
    """Format report for Telegram (ASCII tables)"""
    fund = data['fundamentals']
    
    # Market cap formatting
    mc = fund.get('market_cap', 0)
    if mc > 1e12:
        market_cap = f"${mc/1e12:.2f}T"
    elif mc > 1e9:
        market_cap = f"${mc/1e9:.2f}B"
    elif mc > 1e6:
        market_cap = f"${mc/1e6:.2f}M"
    else:
        market_cap = "N/A"
    
    # Change formatting
    change_emoji = "🟢" if data['change'] >= 0 else "🔴"
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║           📊 INVESTIQ RESEARCH AGENT REPORT                   ║
╚══════════════════════════════════════════════════════════════╝

🏢 {fund.get('name', data['ticker'])}
Ticker: {data['ticker']}  |  Sector: {fund.get('sector', 'N/A')}

═══════════════════════════════════════════════════════════════
💰 PRICE SNAPSHOT
═══════════════════════════════════════════════════════════════

Current:     ${data['current_price']:.2f}  {change_emoji} {data['change']:+.2f} ({data['change_pct']:+.2f}%)
52W Range:   ${data['low_52w']:.2f} - ${data['high_52w']:.2f}
Position:    {data['position_52w']:.1f}% from 52W low

═══════════════════════════════════════════════════════════════
📈 TECHNICAL ANALYSIS
═══════════════════════════════════════════════════════════════

Trend:       {technical['trend']}
RSI (14):    {data['rsi']:.1f}  ({technical['rsi_signal']})
Volume:      {data['volume_trend']}
Range:       {technical['range_signal']}

Moving Averages:
  20-day:  ${data['ma_20']:.2f}  ({'Above' if data['current_price'] > data['ma_20'] else 'Below'})
  50-day:  ${data['ma_50']:.2f}  ({'Above' if data['current_price'] > data['ma_50'] else 'Below'})
  200-day: ${data['ma_200']:.2f}  ({'Above' if data['current_price'] > data['ma_200'] else 'Below'})

Technical Score:  {technical['technical_score']:+d}/10

═══════════════════════════════════════════════════════════════
🏛️ FUNDAMENTAL ANALYSIS
═══════════════════════════════════════════════════════════════

Market Cap:     {market_cap}
P/E Ratio:      {fund.get('pe_ratio', 'N/A')}
Forward P/E:    {fund.get('forward_pe', 'N/A')}
PEG Ratio:      {fund.get('peg_ratio', 'N/A')}
Price/Book:     {fund.get('price_to_book', 'N/A')}
Profit Margin:  {f"{fund.get('profit_margin')*100:.1f}%" if fund.get('profit_margin') else 'N/A'}
Revenue Growth: {f"{fund.get('revenue_growth')*100:.1f}%" if fund.get('revenue_growth') else 'N/A'}
ROE:            {f"{fund.get('return_on_equity')*100:.1f}%" if fund.get('return_on_equity') else 'N/A'}
Debt/Equity:    {fund.get('debt_to_equity', 'N/A')}
Beta:           {fund.get('beta', 'N/A')}
Dividend Yield: {f"{fund.get('dividend_yield')*100:.2f}%" if fund.get('dividend_yield') else 'N/A'}

Key Signals:
"""
    
    for signal in fundamental['signals'][:5]:
        report += f"  • {signal}\n"
    
    report += f"""
Fundamental Assessment:  {fundamental['summary']}
Fundamental Score:       {fundamental['fundamental_score']:+d}/10

═══════════════════════════════════════════════════════════════
🎯 INVESTMENT RECOMMENDATION
═══════════════════════════════════════════════════════════════

RECOMMENDATION:  {recommendation['recommendation']}
CONVICTION:      {recommendation['conviction']}/10

Total Score: {recommendation['total_score']:+d}/20

═══════════════════════════════════════════════════════════════
📝 ANALYST CONSENSUS
═══════════════════════════════════════════════════════════════

Wall Street Rating: {fund.get('recommendation', 'N/A').upper()}
Target Price: ${fund.get('target_price', 'N/A')}

═══════════════════════════════════════════════════════════════
Generated by InvestIQ Research Agent 🦉
Not financial advice — DYOR
"""
    
    return report

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 research_agent.py <TICKER>")
        print("Example: python3 research_agent.py AAPL")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    
    # Fetch data
    data, error = get_stock_data(ticker)
    if error:
        print(f"❌ Error: {error}")
        sys.exit(1)
    
    # Run analyses
    technical = analyze_technicals(data)
    fundamental = analyze_fundamentals(data['fundamentals'])
    recommendation = generate_recommendation(technical, fundamental, data)
    
    # Generate report
    report = format_report(data, technical, fundamental, recommendation)
    
    print(report)
    
    # Also save to file
    filename = f"research_{ticker}_{datetime.now().strftime('%Y%m%d')}.txt"
    with open(filename, 'w') as f:
        f.write(report)
    print(f"\n💾 Report saved to: {filename}", file=sys.stderr)

if __name__ == "__main__":
    main()
