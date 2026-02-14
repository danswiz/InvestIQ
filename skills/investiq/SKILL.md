---
name: investiq
description: Investment research and stock analysis system. Use for ALL stock research, portfolio analysis, market scanning, and investment-related queries. Includes breakout pattern detection, CANSLIM analysis, moat assessment, sector rotation tracking, and trend identification. Triggers on any stock ticker mention, portfolio questions, market analysis requests, or investment strategy discussions.
---

# InvestIQ Investment Research System

InvestIQ is a comprehensive investment research framework for analyzing stocks, portfolios, and market trends.

## When to Use This Skill

Use InvestIQ for ANY investment-related request including:
- Stock analysis and research (single stocks or lists)
- Portfolio tracking and performance review
- Market scanning and opportunity identification
- Technical and fundamental analysis
- Breakout pattern detection
- Moat/competitive advantage assessment
- Sector rotation and industry strength analysis
- Investment strategy development
- Risk assessment and position sizing

## Portfolio Loading (CRITICAL)

**ALWAYS** load Dan's actual portfolio before analyzing "my portfolio" or holdings:

```python
# Load the official portfolio file
import subprocess
result = subprocess.run(['python3', 'skills/investiq/scripts/load_portfolio.py', 'all'], 
                       capture_output=True, text=True)
portfolio_stocks = result.stdout.split()
```

**OR** read directly from `/Users/dansmacmini/.openclaw/workspace/MY_PORTFOLIO.md`

**DO NOT** guess holdings or use stocks from previous scans. The MY_PORTFOLIO.md file is the source of truth.

**Current Portfolio Structure:**
- Defense: LHX, LMT, NOC (3 stocks)
- Grid-to-Chip: PWR, VRT, GEV (3 stocks)
- Core Holdings: 35 individual stocks (MSFT, NVDA, LLY, etc.)
- Core ETFs: 7 ETFs (COPX, GLD, ITA, etc.)

## Core Capabilities

### 1. Breakout Hunter Analysis
Scans for stocks with:
- Flat base consolidation patterns
- Volume dry-up (institutional quiet)
- Trend alignment (Price > SMA50 > SMA200)
- Grade scoring (A+ through C-)

**Script:** `scripts/rater.py <TICKER>`

### 2. CANSLIM Analysis
William O'Neil's 7-factor growth stock rating:
- Current quarterly earnings
- Annual earnings growth
- New products/management/highs
- Supply/demand (float, volume)
- Leader or laggard
- Institutional sponsorship
- Market direction

**Script:** `scripts/canslim.py <TICKER>`

### 3. Universe Scanning
Fast database-driven scanning of 1000+ stocks:
- Technical scoring (trend, breakout, momentum)
- Fundamental scoring (growth, quality, value)
- Sector strength weighting
- Smart money flow indicators

**Script:** `scripts/update_web_scan.py` (fast, DB-only)
**Script:** `scripts/refresh_cache.py` (slow, updates Yahoo data)

### 4. Moat Analysis
Deep qualitative assessment of competitive advantages:
- Network effects
- Switching costs
- Brand strength
- Cost advantages
- Regulatory/IP moats
- Durability assessment

**Reference:** Load `references/moat-analysis.md` when user asks for moat/competitive advantage analysis

### 5. Sector & Industry Analysis
- Sector rotation tracking
- Industry strength scoring
- Supply chain analysis
- Regulatory environment
- Cyclical vs secular trends

**Reference:** Load `references/sector-dynamics.md` for deep sector analysis

### 6. Mega-Trend Identification
Identifies 1st and 2nd order beneficiaries of major trends:
- AI infrastructure
- Electrification
- Biotech innovation
- Aging demographics
- Supply chain reshoring

**Reference:** Load `references/mega-trends.md` for trend framework

### 7. TenX Hunter (Hypergrowth Analysis)
Qualitative overlay for identifying 10X potential stocks:
- New product/innovation cycles
- Business growth engines
- Moat durability during growth phase
- Visionary CEO assessment
- Market tailwinds and timing
- 1st vs 2nd order mega-trend positioning
- "Why now" catalyst identification

**Reference:** Load `references/tenx-hunter.md` for framework details
**Script:** `scripts/tenx_scan.py [TICKERS...]` for automated scoring

**When to Deploy:**
- User asks: "10x scan", "hypergrowth analysis", "what's the next big winner?"
- AFTER technical/fundamental analysis is complete
- For qualitative overlay on top-rated stocks

**Scoring Factors (weighted):**
- New Product/Innovation (20%)
- Growth Engine (20%)
- Moat Durability (20%)
- Visionary CEO (15%)
- Market Tailwinds (15%)
- Mega-Trend Position (10%)

**Grades:**
- A+ (9.0+): Exceptional 10X candidate
- A (8.5+): Strong 10X potential
- A- (8.0+): Very good 10X candidate
- B+ (7.5+): Possible 5-10X with execution
- B and below: Limited 10X characteristics

## Analysis Workflow

### For Single Stock Analysis:
1. Run `scripts/rater.py <TICKER>` for breakout score
2. Fetch current price and fundamentals from DB
3. If user asks for moat: load `references/moat-analysis.md`
4. If user asks for trend exposure: load `references/mega-trends.md`
5. Compile comprehensive report with all requested components

### For Universe Scans:
1. Ensure DB is fresh (check last update)
2. Run `scripts/update_web_scan.py` for fast scan
3. Apply sector caps if requested (max 2 per sector)
4. Rank by composite score
5. Generate HTML report

### For Portfolio Analysis:
1. Load holdings from `holdings.txt`
2. Rate each holding
3. Assess concentration risk
4. Identify gaps/opportunities
5. Compare to market benchmarks

## Report Generation

Always generate clean HTML reports and email to dbirru@gmail.com:
- Use `email_sender.py` for distribution
- Include: grade, score, key metrics, thesis, risks, catalysts
- Format for mobile readability (narrow tables, bullet points)

## Key Files

- `market_data.db` — SQLite database with 1000+ stocks
- `top_stocks.json` — Latest scan results
- `russell1000_tickers.txt` — Universe definition
- `holdings.txt` — User's portfolio positions

## Database Schema

Tables: tickers, prices, fundamentals
Key fields: symbol, close, sma_50, sma_200, revenue_growth, earnings_growth, pe_forward, sector

## Dependencies

- Python 3.x
- yfinance (for data fetching)
- pandas, numpy (for analysis)
- sqlite3 (for data storage)

## Important Notes

- ALWAYS check data freshness (prices from 2026-02-06)
- Use cached DB for speed; refresh_cache.py for updates
- Apply sector caps for diversified portfolios
- Note 10X potential is speculative; include risk disclaimers
