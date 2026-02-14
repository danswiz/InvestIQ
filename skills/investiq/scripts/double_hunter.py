#!/usr/bin/env python3
"""
Double Hunter - Realistic 2X in 12 Months Analysis
More achievable than 10X - focuses on near-term catalysts and valuation expansion
"""

import json
import sys

# Double Hunter criteria - more realistic than 10X
DOUBLE_CRITERIA = {
    "earnings_catalyst": {
        "weight": 0.25,
        "description": "Near-term earnings beats, guidance raises, margin expansion"
    },
    "breakout_setup": {
        "weight": 0.20,
        "description": "Technical breakout pattern, volume confirmation, institutional accumulation"
    },
    "valuation_gap": {
        "weight": 0.20,
        "description": "Trading below peers, multiple expansion potential, reasonable entry"
    },
    "size_sweetspot": {
        "weight": 0.15,
        "description": "$10B-$300B market cap - big enough to be real, small enough to double"
    },
    "sector_tailwinds": {
        "weight": 0.15,
        "description": "Sector in favor, fund flows, narrative alignment"
    },
    "catalyst_timeline": {
        "weight": 0.05,
        "description": "Clear catalysts in next 4-8 quarters"
    }
}

# Double Hunter knowledge base - realistic 2X candidates
DOUBLE_KNOWLEDGE_BASE = {
    # HIGH CONVICTION 2X CANDIDATES
    "VRT": {
        "earnings_catalyst": 9,
        "breakout_setup": 9,
        "valuation_gap": 8,
        "size_sweetspot": 9,
        "sector_tailwinds": 10,
        "catalyst_timeline": 9,
        "thesis": "AI data center power demand exploding. 6-month consolidation breakout. $20B market cap can double. Every AI chip needs power infrastructure.",
        "path_to_2x": "Multiple expansion (20x→35x earnings) + 40% earnings growth. Trading at discount to growth. Grid-to-chip narrative gaining traction.",
        "catalysts": "Q1/Q2 earnings beats, AI data center announcements, grid investment news",
        "risk": "Execution on growth, competition from Eaton",
        "current_price": "$195",
        "target_2x": "$390"
    },
    "MU": {
        "earnings_catalyst": 9,
        "breakout_setup": 8,
        "valuation_gap": 9,
        "size_sweetspot": 8,
        "sector_tailwinds": 9,
        "catalyst_timeline": 9,
        "thesis": "HBM supply-constrained through 2025. Memory cycle turn + AI structural demand. $120B market cap can double on earnings recovery.",
        "path_to_2x": "Memory prices recover + HBM mix improves margins. PE 15x→25x + EPS doubling. Classic cyclical recovery with AI kicker.",
        "catalysts": "Memory price increases, HBM capacity announcements, AI server demand data",
        "risk": "Memory oversupply, China restrictions",
        "current_price": "$95",
        "target_2x": "$190"
    },
    "LLY": {
        "earnings_catalyst": 9,
        "breakout_setup": 7,
        "valuation_gap": 7,
        "size_sweetspot": 6,
        "sector_tailwinds": 10,
        "catalyst_timeline": 9,
        "thesis": "GLP-1 demand outpacing supply. Mounjaro/Zepbound ramping. $900B market cap but massive earnings acceleration ahead.",
        "path_to_2x": "Supply catches demand, Medicare coverage expands, pipeline success. EPS growth 50%+ for 3 years.",
        "catalysts": "Quarterly supply updates, pipeline readouts, Medicare decisions",
        "risk": "$900B already large, Novo Nordisk competition, patent cliffs",
        "current_price": "$1,020",
        "target_2x": "$2,040"
    },
    "ANET": {
        "earnings_catalyst": 8,
        "breakout_setup": 8,
        "valuation_gap": 8,
        "size_sweetspot": 9,
        "sector_tailwinds": 10,
        "catalyst_timeline": 9,
        "thesis": "AI networking leader. Google/Meta/MSFT all using Arista for AI clusters. Displacing Cisco. $110B can double.",
        "path_to_2x": "AI data center capex boom. 800G/1.6G transition. Multiple expansion + 40% revenue growth. Cisco's lunch being eaten.",
        "catalysts": "AI cluster deployments, 800G product ramp, earnings beats",
        "risk": "Cisco competition, customer concentration",
        "current_price": "$350",
        "target_2x": "$700"
    },
    "PWR": {
        "earnings_catalyst": 8,
        "breakout_setup": 8,
        "valuation_gap": 7,
        "size_sweetspot": 7,
        "sector_tailwinds": 9,
        "catalyst_timeline": 8,
        "thesis": "Grid modernization leader. EVs + data centers + renewables all need grid upgrades. $40B market cap.",
        "path_to_2x": "Infrastructure bill flows through. Grid investment accelerating. Earnings +30%, multiple expansion.",
        "catalysts": "Infrastructure awards, grid interconnection backlog, earnings beats",
        "risk": "Interest rates, project delays",
        "current_price": "$260",
        "target_2x": "$520"
    },
    # MODERATE 2X POTENTIAL
    "NVDA": {
        "earnings_catalyst": 10,
        "breakout_setup": 6,
        "valuation_gap": 5,
        "size_sweetspot": 2,
        "sector_tailwinds": 10,
        "catalyst_timeline": 8,
        "thesis": "Best AI position but $4T market cap makes 2X hard ($8T? unlikely in 12 months).",
        "path_to_2x": "Would need $8T market cap. Possible but stretched. Better for 50% gains than 100%.",
        "catalysts": "Blackwell ramp, inference dominance, robotics",
        "risk": "Already $4T, China restrictions, competition",
        "current_price": "$172",
        "target_2x": "$344 (UNLIKELY)",
        "warning": "Great company but $4T→$8T in 12 months is a stretch"
    },
    "TSM": {
        "earnings_catalyst": 8,
        "breakout_setup": 7,
        "valuation_gap": 7,
        "size_sweetspot": 4,
        "sector_tailwinds": 9,
        "catalyst_timeline": 8,
        "thesis": "Foundry monopoly but $1.7T market cap. 2X would be $3.4T - possible but aggressive.",
        "path_to_2x": "AI demand sustains, pricing power, geopolitical clarity. 50-70% upside more realistic.",
        "catalysts": "AI chip demand, price increases, Arizona ramp",
        "risk": "China/Taiwan, Intel competition",
        "current_price": "$330",
        "target_2x": "$660"
    },
    "META": {
        "earnings_catalyst": 7,
        "breakout_setup": 7,
        "valuation_gap": 6,
        "size_sweetspot": 3,
        "sector_tailwinds": 7,
        "catalyst_timeline": 7,
        "thesis": "Strong but $1.7T market cap. 2X = $3.4T. AI improving engagement but already priced in.",
        "path_to_2x": "Would need massive multiple expansion. 50% upside more realistic than 100%.",
        "catalysts": "AI engagement gains, Reels monetization, cost discipline",
        "risk": "Size, TikTok competition, AI capex",
        "current_price": "$670",
        "target_2x": "$1,340"
    },
    # LOW 2X POTENTIAL (Mature/Large)
    "MSFT": {
        "earnings_catalyst": 7,
        "breakout_setup": 5,
        "valuation_gap": 4,
        "size_sweetspot": 1,
        "sector_tailwinds": 8,
        "catalyst_timeline": 6,
        "thesis": "$2.9T market cap. 2X = $5.8T in 12 months? Virtually impossible. Best case: 30-50% gain.",
        "path_to_2x": "Not realistic at this size. Focus on 20-30% annual returns.",
        "warning": "Too large for 2X in 12 months"
    },
    "AMZN": {
        "earnings_catalyst": 6,
        "breakout_setup": 6,
        "valuation_gap": 6,
        "size_sweetspot": 2,
        "sector_tailwinds": 6,
        "catalyst_timeline": 6,
        "thesis": "$2.4T market cap. 2X = $4.8T. Possible but very aggressive. 40-60% more realistic.",
        "path_to_2x": "AWS reacceleration + retail margin expansion. Doable but stretched.",
        "warning": "Large cap, 2X would be massive"
    },
    "GOOGL": {
        "earnings_catalyst": 6,
        "breakout_setup": 6,
        "valuation_gap": 6,
        "size_sweetspot": 2,
        "sector_tailwinds": 6,
        "catalyst_timeline": 6,
        "thesis": "$4T market cap. 2X = $8T. Unlikely in 12 months. 30-50% more realistic.",
        "path_to_2x": "AI integration drives search share + cloud growth. But size is constraint.",
        "warning": "Already $4T, regulatory risk"
    },
    "AVGO": {
        "earnings_catalyst": 7,
        "breakout_setup": 6,
        "valuation_gap": 5,
        "size_sweetspot": 4,
        "sector_tailwinds": 7,
        "catalyst_timeline": 7,
        "thesis": "$1.5T market cap. AI chip demand + VMware synergies. 2X possible but aggressive.",
        "path_to_2x": "Custom silicon demand + software growth. 50-80% upside more likely than 100%.",
        "current_price": "$320",
        "target_2x": "$640"
    },
    "ASML": {
        "earnings_catalyst": 7,
        "breakout_setup": 5,
        "valuation_gap": 5,
        "size_sweetspot": 5,
        "sector_tailwinds": 7,
        "catalyst_timeline": 7,
        "thesis": "$520B market cap. Monopoly position but 2X = $1T. Possible with AI capex boom.",
        "path_to_2x": "Fab buildout cycle + High-NA EUV. Stretched but possible.",
        "current_price": "$700",
        "target_2x": "$1,400"
    },
    # SPECIFIC UNDERPERFORMERS WITH 2X POTENTIAL
    "TSLA": {
        "earnings_catalyst": 4,
        "breakout_setup": 4,
        "valuation_gap": 3,
        "size_sweetspot": 4,
        "sector_tailwinds": 5,
        "catalyst_timeline": 4,
        "thesis": "$1.5T market cap but struggling. No moat, competition intensifying. 2X would need massive turnaround.",
        "path_to_2x": "Unlikely without FSD breakthrough or Model 2 success. At risk of DOWN 50%, not up 100%.",
        "warning": "FADING COMPETITIVE POSITION - avoid"
    },
    "PLTR": {
        "earnings_catalyst": 5,
        "breakout_setup": 3,
        "valuation_gap": 2,
        "size_sweetspot": 7,
        "catalyst_timeline": 5,
        "thesis": "$310B market cap. 200x PE. Government lumpy revenue. 2X would be $620B - hype exceeds fundamentals.",
        "path_to_2x": "Valuation too stretched. At risk of 50% correction, not 100% gain.",
        "warning": "EXTREME VALUATION - avoid"
    },
    "UBER": {
        "earnings_catalyst": 5,
        "breakout_setup": 5,
        "valuation_gap": 5,
        "size_sweetspot": 7,
        "sector_tailwinds": 4,
        "catalyst_timeline": 5,
        "thesis": "$157B market cap. Commoditized service, no pricing power. 2X possible but not high conviction.",
        "path_to_2x": "Autonomous breakthrough or monopoly formation. Unlikely.",
        "warning": "No moat, low margins"
    },
    # BOTTOM OF PORTFOLIO - NO 2X POTENTIAL
    "LHX": {"skip": True, "reason": "Defense contractor, mature, no hypergrowth"},
    "LMT": {"skip": True, "reason": "Defense, largest contractor, slow growth"},
    "NOC": {"skip": True, "reason": "Defense, space/cyber growing but not 2X"},
    "CAT": {"skip": True, "reason": "Cyclical machinery, mature"},
    "HD": {"skip": True, "reason": "Retail, housing dependent, mature"},
    "JPM": {"skip": True, "reason": "Bank, regulatory constraints, mature"},
    "V": {"skip": True, "reason": "Payments duopoly, mature market"},
    "BRK-B": {"skip": True, "reason": "Conglomerate, $1T+, value not growth"},
    "UNH": {"skip": True, "reason": "Healthcare insurance, regulatory risk"},
    "NFLX": {"skip": True, "reason": "Streaming mature, content arms race"},
    "NOW": {"skip": True, "reason": "Enterprise software, 61x PE, mature"},
    "ORCL": {"skip": True, "reason": "Legacy tech, slow growth"},
    "CRM": {"skip": True, "reason": "50x PE, slowing growth"},
    "PANW": {"skip": True, "reason": "Cybersecurity crowded, commoditizing"},
    "CRWD": {"skip": True, "reason": "Endpoint security, MSFT competition"},
    "MRVL": {"skip": True, "reason": "No moat vs NVDA"},
    "WDC": {"skip": True, "reason": "Storage commodity"},
    "STX": {"skip": True, "reason": "Storage commodity"},
    "AMAT": {"skip": True, "reason": "Semi equipment oligopoly, cyclical"},
    "LRCX": {"skip": True, "reason": "Semi equipment oligopoly, cyclical"},
    "AMD": {"skip": True, "reason": "No ecosystem moat vs NVDA"},
    "ISRG": {"skip": True, "reason": "MedTech mature, installed base"},
    "TMUS": {"skip": True, "reason": "Telecom commodity"},
    "GEV": {"skip": True, "reason": "Post-spinoff power, slow growth"},
    "GE": {"skip": True, "reason": "Aerospace duopoly, cyclical"}
}

