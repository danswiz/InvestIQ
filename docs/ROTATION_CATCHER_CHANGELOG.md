# Rotation Catcher - Change Log

## Version 2.0 - Universal Rotation Detector (2026-02-28)

### ✅ CRITICAL FIX: Removed Mag7 Dependency

**Problem:** Signal 7 "Mega-Cap Weakness" was hardcoded to Mag7 stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA), making it non-universal and biased toward tech rotation detection.

**Solution:** Removed Signal 7 entirely and redistributed its 10% weight proportionally across the remaining 6 signals.

---

## Changes Made

### 1. **Removed Code**
   - ❌ `MAG7` constant (list of 7 tech stocks)
   - ❌ `_get_mag7_data()` method
   - ❌ `_signal_megacap_weakness()` method
   - ❌ All references to `megacap_weakness` in results

### 2. **Weight Redistribution**

**Before (7 signals):**
```python
WEIGHTS = {
    'rs_divergence': 0.20,          # 20%
    'earnings_revisions': 0.15,     # 15%
    'valuation_gap': 0.15,          # 15%
    'stage_breakout': 0.20,         # 20%
    'volume_accumulation': 0.10,    # 10%
    'sector_momentum': 0.10,        # 10%
    'megacap_weakness': 0.10,       # 10% ← REMOVED
}
```

**After (6 signals):**
```python
WEIGHTS = {
    'rs_divergence': 0.2222,        # 22.22% (+2.22%)
    'earnings_revisions': 0.1667,   # 16.67% (+1.67%)
    'valuation_gap': 0.1667,        # 16.67% (+1.67%)
    'stage_breakout': 0.2222,       # 22.22% (+2.22%)
    'volume_accumulation': 0.1111,  # 11.11% (+1.11%)
    'sector_momentum': 0.1111,      # 11.11% (+1.11%)
}
```

**Mathematical verification:** Sum = 1.0000 (100%) ✓

### 3. **Result Structure Update**

**Before:**
```python
{
    'signals': {
        'rs_divergence': {...},
        'earnings_revisions': {...},
        'valuation_gap': {...},
        'stage_breakout': {...},
        'volume_accumulation': {...},
        'sector_momentum': {...},
        'megacap_weakness': {...},  # ← REMOVED
    }
}
```

**After:**
```python
{
    'signals': {
        'rs_divergence': {...},
        'earnings_revisions': {...},
        'valuation_gap': {...},
        'stage_breakout': {...},
        'volume_accumulation': {...},
        'sector_momentum': {...},
    }
}
```

---

## Testing Results

### Original Test (with Mag7 dependency):
```
VRT    Rotation: 76.2  Signal: ROTATION WATCH
MU     Rotation: 65.0  Signal: ROTATION WATCH
LLY    Rotation: 53.4  Signal: NEUTRAL
GOOGL  Rotation: 59.8  Signal: NEUTRAL
NVT    Rotation: 78.8  Signal: ROTATION WATCH
```

### New Test (6 signals, no Mag7):
```
VRT    Rotation: 69.4  Signal: ROTATION WATCH
MU     Rotation: 56.6  Signal: NEUTRAL
LLY    Rotation: 48.2  Signal: NEUTRAL
GOOGL  Rotation: 51.6  Signal: NEUTRAL
NVT    Rotation: 72.3  Signal: ROTATION WATCH
```

### Universal Sector Test:
```
JPM    (Financial)           Rotation: 23.2  WEAK
XOM    (Energy)              Rotation: 62.9  ROTATION WATCH
PFE    (Healthcare)          Rotation: 50.0  NEUTRAL
CAT    (Industrials)         Rotation: 52.9  NEUTRAL
WMT    (Consumer Defensive)  Rotation: 50.1  NEUTRAL
DIS    (Communication)       Rotation: 25.7  WEAK
```

✅ **All sectors tested successfully - no Mag7 dependency!**

---

## Why This Is Better

1. **Universal Application:** Works for ANY stock in ANY sector (not just tech vs non-tech)
2. **No Hardcoded Biases:** Doesn't assume rotation = "money leaving Mag7"
3. **Simpler & Faster:** Removed 7 API calls per stock (Mag7 data fetches)
4. **Cleaner Logic:** Volume accumulation already captures institutional flow
5. **Mathematically Sound:** Weight redistribution preserves signal importance proportionally

---

## The 6 Rotation Signals

| Signal                    | Weight  | What It Measures                                    |
|---------------------------|---------|-----------------------------------------------------|
| RS Divergence             | 22.22%  | Outperformance vs SPY/QQQ, acceleration             |
| Earnings Revisions        | 16.67%  | Forward EPS growth, revenue/earnings momentum       |
| Valuation Gap             | 16.67%  | P/E discount, PEG ratio, coiled spring setup        |
| Stage Breakout            | 22.22%  | Weinstein MA crossover, volume surge, 52w high      |
| Volume Accumulation       | 11.11%  | Up/down volume ratio, OBV trend, institutional flow |
| Sector Momentum           | 11.11%  | Sector ETF alpha vs SPY, acceleration, strength     |

**Total:** 100%

---

## Integration Status

✅ `rotation_catcher.py` - Updated (6 signals)  
✅ `update_web_scan.py` - Already integrated (no changes needed)  
✅ `generate_watchlist.py` - Already integrated (no changes needed)  
✅ `index.html` - Already integrated (no changes needed)  

**Next scan will automatically use the new 6-signal model.**

---

## Migration Notes

**No breaking changes for existing integrations:**
- The `score()` method signature is unchanged
- Return structure is compatible (just removed one signal key)
- All scores normalized to 0-100 scale
- Classification thresholds remain the same

**For users of `all_stocks.json`:**
- `rotation_score` field remains (composite score 0-100)
- `rotation_signal` field remains (classification string)
- Scores will be slightly different due to weight redistribution
