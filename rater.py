import yfinance as yf
import pandas as pd
import numpy as np
import os
import traceback
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

# Optional: DB-backed incremental updates
try:
    from market_data import MarketDB
    db = MarketDB()
except:
    db = None

# v5.0 Global Caches
_spy_cache = None
_sector_etf_cache = {}

def get_spy_data():
    """Fetch SPY data once per session and cache it"""
    global _spy_cache
    if _spy_cache is None:
        try:
            spy = yf.Ticker("SPY")
            _spy_cache = spy.history(period="1y")
        except:
            _spy_cache = pd.DataFrame()  # Empty fallback
    return _spy_cache

def get_sector_etf_data(sector_etf):
    """Fetch sector ETF data once per ETF per session and cache it"""
    global _sector_etf_cache
    if sector_etf not in _sector_etf_cache:
        try:
            etf = yf.Ticker(sector_etf)
            _sector_etf_cache[sector_etf] = etf.history(period="6mo")
        except:
            _sector_etf_cache[sector_etf] = pd.DataFrame()  # Empty fallback
    return _sector_etf_cache[sector_etf]

@dataclass
class CriterionResult:
    name: str
    category: str
    passed: bool
    value: str
    threshold: str
    points: int = 0

def get_ttm_growth(symbol, db_conn):
    """Calculate TTM growth from quarterly data"""
    try:
        c = db_conn.cursor()
        c.execute('''
            SELECT year, quarter, revenue FROM quarterly_revenue
            WHERE symbol = ? AND revenue IS NOT NULL
            ORDER BY year DESC, quarter DESC
            LIMIT 12
        ''', (symbol,))
        rows = c.fetchall()

        if len(rows) < 8:
            return None, None

        # TTM Current = sum of most recent 4 quarters
        ttm_current = sum(r[2] for r in rows[0:4])
        # TTM Prior Year = sum of quarters 5-8
        ttm_prior = sum(r[2] for r in rows[4:8])

        rev_g = None
        rev_g_prior = None

        if ttm_prior > 0:
            rev_g = (ttm_current - ttm_prior) / ttm_prior

        # TTM 2 Years Ago = sum of quarters 9-12
        if len(rows) >= 12:
            ttm_2yr = sum(r[2] for r in rows[8:12])
            if ttm_2yr > 0:
                rev_g_prior = (ttm_prior - ttm_2yr) / ttm_2yr

        return rev_g, rev_g_prior
    except:
        return None, None

