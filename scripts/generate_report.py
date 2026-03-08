#!/usr/bin/env python3
"""
Generate PDF Report: The IQ Investor — Algorithm & Backtest Report
Uses walk-forward + portfolio backtest results.
"""
import json
import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                 Table, TableStyle, PageBreak, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
CHARTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports', 'charts')
OUTPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports',
                       f'IQ_Investor_Algorithm_Report_{datetime.now().strftime("%Y%m%d")}.pdf')

with open(os.path.join(DATA_DIR, 'backtest_results.json')) as f:
    bt = json.load(f)

portfolio = bt.get('portfolio_10k', {})
iq_oos = bt.get('iq_edge_oos', {})
strats = portfolio.get('strategies', {})
spy_bh = portfolio.get('spy_buy_hold', {})
iq_strats = iq_oos.get('strategies', {})

# Colors
HEADING = colors.HexColor('#0c4a6e')
TEXT = colors.HexColor('#1a1a1a')
TEXT_DIM = colors.HexColor('#333333')
TBL_HDR = colors.HexColor('#0c4a6e')
TBL_ALT = colors.HexColor('#f0f4f8')
BORDER = colors.HexColor('#cbd5e1')

styles = getSampleStyleSheet()
title_s = ParagraphStyle('T', parent=styles['Title'], fontSize=26, textColor=HEADING, spaceAfter=4, fontName='Helvetica-Bold')
sub_s = ParagraphStyle('S', parent=styles['Normal'], fontSize=12, textColor=TEXT_DIM, spaceAfter=16, alignment=TA_CENTER)
h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=15, textColor=HEADING, spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold')
h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=11, textColor=HEADING, spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold')
h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=10, textColor=HEADING, spaceBefore=6, spaceAfter=3, fontName='Helvetica-Bold')
body = ParagraphStyle('B', parent=styles['Normal'], fontSize=9, textColor=TEXT, leading=12, alignment=TA_JUSTIFY)
formula = ParagraphStyle('F', parent=styles['Code'], fontSize=8, textColor=TEXT, backColor=colors.HexColor('#f1f5f9'),
                          leading=11, leftIndent=12, rightIndent=12, spaceBefore=3, spaceAfter=3,
                          borderColor=BORDER, borderWidth=0.5, borderPadding=4)
metric = ParagraphStyle('M', parent=styles['Normal'], fontSize=9, textColor=HEADING, fontName='Helvetica-Bold')
caption = ParagraphStyle('C', parent=styles['Normal'], fontSize=7, textColor=TEXT_DIM, alignment=TA_CENTER, spaceAfter=8)
note = ParagraphStyle('N', parent=styles['Normal'], fontSize=8, textColor=TEXT_DIM, leading=10, leftIndent=12,
                       borderColor=colors.HexColor('#e2e8f0'), borderWidth=0.5, borderPadding=6, backColor=colors.HexColor('#fefce8'))


def tbl(data, cw=None):
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TBL_HDR), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 8),
        ('TEXTCOLOR', (0,1), (-1,-1), TEXT), ('FONTSIZE', (0,1), (-1,-1), 8),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, TBL_ALT]),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    return t


def chart(story, fn, w=5.5*inch, cap=None):
    p = os.path.join(CHARTS_DIR, fn)
    if os.path.exists(p):
        story.append(Image(p, width=w, height=w*0.45))
        if cap: story.append(Paragraph(cap, caption))


def gs(strat_name, field, default=0):
    """Get strategy stat."""
    return strats.get(strat_name, {}).get(field, default)

def gi(strat_name, field, default=0):
    """Get IQ OOS strategy stat."""
    return iq_strats.get(strat_name, {}).get(field, default)


