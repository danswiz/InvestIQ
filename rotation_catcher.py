#!/usr/bin/env python3
"""
Rotation Catcher v1.0 - 6-Signal Stock Rotation Detector
Scores stocks on rotation signals: RS divergence, earnings momentum, valuation gap,
stage breakout, volume accumulation, sector momentum.
Works for any stock in any sector — no hardcoded tickers or assumptions.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Sector to ETF mapping (auto-detected from stock info)
SECTOR_ETFS = {
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
    'Communication Services': 'XLC',
}

# Signal weights (sum to 1.0) — 6 signals
WEIGHTS = {
    'rs_divergence': 0.22,
    'earnings_revisions': 0.17,
    'valuation_gap': 0.17,
    'stage_breakout': 0.22,
    'volume_accumulation': 0.11,
    'sector_momentum': 0.11,
}


class RotationCatcher:
    """
    Session-persistent rotation detector with aggressive caching.
    
    Usage:
        rc = RotationCatcher()
        result = rc.score('AAPL')
        print(result['composite_score'])  # 0-100
        print(result['signal'])           # e.g. "ROTATION WATCH"
    """
    
    def __init__(self):
        self._spy_cache = None
        self._qqq_cache = None
        self._sector_etf_cache = {}
        
    def _get_spy_data(self):
        if self._spy_cache is None:
            try:
                self._spy_cache = yf.Ticker("SPY").history(period="1y", interval="1wk")
            except:
                self._spy_cache = pd.DataFrame()
        return self._spy_cache
    
    def _get_qqq_data(self):
        if self._qqq_cache is None:
            try:
                self._qqq_cache = yf.Ticker("QQQ").history(period="1y", interval="1wk")
            except:
                self._qqq_cache = pd.DataFrame()
        return self._qqq_cache
    
    def _get_sector_etf_data(self, etf_ticker):
        if etf_ticker not in self._sector_etf_cache:
            try:
                self._sector_etf_cache[etf_ticker] = yf.Ticker(etf_ticker).history(period="1y", interval="1wk")
            except:
                self._sector_etf_cache[etf_ticker] = pd.DataFrame()
        return self._sector_etf_cache[etf_ticker]
    
    def _calc_return(self, prices, weeks):
        if len(prices) < weeks:
            return None
        return (prices.iloc[-1] - prices.iloc[-weeks]) / prices.iloc[-weeks]
    
    def score(self, ticker):
        """
        Score a stock on 6 rotation signals.
        
        Returns dict with composite_score (0-100), signal classification,
        convergence_bonus, and per-signal breakdown.
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist_weekly = stock.history(period="1y", interval="1wk")
            hist_daily = stock.history(period="3mo", interval="1d")
            
            if hist_weekly.empty or len(hist_weekly) < 30:
                return self._empty_result(ticker, "Insufficient data")
            
            spy_weekly = self._get_spy_data()
            qqq_weekly = self._get_qqq_data()
            
            # Auto-detect sector ETF
            sector = info.get('sector', '')
            sector_etf_ticker = SECTOR_ETFS.get(sector)
            sector_etf_data = self._get_sector_etf_data(sector_etf_ticker) if sector_etf_ticker else None
            
            # Score all 6 signals
            signals = {
                'rs_divergence': self._signal_rs_divergence(hist_weekly, spy_weekly, qqq_weekly),
                'earnings_revisions': self._signal_earnings_revisions(info),
                'valuation_gap': self._signal_valuation_gap(info),
                'stage_breakout': self._signal_stage_breakout(hist_weekly, hist_daily),
                'volume_accumulation': self._signal_volume_accumulation(hist_weekly, hist_daily),
                'sector_momentum': self._signal_sector_momentum(sector_etf_data, spy_weekly, sector, sector_etf_ticker),
            }
            
            # Weighted composite
            composite = sum(
                signals[key]['score'] * WEIGHTS[key]
                for key in WEIGHTS
            )
            
            # Convergence bonus: multiple strong signals firing together
            high_count = sum(1 for sig in signals.values() if sig['score'] >= 60)
            if high_count >= 5:
                convergence_bonus = 10
            elif high_count >= 4:
                convergence_bonus = 7
            elif high_count >= 3:
                convergence_bonus = 4
            else:
                convergence_bonus = 0
            
            composite = min(100, round(composite + convergence_bonus, 1))
            
            # Classification
            if composite >= 80:
                signal = "STRONG ROTATION BUY"
            elif composite >= 60:
                signal = "ROTATION WATCH"
            elif composite >= 40:
                signal = "NEUTRAL"
            elif composite >= 20:
                signal = "WEAK"
            else:
                signal = "NO ROTATION"
            
            return {
                'ticker': ticker,
                'composite_score': composite,
                'signal': signal,
                'convergence_bonus': convergence_bonus,
                'signals': signals,
            }
            
        except Exception as e:
            return self._empty_result(ticker, str(e))
    
    def _empty_result(self, ticker, reason="Unknown"):
        return {
            'ticker': ticker,
            'composite_score': 0,
            'signal': 'NO DATA',
            'convergence_bonus': 0,
            'error': reason,
            'signals': {k: {'score': 0} for k in WEIGHTS},
        }
    
    # ─── SIGNAL 1: RS Divergence (max 100) ───
    def _signal_rs_divergence(self, hist_weekly, spy_weekly, qqq_weekly):
        score = 0
        details = {}
        close = hist_weekly['Close']
        
        # Mansfield RS vs SPY (52-week)
        if not spy_weekly.empty and len(spy_weekly) >= 52 and len(close) >= 52:
            stock_ret = self._calc_return(close, 52) or 0
            spy_ret = self._calc_return(spy_weekly['Close'], 52) or 0
            mansfield = (stock_ret - spy_ret) * 100
            details['mansfield_rs'] = round(mansfield, 1)
            if mansfield > 20: score += 30
            elif mansfield > 10: score += 20
            elif mansfield > 0: score += 10
        
        # RS vs QQQ (26-week)
        if not qqq_weekly.empty and len(qqq_weekly) >= 26 and len(close) >= 26:
            stock_ret = self._calc_return(close, 26) or 0
            qqq_ret = self._calc_return(qqq_weekly['Close'], 26) or 0
            rs_qqq = (stock_ret - qqq_ret) * 100
            details['rs_vs_qqq'] = round(rs_qqq, 1)
            if rs_qqq > 15: score += 25
            elif rs_qqq > 5: score += 15
            elif rs_qqq > 0: score += 8
        
        # RS Acceleration (last 8w vs prior 8w)
        if not spy_weekly.empty and len(close) >= 16 and len(spy_weekly) >= 16:
            rs_ratio = close / spy_weekly['Close'].reindex(close.index, method='ffill')
            rs_ratio = rs_ratio.dropna()
            if len(rs_ratio) >= 16:
                rs_recent = rs_ratio.iloc[-1] / rs_ratio.iloc[-8] - 1
                rs_prior = rs_ratio.iloc[-8] / rs_ratio.iloc[-16] - 1
                accel = (rs_recent - rs_prior) * 100
                details['rs_acceleration'] = round(accel, 2)
                if accel > 5: score += 25
                elif accel > 2: score += 15
                elif accel > 0: score += 8
        
        # Divergence: stock 12w vs QQQ 12w
        if not qqq_weekly.empty and len(close) >= 12 and len(qqq_weekly) >= 12:
            stock_12w = self._calc_return(close, 12) or 0
            qqq_12w = self._calc_return(qqq_weekly['Close'], 12) or 0
            div = (stock_12w - qqq_12w) * 100
            details['divergence'] = round(div, 1)
            if div > 15: score += 20
            elif div > 5: score += 12
            elif div > 0: score += 5
        
        return {'score': min(100, score), **details}
    
    # ─── SIGNAL 2: Earnings Revisions (max 100) ───
    def _signal_earnings_revisions(self, info):
        score = 0
        details = {}
        
        # Forward EPS growth
        fwd_eps = info.get('forwardEps')
        trail_eps = info.get('trailingEps')
        if fwd_eps and trail_eps and trail_eps > 0:
            growth = (fwd_eps / trail_eps - 1) * 100
            details['fwd_eps_growth'] = round(growth, 1)
            if growth > 100: score += 35
            elif growth > 50: score += 25
            elif growth > 25: score += 15
            elif growth > 10: score += 8
        
        # Revenue growth
        rev = info.get('revenueGrowth')
        if rev is not None:
            details['revenue_growth'] = round(rev * 100, 1)
            if rev > 0.50: score += 30
            elif rev > 0.25: score += 20
            elif rev > 0.10: score += 12
            elif rev > 0: score += 5
        
        # Earnings growth
        eg = info.get('earningsGrowth')
        if eg is not None:
            details['earnings_growth'] = round(eg * 100, 1)
            if eg > 1.0: score += 20
            elif eg > 0.50: score += 12
            elif eg > 0.20: score += 8
        
        # Analyst recommendation (1=strong buy, 5=sell)
        rec = info.get('recommendationMean')
        if rec:
            details['analyst_rec'] = round(rec, 2)
            if rec <= 1.5: score += 15
            elif rec <= 2.0: score += 10
            elif rec <= 2.5: score += 5
        
        return {'score': min(100, score), **details}
    
    # ─── SIGNAL 3: Valuation Gap (max 100) ───
    def _signal_valuation_gap(self, info):
        score = 0
        details = {}
        
        fwd_pe = info.get('forwardPE')
        peg = info.get('pegRatio')
        ps = info.get('priceToSalesTrailing12Months')
        
        # Forward P/E discount vs ~23x market avg
        if fwd_pe and fwd_pe > 0:
            details['forward_pe'] = round(fwd_pe, 1)
            if fwd_pe < 12: score += 35
            elif fwd_pe < 18: score += 25
            elif fwd_pe < 23: score += 15
            elif fwd_pe < 30: score += 5
            if fwd_pe > 50: score -= 10
        
        # PEG < 1 = undervalued for growth
        if peg and peg > 0:
            details['peg'] = round(peg, 2)
            if peg < 0.5: score += 30
            elif peg < 1.0: score += 20
            elif peg < 1.5: score += 10
        
        # Price-to-Sales
        if ps and ps > 0:
            details['ps_ratio'] = round(ps, 1)
            if ps < 3: score += 20
            elif ps < 6: score += 12
            elif ps < 10: score += 5
        
        # Coiled spring: high growth + low P/E
        fwd_eps = info.get('forwardEps')
        trail_eps = info.get('trailingEps')
        if fwd_eps and trail_eps and trail_eps > 0 and fwd_pe and fwd_pe < 15:
            eps_growth = (fwd_eps / trail_eps - 1)
            if eps_growth > 0.50:
                score += 15
                details['coiled_spring'] = True
        
        return {'score': max(0, min(100, score)), **details}
    
    # ─── SIGNAL 4: Weinstein Stage Breakout (max 100) ───
    def _signal_stage_breakout(self, hist_weekly, hist_daily):
        score = 0
        details = {}
        
        if len(hist_weekly) < 35:
            return {'score': 0, 'error': 'Insufficient weekly data'}
        
        close = hist_weekly['Close']
        volume = hist_weekly['Volume']
        ma30 = close.rolling(30).mean()
        current_price = close.iloc[-1]
        current_ma = ma30.iloc[-1]
        
        if pd.isna(current_ma):
            return {'score': 0, 'error': 'MA not available'}
        
        price_vs_ma = (current_price - current_ma) / current_ma * 100
        details['price_vs_30w_ma'] = round(price_vs_ma, 1)
        
        # MA slope (last 10 weeks)
        if len(ma30.dropna()) >= 10:
            ma_slope = (ma30.iloc[-1] - ma30.iloc[-10]) / ma30.iloc[-10] * 100
            details['ma_slope_10w'] = round(ma_slope, 2)
        else:
            ma_slope = 0
        
        # Fresh crossover detection (crossed within last 8 weeks)
        weeks_since_cross = None
        for i in range(1, min(12, len(close))):
            idx = -i
            if len(ma30) >= abs(idx) and pd.notna(ma30.iloc[idx]):
                if close.iloc[idx] < ma30.iloc[idx]:
                    weeks_since_cross = i - 1
                    break
        details['weeks_since_cross'] = weeks_since_cross
        
        if weeks_since_cross is not None:
            if 1 <= weeks_since_cross <= 4: score += 30
            elif 5 <= weeks_since_cross <= 8: score += 20
            elif weeks_since_cross == 0: score += 25
        
        # Price above MA + MA turning up
        if price_vs_ma > 0 and ma_slope > 0:
            if ma_slope > 3: score += 25
            elif ma_slope > 1: score += 15
            else: score += 8
        
        # Volume surge (4w vs 30w)
        avg_vol_30w = volume.iloc[-30:].mean()
        recent_vol_4w = volume.iloc[-4:].mean()
        if avg_vol_30w > 0:
            vol_ratio = recent_vol_4w / avg_vol_30w
            details['vol_breakout_ratio'] = round(vol_ratio, 2)
            if vol_ratio > 2.0: score += 25
            elif vol_ratio > 1.5: score += 18
            elif vol_ratio > 1.2: score += 10
        
        # Near/at 52-week high
        high_52w = close.iloc[-52:].max() if len(close) >= 52 else close.max()
        pct_from_high = (current_price / high_52w - 1) * 100
        details['pct_from_52w_high'] = round(pct_from_high, 1)
        if pct_from_high >= 0: score += 20
        elif pct_from_high > -5: score += 12
        elif pct_from_high > -15: score += 5
        
        return {'score': min(100, score), **details}
    
    # ─── SIGNAL 5: Volume Accumulation (max 100) ───
    def _signal_volume_accumulation(self, hist_weekly, hist_daily):
        score = 0
        details = {}
        
        close_w = hist_weekly['Close']
        vol_w = hist_weekly['Volume']
        
        if len(close_w) < 20:
            return {'score': 0, 'error': 'Insufficient data'}
        
        # Up/Down volume ratio (12 weeks)
        n = min(12, len(close_w) - 1)
        up_vol, down_vol = 0, 0
        for i in range(-n, 0):
            if close_w.iloc[i] > close_w.iloc[i - 1]:
                up_vol += vol_w.iloc[i]
            else:
                down_vol += vol_w.iloc[i]
        
        if down_vol > 0:
            ud_ratio = up_vol / down_vol
            details['up_down_vol_ratio'] = round(ud_ratio, 2)
            if ud_ratio > 2.5: score += 35
            elif ud_ratio > 1.8: score += 25
            elif ud_ratio > 1.3: score += 15
            elif ud_ratio > 1.0: score += 5
        
        # OBV trend (12 weeks)
        obv = (np.sign(close_w.diff()) * vol_w).cumsum()
        if len(obv) >= 12:
            obv_start = abs(obv.iloc[-12])
            if obv_start > 0:
                obv_slope = (obv.iloc[-1] - obv.iloc[-12]) / obv_start * 100
                details['obv_trend_12w'] = round(obv_slope, 1)
                if obv_slope > 30: score += 30
                elif obv_slope > 15: score += 20
                elif obv_slope > 5: score += 10
        
        # Volume expansion (4w vs 20w)
        avg_4w = vol_w.iloc[-4:].mean()
        avg_20w = vol_w.iloc[-20:].mean()
        if avg_20w > 0:
            expansion = avg_4w / avg_20w
            details['vol_expansion'] = round(expansion, 2)
            if expansion > 2.0: score += 20
            elif expansion > 1.5: score += 15
            elif expansion > 1.2: score += 8
        
        # Tight closes on high volume (institutional absorption)
        recent = hist_weekly.iloc[-8:]
        if len(recent) >= 4:
            body_pct = abs(recent['Close'] - recent['Open']) / recent['Open'] * 100
            avg_body = body_pct.mean()
            tight_high_vol = 0
            for i in range(len(recent)):
                if vol_w.iloc[-(8 - i)] > avg_20w * 1.2 and body_pct.iloc[i] < avg_body:
                    tight_high_vol += 1
            if tight_high_vol >= 3: score += 15
            elif tight_high_vol >= 2: score += 8
        
        return {'score': min(100, score), **details}
    
    # ─── SIGNAL 6: Sector Momentum (max 100) ───
    def _signal_sector_momentum(self, sector_etf_data, spy_weekly, sector, sector_etf_ticker):
        score = 0
        details = {'sector': sector, 'etf': sector_etf_ticker}
        
        if sector_etf_data is None or sector_etf_data.empty or len(sector_etf_data) < 12:
            return {'score': 0, **details}
        
        etf_close = sector_etf_data['Close']
        
        # Sector vs SPY (12-week alpha)
        if not spy_weekly.empty and len(spy_weekly) >= 12:
            etf_12w = self._calc_return(etf_close, 12)
            spy_12w = self._calc_return(spy_weekly['Close'], 12)
            if etf_12w is not None and spy_12w is not None:
                alpha = (etf_12w - spy_12w) * 100
                details['sector_alpha_12w'] = round(alpha, 1)
                if alpha > 15: score += 40
                elif alpha > 8: score += 28
                elif alpha > 3: score += 15
                elif alpha > 0: score += 5
        
        # Sector acceleration (4w vs prior 4w)
        if len(etf_close) >= 8:
            recent = self._calc_return(etf_close, 4) or 0
            prior = (etf_close.iloc[-4] - etf_close.iloc[-8]) / etf_close.iloc[-8]
            accel = (recent - prior) * 100
            details['sector_accel'] = round(accel, 1)
            if accel > 5: score += 30
            elif accel > 2: score += 18
            elif accel > 0: score += 8
        
        # Sector near 52-week high
        high = etf_close.max()
        proximity = (etf_close.iloc[-1] / high) * 100 if high > 0 else 0
        details['sector_52w_proximity'] = round(proximity, 1)
        if proximity >= 98: score += 30
        elif proximity >= 92: score += 18
        elif proximity >= 85: score += 8
        
        return {'score': min(100, score), **details}


if __name__ == '__main__':
    rc = RotationCatcher()
    tickers = ['VRT', 'MU', 'LLY', 'GOOGL', 'NVT']
    for t in tickers:
        r = rc.score(t)
        print(f"\n{t}: {r['composite_score']:.1f} — {r['signal']}")
        for name, sig in r['signals'].items():
            print(f"  {name:25} {sig['score']:3}/100")
