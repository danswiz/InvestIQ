#!/usr/bin/env python3
"""
Backtest Engine — Tests all IQ Investor signals against 5yr historical data.

Generates backtesting results for:
1. Quality Score (Grade A vs B vs C vs D/F)
2. EWROS (Top decile vs bottom decile)
3. Rotation Score (High rotation vs low)
4. IQ Edge Score (ML breakout prediction)
5. Power Matrix (combined EWROS + Rotation)
6. Combined Signal (all signals aligned)

Outputs: data/backtest_results.json + matplotlib charts in reports/charts/

Usage:
    python3 scripts/backtest_engine.py
"""
import json
import os
import sys
import warnings
from datetime import datetime, timedelta

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports', 'charts')
OHLCV_FILE = os.path.join(DATA_DIR, 'historical_ohlcv.parquet')
EVENTS_FILE = os.path.join(DATA_DIR, 'breakout_events.parquet')
STOCKS_FILE = os.path.join(DATA_DIR, 'all_stocks.json')
OUTPUT_FILE = os.path.join(DATA_DIR, 'backtest_results.json')

os.makedirs(CHARTS_DIR, exist_ok=True)

# Chart styling
plt.rcParams.update({
    'figure.facecolor': '#0f172a',
    'axes.facecolor': '#1e293b',
    'axes.edgecolor': '#374151',
    'axes.labelcolor': '#94a3b8',
    'text.color': '#f8fafc',
    'xtick.color': '#94a3b8',
    'ytick.color': '#94a3b8',
    'grid.color': '#2d3748',
    'grid.alpha': 0.5,
    'font.family': 'sans-serif',
    'font.size': 10,
})


def load_data():
    print('📊 Loading data...')
    ohlcv = pd.read_parquet(OHLCV_FILE)
    ohlcv['date'] = pd.to_datetime(ohlcv['date'])
    
    with open(STOCKS_FILE) as f:
        stocks_data = json.load(f)
    
    events = pd.read_parquet(EVENTS_FILE)
    
    # Get SPY data
    spy = ohlcv[ohlcv['ticker'] == 'SPY'].copy() if 'SPY' in ohlcv['ticker'].values else None
    
    # Pivot to get per-ticker daily returns
    prices = ohlcv.pivot_table(index='date', columns='ticker', values='close')
    returns = prices.pct_change()
    
    print(f'   {len(prices.columns)} tickers, {len(prices)} trading days')
    return ohlcv, prices, returns, stocks_data, events, spy


def forward_returns(prices, holding_periods=[21, 63, 126, 252]):
    """Compute forward returns for all stocks at each date."""
    fwd = {}
    for days in holding_periods:
        fwd[f'fwd_{days}d'] = prices.shift(-days) / prices - 1
    return fwd