class BreakoutRater:
    def __init__(self):
        # v5.0 Enhanced Algorithm - 100 Point Scale
        self.weights = {
            # Technical (48 pts)
            "Breakout Pattern": 22,      # Core timing
            "Consolidation": 10,         # Base quality  
            "Volume Dry-up": 8,          # Institutional quiet
            "Trend Alignment": 8,        # Direction
            
            # Growth (38 pts)
            "Sales Growth": 30,          # Revenue engine (graduated)
            "Earnings Acceleration": 8,  # QoQ EPS growth acceleration (NEW v5.0)
            
            # Quality (18 pts)
            "ROE Quality": 5,            # Capital efficiency
            "Operating Margin": 5,       # Profitability
            "Valuation Sanity": 5,       # PEG < 2.0
            "FCF Quality": 3,            # Cash generation
            
            # Timing (10 pts)
            "52W Proximity": 5,          # Near highs
            "Volatility Compression": 5, # ATR squeeze (FIXED: 10d vs 50d)
            
            # Context (10 pts)
            "Industry Strength": 5,      # Dynamic sector strength (NEW v5.0)
            "Relative Strength": 5,      # Real RS vs SPY (ENHANCED v5.0)
            
            # Size Penalty
            "Size Factor": 0             # -5 to -10 penalty
        }
        
        # Sector to ETF mapping for dynamic sector strength
        self.SECTOR_ETFS = {
            'Technology': 'XLK',
            'Consumer Cyclical': 'XLY',
            'Energy': 'XLE',
            'Basic Materials': 'XLB',
            'Industrials': 'XLI',
            'Healthcare': 'XLV',
            'Financial Services': 'XLF',
            'Consumer Defensive': 'XLP',
            'Utilities': 'XLU',
            'Real Estate': 'XLRE',
            'Communication Services': 'XLC'
        }

    def rate_stock(self, ticker):
        ticker = ticker.upper()
        try:
            stock = yf.Ticker(ticker)
            # 1. Get Price History (Database-first optimized)
            if db:
                hist = db.get_history_smart(ticker)
            else:
                hist = stock.history(period="1y")  # Need 1y for 52w high
            
            if hist is None or hist.empty or len(hist) < 130:
                return {"error": "Insufficient history (130 days required)"}
            
            info = stock.info
            results = []
            
            # --- 1. MOMENTUM & BREAKOUT ---
            close = hist['Close']
            sma50 = close.rolling(50).mean().iloc[-1]
            sma200 = close.rolling(200).mean().iloc[-1]
            current_price = close.iloc[-1]
            price_above_50 = bool(current_price > sma50)
            
            # Trend Alignment (8 pts)
            if pd.notna(sma200):
                passed_trend = bool(price_above_50 and (sma50 > sma200))
                trend_desc = f"${float(current_price):.2f} > ${float(sma50):.2f} > ${float(sma200):.2f}"
            else:
                sma50_prev = close.rolling(50).mean().iloc[-5]
                passed_trend = bool(price_above_50 and sma50 > sma50_prev)
                trend_desc = f"${float(current_price):.2f} > ${float(sma50):.2f} (rising)"
            results.append(CriterionResult("Trend Alignment", "Momentum", passed_trend, trend_desc, "Price > SMA50 > SMA200", 8 if passed_trend else 0))

            # Breakout Pattern (22 pts)
            window = hist.iloc[-130:-5]
            high_1 = window.iloc[:65]['High'].max()
            high_2 = window.iloc[65:]['High'].max()
            drift = (high_2 - high_1) / high_1
            base_ceiling = max(high_1, high_2)
            dist = (base_ceiling - close.iloc[-1]) / base_ceiling
            passed_bo = bool((drift < 0.10) and (dist < 0.05))
            results.append(CriterionResult("Breakout Pattern", "Breakout", passed_bo, f"{float(dist)*100:+.1f}% from Base", "Flat Base + Near High", 22 if passed_bo else 0))

            # Consolidation (10 pts)
            depth = (window['High'].max() - window['Low'].min()) / window['High'].max()
            passed_con = bool(depth < 0.45)
            results.append(CriterionResult("Consolidation", "Breakout", passed_con, f"Depth {float(depth)*100:.0f}%", "Depth < 40%", 10 if passed_con else 0))

            # Volume Dry-up (8 pts)
            v5, v50 = hist['Volume'].tail(5).mean(), hist['Volume'].tail(50).mean()
            passed_vol = bool(v5 < (v50 * 1.2))
            results.append(CriterionResult("Volume Dry-up", "Breakout", passed_vol, f"{float(v5/v50):.1f}x avg", "Vol < 1.2x Avg", 8 if passed_vol else 0))

            # --- 2. TIMING SIGNALS ---
            # 52-Week Proximity (5 pts)
            high_52w = hist['High'].max()
            proximity = current_price / high_52w
            passed_52w = bool(proximity > 0.90)
            results.append(CriterionResult("52W Proximity", "Timing", passed_52w, f"{float(proximity)*100:.1f}%", "> 90% of 52W High", 5 if passed_52w else 0))
            
            # Volatility Compression (5 pts) - FIXED v5.0: 10d vs 50d
            atr_10d = (hist['High'].tail(10) - hist['Low'].tail(10)).mean()
            atr_50d = (hist['High'].tail(50) - hist['Low'].tail(50)).mean()
            passed_atr = bool(atr_10d < 0.75 * atr_50d)  # 25% compression = squeeze
            atr_val = f"{float(atr_10d/atr_50d)*100:.0f}% of 50d ATR" if atr_50d > 0 else "N/A"
            results.append(CriterionResult("Volatility Compression", "Timing", passed_atr, atr_val, "10d ATR < 75% of 50d ATR", 5 if passed_atr else 0))

            # --- 3. GROWTH & QUALITY ---
            # Sales Growth with Graduated Scoring (0-30 pts) - ENHANCED v5.0
            # Uses quarterly data for Trailing Twelve Months comparison
            
            rev_g = info.get('revenueGrowth')  # Fallback to yfinance TTM
            rev_g_prior = None
            
            # Calculate TTM from quarterly data if available
            try:
                if db:
                    c = db.conn.cursor()
                    # Get last 12 quarters for TTM calculations
                    c.execute('''
                        SELECT year, quarter, revenue FROM quarterly_revenue
                        WHERE symbol = ? AND revenue IS NOT NULL
                        ORDER BY year DESC, quarter DESC
                        LIMIT 12
                    ''', (ticker,))
                    rows = c.fetchall()
                    
                    if len(rows) >= 8:
                        # TTM Current = sum of most recent 4 quarters
                        ttm_current = sum(r[2] for r in rows[0:4])
                        # TTM Prior Year = sum of quarters 5-8 (4 quarters ago)
                        ttm_prior = sum(r[2] for r in rows[4:8])
                        
                        if ttm_prior > 0:
                            rev_g = (ttm_current - ttm_prior) / ttm_prior
                        
                        # TTM 2 Years Ago = sum of quarters 9-12 (if available)
                        if len(rows) >= 12:
                            ttm_2yr = sum(r[2] for r in rows[8:12])
                            if ttm_2yr > 0:
                                rev_g_prior = (ttm_prior - ttm_2yr) / ttm_2yr
            except:
                pass
            
            # For prior year, fallback to fiscal year data if TTM not available
            if rev_g_prior is None:
                try:
                    if db:
                        c = db.conn.cursor()
                        c.execute('''
                            SELECT revenue_growth_yoy FROM revenue_history 
                            WHERE symbol = ? AND revenue_growth_yoy IS NOT NULL
                            ORDER BY fiscal_year DESC LIMIT 1 OFFSET 1
                        ''', (ticker,))
                        row = c.fetchone()
                        if row:
                            rev_g_prior = row[0]
                except:
                    pass
            
            # GRADUATED SCORING (v5.0): Softer gate, rewards tiers
            if rev_g is None:
                sales_points = 0
                growth_display = "N/A"
            else:
                # Current year points (0-15)
                if rev_g >= 0.20:
                    current_pts = 15
                elif rev_g >= 0.10:
                    current_pts = 12
                elif rev_g >= 0.05:
                    current_pts = 6
                else:
                    current_pts = 0
                
                # Prior year points (0-12)
                if rev_g_prior is not None:
                    if rev_g_prior >= 0.20:
                        prior_pts = 12
                    elif rev_g_prior >= 0.10:
                        prior_pts = 9
                    elif rev_g_prior >= 0.05:
                        prior_pts = 4
                    else:
                        prior_pts = 0
                else:
                    prior_pts = 0
                
                # Consistency bonus: both years >= 10% = +3
                consistency_bonus = 3 if (rev_g >= 0.10 and rev_g_prior is not None and rev_g_prior >= 0.10) else 0
                
                sales_points = current_pts + prior_pts + consistency_bonus  # max 30
                
                if rev_g_prior is not None:
                    growth_display = f"Cur: {float(rev_g)*100:.1f}%, Prior: {float(rev_g_prior)*100:.1f}%"
                else:
                    growth_display = f"Current: {float(rev_g)*100:.1f}%"
            
            results.append(CriterionResult("Sales Growth (2yr)", "Growth", sales_points > 0, growth_display, "Graduated: 20%/10%/5% tiers", int(sales_points)))

            # Earnings Acceleration (8 pts) - NEW v5.0
            # Fetch quarterly EPS and check if growth is ACCELERATING
            earnings_accel_pts = 0
            earnings_accel_val = "N/A"
            try:
                # Try new API first: quarterly income statement
                quarterly_income = stock.quarterly_income_stmt
                if quarterly_income is not None and not quarterly_income.empty and 'Net Income' in quarterly_income.index:
                    # Get Net Income values (most recent quarters first in columns)
                    net_income = quarterly_income.loc['Net Income'].dropna()
                    if len(net_income) >= 3:
                        # Reverse to chronological order (oldest first)
                        net_income_values = net_income.values[::-1]
                        
                        # Calculate growth rates between consecutive quarters
                        growth_rates = []
                        for i in range(1, min(len(net_income_values), 4)):
                            if net_income_values[i-1] != 0:
                                gr = (net_income_values[i] - net_income_values[i-1]) / abs(net_income_values[i-1])
                                growth_rates.append(gr)
                        
                        if len(growth_rates) >= 2:
                            # Check if growth rates are increasing (acceleration)
                            accelerating = all(growth_rates[i] > growth_rates[i-1] for i in range(1, len(growth_rates)))
                            positive = all(gr > 0 for gr in growth_rates)
                            
                            if accelerating and positive:
                                earnings_accel_pts = 8
                                earnings_accel_val = "Accelerating"
                            elif positive:
                                earnings_accel_pts = 4
                                earnings_accel_val = "Positive, flat"
                            else:
                                earnings_accel_pts = 0
                                earnings_accel_val = "Decelerating/Negative"
                        else:
                            earnings_accel_val = "Insufficient quarters"
            except Exception as e:
                earnings_accel_val = "Data unavailable"
            
            results.append(CriterionResult("Earnings Acceleration", "Growth", earnings_accel_pts > 0, earnings_accel_val, "QoQ growth accelerating", earnings_accel_pts))

            # ROE Quality (5 pts)
            roe = info.get('returnOnEquity')
            passed_roe = bool(roe is not None and roe > 0.15)
            results.append(CriterionResult("ROE Quality", "Quality", passed_roe, f"{float(roe)*100:.1f}%" if roe else "N/A", "> 15%", 5 if passed_roe else 0))

            # Operating Margin (5 pts)
            marg = info.get('operatingMargins')
            passed_marg = bool(marg is not None and marg > 0.10)
            results.append(CriterionResult("Operating Margin", "Quality", passed_marg, f"{float(marg)*100:.1f}%" if marg else "N/A", "> 10%", 5 if passed_marg else 0))

            # Valuation Sanity (5 pts) - PEG < 2.0
            peg = info.get('pegRatio')
            passed_peg = bool(peg is not None and peg < 2.0 and peg > 0)
            results.append(CriterionResult("Valuation Sanity", "Quality", passed_peg, f"{float(peg):.2f}" if peg else "N/A", "PEG < 2.0", 5 if passed_peg else 0))

            # FCF Quality (3 pts)
            fcf = info.get('freeCashflow')
            passed_fcf = bool(fcf and fcf > 0)
            results.append(CriterionResult("FCF Quality", "Quality", passed_fcf, "Positive" if passed_fcf else "Negative/NA", "FCF > 0", 3 if passed_fcf else 0))

            # --- 4. CONTEXT ---
            # Industry Strength (5 pts) - DYNAMIC v5.0
            # Compare sector ETF performance vs SPY over 3 months
            sector = info.get('sector', '')
            sector_etf = self.SECTOR_ETFS.get(sector)
            passed_ind = False
            ind_val = sector or "Unknown"
            
            if sector_etf:
                try:
                    spy_hist = get_spy_data()
                    etf_hist = get_sector_etf_data(sector_etf)
                    
                    if not spy_hist.empty and not etf_hist.empty and len(spy_hist) >= 63 and len(etf_hist) >= 63:
                        spy_close = spy_hist['Close']
                        etf_close = etf_hist['Close']
                        
                        # 3-month returns
                        etf_3m_return = (etf_close.iloc[-1] - etf_close.iloc[-63]) / etf_close.iloc[-63]
                        spy_3m_return = (spy_close.iloc[-1] - spy_close.iloc[-63]) / spy_close.iloc[-63]
                        
                        sector_outperformance = etf_3m_return - spy_3m_return
                        passed_ind = sector_outperformance > 0
                        
                        ind_val = f"{sector} ({sector_etf}: {float(sector_outperformance)*100:+.1f}% vs SPY)"
                except:
                    ind_val = f"{sector} (no data)"
            
            results.append(CriterionResult("Industry Strength", "Context", passed_ind, ind_val, "Sector outperforming SPY (3mo)", 5 if passed_ind else 0))
            
            # Relative Strength (5 pts) - REAL RS v5.0
            # Calculate 6-month stock return vs SPY
            rs_points = 0
            rs_val = "N/A"
            
            try:
                spy_hist = get_spy_data()
                
                if not spy_hist.empty and len(close) >= 130 and len(spy_hist) >= 130:
                    # 6-month returns (130 trading days ≈ 6 months)
                    price_6m_ago = close.iloc[-130]
                    stock_6m_return = (current_price - price_6m_ago) / price_6m_ago
                    
                    spy_close = spy_hist['Close']
                    spy_6m_return = (spy_close.iloc[-1] - spy_close.iloc[-130]) / spy_close.iloc[-130]
                    
                    # RS = relative outperformance
                    relative_strength = stock_6m_return - spy_6m_return
                    
                    # Score: outperforming SPY by >10% = 5pts, >5% = 3pts, >0% = 1pt
                    if relative_strength > 0.10:
                        rs_points = 5
                    elif relative_strength > 0.05:
                        rs_points = 3
                    elif relative_strength > 0:
                        rs_points = 1
                    else:
                        rs_points = 0
                    
                    rs_val = f"{float(relative_strength)*100:+.1f}% vs SPY (6mo)"
                else:
                    rs_val = "Insufficient data"
            except:
                rs_val = "Error calculating RS"
            
            passed_rs = rs_points > 0
            results.append(CriterionResult("Relative Strength", "Context", passed_rs, rs_val, ">0% outperformance vs SPY", rs_points))

            # --- 5. SIZE PENALTY ---
            market_cap = info.get('marketCap', 0)
            size_penalty = 0
            if market_cap > 1_000_000_000_000:  # $1T+
                size_penalty = -10
            elif market_cap > 500_000_000_000:  # $500B+
                size_penalty = -5
            
            if size_penalty < 0:
                results.append(CriterionResult("Size Factor", "Context", False, f"${market_cap/1e12:.1f}T" if market_cap > 1e12 else f"${market_cap/1e9:.0f}B", "Large Cap Penalty", size_penalty))

            # Final Score Calculation (0-100)
            score = min(100, int(sum(r.points for r in results)))  # Cap at 100
            
            # Tighter grading: A=70+ (70% of max), B=55-69, C=40-54, D=25-39, F=<25
            grade = 'A' if score >= 70 else 'B' if score >= 55 else 'C' if score >= 40 else 'D' if score >= 25 else 'F'

            technical_score = int(sum(r.points for r in results if r.category in ["Momentum", "Breakout", "Timing"]))
            growth_score = int(sum(r.points for r in results if r.category == "Growth"))
            quality_score = int(sum(r.points for r in results if r.category == "Quality"))
            context_score = int(sum(r.points for r in results if r.category == "Context"))

            # News Relay
            news_items = []
            try:
                raw_news = stock.news or []
                for n in raw_news[:5]:
                    content = n.get('content', {})
                    title = content.get('title')
                    publisher = content.get('provider', {}).get('displayName')
                    link = content.get('canonicalUrl', {}).get('url')
                    pub_date = content.get('pubDate')
                    
                    if title:
                        time_str = "Recently"
                        if pub_date:
                            try:
                                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                                time_str = dt.strftime('%b %d, %H:%M')
                            except:
                                time_str = pub_date[:16] if pub_date else "Recently"
                        
                        news_items.append({
                            "title": title,
                            "publisher": publisher or "Yahoo Finance",
                            "link": link,
                            "time": time_str
                        })
            except Exception:
                pass

            target_mean = info.get('targetMeanPrice')
            if target_mean: target_mean = float(target_mean)

            return {
                "ticker": ticker,
                "name": str(info.get('shortName', ticker)),
                "sector": str(info.get('sector', 'N/A')),
                "industry": str(info.get('industry', 'N/A')),
                "score": score,
                "grade": grade,
                "max_score": 100,
                "technical_score": technical_score,
                "growth_score": growth_score,
                "quality_score": quality_score,
                "context_score": context_score,
                "results": [asdict(r) for r in results],
                "news": news_items,
                "market_cap": market_cap,
                "valuation": {
                    "forward_pe": info.get('forwardPE'),
                    "trailing_pe": info.get('trailingPE'),
                    "peg_ratio": info.get('pegRatio'),
                    "book_value": info.get('bookValue'),
                    "price_to_book": info.get('priceToBook'),
                    "roe": info.get('returnOnEquity')
                },
                "opinions": {
                    "recommendation": str(info.get('recommendationKey', 'N/A')).replace('_', ' ').title(),
                    "target_mean": target_mean,
                    "analysts": info.get('numberOfAnalystOpinions')
                }
            }
        except Exception as e:
            return {"error": str(e), "trace": traceback.format_exc()}

if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
        rater = BreakoutRater()
        result = rater.rate_stock(ticker)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python rater.py TICKER")
