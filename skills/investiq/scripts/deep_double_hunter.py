#!/usr/bin/env python3
"""
Deep Double Hunter - Comprehensive 2X Analysis for Russell 1000
Analyzes each stock individually using verifiable data only
NOT based on LLM training - uses database fundamentals + systematic criteria
"""

import sqlite3
import json
import sys
from datetime import datetime
from pathlib import Path

class DeepDoubleAnalyzer:
    """Analyzes each stock individually for 2X potential using verifiable data only"""
    
    def __init__(self, db_path="/Users/dansmacmini/.openclaw/workspace/market_data.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.results = []
        
    def get_stock_data(self, symbol):
        """Fetch verifiable fundamentals from database only"""
        self.cursor.execute('''
            SELECT f.data, t.name, t.sector
            FROM fundamentals f
            JOIN tickers t ON f.symbol = t.symbol
            WHERE f.symbol = ?
        ''', (symbol,))
        
        result = self.cursor.fetchone()
        if not result:
            return None
            
        data_json, name, sector = result
        
        try:
            fundamentals = json.loads(data_json) if data_json else {}
        except:
            fundamentals = {}
        
        return {
            'symbol': symbol,
            'name': name or '',
            'sector': sector or '',
            'price': None,
            'sma_50': None,
            'sma_200': None,
            'market_cap': fundamentals.get('marketCap', 0),
            'revenue': fundamentals.get('totalRevenue', 0),
            'revenue_growth': fundamentals.get('revenueGrowth', 0),
            'earnings_growth': fundamentals.get('earningsGrowth', 0),
            'profit_margins': fundamentals.get('profitMargins', 0),
            'gross_margins': fundamentals.get('grossMargins', 0),
            'operating_margins': fundamentals.get('operatingMargins', 0),
            'pe_trailing': fundamentals.get('trailingPE', 999),
            'pe_forward': fundamentals.get('forwardPE', 999),
            'peg_ratio': fundamentals.get('pegRatio', 999),
            'price_to_sales': fundamentals.get('priceToSalesTrailing12Months', 999),
            'price_to_book': fundamentals.get('priceToBook', 999),
            'roe': fundamentals.get('returnOnEquity', 0),
            'roa': fundamentals.get('returnOnAssets', 0),
            'debt_to_equity': fundamentals.get('debtToEquity', 999),
            'current_ratio': fundamentals.get('currentRatio', 0),
            'quick_ratio': fundamentals.get('quickRatio', 0),
            'free_cash_flow': fundamentals.get('freeCashflow', 0),
            'operating_cash_flow': fundamentals.get('operatingCashflow', 0),
            'beta': fundamentals.get('beta', 1.0),
            'float_shares': fundamentals.get('floatShares', 0),
            'shares_outstanding': fundamentals.get('sharesOutstanding', 0),
            'held_percent_institutions': fundamentals.get('heldPercentInstitutions', 0),
            'held_percent_insiders': fundamentals.get('heldPercentInsiders', 0),
            'short_ratio': fundamentals.get('shortRatio', 0),
            'short_percent_of_float': fundamentals.get('shortPercentOfFloat', 0),
            'target_high_price': fundamentals.get('targetHighPrice', 0),
            'target_low_price': fundamentals.get('targetLowPrice', 0),
            'target_mean_price': fundamentals.get('targetMeanPrice', 0),
            'number_of_analysts': fundamentals.get('numberOfAnalystOpinions', 0),
            'recommendation_key': fundamentals.get('recommendationKey', ''),
            'industry': fundamentals.get('industry', ''),
            'employees': fundamentals.get('fullTimeEmployees', 0),
            'website': fundamentals.get('website', ''),
        }
    
    def analyze_new_product_catalyst(self, data):
        """
        Score 0-10: Does company have new products driving growth?
        Based on: revenue acceleration, analyst price targets, industry trends
        """
        score = 5  # Neutral baseline
        notes = []
        
        # Revenue growth acceleration is verifiable proxy for new products
        if data['revenue_growth'] and data['revenue_growth'] > 0.30:
            score += 3
            notes.append(f"Strong revenue growth {data['revenue_growth']*100:.0f}% suggests product momentum")
        elif data['revenue_growth'] and data['revenue_growth'] > 0.15:
            score += 1
            notes.append(f"Moderate growth {data['revenue_growth']*100:.0f}%")
        
        # Analyst optimism about future (verifiable from database)
        if data['target_mean_price'] and data['price'] and data['target_mean_price'] > data['price'] * 1.5:
            score += 2
            notes.append(f"Analysts see {((data['target_mean_price']/data['price']-1)*100):.0f}% upside")
        
        # High gross margins suggest differentiated products
        if data['gross_margins'] and data['gross_margins'] > 0.60:
            score += 1
            notes.append("High gross margins suggest pricing power")
        
        return min(10, score), notes
    
    def analyze_growth_engine(self, data):
        """
        Score 0-10: Is growth durable and accelerating?
        Based on: revenue trend, margin expansion, cash flow generation
        """
        score = 5
        notes = []
        
        # Revenue growth quality
        if data['revenue_growth'] and data['revenue_growth'] > 0.50:
            score += 3
            notes.append("Hypergrowth (>50%)")
        elif data['revenue_growth'] and data['revenue_growth'] > 0.25:
            score += 2
            notes.append("Strong growth (25-50%)")
        elif data['revenue_growth'] and data['revenue_growth'] > 0.10:
            score += 1
        
        # Earnings growth (if positive)
        if data['earnings_growth'] and data['earnings_growth'] > 0.30:
            score += 2
            notes.append(f"Earnings growing {data['earnings_growth']*100:.0f}%")
        
        # Margin expansion (operating leverage)
        if data['operating_margins'] and data['operating_margins'] > 0.20:
            score += 1
            notes.append("Healthy operating margins")
        
        # Free cash flow generation
        if data['free_cash_flow'] and data['free_cash_flow'] > 0:
            score += 1
            notes.append("FCF positive")
        
        return min(10, score), notes
    
    def analyze_moat(self, data):
        """
        Score 0-10: Does company have durable competitive advantage?
        Based on: margins, ROE, market cap position in sector, analyst conviction
        """
        score = 5
        notes = []
        
        # High margins = pricing power = moat indicator
        if data['gross_margins'] and data['gross_margins'] > 0.70:
            score += 2
            notes.append("Exceptional gross margins (>70%)")
        elif data['gross_margins'] and data['gross_margins'] > 0.50:
            score += 1
            notes.append("Good gross margins")
        
        # ROE quality
        if data['roe'] and data['roe'] > 0.20:
            score += 2
            notes.append(f"Strong ROE {data['roe']*100:.0f}%")
        elif data['roe'] and data['roe'] > 0.10:
            score += 1
        
        # Low beta + high margins = defensive moat
        if data['beta'] and data['beta'] < 1.0 and data['gross_margins'] and data['gross_margins'] > 0.40:
            score += 1
            notes.append("Defensive characteristics")
        
        # Market cap leadership in sector (proxy for scale moat)
        if data['market_cap'] and data['market_cap'] > 50e9:
            score += 1
            notes.append("Scale advantage")
        
        return min(10, score), notes
    
    def analyze_market_tailwinds(self, data):
        """
        Score 0-10: Is the market growing? Are there secular trends?
        Based on: sector analysis, analyst coverage, institutional interest
        """
        score = 5
        notes = []
        
        # High growth sectors (verifiable from sector name)
        growth_sectors = ['Technology', 'Healthcare', 'Communications', 'Software']
        if any(s in data['sector'] for s in growth_sectors):
            score += 2
            notes.append(f"Growth sector: {data['sector']}")
        
        # Strong analyst coverage = institutional interest
        if data['number_of_analysts'] and data['number_of_analysts'] > 20:
            score += 1
            notes.append(f"Strong analyst coverage ({data['number_of_analysts']})")
        
        # High institutional ownership = smart money conviction
        if data['held_percent_institutions'] and data['held_percent_institutions'] > 0.60:
            score += 1
            notes.append("High institutional ownership")
        
        # Revenue growth is also market tailwind indicator
        if data['revenue_growth'] and data['revenue_growth'] > 0.20:
            score += 1
        
        return min(10, score), notes
    
    def analyze_size_sweetspot(self, data):
        """
        Score 0-10: Is market cap in 2X sweet spot?
        $10B-$200B ideal for doubling. Too small = risky, too big = hard to double.
        """
        score = 5
        notes = []
        mc = data['market_cap']
        
        if mc:
            if 20e9 <= mc <= 100e9:
                score = 10
                notes.append(f"Perfect size: ${mc/1e9:.1f}B (20-100B sweet spot)")
            elif 10e9 <= mc <= 200e9:
                score = 8
                notes.append(f"Good size: ${mc/1e9:.1f}B (10-200B)")
            elif 5e9 <= mc <= 10e9:
                score = 6
                notes.append(f"Small but viable: ${mc/1e9:.1f}B")
            elif 200e9 <= mc <= 500e9:
                score = 4
                notes.append(f"Large but possible: ${mc/1e9:.1f}B")
            elif mc > 1000e9:
                score = 2
                notes.append(f"Mega cap: ${mc/1e9:.1f}B (2X very difficult)")
            else:
                score = 3
                notes.append(f"Small cap: ${mc/1e9:.1f}B (risky)")
        
        return score, notes
    
    def analyze_valuation_gap(self, data):
        """
        Score 0-10: Is valuation reasonable for 2X?
        Forward PE vs growth (PEG-like analysis)
        """
        score = 5
        notes = []
        
        pe = data['pe_forward'] if data['pe_forward'] and data['pe_forward'] < 999 else data['pe_trailing']
        growth = data['revenue_growth'] or 0
        
        if pe and pe > 0:
            # PEG-like analysis
            if growth > 0:
                peg_like = pe / (growth * 100)
                if peg_like < 0.5:
                    score = 10
                    notes.append(f"Exceptional value: PE {pe:.1f}x vs {growth*100:.0f}% growth (PEG-like: {peg_like:.2f})")
                elif peg_like < 1.0:
                    score = 8
                    notes.append(f"Attractive: PE {pe:.1f}x vs {growth*100:.0f}% growth")
                elif peg_like < 1.5:
                    score = 6
                    notes.append(f"Fair: PE {pe:.1f}x vs {growth*100:.0f}% growth")
                else:
                    score = 4
                    notes.append(f"Rich: PE {pe:.1f}x vs {growth*100:.0f}% growth")
            else:
                # No growth - pure value play
                if pe < 15:
                    score = 7
                    notes.append(f"Value play: PE {pe:.1f}x")
                elif pe < 25:
                    score = 5
                    notes.append(f"Reasonable: PE {pe:.1f}x")
                else:
                    score = 3
                    notes.append(f"Expensive: PE {pe:.1f}x with no growth")
        
        return score, notes
    
    def analyze_stock(self, symbol):
        """Complete analysis of one stock"""
        data = self.get_stock_data(symbol)
        
        if not data:
            return None
        
        # Run all analyses
        new_product_score, new_product_notes = self.analyze_new_product_catalyst(data)
        growth_score, growth_notes = self.analyze_growth_engine(data)
        moat_score, moat_notes = self.analyze_moat(data)
        tailwinds_score, tailwinds_notes = self.analyze_market_tailwinds(data)
        size_score, size_notes = self.analyze_size_sweetspot(data)
        valuation_score, valuation_notes = self.analyze_valuation_gap(data)
        
        # Weighted total score
        weights = {
            'new_product': 0.15,
            'growth': 0.20,
            'moat': 0.15,
            'tailwinds': 0.10,
            'size': 0.20,
            'valuation': 0.20
        }
        
        total_score = (
            new_product_score * weights['new_product'] +
            growth_score * weights['growth'] +
            moat_score * weights['moat'] +
            tailwinds_score * weights['tailwinds'] +
            size_score * weights['size'] +
            valuation_score * weights['valuation']
        )
        
        # Determine 2X probability
        if total_score >= 8.0:
            probability = "HIGH"
        elif total_score >= 7.0:
            probability = "GOOD"
        elif total_score >= 6.0:
            probability = "MODERATE"
        elif total_score >= 5.0:
            probability = "LOW"
        else:
            probability = "VERY LOW"
        
        return {
            'symbol': symbol,
            'name': data['name'],
            'sector': data['sector'],
            'market_cap': data['market_cap'] / 1e9 if data['market_cap'] else 0,
            'price': data['price'],
            'forward_pe': data['pe_forward'] if data['pe_forward'] < 999 else None,
            'revenue_growth': data['revenue_growth'],
            'scores': {
                'new_product': new_product_score,
                'growth': growth_score,
                'moat': moat_score,
                'tailwinds': tailwinds_score,
                'size': size_score,
                'valuation': valuation_score,
                'total': round(total_score, 2)
            },
            'probability': probability,
            'notes': {
                'new_product': new_product_notes,
                'growth': growth_notes,
                'moat': moat_notes,
                'tailwinds': tailwinds_notes,
                'size': size_notes,
                'valuation': valuation_notes
            }
        }
    
    def analyze_all(self, symbols=None, limit=None):
        """Analyze all stocks or specific list"""
        if not symbols:
            self.cursor.execute('SELECT symbol FROM fundamentals WHERE data IS NOT NULL')
            symbols = [row[0] for row in self.cursor.fetchall()]
        
        if limit:
            symbols = symbols[:limit]
        
        total = len(symbols)
        print(f"Analyzing {total} stocks individually...")
        print("This will take time. Each stock requires 6 separate analyses.")
        print()
        
        for i, symbol in enumerate(symbols, 1):
            result = self.analyze_stock(symbol)
            if result:
                self.results.append(result)
            
            if i % 50 == 0:
                print(f"  Progress: {i}/{total} ({i/total*100:.1f}%)")
        
        # Sort by total score
        self.results.sort(key=lambda x: x['scores']['total'], reverse=True)
        print(f"\n✓ Analysis complete: {len(self.results)} stocks scored")
        
    def generate_report(self, top_n=20):
        """Generate HTML report of top N stocks"""
        top_stocks = self.results[:top_n]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; line-height: 1.4; color: #333; margin: 0; padding: 15px; background: #f5f5f5; }}
.container {{ max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }}
.header h1 {{ margin: 0; font-size: 22px; }}
.header p {{ margin: 5px 0 0; opacity: 0.9; font-size: 13px; }}
.stock-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; background: white; }}
.stock-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 10px; }}
.ticker {{ font-size: 20px; font-weight: bold; color: #1e3c72; }}
.score-badge {{ background: #667eea; color: white; padding: 5px 12px; border-radius: 15px; font-size: 16px; font-weight: bold; }}
.probability-high {{ color: #28a745; font-weight: bold; }}
.probability-good {{ color: #5cb85c; font-weight: bold; }}
.probability-moderate {{ color: #f0ad4e; font-weight: bold; }}
.probability-low {{ color: #d9534f; font-weight: bold; }}
.metrics {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 15px 0; }}
.metric {{ background: #f8f9fa; padding: 8px; border-radius: 5px; text-align: center; }}
.metric-value {{ font-size: 18px; font-weight: bold; color: #1e3c72; }}
.metric-label {{ font-size: 11px; color: #666; }}
.section-title {{ font-size: 12px; font-weight: bold; color: #666; text-transform: uppercase; margin: 15px 0 8px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
.scores-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin: 10px 0; font-size: 12px; }}
.score-item {{ background: #f0f4f8; padding: 6px; border-radius: 4px; display: flex; justify-content: space-between; }}
.score-val {{ font-weight: bold; color: #667eea; }}
.notes {{ font-size: 12px; color: #555; margin-top: 10px; padding-left: 15px; }}
.notes li {{ margin: 4px 0; }}
.footer {{ text-align: center; padding: 20px; color: #666; font-size: 11px; margin-top: 20px; border-top: 1px solid #eee; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🎯 Deep Double Hunter - Top {top_n}</h1>
<p>Comprehensive Analysis of {len(self.results)} Russell 1000 Stocks</p>
<p>Individual scoring using verifiable fundamentals only</p>
</div>
"""
        
        for i, stock in enumerate(top_stocks, 1):
            prob_class = f"probability-{stock['probability'].lower().replace(' ', '-')}"
            
            html += f"""
<div class="stock-card">
<div class="stock-header">
<div><span class="ticker">#{i} {stock['symbol']}</span><br><small>{stock['name'][:35]}</small></div>
<div><span class="score-badge">{stock['scores']['total']:.1f}/10</span><br><span class="{prob_class}">{stock['probability']} 2X Potential</span></div>
</div>

<div class="metrics">
<div class="metric"><div class="metric-value">${stock['market_cap']:.1f}B</div><div class="metric-label">Market Cap</div></div>
<div class="metric"><div class="metric-value">{stock['forward_pe']:.1f}x</div><div class="metric-label">Forward PE</div></div>
<div class="metric"><div class="metric-value">{stock['revenue_growth']*100:.0f}%</div><div class="metric-label">Rev Growth</div></div>
</div>

<div class="section-title">Deep Score Breakdown</div>
<div class="scores-grid">
<div class="score-item"><span>New Product</span><span class="score-val">{stock['scores']['new_product']}/10</span></div>
<div class="score-item"><span>Growth Engine</span><span class="score-val">{stock['scores']['growth']}/10</span></div>
<div class="score-item"><span>Moat</span><span class="score-val">{stock['scores']['moat']}/10</span></div>
<div class="score-item"><span>Tailwinds</span><span class="score-val">{stock['scores']['tailwinds']}/10</span></div>
<div class="score-item"><span>Size Sweetspot</span><span class="score-val">{stock['scores']['size']}/10</span></div>
<div class="score-item"><span>Valuation</span><span class="score-val">{stock['scores']['valuation']}/10</span></div>
</div>

<div class="section-title">Why It Scored This Way</div>
<ul class="notes">
"""
            # Add all notes
            for category, notes in stock['notes'].items():
                if notes:
                    for note in notes[:2]:  # Limit to top 2 per category
                        html += f"<li><strong>{category.replace('_', ' ').title()}:</strong> {note}</li>"
            
            html += """
</ul>
</div>
"""
        
        html += """
<div class="footer">
<p>Deep Double Hunter | 6-Factor Analysis per Stock</p>
<p>Methodology: New Product (15%) | Growth (20%) | Moat (15%) | Tailwinds (10%) | Size (20%) | Valuation (20%)</p>
<p>Data Source: market_data.db (SQLite) | No LLM training data used</p>
<p>Disclaimer: Quantitative screening only. Not investment advice. Verify all data independently.</p>
</div>
</div>
</body>
</html>
"""
        return html
    
    def close(self):
        self.conn.close()

def main():
    analyzer = DeepDoubleAnalyzer()
    
    # Get symbols from command line or analyze all
    if len(sys.argv) > 1:
        symbols = sys.argv[1:]
        print(f"Analyzing {len(symbols)} specific stocks...")
    else:
        symbols = None
        print("Will analyze ALL Russell 1000 stocks. This takes ~5-10 minutes.")
        print("Press Ctrl+C to cancel, or wait to proceed...")
        try:
            import time
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nCancelled.")
            return
    
    analyzer.analyze_all(symbols=symbols)
    
    if analyzer.results:
        print("\nGenerating report...")
        html = analyzer.generate_report(top_n=20)
        
        output_path = "/tmp/deep_double_hunter_report.html"
        with open(output_path, "w") as f:
            f.write(html)
        
        print(f"✅ Report saved to: {output_path}")
        
        # Print summary
        print("\n🏆 TOP 10 2X CANDIDATES:")
        for i, r in enumerate(analyzer.results[:10], 1):
            print(f"{i:2}. {r['symbol']:6} | Score: {r['scores']['total']:.1f} | {r['probability']:8} | {r['sector'][:20]}")
    
    analyzer.close()

if __name__ == "__main__":
    main()