def backtest_quality_score(prices, returns, stocks_data):
    """Backtest: Buy stocks by quality grade, measure forward returns."""
    print('\n🔬 Backtesting Quality Score (Grade A vs B vs C vs D/F)...')
    
    stocks = stocks_data.get('stocks', {})
    grades = {'A': [], 'B': [], 'C': [], 'D': [], 'F': []}
    
    for ticker, s in stocks.items():
        grade = s.get('grade', '')
        if grade in grades and ticker in prices.columns:
            grades[grade].append(ticker)
    
    # Use last available prices to compute trailing returns
    results = {}
    for period_name, days in [('1mo', 21), ('3mo', 63), ('6mo', 126), ('1yr', 252)]:
        period_returns = {}
        for grade, tickers in grades.items():
            if not tickers:
                continue
            valid_tickers = [t for t in tickers if t in prices.columns]
            if not valid_tickers:
                continue
            # Average return over the period (using available data)
            start_idx = max(0, len(prices) - days)
            period_prices = prices.iloc[start_idx:]
            avg_ret = 0
            count = 0
            for t in valid_tickers:
                series = period_prices[t].dropna()
                if len(series) >= 2:
                    ret = (series.iloc[-1] / series.iloc[0]) - 1
                    avg_ret += ret
                    count += 1
            period_returns[grade] = round((avg_ret / count * 100) if count > 0 else 0, 2)
        results[period_name] = period_returns
    
    # Chart
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(results))
    width = 0.15
    grade_colors = {'A': '#10b981', 'B': '#38bdf8', 'C': '#eab308', 'D': '#f97316', 'F': '#ef4444'}
    
    for i, (grade, color) in enumerate(grade_colors.items()):
        vals = [results[p].get(grade, 0) for p in results]
        ax.bar(x + i * width, vals, width, label=f'Grade {grade} ({len(grades[grade])})', color=color, alpha=0.85)
    
    ax.set_xlabel('Holding Period')
    ax.set_ylabel('Average Return (%)')
    ax.set_title('Quality Score: Returns by Grade', fontweight='bold', fontsize=14)
    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(list(results.keys()))
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, axis='y')
    ax.axhline(y=0, color='#94a3b8', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'quality_score_backtest.png'), dpi=150)
    plt.close()
    
    print(f'   Grade counts: A={len(grades["A"])}, B={len(grades["B"])}, C={len(grades["C"])}, D={len(grades["D"])}, F={len(grades["F"])}')
    for period, rets in results.items():
        print(f'   {period}: {rets}')
    
    return {'returns_by_grade': results, 'counts': {g: len(t) for g, t in grades.items()}}