def calculate_double_score(stock_data):
    """Calculate weighted 2X score"""
    if stock_data.get("skip"):
        return 0
    total_score = 0
    for criterion, config in DOUBLE_CRITERIA.items():
        score = stock_data.get(criterion, 5)
        total_score += score * config["weight"]
    return round(total_score, 1)

def get_double_grade(score):
    """Convert score to 2X potential grade"""
    if score >= 8.5:
        return "A+", "High Conviction 2X"
    elif score >= 8.0:
        return "A", "Strong 2X Potential"
    elif score >= 7.5:
        return "A-", "Possible 2X"
    elif score >= 7.0:
        return "B+", "50-100% Upside"
    elif score >= 6.0:
        return "B", "30-70% Upside"
    elif score >= 5.0:
        return "C+", "20-40% Upside"
    else:
        return "C", "Limited Upside"

def analyze_double(ticker):
    """Analyze a single stock for 2X potential"""
    ticker = ticker.upper().strip()
    
    if ticker in DOUBLE_KNOWLEDGE_BASE:
        data = DOUBLE_KNOWLEDGE_BASE[ticker].copy()
    else:
        data = {"skip": True, "reason": "No analysis available"}
    
    if data.get("skip"):
        return {
            "ticker": ticker,
            "score": 0,
            "grade": "D",
            "grade_description": "Skip - " + data.get("reason", "No 2X potential"),
            "skip": True
        }
    
    score = calculate_double_score(data)
    grade, description = get_double_grade(score)
    
    return {
        "ticker": ticker,
        "score": score,
        "grade": grade,
        "grade_description": description,
        "thesis": data.get("thesis", ""),
        "path_to_2x": data.get("path_to_2x", ""),
        "catalysts": data.get("catalysts", ""),
        "risk": data.get("risk", ""),
        "current_price": data.get("current_price", ""),
        "target_2x": data.get("target_2x", ""),
        "warning": data.get("warning", None)
    }

def main():
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        tickers = []
    
    print(f"🔍 Double Hunter: Analyzing {len(tickers)} stocks for 2X potential in 12 months...\n")
    
    results = []
    for ticker in tickers:
        result = analyze_double(ticker)
        results.append(result)
        if not result.get("skip"):
            print(f"  {ticker}: {result['score']:.1f} ({result['grade']}) - {result['grade_description']}")
        else:
            print(f"  {ticker}: SKIP - {result['grade_description']}")
    
    # Filter to valid results and sort
    valid_results = [r for r in results if not r.get("skip")]
    valid_results.sort(key=lambda x: x["score"], reverse=True)
    
    print(f"\n🏆 Top 2X Candidates:")
    for i, r in enumerate(valid_results[:10], 1):
        print(f"  {i}. {r['ticker']}: {r['score']:.1f} - {r.get('target_2x', '')}")
    
    print(f"\n⚠️ Skip these (no 2X potential):")
    skipped = [r for r in results if r.get("skip")]
    for r in skipped:
        print(f"  {r['ticker']}: {r['grade_description']}")

if __name__ == "__main__":
    main()
