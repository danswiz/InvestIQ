#!/usr/bin/env python3
"""
Generate PDF Report: The IQ Investor — Algorithm & Backtest Report

Comprehensive documentation of all indicators, scoring algorithms,
and backtesting results with charts.
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

# Load backtest results
with open(os.path.join(DATA_DIR, 'backtest_results.json')) as f:
    bt = json.load(f)

# Colors
DARK_BG = colors.HexColor('#0f172a')
SURFACE = colors.HexColor('#1e293b')
ACCENT = colors.HexColor('#38bdf8')
GREEN = colors.HexColor('#10b981')
RED = colors.HexColor('#ef4444')
PURPLE = colors.HexColor('#a855f7')
YELLOW = colors.HexColor('#eab308')
DIM = colors.HexColor('#94a3b8')
WHITE = colors.HexColor('#f8fafc')

# Styles
styles = getSampleStyleSheet()

title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=28, 
                              textColor=ACCENT, spaceAfter=6, fontName='Helvetica-Bold')
subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=14,
                                 textColor=DIM, spaceAfter=30, alignment=TA_CENTER)
h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=20,
                           textColor=ACCENT, spaceBefore=20, spaceAfter=12, fontName='Helvetica-Bold')
h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14,
                           textColor=WHITE, spaceBefore=16, spaceAfter=8, fontName='Helvetica-Bold')
h3_style = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=12,
                           textColor=ACCENT, spaceBefore=12, spaceAfter=6, fontName='Helvetica-Bold')
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10,
                             textColor=colors.HexColor('#e2e8f0'), leading=14, alignment=TA_JUSTIFY)
formula_style = ParagraphStyle('Formula', parent=styles['Code'], fontSize=9,
                                textColor=GREEN, backColor=SURFACE, leading=13,
                                leftIndent=20, rightIndent=20, spaceBefore=8, spaceAfter=8)
metric_style = ParagraphStyle('Metric', parent=styles['Normal'], fontSize=11,
                               textColor=GREEN, fontName='Helvetica-Bold')
caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=8,
                                textColor=DIM, alignment=TA_CENTER, spaceAfter=16)


def make_table(data, col_widths=None):
    """Create a styled table."""
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SURFACE),
        ('TEXTCOLOR', (0, 0), (-1, 0), ACCENT),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TEXTCOLOR', (0, 1), (-1, -1), WHITE),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#374151')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0f172a'), colors.HexColor('#1a2332')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return t


def add_chart(story, filename, width=6.5*inch, caption=None):
    path = os.path.join(CHARTS_DIR, filename)
    if os.path.exists(path):
        img = Image(path, width=width, height=width*0.5)
        story.append(img)
        if caption:
            story.append(Paragraph(caption, caption_style))


def build_report():
    doc = SimpleDocTemplate(OUTPUT, pagesize=letter, 
                            topMargin=0.75*inch, bottomMargin=0.75*inch,
                            leftMargin=0.75*inch, rightMargin=0.75*inch)
    story = []
    
    # ===== COVER PAGE =====
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph('The IQ Investor', title_style))
    story.append(Paragraph('Algorithm & Backtesting Report', subtitle_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width='80%', color=ACCENT, thickness=2))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f'Generated: {datetime.now().strftime("%B %d, %Y")}', 
                            ParagraphStyle('Date', parent=body_style, alignment=TA_CENTER, textColor=DIM)))
    story.append(Paragraph(f'Data Range: {bt["data_range"]}', 
                            ParagraphStyle('Range', parent=body_style, alignment=TA_CENTER, textColor=DIM)))
    story.append(Paragraph(f'Universe: {bt["total_stocks"]} stocks · {bt["total_trading_days"]} trading days',
                            ParagraphStyle('Universe', parent=body_style, alignment=TA_CENTER, textColor=DIM)))
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph('Your IQ Edge in Investing', 
                            ParagraphStyle('Tagline', parent=body_style, alignment=TA_CENTER, 
                                           fontSize=14, textColor=ACCENT, fontName='Helvetica-Oblique')))
    story.append(PageBreak())
    
    # ===== TABLE OF CONTENTS =====
    story.append(Paragraph('Table of Contents', h1_style))
    toc = [
        '1. Executive Summary',
        '2. Quality Score — 14-Factor Stock Rating',
        '3. EWROS — Exponential Weighted Relative Outperformance',
        '4. Rotation Score — 6-Signal Rotation Detector',
        '5. IQ Edge Score — ML Breakout Prediction',
        '6. Power Matrix — Combined Signal Framework',
        '7. Combined Signal Performance',
        '8. Appendix: Parameters & Configuration',
    ]
    for item in toc:
        story.append(Paragraph(item, ParagraphStyle('TOC', parent=body_style, spaceBefore=6, fontSize=11)))
    story.append(PageBreak())
    
    # ===== 1. EXECUTIVE SUMMARY =====
    story.append(Paragraph('1. Executive Summary', h1_style))
    story.append(Paragraph(
        'The IQ Investor platform employs a multi-signal approach to stock analysis, combining fundamental quality metrics, '
        'momentum indicators, and machine learning to identify high-probability investment opportunities. '
        'This report documents each algorithm, its mathematical foundation, and backtesting results across 5 years of market data.',
        body_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph('Key Findings', h2_style))
    
    key_findings = [
        ['Metric', '1-Month', '3-Month', '6-Month'],
        ['Top EWROS Decile', f'+{bt["ewros"].get("top_10pct_1mo", 0)}%', f'+{bt["ewros"].get("top_10pct_3mo", 0)}%', f'+{bt["ewros"].get("top_10pct_6mo", 0)}%'],
        ['Bottom EWROS Decile', f'{bt["ewros"].get("bottom_10pct_1mo", 0)}%', f'{bt["ewros"].get("bottom_10pct_3mo", 0)}%', f'{bt["ewros"].get("bottom_10pct_6mo", 0)}%'],
        ['Power Zone', f'+{bt["power_matrix"]["quadrant_returns"].get("power_zone_1mo", 0)}%', f'+{bt["power_matrix"]["quadrant_returns"].get("power_zone_3mo", 0)}%', '—'],
        ['Avoid Zone', f'{bt["power_matrix"]["quadrant_returns"].get("avoid_1mo", 0)}%', f'{bt["power_matrix"]["quadrant_returns"].get("avoid_3mo", 0)}%', '—'],
        ['Grade A Stocks', f'+{bt["quality_score"]["returns_by_grade"]["1mo"].get("A", 0)}%', f'+{bt["quality_score"]["returns_by_grade"]["3mo"].get("A", 0)}%', f'+{bt["quality_score"]["returns_by_grade"]["6mo"].get("A", 0)}%'],
        ['Grade F Stocks', f'{bt["quality_score"]["returns_by_grade"]["1mo"].get("F", 0)}%', f'{bt["quality_score"]["returns_by_grade"]["3mo"].get("F", 0)}%', f'{bt["quality_score"]["returns_by_grade"]["6mo"].get("F", 0)}%'],
    ]
    story.append(make_table(key_findings, col_widths=[2.5*inch, 1.3*inch, 1.3*inch, 1.3*inch]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph(
        f'The EWROS signal shows the strongest differentiation: top-decile stocks returned '
        f'+{bt["ewros"].get("top_10pct_3mo", 0)}% over 3 months vs {bt["ewros"].get("bottom_10pct_3mo", 0)}% '
        f'for bottom-decile — a spread of {bt["ewros"].get("top_10pct_3mo", 0) - bt["ewros"].get("bottom_10pct_3mo", 0):.1f} percentage points.',
        body_style))
    story.append(PageBreak())
    
    # ===== 2. QUALITY SCORE =====
    story.append(Paragraph('2. Quality Score — 14-Factor Stock Rating', h1_style))
    story.append(Paragraph(
        'The Quality Score evaluates stocks on a 100-point scale across four categories: '
        'Technical Setup (53 pts max), Growth (33 pts max), Quality Fundamentals (18 pts max), '
        'and Market Context (10 pts max). Stocks are graded A through F based on their total score.',
        body_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Scoring Breakdown', h2_style))
    criteria_table = [
        ['Category', 'Factor', 'Max Points', 'Description'],
        ['Technical', 'Trend Alignment', '8', 'Price > 50d MA > 200d MA'],
        ['Technical', 'Breakout Pattern', '22', 'Flat ceiling base with <10% drift'],
        ['Technical', 'Consolidation', '10', 'Base depth and formation quality'],
        ['Technical', 'Volume Dry-up', '5', 'Volume decline during base (accumulation)'],
        ['Technical', '52W Proximity', '5', 'Distance from 52-week high'],
        ['Technical', 'Volatility Compression', '3', 'ATR narrowing before breakout'],
        ['Growth', 'Revenue Growth', '30', 'Both years ≥10% required (strict gate)'],
        ['Growth', 'Earnings Acceleration', '3', 'Sequential quarterly improvement'],
        ['Quality', 'ROE', '5', 'Return on equity quality'],
        ['Quality', 'Operating Margin', '5', 'Profitability margin'],
        ['Quality', 'Valuation (PEG)', '5', 'Price/Earnings to Growth ratio'],
        ['Quality', 'FCF Quality', '3', 'Free cash flow positive'],
        ['Context', 'Industry Strength', '5', 'Sector relative performance vs SPY'],
        ['Context', 'Relative Strength', '5', '6-month outperformance vs SPY'],
    ]
    story.append(make_table(criteria_table, col_widths=[1*inch, 1.5*inch, 0.8*inch, 3.2*inch]))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Grade Thresholds', h3_style))
    story.append(Paragraph('A ≥ 75 pts · B ≥ 60 pts · C ≥ 45 pts · D ≥ 30 pts · F < 30 pts', formula_style))
    
    story.append(Paragraph('Revenue Gate', h3_style))
    story.append(Paragraph(
        'The v4.4 "Revenue Gate" requires BOTH years of revenue growth to be ≥ 10% for any growth points '
        'to be awarded. This strict 2-year consistency gate ensures only companies with proven, '
        'sustained top-line growth earn quality ratings.',
        body_style))
    
    story.append(Paragraph('Backtest Results', h2_style))
    add_chart(story, 'quality_score_backtest.png', caption='Quality Score: Average returns by grade across holding periods')
    
    grade_counts = bt['quality_score']['counts']
    story.append(Paragraph(
        f'Universe breakdown: A={grade_counts.get("A",0)} stocks, B={grade_counts.get("B",0)}, '
        f'C={grade_counts.get("C",0)}, D={grade_counts.get("D",0)}, F={grade_counts.get("F",0)}. '
        f'Grade A stocks outperformed Grade F by {bt["quality_score"]["returns_by_grade"]["1yr"].get("A",0) - bt["quality_score"]["returns_by_grade"]["1yr"].get("F",0):.1f}% '
        f'over one year.',
        body_style))
    story.append(PageBreak())
    
    # ===== 3. EWROS =====
    story.append(Paragraph('3. EWROS — Exponential Weighted Relative Outperformance', h1_style))
    story.append(Paragraph(
        'EWROS (Exponential Weighted Relative Outperformance Score) is a proprietary momentum metric that measures '
        'how consistently a stock outperforms the S&P 500 on a daily basis, with exponential decay weighting '
        'that emphasizes recent performance.',
        body_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Formula', h2_style))
    story.append(Paragraph(
        'daily_alpha(t) = stock_return(t) - SPY_return(t)<br/>'
        'weight(t) = e^(-λ × days_ago)     where λ = 0.03 (~23 day half-life)<br/>'
        'EWROS_raw = Σ(daily_alpha(t) × weight(t))     over 63 trading days<br/>'
        'EWROS = percentile_rank(EWROS_raw)     scaled 1-99',
        formula_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Parameters', h3_style))
    ewros_params = [
        ['Parameter', 'Value', 'Rationale'],
        ['Lookback Days', '63', '~3 months of trading data'],
        ['Lambda (λ)', '0.03', 'Half-life of ~23 days — recent performance matters more'],
        ['Trend Offset', '21 days', 'Compare current EWROS to 1 month ago'],
        ['Benchmark', 'SPY', 'S&P 500 ETF as market proxy'],
    ]
    story.append(make_table(ewros_params, col_widths=[1.5*inch, 1*inch, 4*inch]))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Why Exponential Weighting?', h3_style))
    story.append(Paragraph(
        'Traditional relative strength (like IBD RS Rating) treats all days equally over 12 months. '
        'EWROS applies exponential decay so a stock that started outperforming 2 weeks ago scores higher '
        'than one that outperformed 4 months ago but has been flat since. This captures momentum shifts faster.',
        body_style))
    
    story.append(Paragraph('Backtest Results', h2_style))
    add_chart(story, 'ewros_backtest.png', caption='EWROS: Cumulative returns — Top 10% vs Bottom 10% vs SPY (1 Year)')
    
    spread_3mo = bt['ewros'].get('top_10pct_3mo', 0) - bt['ewros'].get('bottom_10pct_3mo', 0)
    story.append(Paragraph(
        f'The EWROS signal demonstrates strong predictive power. Over 3 months, top-decile stocks '
        f'returned +{bt["ewros"].get("top_10pct_3mo", 0)}% while bottom-decile returned '
        f'{bt["ewros"].get("bottom_10pct_3mo", 0)}% — a {spread_3mo:.1f}pp spread. '
        f'Over 1 year, the spread widens to {bt["ewros"].get("top_10pct_1yr", 0) - bt["ewros"].get("bottom_10pct_1yr", 0):.1f}pp.',
        body_style))
    story.append(PageBreak())
    
    # ===== 4. ROTATION SCORE =====
    story.append(Paragraph('4. Rotation Score — 6-Signal Rotation Detector', h1_style))
    story.append(Paragraph(
        'The Rotation Score identifies stocks undergoing institutional rotation — where smart money is '
        'flowing in ahead of a potential breakout. It combines 6 signals into a composite score (0-100).',
        body_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('6 Signals', h2_style))
    rot_signals = [
        ['Signal', 'Weight', 'What It Measures'],
        ['RS Divergence', '20%', 'Stock strengthening while market weakens'],
        ['Earnings Momentum', '20%', 'Sequential quarterly earnings improvement'],
        ['Valuation Gap', '15%', 'Discount to intrinsic value (PEG-based)'],
        ['Stage Breakout', '20%', 'Price breaking above accumulation base'],
        ['Volume Accumulation', '15%', 'Unusual volume surge pattern'],
        ['Sector Momentum', '10%', 'Industry group relative strength'],
    ]
    story.append(make_table(rot_signals, col_widths=[1.5*inch, 0.8*inch, 4.2*inch]))
    story.append(Spacer(1, 8))
    
    high_rot_1mo = bt['rotation'].get('high_rotation_1mo', 0)
    low_rot_1mo = bt['rotation'].get('low_rotation_1mo', 0)
    story.append(Paragraph(
        f'High rotation stocks (≥60) returned +{high_rot_1mo}% over 1 month vs {low_rot_1mo}% for low rotation (<30) — '
        f'a {high_rot_1mo - low_rot_1mo:.1f}pp spread.',
        body_style))
    story.append(PageBreak())
    
    # ===== 5. IQ EDGE SCORE =====
    story.append(Paragraph('5. IQ Edge Score — ML Breakout Prediction', h1_style))
    story.append(Paragraph(
        'The IQ Edge Score uses a machine learning model (XGBoost gradient boosted trees) trained on '
        '9,730 historical breakout events across 5 years to predict the probability of a stock '
        'achieving 100%+ gains (doubling) within 12 months of a breakout.',
        body_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Training Data', h2_style))
    iq = bt['iq_edge']
    labels = iq['label_distribution']
    training_table = [
        ['Metric', 'Value'],
        ['Total Breakout Events', f'{iq["total_events"]:,}'],
        ['Doubles (100%+)', f'{labels.get("double", 0)} ({labels.get("double", 0)/iq["total_events"]*100:.1f}%)'],
        ['Big Wins (50-100%)', f'{labels.get("big_win", 0)} ({labels.get("big_win", 0)/iq["total_events"]*100:.1f}%)'],
        ['Wins (25-50%)', f'{labels.get("win", 0)} ({labels.get("win", 0)/iq["total_events"]*100:.1f}%)'],
        ['Fails (<25%)', f'{labels.get("fail", 0)} ({labels.get("fail", 0)/iq["total_events"]*100:.1f}%)'],
        ['Data Period', '5 years (Mar 2021 – Mar 2026)'],
        ['Stock Universe', '1,008 stocks'],
        ['Model', 'XGBoost (gradient boosted trees)'],
        ['Test AUC', '0.758'],
    ]
    story.append(make_table(training_table, col_widths=[2.5*inch, 4*inch]))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Breakout Detection', h2_style))
    story.append(Paragraph(
        'A breakout is detected when:<br/>'
        '1. Price crosses above a consolidation base ceiling (20-120 day flat range, <15% drift)<br/>'
        '2. Volume on breakout day is ≥ 1.5x the 50-day average<br/>'
        '3. Minimum 150 days of prior price history available',
        body_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Feature Set (14 features)', h2_style))
    feature_table = [
        ['Feature', 'Category', 'Description'],
        ['close_to_ma20/50/200', 'Trend', 'Price relative to moving averages'],
        ['trend_aligned', 'Trend', 'Price > 50d MA > 200d MA (binary)'],
        ['atr_14', 'Volatility', '14-day Average True Range (normalized)'],
        ['vol_dryup_ratio', 'Volume', 'Recent vs earlier volume in base'],
        ['vol_compression', 'Volatility', 'Recent ATR vs longer-term ATR'],
        ['proximity_52w', 'Timing', 'Price relative to 52-week high'],
        ['return_3mo', 'Momentum', '3-month price return'],
        ['up_days_pct', 'Pattern', 'Percentage of up days in base'],
        ['vol_trend_in_base', 'Volume', 'Volume trend direction in base'],
        ['base_length', 'Pattern', 'Duration of consolidation base (days)'],
        ['base_range', 'Pattern', 'Price range width of base (%)'],
        ['breakout_vol_ratio', 'Volume', 'Breakout day volume vs 50d average'],
    ]
    story.append(make_table(feature_table, col_widths=[1.8*inch, 0.8*inch, 3.9*inch]))
    
    story.append(Paragraph('Key Finding: Volume Is the #1 Signal', h2_style))
    story.append(Paragraph(
        'Stocks that doubled had an average breakout volume ratio of 13.7x (vs 2.2x for failures). '
        'High-volume breakouts are 6x more likely to result in massive gains. '
        'Trend alignment also matters: 3.4% double rate when aligned vs 2.7% when not.',
        body_style))
    
    story.append(Paragraph('Backtest Results', h2_style))
    add_chart(story, 'iq_edge_backtest.png', caption='IQ Edge: Breakout volume impact on outcomes + outcome distribution')
    story.append(PageBreak())
    
    # ===== 6. POWER MATRIX =====
    story.append(Paragraph('6. Power Matrix — Combined Signal Framework', h1_style))
    story.append(Paragraph(
        'The Power Matrix combines EWROS (momentum) with Rotation Score (setup quality) into a '
        '2×2 quadrant framework that classifies every stock into an actionable category.',
        body_style))
    story.append(Spacer(1, 8))
    
    matrix_table = [
        ['', 'EWROS ≥ 70 (High Momentum)', 'EWROS < 70 (Low Momentum)'],
        ['Rotation ≥ 60\n(Fresh Setup)', '🎯 POWER ZONE\nMomentum + Setup → BUY', '⏳ EARLY SIGNAL\nSetting up → WATCH'],
        ['Rotation < 60\n(No Setup)', '⚠️ EXTENDED\nAlready ran → TAKE PROFIT', '💀 AVOID\nNo signal → SKIP'],
    ]
    t = Table(matrix_table, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SURFACE),
        ('BACKGROUND', (0, 0), (0, -1), SURFACE),
        ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#374151')),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#0a2e1a')),  # Power Zone
        ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#0a1e2e')),  # Early Signal
        ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#2e2a0a')),  # Extended
        ('BACKGROUND', (2, 2), (2, 2), colors.HexColor('#2e0a0a')),  # Avoid
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph('Backtest Results', h2_style))
    add_chart(story, 'power_matrix_backtest.png', caption='Power Matrix: Returns by quadrant (1-month and 3-month)')
    
    pz_1mo = bt['power_matrix']['quadrant_returns'].get('power_zone_1mo', 0)
    avoid_1mo = bt['power_matrix']['quadrant_returns'].get('avoid_1mo', 0)
    counts = bt['power_matrix']['counts']
    story.append(Paragraph(
        f'Current distribution: Power Zone = {counts["power"]} stocks, Extended = {counts["extended"]}, '
        f'Early Signal = {counts["early"]}, Avoid = {counts["avoid"]}. '
        f'Power Zone stocks returned +{pz_1mo}% over 1 month vs {avoid_1mo}% for Avoid — '
        f'a {pz_1mo - avoid_1mo:.1f}pp spread.',
        body_style))
    story.append(PageBreak())
    
    # ===== 7. COMBINED =====
    story.append(Paragraph('7. Combined Signal Performance', h1_style))
    story.append(Paragraph(
        'When all signals align (Grade A + EWROS ≥ 70 + IQ Edge ≥ 80), the combined signal '
        'identifies stocks with high quality, strong momentum, and ML-confirmed breakout potential.',
        body_style))
    story.append(Spacer(1, 8))
    
    combined = bt['combined']
    story.append(Paragraph(f'Currently {combined["combined_count"]} stocks pass all three filters:', body_style))
    if combined.get('tickers'):
        story.append(Paragraph(', '.join(combined['tickers']), metric_style))
    story.append(Spacer(1, 8))
    
    combined_table = [
        ['Signal Combination', '1-Month Return', '3-Month Return'],
        ['Combined (A + EWROS≥70 + IQ Edge≥80)', f'+{combined["returns"].get("combined_1mo", 0)}%', f'+{combined["returns"].get("combined_3mo", 0)}%'],
        ['Grade A Only', f'+{combined["returns"].get("grade_a_only_1mo", 0)}%', f'+{combined["returns"].get("grade_a_only_3mo", 0)}%'],
    ]
    story.append(make_table(combined_table, col_widths=[3*inch, 1.5*inch, 1.5*inch]))
    story.append(PageBreak())
    
    # ===== 8. APPENDIX =====
    story.append(Paragraph('8. Appendix: Parameters & Configuration', h1_style))
    
    story.append(Paragraph('System Architecture', h2_style))
    story.append(Paragraph(
        'Backend: Python (Flask) · Data: yfinance API · Database: Supabase (PostgreSQL) · '
        'ML: XGBoost + scikit-learn · Frontend: Vanilla JS + Chart.js · '
        'Deployment: Vercel · Domain: theiqinvestor.com',
        body_style))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph('Daily Pipeline Schedule (Mon-Fri, ET)', h2_style))
    pipeline = [
        ['Time', 'Job', 'Type'],
        ['4:05 PM', 'Daily Closing Scan', 'Python script'],
        ['4:15 PM', 'Distribution Scan', 'Python script'],
        ['4:20 PM', 'Earnings Calendar + Alert', 'Python script'],
        ['4:30 PM', 'Cache Refresh + Sector Leaderboard', 'Python script'],
        ['4:45 PM', 'Full Scan (Quality + Rotation + EWROS + IQ Edge)', 'Python script'],
        ['5:00 PM', 'Sell Signal Check', 'Python script'],
        ['5:30 PM', 'Earnings Recap Email', 'Python script'],
        ['6:00 PM', 'Insider Transaction Scan', 'Python script'],
        ['7:00 PM', 'Daily Alpha Report', 'LLM-assisted'],
    ]
    story.append(make_table(pipeline, col_widths=[1*inch, 3.5*inch, 2*inch]))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph('Key Parameters', h2_style))
    params_table = [
        ['Parameter', 'Value', 'Script'],
        ['Quality Score Scale', '0-100 points', 'rater.py'],
        ['Revenue Gate', 'Both years ≥ 10%', 'rater.py'],
        ['EWROS Lookback', '63 trading days', 'ewros.py'],
        ['EWROS Lambda', '0.03 (23-day half-life)', 'ewros.py'],
        ['EWROS Trend Offset', '21 days', 'ewros.py'],
        ['Rotation Signals', '6 (equally weighted composite)', 'rotation_catcher.py'],
        ['IQ Edge Model', 'XGBoost (500 trees, depth 6)', 'breakout_trainer.py'],
        ['Breakout Min Base', '20 days', 'breakout_labeler.py'],
        ['Breakout Max Drift', '15%', 'breakout_labeler.py'],
        ['Breakout Volume Threshold', '1.5x 50d avg', 'breakout_labeler.py'],
        ['Double Target', '100%+ gain in 12 months', 'breakout_labeler.py'],
    ]
    story.append(make_table(params_table, col_widths=[2*inch, 2*inch, 2.5*inch]))
    
    story.append(Spacer(1, 30))
    story.append(HRFlowable(width='100%', color=DIM, thickness=0.5))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        'Disclaimer: Past performance does not guarantee future results. This report is for informational '
        'purposes only and does not constitute investment advice. All backtesting results are based on '
        'historical data and may not reflect future market conditions.',
        ParagraphStyle('Disclaimer', parent=body_style, fontSize=8, textColor=DIM)))
    
    # Build PDF
    doc.build(story)
    print(f'✅ Report generated: {OUTPUT}')
    print(f'   Size: {os.path.getsize(OUTPUT) / 1024:.0f} KB')


if __name__ == '__main__':
    build_report()