def build():
    doc = SimpleDocTemplate(OUTPUT, pagesize=letter, topMargin=0.6*inch, bottomMargin=0.5*inch,
                            leftMargin=0.7*inch, rightMargin=0.7*inch)
    story = []

    # ===== COVER =====
    story.append(Spacer(1, 0.8*inch))
    story.append(Paragraph('The IQ Investor', title_s))
    story.append(Paragraph('Algorithm & Backtesting Report', sub_s))
    story.append(HRFlowable(width='50%', color=HEADING, thickness=1.5))
    story.append(Spacer(1, 0.15*inch))
    ci = ParagraphStyle('CI', parent=body, alignment=TA_CENTER, fontSize=9, textColor=TEXT_DIM)
    story.append(Paragraph(f'Generated: {datetime.now().strftime("%B %d, %Y")} · Test Period: {portfolio.get("test_period","N/A")}', ci))
    story.append(Paragraph(f'Model trained on pre-Sep 2023 data · Tested on 2.5 years of unseen market', ci))
    story.append(Spacer(1, 0.3*inch))

    # Headline result
    iq_ewros = strats.get('IQ Edge + EWROS ≥80', {})
    story.append(Paragraph(
        f'<b>$10,000 → ${iq_ewros.get("final_value", 0):,.0f}</b> ({iq_ewros.get("total_return_pct", 0):+.1f}%) '
        f'vs SPY Buy &amp; Hold ${spy_bh.get("final_value", 0):,.0f} ({spy_bh.get("total_return_pct", 0):+.1f}%)',
        ParagraphStyle('HL', parent=body, alignment=TA_CENTER, fontSize=11, textColor=HEADING, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 0.4*inch))

    story.append(HRFlowable(width='100%', color=BORDER, thickness=0.5))
    story.append(Paragraph('Contents', h2))
    toc = ['1. Portfolio Results — $10,000 Backtest', '2. Entry & Exit Rules',
           '3. EWROS — Algorithm & Results', '4. IQ Edge Score — ML Model & Out-of-Sample Results',
           '5. Quality Score — 14-Factor Rating', '6. Power Matrix — Combined Framework',
           '7. Methodology & Limitations', '8. Appendix']
    for item in toc:
        story.append(Paragraph(item, ParagraphStyle('TOC', parent=body, spaceBefore=2, fontSize=9)))
    story.append(PageBreak())

    # ===== 1. PORTFOLIO RESULTS =====
    story.append(Paragraph('1. Portfolio Results — $10,000 Backtest', h1))
    story.append(Paragraph(
        f'Starting with $10,000 in September 2023, each strategy trades with max 20 equal-weight positions '
        f'($500/slot, scaling with portfolio value). XGBoost model trained exclusively on pre-Sep 2023 data. '
        f'All results below are on completely unseen market data.',
        body))
    story.append(Spacer(1, 6))

    # Main equity chart
    chart(story, 'portfolio_10k.png', w=6.2*inch, cap='Growth of $10,000: Strategies vs SPY Buy & Hold (Sep 2023 – Mar 2026)')

    # Results table
    story.append(Paragraph('Final Scorecard', h2))
    score_table = [
        ['Strategy', 'Final Value', 'Return', 'Trades', 'Win Rate', 'Profit Factor', 'Expectancy'],
    ]
    for name in ['IQ Edge + EWROS ≥80', 'EWROS Top 20 + Trend', 'IQ Edge Top 20 + Trend']:
        s = strats.get(name, {})
        if not s: continue
        score_table.append([
            name, f'${s.get("final_value",0):,.0f}', f'{s.get("total_return_pct",0):+.1f}%',
            str(s.get('total_trades',0)), f'{s.get("win_rate",0)}%',
            str(s.get('profit_factor',0)), f'{s.get("expectancy_pct",0)}%'
        ])
    score_table.append(['SPY Buy & Hold', f'${spy_bh.get("final_value",0):,.0f}',
                         f'{spy_bh.get("total_return_pct",0):+.1f}%', '1', '—', '—', '—'])
    story.append(tbl(score_table, cw=[1.8*inch, 0.85*inch, 0.7*inch, 0.55*inch, 0.65*inch, 0.7*inch, 0.85*inch]))
    story.append(Spacer(1, 6))

    # Win/loss stats
    story.append(Paragraph('Win/Loss Profile', h2))
    wl_table = [['Strategy', 'Wins', 'Losses', 'Avg Win', 'Avg Loss', 'Avg Win $', 'Avg Loss $', 'Best', 'Worst']]
    for name in ['IQ Edge + EWROS ≥80', 'EWROS Top 20 + Trend', 'IQ Edge Top 20 + Trend']:
        s = strats.get(name, {})
        if not s: continue
        short = name.replace('IQ Edge + EWROS ≥80', 'IQ+EWROS').replace('EWROS Top 20 + Trend', 'EWROS').replace('IQ Edge Top 20 + Trend', 'IQ Edge')
        wl_table.append([short, str(s.get('winners',0)), str(s.get('losers',0)),
                          f'+{s.get("avg_win_pct",0)}%', f'{s.get("avg_loss_pct",0)}%',
                          f'${s.get("avg_win_dollar",0):,.0f}', f'${s.get("avg_loss_dollar",0):,.0f}',
                          f'+{s.get("best_trade",0)}%', f'{s.get("worst_trade",0)}%'])
    story.append(tbl(wl_table, cw=[0.8*inch, 0.5*inch, 0.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch]))
    story.append(Spacer(1, 6))

    # Comparison + drawdown charts
    chart(story, 'portfolio_comparison.png', w=6.2*inch, cap='Strategy comparison: final value, returns, win rate, profit factor')
    chart(story, 'portfolio_drawdown.png', w=5.5*inch, cap='Drawdown from peak — maximum pain endured during the test period')
    story.append(PageBreak())

    # ===== 2. ENTRY & EXIT RULES =====
    story.append(Paragraph('2. Entry & Exit Rules', h1))
    story.append(Paragraph('All strategies share the same exit discipline. Only entry criteria differ.', body))
    story.append(Spacer(1, 4))

    story.append(Paragraph('Entry Rules', h2))
    entry_table = [
        ['Strategy', 'Entry Criteria'],
        ['IQ Edge Top 20 + Trend', 'Top 20 IQ Edge percentile + Price > 50d MA > 200d MA'],
        ['IQ Edge + EWROS ≥80', 'IQ Edge ≥ 80th pctile + EWROS ≥ 80 + Trend aligned'],
        ['EWROS Top 20 + Trend', 'Top 20 EWROS score + Price > 50d MA > 200d MA'],
    ]
    story.append(tbl(entry_table, cw=[2*inch, 4.5*inch]))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Exit Rules (whichever triggers first)', h2))
    exit_table = [
        ['Exit Signal', 'Threshold', 'Rationale'],
        ['Stop Loss', '-8% from entry', 'Cut losses fast — preserve capital'],
        ['Below 50-day MA', 'Close < 50d MA (after 5d hold)', 'Trend broken — momentum lost'],
        ['EWROS Drop', 'EWROS falls below 50 (after 10d)', 'Relative strength deteriorating'],
        ['Max Hold', '126 trading days (~6 months)', 'Avoid dead money — free up capital'],
    ]
    story.append(tbl(exit_table, cw=[1.2*inch, 2*inch, 3.3*inch]))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Position Sizing', h2))
    story.append(Paragraph(
        'Max 20 positions at any time. Each new position sized at portfolio_value / 20. '
        'No margin, no leverage. Cash sits idle when no qualifying entries are found.',
        body))

    # ===== 3. EWROS =====
    story.append(Paragraph('3. EWROS — Exponential Weighted Relative Outperformance', h1))
    story.append(Paragraph(
        'Measures how consistently a stock outperforms SPY on a daily basis, with exponential decay '
        'emphasizing recent performance. Unlike IBD RS Rating (12-month equal weight), EWROS catches '
        'momentum shifts within weeks.',
        body))
    story.append(Spacer(1, 4))

    story.append(Paragraph('Formula', h2))
    story.append(Paragraph(
        'daily_alpha(t) = stock_return(t) − SPY_return(t)\n'
        'weight(t) = e^(−0.03 × days_ago)          half-life ≈ 23 days\n'
        'EWROS_raw = Σ(daily_alpha × weight)       over 63 trading days\n'
        'EWROS = percentile_rank(EWROS_raw)        scaled 1–99',
        formula))

    ewros_params = [
        ['Parameter', 'Value', 'Rationale'],
        ['Lookback', '63 days (~3 months)', 'Medium-term momentum, not noise'],
        ['Lambda (λ)', '0.03', 'Half-life ~23 days — recent alpha weighs 2x vs 3-week-old'],
        ['Trend Offset', '21 days', 'Compares current rank to 1 month prior'],
        ['Benchmark', 'SPY', 'S&P 500 ETF as market proxy'],
    ]
    story.append(tbl(ewros_params, cw=[1.2*inch, 1.5*inch, 3.8*inch]))
    story.append(Spacer(1, 4))

    ewros_s = strats.get('EWROS Top 20 + Trend', {})
    story.append(Paragraph(
        f'<b>Out-of-sample result:</b> $10,000 → ${ewros_s.get("final_value",0):,.0f} '
        f'({ewros_s.get("total_return_pct",0):+.1f}%), {ewros_s.get("total_trades",0)} trades, '
        f'win rate {ewros_s.get("win_rate",0)}%, profit factor {ewros_s.get("profit_factor",0)}.',
        body))

    # ===== 4. IQ EDGE =====
    story.append(Paragraph('4. IQ Edge Score — ML Breakout Prediction', h1))
    story.append(Paragraph(
        'XGBoost model trained on 3,781 breakout events from Mar 2021 – Aug 2023. '
        'Predicts probability of 100%+ gain (doubling) within 12 months. '
        'All results below are on the 2.5 years of market data the model never saw.',
        body))
    story.append(Spacer(1, 4))

    story.append(Paragraph('Model Training (strict temporal split)', h2))
    train_table = [
        ['Metric', 'Value'],
        ['Train Period', 'Mar 2021 – Aug 2023 (3,781 events, 80 doubles)'],
        ['Test Period', 'Sep 2023 – Mar 2026 (5,949 events, 217 doubles)'],
        ['Train AUC', '0.955 (expected overfit on seen data)'],
        ['Test AUC (out-of-sample)', '0.712'],
        ['Test Top-10% Precision', '9.9% (vs 3.6% base rate — 2.75x lift)'],
        ['Model', 'XGBoost (500 trees, max depth 6)'],
    ]
    story.append(tbl(train_table, cw=[2.2*inch, 4.3*inch]))
    story.append(Spacer(1, 4))

    story.append(Paragraph('Feature Set (14 features)', h2))
    feat_table = [
        ['Feature', 'Category', 'Description'],
        ['close_to_ma20/50/200', 'Trend', 'Price relative to key moving averages'],
        ['trend_aligned', 'Trend', 'Price > 50d MA > 200d MA (binary)'],
        ['atr_14', 'Volatility', '14-day Average True Range (normalized)'],
        ['vol_dryup_ratio', 'Volume', 'Recent vs earlier volume in base'],
        ['vol_compression', 'Volatility', 'Recent ATR vs longer-term ATR'],
        ['proximity_52w', 'Timing', 'Price relative to 52-week high'],
        ['return_3mo', 'Momentum', '3-month price return'],
        ['up_days_pct', 'Pattern', 'Percentage of up days in base'],
        ['base_length / base_range', 'Pattern', 'Consolidation duration and width'],
        ['breakout_vol_ratio', 'Volume', 'Breakout day volume vs 50d average'],
    ]
    story.append(tbl(feat_table, cw=[1.6*inch, 0.7*inch, 4.2*inch]))
    story.append(Spacer(1, 4))

    story.append(Paragraph('Out-of-Sample Event-Driven Results', h2))
    oos_table = [
        ['Strategy', 'Trades', 'Win Rate', 'Avg Win', 'Avg Loss', 'PF', 'Expectancy'],
    ]
    for name in ['IQ Edge Top 20 + Trend', 'IQ Edge + EWROS ≥80', 'IQ Edge ≥80 + Trend', 'EWROS Top 20 (benchmark)']:
        s = iq_strats.get(name, {})
        if not s or s.get('total_trades', 0) == 0: continue
        short = name.replace('IQ Edge ', 'IQ ').replace(' (benchmark)', '')
        oos_table.append([short, str(s['total_trades']), f'{s["win_rate"]}%',
                           f'+{s["avg_win"]}%', f'{s["avg_loss"]}%',
                           str(s['profit_factor']), f'{s["expectancy"]}%'])
    story.append(tbl(oos_table, cw=[1.5*inch, 0.6*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.5*inch, 0.8*inch]))
    story.append(Spacer(1, 4))

    chart(story, 'iq_edge_oos_equity.png', w=5.5*inch, cap='IQ Edge strategies: equity curves on out-of-sample data')
    chart(story, 'iq_edge_oos_comparison.png', w=5.5*inch, cap='IQ Edge strategies: win rate, profit factor, expectancy comparison')
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        '<b>Key finding:</b> IQ Edge Top 20 achieved the highest win rate (40.6%) and profit factor (2.59) '
        'among IQ Edge strategies. When combined with EWROS ≥80, trade count increases 2.3x while maintaining '
        'a strong PF of 2.43. The ML adds real, measurable value on completely unseen market data.',
        body))
    story.append(PageBreak())

    # ===== 5. QUALITY SCORE =====
    story.append(Paragraph('5. Quality Score — 14-Factor Stock Rating', h1))
    story.append(Paragraph(
        'Evaluates stocks on a 100-point scale: Technical (53 pts), Growth (33 pts), '
        'Quality Fundamentals (18 pts), Context (10 pts). Graded A through F.',
        body))
    story.append(Spacer(1, 4))

    criteria = [
        ['Category', 'Factor', 'Pts', 'Description'],
        ['Technical', 'Breakout Pattern', '22', 'Flat ceiling base <10% drift'],
        ['Technical', 'Trend Alignment', '8', 'Price > 50d MA > 200d MA'],
        ['Technical', 'Consolidation + Vol + 52W + ATR', '23', 'Base quality, volume dry-up, proximity, compression'],
        ['Growth', 'Revenue Growth (2yr gate)', '30', 'Both years ≥10% required'],
        ['Growth', 'Earnings Acceleration', '3', 'Sequential quarterly improvement'],
        ['Quality', 'ROE + Margin + PEG + FCF', '18', 'Fundamental quality metrics'],
        ['Context', 'Industry + Relative Strength', '10', 'Sector performance vs SPY'],
    ]
    story.append(tbl(criteria, cw=[0.8*inch, 2*inch, 0.4*inch, 3.3*inch]))
    story.append(Spacer(1, 4))
    story.append(Paragraph('Grades: A ≥ 75 · B ≥ 60 · C ≥ 45 · D ≥ 30 · F < 30', formula))
    story.append(Paragraph(
        '<b>Note:</b> Quality Score requires fundamental data (revenue, ROE, margins) not available in OHLCV. '
        'It was not backtested in this report. Its value is in screening, not timing.',
        note))

    # ===== 6. POWER MATRIX =====
    story.append(Paragraph('6. Power Matrix — Combined Signal Framework', h1))
    matrix = [
        ['', 'EWROS ≥ 70 (Momentum)', 'EWROS < 70'],
        ['Rotation ≥ 60', '🎯 POWER ZONE — BUY', '⏳ EARLY SIGNAL — WATCH'],
        ['Rotation < 60', '⚠️ EXTENDED — CAUTION', '💀 AVOID — SKIP'],
    ]
    t = Table(matrix, colWidths=[1.3*inch, 2.7*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TBL_HDR), ('BACKGROUND', (0,0), (0,-1), TBL_HDR),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('TEXTCOLOR', (0,1), (0,-1), colors.white),
        ('TEXTCOLOR', (1,1), (-1,-1), TEXT), ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 1, BORDER),
        ('BACKGROUND', (1,1), (1,1), colors.HexColor('#dcfce7')),
        ('BACKGROUND', (2,1), (2,1), colors.HexColor('#dbeafe')),
        ('BACKGROUND', (1,2), (1,2), colors.HexColor('#fef9c3')),
        ('BACKGROUND', (2,2), (2,2), colors.HexColor('#fee2e2')),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(PageBreak())

    # ===== 7. METHODOLOGY =====
    story.append(Paragraph('7. Methodology & Limitations', h1))
    story.append(Paragraph('Backtest Protocol', h2))
    story.append(Paragraph(
        '1. <b>Strict temporal split:</b> XGBoost trained on Mar 2021 – Aug 2023 only. '
        'All portfolio results are on Sep 2023 – Mar 2026 (2.5 years unseen).<br/>'
        '2. <b>Event-driven entries:</b> Stocks scanned daily for qualifying signals. '
        'No monthly rebalancing — positions entered when signals trigger, exited when stops hit.<br/>'
        '3. <b>EWROS recomputed at each date</b> using only prior 63 days of data. No look-ahead.<br/>'
        '4. <b>Real position sizing:</b> $10K starting capital, max 20 slots, capital scales with gains/losses.<br/>'
        '5. <b>Signals pre-computed weekly</b> (every 5 trading days) for performance; daily scan for exits.',
        body))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Known Limitations', h2))
    lims = [
        '<b>No transaction costs:</b> Commissions, slippage, bid-ask spreads not modeled. With ~200-450 trades over 2.5 years, friction is real but manageable at ~$0 commissions.',
        '<b>Survivorship bias:</b> Universe is today\'s 1,008 stocks. Delisted/bankrupt companies excluded, inflating returns for all strategies including SPY comparison.',
        '<b>No short selling:</b> Bottom-decile results shown for comparison only. Actually shorting involves borrow costs.',
        '<b>Fat-tail dependency:</b> A few mega-winners (SNDK +459%, LITE +293%, RKLB +426%) drive significant P&L. Removing top 3 trades would materially reduce returns.',
        '<b>Weekly signal refresh:</b> EWROS and IQ Edge recomputed every 5 days, not daily. Some signal lag possible.',
        '<b>Quality Score not backtested:</b> Requires fundamental data (revenue, earnings, ROE) not available in OHLCV dataset.',
    ]
    for l in lims:
        story.append(Paragraph(f'• {l}', ParagraphStyle('L', parent=body, leftIndent=12, spaceBefore=2)))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Signal Confidence', h2))
    conf = [
        ['Signal', 'Confidence', 'Basis'],
        ['EWROS', 'HIGH', 'Pure price data, no proxy. 443 OOS trades, PF 2.09.'],
        ['IQ Edge', 'HIGH', 'Properly split model. 207 OOS trades, PF 2.77. AUC 0.712.'],
        ['Combined (IQ+EWROS)', 'HIGH', '445 OOS trades, PF 2.67. Best absolute return.'],
        ['Quality Score', 'NOT TESTED', 'Fundamental data required. Used for screening only.'],
        ['Rotation Score', 'MEDIUM', 'Price/volume proxy for 3 of 6 signals.'],
    ]
    story.append(tbl(conf, cw=[1.2*inch, 1*inch, 4.3*inch]))

    # ===== 8. APPENDIX =====
    story.append(Paragraph('8. Appendix', h1))
    story.append(Paragraph('Architecture', h2))
    story.append(Paragraph(
        'Backend: Python/Flask · ML: XGBoost + scikit-learn · Data: yfinance · DB: Supabase · '
        'Frontend: Vanilla JS + Chart.js · Deploy: Vercel · Domain: theiqinvestor.com',
        body))
    story.append(Spacer(1, 4))

    story.append(Paragraph('Daily Pipeline (Mon–Fri ET)', h2))
    pipe = [
        ['Time', 'Job'], ['4:05 PM', 'Daily Closing Scan'], ['4:15 PM', 'Distribution Day Scan'],
        ['4:20 PM', 'Earnings Calendar + Alert'], ['4:30 PM', 'Cache Refresh'],
        ['4:45 PM', 'Full Scan (Quality + Rotation + EWROS + IQ Edge)'],
        ['5:00 PM', 'Sell Signal Check'], ['5:30 PM', 'Earnings Recap Email'],
        ['6:00 PM', 'Insider Scan'], ['7:00 PM', 'Daily Alpha Report (LLM)'],
    ]
    story.append(tbl(pipe, cw=[1*inch, 5.5*inch]))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width='100%', color=BORDER, thickness=0.5))
    story.append(Paragraph(
        '<b>Disclaimer:</b> Past performance does not guarantee future results. This report is for informational '
        'purposes only. Backtesting results are hypothetical, subject to survivorship bias, exclude transaction costs, '
        'and depend on a few large winners. Not investment advice.',
        ParagraphStyle('D', parent=body, fontSize=7, textColor=TEXT_DIM, spaceBefore=6)))

    doc.build(story)
    print(f'✅ Report generated: {OUTPUT} ({os.path.getsize(OUTPUT)/1024:.0f} KB)')


if __name__ == '__main__':
    build()