def backtest_ewros(prices, returns, stocks_data):
    """Backtest: Top EWROS decile vs bottom decile vs SPY."""
    print('\n⚡ Backtesting EWROS (Top 10% vs Bottom 10% vs SPY)...')
    
    stocks = stocks_data.get('stocks', {})
    ewros_scores = [(t, s.get('ewros_score', 0)) for t, s in stocks.items() if s.get('ewros_score') and t in prices.columns]
    ewros_scores.sort(key=lambda x: -x[1])
    
    n = len(ewros_scores)
    top_10 = [t for t, _ in ewros_scores[:n//10]]
    bottom_10 = [t for t, _ in ewros_scores[-n//10:]]
    
    results = {}
    for period_name, days in [('1mo', 21), ('3mo', 63), ('6mo', 126), ('1yr', 252)]:
        start_idx = max(0, len(prices) - days)
        period_prices = prices.iloc[start_idx:]
        
        for label, tickers in [('top_10pct', top_10), ('bottom_10pct', bottom_10)]:
            rets = []
            for t in tickers:
                series = period_prices[t].dropna()
                if len(series) >= 2:
                    rets.append((series.iloc[-1] / series.iloc[0]) - 1)
            results[f'{label}_{period_name}'] = round(np.mean(rets) * 100 if rets else 0, 2)
        
        # SPY benchmark
        if 'SPY' in prices.columns:
            spy_series = period_prices['SPY'].dropna()
            if len(spy_series) >= 2:
                results[f'spy_{period_name}'] = round((spy_series.iloc[-1] / spy_series.iloc[0] - 1) * 100, 2)
    
    # Chart: cumulative returns comparison (last year)
    fig, ax = plt.subplots(figsize=(10, 5))
    start_idx = max(0, len(prices) - 252)
    period_prices = prices.iloc[start_idx:].copy()
    
    for label, tickers, color in [('Top 10% EWROS', top_10, '#10b981'), ('Bottom 10% EWROS', bottom_10, '#ef4444'), ('SPY', ['SPY'] if 'SPY' in prices.columns else [], '#38bdf8')]:
        valid = [t for t in tickers if t in period_prices.columns]
        if valid:
            avg_price = period_prices[valid].mean(axis=1).dropna()
            if len(avg_price) > 0:
                cumret = (avg_price / avg_price.iloc[0] - 1) * 100
                ax.plot(cumret.index, cumret.values, label=label, color=color, linewidth=2)
    
    ax.set_title('EWROS: Top 10% vs Bottom 10% vs SPY (1 Year)', fontweight='bold', fontsize=14)
    ax.set_ylabel('Cumulative Return (%)')
    ax.legend(fontsize=10)
    ax.grid(True)
    ax.axhline(y=0, color='#94a3b8', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'ewros_backtest.png'), dpi=150)
    plt.close()
    
    print(f'   Top 10%: {len(top_10)} stocks, Bottom 10%: {len(bottom_10)} stocks')
    for k, v in results.items():
        print(f'   {k}: {v}%')
    
    return results


def backtest_rotation(prices, stocks_data):
    """Backtest: High rotation score vs low rotation score."""
    print('\n🔄 Backtesting Rotation Score (≥60 vs <30)...')
    
    stocks = stocks_data.get('stocks', {})
    high_rot = [t for t, s in stocks.items() if (s.get('rotation_score') or 0) >= 60 and t in prices.columns]
    low_rot = [t for t, s in stocks.items() if (s.get('rotation_score') or 0) < 30 and t in prices.columns]
    
    results = {}
    for period_name, days in [('1mo', 21), ('3mo', 63), ('6mo', 126)]:
        start_idx = max(0, len(prices) - days)
        pp = prices.iloc[start_idx:]
        
        for label, tickers in [('high_rotation', high_rot), ('low_rotation', low_rot)]:
            rets = []
            for t in tickers:
                s = pp[t].dropna()
                if len(s) >= 2:
                    rets.append((s.iloc[-1] / s.iloc[0]) - 1)
            results[f'{label}_{period_name}'] = round(np.mean(rets) * 100 if rets else 0, 2)
    
    print(f'   High rotation (≥60): {len(high_rot)} stocks')
    print(f'   Low rotation (<30): {len(low_rot)} stocks')
    for k, v in results.items():
        print(f'   {k}: {v}%')
    
    return results


def backtest_iq_edge(events):
    """Backtest: IQ Edge model accuracy on labeled breakout events."""
    print('\n🧠 Backtesting IQ Edge Score (breakout prediction accuracy)...')
    
    labels = events['label'].value_counts()
    total = len(events)
    
    # Outcome by volume ratio buckets
    events['vol_bucket'] = pd.cut(events['breakout_vol_ratio'].clip(0, 20), 
                                   bins=[0, 2, 5, 10, 20], labels=['1-2x', '2-5x', '5-10x', '10-20x'])
    vol_outcomes = events.groupby('vol_bucket')['label'].apply(
        lambda x: {'double_rate': round((x == 'double').mean() * 100, 1),
                    'win_rate': round(x.isin(['double', 'big_win', 'win']).mean() * 100, 1),
                    'count': len(x)}
    ).to_dict()
    
    # Outcome by trend alignment
    aligned = events[events['trend_aligned'] == 1]
    not_aligned = events[events['trend_aligned'] == 0]
    trend_results = {
        'aligned_double_rate': round((aligned['label'] == 'double').mean() * 100, 1) if len(aligned) > 0 else 0,
        'not_aligned_double_rate': round((not_aligned['label'] == 'double').mean() * 100, 1) if len(not_aligned) > 0 else 0,
        'aligned_win_rate': round(aligned['label'].isin(['double', 'big_win', 'win']).mean() * 100, 1) if len(aligned) > 0 else 0,
        'not_aligned_win_rate': round(not_aligned['label'].isin(['double', 'big_win', 'win']).mean() * 100, 1) if len(not_aligned) > 0 else 0,
    }
    
    # Chart: Double rate by volume bucket
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Volume bucket chart
    buckets = ['1-2x', '2-5x', '5-10x', '10-20x']
    double_rates = [vol_outcomes.get(b, {}).get('double_rate', 0) for b in buckets]
    win_rates = [vol_outcomes.get(b, {}).get('win_rate', 0) for b in buckets]
    counts = [vol_outcomes.get(b, {}).get('count', 0) for b in buckets]
    
    x = np.arange(len(buckets))
    axes[0].bar(x - 0.15, double_rates, 0.3, label='Double Rate (%)', color='#a855f7')
    axes[0].bar(x + 0.15, win_rates, 0.3, label='Win Rate (%)', color='#10b981')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([f'{b}\n(n={c})' for b, c in zip(buckets, counts)])
    axes[0].set_title('Breakout Volume → Outcome', fontweight='bold')
    axes[0].set_ylabel('Rate (%)')
    axes[0].legend(fontsize=8)
    axes[0].grid(True, axis='y')
    
    # Label distribution pie
    colors = ['#ef4444', '#eab308', '#10b981', '#a855f7']
    axes[1].pie([labels.get('fail', 0), labels.get('win', 0), labels.get('big_win', 0), labels.get('double', 0)],
                labels=['Fail', 'Win 25%+', 'Big Win 50%+', 'Double 100%+'],
                colors=colors, autopct='%1.1f%%', startangle=90,
                textprops={'color': '#f8fafc', 'fontsize': 9})
    axes[1].set_title('Breakout Outcome Distribution', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'iq_edge_backtest.png'), dpi=150)
    plt.close()
    
    # Average max gain by label
    avg_gains = events.groupby('label')['max_gain_pct'].mean().to_dict()
    
    results = {
        'total_events': total,
        'label_distribution': {k: int(v) for k, v in labels.items()},
        'volume_outcomes': {str(k): v for k, v in vol_outcomes.items()},
        'trend_alignment': trend_results,
        'avg_max_gain_by_label': {k: round(v, 1) for k, v in avg_gains.items()},
    }
    
    print(f'   Total events: {total}')
    print(f'   Labels: {dict(labels)}')
    print(f'   Volume → Double rate: {dict(zip(buckets, double_rates))}')
    print(f'   Trend aligned double rate: {trend_results["aligned_double_rate"]}% vs not: {trend_results["not_aligned_double_rate"]}%')
    
    return results


def backtest_power_matrix(prices, stocks_data):
    """Backtest: Power Zone (high EWROS + high Rotation) vs others."""
    print('\n🎯 Backtesting Power Matrix (EWROS × Rotation)...')
    
    stocks = stocks_data.get('stocks', {})
    power = [t for t, s in stocks.items() if (s.get('ewros_score') or 0) >= 70 and (s.get('rotation_score') or 0) >= 60 and t in prices.columns]
    extended = [t for t, s in stocks.items() if (s.get('ewros_score') or 0) >= 70 and (s.get('rotation_score') or 0) < 60 and t in prices.columns]
    early = [t for t, s in stocks.items() if (s.get('ewros_score') or 0) < 70 and (s.get('rotation_score') or 0) >= 60 and t in prices.columns]
    avoid = [t for t, s in stocks.items() if (s.get('ewros_score') or 0) < 70 and (s.get('rotation_score') or 0) < 60 and t in prices.columns]
    
    results = {}
    for period_name, days in [('1mo', 21), ('3mo', 63)]:
        start_idx = max(0, len(prices) - days)
        pp = prices.iloc[start_idx:]
        
        for label, tickers in [('power_zone', power), ('extended', extended), ('early_signal', early), ('avoid', avoid)]:
            rets = []
            for t in tickers:
                s = pp[t].dropna()
                if len(s) >= 2:
                    rets.append((s.iloc[-1] / s.iloc[0]) - 1)
            results[f'{label}_{period_name}'] = round(np.mean(rets) * 100 if rets else 0, 2)
    
    # Chart
    fig, ax = plt.subplots(figsize=(10, 5))
    quadrants = ['Power Zone', 'Extended', 'Early Signal', 'Avoid']
    colors_q = ['#10b981', '#eab308', '#38bdf8', '#ef4444']
    counts = [len(power), len(extended), len(early), len(avoid)]
    
    for period_name, days in [('1mo', 21), ('3mo', 63)]:
        vals = [results.get(f'{q}_{period_name}', 0) for q in ['power_zone', 'extended', 'early_signal', 'avoid']]
        offset = -0.15 if period_name == '1mo' else 0.15
        width = 0.3
        x = np.arange(len(quadrants))
        bars = ax.bar(x + offset, vals, width, label=period_name, 
                      color=[c + 'cc' for c in colors_q] if period_name == '1mo' else [c + '88' for c in colors_q])
    
    ax.set_xticks(np.arange(len(quadrants)))
    ax.set_xticklabels([f'{q}\n(n={c})' for q, c in zip(quadrants, counts)])
    ax.set_ylabel('Average Return (%)')
    ax.set_title('Power Matrix: Returns by Quadrant', fontweight='bold', fontsize=14)
    ax.legend()
    ax.grid(True, axis='y')
    ax.axhline(y=0, color='#94a3b8', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'power_matrix_backtest.png'), dpi=150)
    plt.close()
    
    print(f'   Power Zone: {len(power)}, Extended: {len(extended)}, Early: {len(early)}, Avoid: {len(avoid)}')
    for k, v in results.items():
        print(f'   {k}: {v}%')
    
    return {'quadrant_returns': results, 'counts': {'power': len(power), 'extended': len(extended), 'early': len(early), 'avoid': len(avoid)}}


def backtest_combined(prices, stocks_data):
    """Backtest: All signals aligned (Grade A + EWROS ≥70 + IQ Edge ≥80)."""
    print('\n🏆 Backtesting Combined Signal (Grade A + EWROS ≥70 + IQ Edge ≥80)...')
    
    stocks = stocks_data.get('stocks', {})
    combined = [t for t, s in stocks.items() 
                if s.get('grade') == 'A' 
                and (s.get('ewros_score') or 0) >= 70 
                and (s.get('iq_edge') or 0) >= 80
                and t in prices.columns]
    
    all_a = [t for t, s in stocks.items() if s.get('grade') == 'A' and t in prices.columns]
    
    results = {}
    for period_name, days in [('1mo', 21), ('3mo', 63)]:
        start_idx = max(0, len(prices) - days)
        pp = prices.iloc[start_idx:]
        
        for label, tickers in [('combined', combined), ('grade_a_only', all_a)]:
            rets = []
            for t in tickers:
                s = pp[t].dropna()
                if len(s) >= 2:
                    rets.append((s.iloc[-1] / s.iloc[0]) - 1)
            results[f'{label}_{period_name}'] = round(np.mean(rets) * 100 if rets else 0, 2)
    
    print(f'   Combined signal stocks: {len(combined)}')
    print(f'   Grade A only: {len(all_a)}')
    if combined:
        print(f'   Tickers: {combined[:15]}')
    for k, v in results.items():
        print(f'   {k}: {v}%')
    
    return {'returns': results, 'combined_count': len(combined), 'grade_a_count': len(all_a), 'tickers': combined[:20]}


def main():
    print('🚀 IQ Investor Backtest Engine')
    print(f'   {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
    
    ohlcv, prices, returns, stocks_data, events, spy = load_data()
    
    results = {
        'generated_at': datetime.now().isoformat(),
        'data_range': f'{prices.index[0].strftime("%Y-%m-%d")} to {prices.index[-1].strftime("%Y-%m-%d")}',
        'total_stocks': len(prices.columns),
        'total_trading_days': len(prices),
    }
    
    results['quality_score'] = backtest_quality_score(prices, returns, stocks_data)
    results['ewros'] = backtest_ewros(prices, returns, stocks_data)
    results['rotation'] = backtest_rotation(prices, stocks_data)
    results['iq_edge'] = backtest_iq_edge(events)
    results['power_matrix'] = backtest_power_matrix(prices, stocks_data)
    results['combined'] = backtest_combined(prices, stocks_data)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f'\n✅ Backtest complete!')
    print(f'   Results: {OUTPUT_FILE}')
    print(f'   Charts: {CHARTS_DIR}/')
    for f_name in os.listdir(CHARTS_DIR):
        if f_name.endswith('.png'):
            print(f'      {f_name}')


if __name__ == '__main__':
    main()
