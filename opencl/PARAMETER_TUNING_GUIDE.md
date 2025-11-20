# Individual Parameter Range Tuning Guide

## Overview

The optimizer now supports **individual percentage ranges** for each parameter. This gives you fine-grained control over the search space, allowing you to:

- Narrow the search for well-optimized parameters (e.g., ±1%)
- Widen the search for uncertain parameters (e.g., ±15%)
- Mix narrow and wide ranges to balance speed vs. exploration

---

## Configuration Files

Each timeframe has its own configuration file with individual percentage controls:

- **1h**: `strategies/adaptive_ema_v1/config_1h.h`
- **4h**: `strategies/adaptive_ema_v1/config_4h.h`
- **1d**: `strategies/adaptive_ema_v1/config_1d.h`

---

## How to Set Individual Ranges

### Example: config_1h.h

```c
// Default parameter values
#define FAST_LOW_1H 6
#define SLOW_LOW_1H 78
#define FAST_MED_1H 18
#define SLOW_MED_1H 85
// ... more parameters

// Individual search percentages for each parameter
#define SEARCH_PERCENT_FAST_LOW_1H 0.02     // ±2% from FAST_LOW_1H (6)
#define SEARCH_PERCENT_SLOW_LOW_1H 0.05     // ±5% from SLOW_LOW_1H (78)
#define SEARCH_PERCENT_FAST_MED_1H 0.01     // ±1% from FAST_MED_1H (18)
#define SEARCH_PERCENT_SLOW_MED_1H 0.03     // ±3% from SLOW_MED_1H (85)
// ... more percentages
```

### What the Percentages Mean

| Percentage | Description | Use Case | Example: FAST_LOW_1H=6 |
|------------|-------------|----------|------------------------|
| `0.01` | ±1% | Fine-tuning well-optimized params | 5.94-6.06 → tests 5,6 (2 values) |
| `0.02` | ±2% | Minor adjustments | 5.88-6.12 → tests 5,6 (2 values) |
| `0.05` | ±5% | Moderate exploration | 5.7-6.3 → tests 5,6 (2 values) |
| `0.10` | ±10% | Wide exploration | 5.4-6.6 → tests 5,6 (2 values) |
| `0.15` | ±15% | Very wide exploration | 5.1-6.9 → tests 5,6,7 (3 values) |

**Note**: Integer casting means small percentages on small values may produce the same min/max.

---

## Strategy: When to Use Different Ranges

### Scenario 1: Fine-Tuning Known-Good Parameters

You've already optimized and found good parameters. Now refine them.

```c
// Narrow ranges for all parameters (fast optimization)
#define SEARCH_PERCENT_FAST_LOW_1H 0.01     // ±1%
#define SEARCH_PERCENT_SLOW_LOW_1H 0.01     // ±1%
#define SEARCH_PERCENT_FAST_MED_1H 0.01     // ±1%
#define SEARCH_PERCENT_SLOW_MED_1H 0.01     // ±1%
#define SEARCH_PERCENT_FAST_HIGH_1H 0.01    // ±1%
#define SEARCH_PERCENT_SLOW_HIGH_1H 0.01    // ±1%
#define SEARCH_PERCENT_ATR_1H 0.01          // ±1%
#define SEARCH_PERCENT_VOL_1H 0.01          // ±1%
#define SEARCH_PERCENT_LOW_PCT_1H 0.01      // ±1%
#define SEARCH_PERCENT_HIGH_PCT_1H 0.01     // ±1%
```

**Result**: Very fast optimization (~0.1-1 sec), tests ~100-1000 combinations

---

### Scenario 2: Initial Exploration

You're starting fresh and want to explore a wide parameter space.

```c
// Wide ranges for all parameters (thorough exploration)
#define SEARCH_PERCENT_FAST_LOW_1H 0.10     // ±10%
#define SEARCH_PERCENT_SLOW_LOW_1H 0.10     // ±10%
#define SEARCH_PERCENT_FAST_MED_1H 0.10     // ±10%
#define SEARCH_PERCENT_SLOW_MED_1H 0.10     // ±10%
#define SEARCH_PERCENT_FAST_HIGH_1H 0.10    // ±10%
#define SEARCH_PERCENT_SLOW_HIGH_1H 0.10    // ±10%
#define SEARCH_PERCENT_ATR_1H 0.10          // ±10%
#define SEARCH_PERCENT_VOL_1H 0.10          // ±10%
#define SEARCH_PERCENT_LOW_PCT_1H 0.10      // ±10%
#define SEARCH_PERCENT_HIGH_PCT_1H 0.10     // ±10%
```

**Result**: Slower optimization (~5-30 sec), tests ~100M+ combinations

---

### Scenario 3: Mixed Strategy (Recommended)

Focus wide search on uncertain parameters, narrow search on stable ones.

```c
// EMA periods - fairly confident, narrow search
#define SEARCH_PERCENT_FAST_LOW_1H 0.02     // ±2%
#define SEARCH_PERCENT_SLOW_LOW_1H 0.02     // ±2%
#define SEARCH_PERCENT_FAST_MED_1H 0.02     // ±2%
#define SEARCH_PERCENT_SLOW_MED_1H 0.02     // ±2%
#define SEARCH_PERCENT_FAST_HIGH_1H 0.02    // ±2%
#define SEARCH_PERCENT_SLOW_HIGH_1H 0.02    // ±2%

// Volatility parameters - less certain, wider search
#define SEARCH_PERCENT_ATR_1H 0.08          // ±8%
#define SEARCH_PERCENT_VOL_1H 0.08          // ±8%

// Percentile thresholds - very uncertain, widest search
#define SEARCH_PERCENT_LOW_PCT_1H 0.15      // ±15%
#define SEARCH_PERCENT_HIGH_PCT_1H 0.15     // ±15%
```

**Result**: Balanced optimization (~2-10 sec), focused exploration where it matters

---

## Calculating Search Space Size

The total number of combinations is the **product** of individual parameter ranges:

```
Total Combinations = 
  (fast_low range) × (slow_low range) × (fast_med range) × ... × (high_pct range)
```

### Example Calculation

```c
// Given these settings:
FAST_LOW_1H = 6,  SEARCH_PERCENT = 0.05  →  5.7-6.3  →  2 values (5,6)
SLOW_LOW_1H = 78, SEARCH_PERCENT = 0.05  →  74.1-81.9 →  8 values (74-81)
FAST_MED_1H = 18, SEARCH_PERCENT = 0.05  →  17.1-18.9 →  2 values (17,18)
// ... and so on for all 10 parameters

Total = 2 × 8 × 2 × ... (multiply all ranges)
```

**Tip**: Use narrow ranges (±1-2%) to keep combinations under 1 million for sub-second optimization.

---

## Practical Workflow

### Step 1: Initial Wide Search

```bash
# Edit config_1h.h: Set all percentages to 0.08-0.10
nano strategies/adaptive_ema_v1/config_1h.h

# Run optimization
./run.sh QQQ 1h
```

**Record the best parameters from the HTML report.**

---

### Step 2: Update Defaults with Best Parameters

```c
// In config_1h.h, update the #define values:
#define FAST_LOW_1H 5      // Was 6, optimizer found 5 is better
#define SLOW_LOW_1H 82     // Was 78, optimizer found 82 is better
// ... update ALL parameters
```

---

### Step 3: Narrow Search

```bash
# Edit config_1h.h: Set all percentages to 0.02-0.03
nano strategies/adaptive_ema_v1/config_1h.h

# Run optimization again
./run.sh QQQ 1h
```

**Repeat Steps 2-3 until Calmar Ratio stops improving.**

---

### Step 4: Final Fine-Tuning

```bash
# Edit config_1h.h: Set all percentages to 0.01
nano strategies/adaptive_ema_v1/config_1h.h

# Run final optimization
./run.sh QQQ 1h
```

---

## Advanced: Parameter Sensitivity Analysis

Test how sensitive the strategy is to each parameter by varying only its range:

```c
// Test 1: Vary only FAST_LOW_1H
#define SEARCH_PERCENT_FAST_LOW_1H 0.15     // ±15%
#define SEARCH_PERCENT_SLOW_LOW_1H 0.00     // No variation
#define SEARCH_PERCENT_FAST_MED_1H 0.00     // No variation
// ... all others = 0.00

// Run: ./run.sh QQQ 1h
// Observe: How much does Calmar Ratio change?
// High variance = parameter is important
// Low variance = parameter is less critical
```

Repeat for each parameter to identify which ones matter most.

---

## Tips & Best Practices

### 1. Start Wide, Then Narrow

```
Iteration 1: ±10% (exploration)
Iteration 2: ±5%  (refinement)
Iteration 3: ±2%  (tuning)
Iteration 4: ±1%  (final polish)
```

### 2. Use Mixed Ranges for Efficiency

Don't use the same percentage for all parameters. Focus wide searches on parameters you're uncertain about.

### 3. Monitor Combination Count

Before running, estimate combinations:
- < 1M combinations: Very fast (<1 sec)
- 1M-10M: Fast (1-5 sec)
- 10M-100M: Moderate (5-30 sec)
- > 100M: Slow (30+ sec, may crash on limited GPUs)

### 4. Validate Across Multiple Symbols

After finding optimal parameters for QQQ, test on SPY, AAPL, MSFT, etc. to ensure they're not overfit.

### 5. Document Your Settings

Keep a log of which percentages you used for each iteration:

```
Iteration 1: All at 0.10 → Calmar: 1.45
Iteration 2: All at 0.05 → Calmar: 1.61
Iteration 3: All at 0.02 → Calmar: 1.67
Iteration 4: All at 0.01 → Calmar: 1.68 (minimal improvement, stop here)
```

---

## Quick Reference: All 10 Parameters

| Parameter | Config Defines | Controls |
|-----------|----------------|----------|
| Fast EMA (Low Vol) | `FAST_LOW_*`, `SEARCH_PERCENT_FAST_LOW_*` | Fast EMA period in low volatility |
| Slow EMA (Low Vol) | `SLOW_LOW_*`, `SEARCH_PERCENT_SLOW_LOW_*` | Slow EMA period in low volatility |
| Fast EMA (Med Vol) | `FAST_MED_*`, `SEARCH_PERCENT_FAST_MED_*` | Fast EMA period in medium volatility |
| Slow EMA (Med Vol) | `SLOW_MED_*`, `SEARCH_PERCENT_SLOW_MED_*` | Slow EMA period in medium volatility |
| Fast EMA (High Vol) | `FAST_HIGH_*`, `SEARCH_PERCENT_FAST_HIGH_*` | Fast EMA period in high volatility |
| Slow EMA (High Vol) | `SLOW_HIGH_*`, `SEARCH_PERCENT_SLOW_HIGH_*` | Slow EMA period in high volatility |
| ATR Length | `ATR_LENGTH_*`, `SEARCH_PERCENT_ATR_*` | Lookback period for ATR calculation |
| Volatility Length | `VOL_LENGTH_*`, `SEARCH_PERCENT_VOL_*` | Lookback for volatility measurement |
| Low Vol Percentile | `LOW_VOL_PCT_*`, `SEARCH_PERCENT_LOW_PCT_*` | Threshold for low volatility regime |
| High Vol Percentile | `HIGH_VOL_PCT_*`, `SEARCH_PERCENT_HIGH_PCT_*` | Threshold for high volatility regime |

Replace `*` with `1H`, `4H`, or `1D` depending on the timeframe you're configuring.

---

## Example: Complete Configuration

Here's a complete example for `config_1h.h`:

```c
/**
 * Adaptive EMA Strategy v1 - 1H Configuration
 */

#ifndef ADAPTIVE_EMA_V1_CONFIG_1H_H
#define ADAPTIVE_EMA_V1_CONFIG_1H_H

// ============================================================
// 1H INTERVAL - DEFAULT PARAMETERS
// ============================================================

// Low Volatility Regime
#define FAST_LOW_1H 6
#define SLOW_LOW_1H 78

// Medium Volatility Regime
#define FAST_MED_1H 18
#define SLOW_MED_1H 85

// High Volatility Regime
#define FAST_HIGH_1H 43
#define SLOW_HIGH_1H 113

// Volatility Calculation
#define ATR_LENGTH_1H 11
#define VOL_LENGTH_1H 68
#define LOW_VOL_PCT_1H 18
#define HIGH_VOL_PCT_1H 62

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_1H

// Individual search percentages for each parameter
#define SEARCH_PERCENT_FAST_LOW_1H 0.02     // ±2% from FAST_LOW_1H
#define SEARCH_PERCENT_SLOW_LOW_1H 0.02     // ±2% from SLOW_LOW_1H
#define SEARCH_PERCENT_FAST_MED_1H 0.02     // ±2% from FAST_MED_1H
#define SEARCH_PERCENT_SLOW_MED_1H 0.02     // ±2% from SLOW_MED_1H
#define SEARCH_PERCENT_FAST_HIGH_1H 0.02    // ±2% from FAST_HIGH_1H
#define SEARCH_PERCENT_SLOW_HIGH_1H 0.02    // ±2% from SLOW_HIGH_1H
#define SEARCH_PERCENT_ATR_1H 0.05          // ±5% from ATR_LENGTH_1H (less certain)
#define SEARCH_PERCENT_VOL_1H 0.05          // ±5% from VOL_LENGTH_1H (less certain)
#define SEARCH_PERCENT_LOW_PCT_1H 0.08      // ±8% from LOW_VOL_PCT_1H (uncertain)
#define SEARCH_PERCENT_HIGH_PCT_1H 0.08     // ±8% from HIGH_VOL_PCT_1H (uncertain)

// Strategy Settings
#define INITIAL_CAPITAL_1H 10000.0f
#define MIN_TRADES_1H 1
#define MAX_DRAWDOWN_FILTER_1H 50.0f
#define WARMUP_PERIOD_1H 50

#endif // ADAPTIVE_EMA_V1_CONFIG_1H_H
```

---

## Testing Your Changes

After editing a config file:

```bash
# Clean previous build
make clean

# Compile
make STRATEGY=adaptive_ema_v1

# Run optimization
./run.sh QQQ 1h
```

The optimizer will automatically use your new individual percentage settings.

---

## Troubleshooting

### Problem: Optimization is too slow

**Solution**: Reduce the larger percentages. Start by halving the widest ranges.

### Problem: No improvement across iterations

**Solution**: Your parameters may already be optimal. Try:
1. Testing on a different symbol
2. Testing on a different timeframe
3. Increasing percentages to explore further

### Problem: Results are inconsistent across symbols

**Solution**: Your ranges may be too wide, causing overfitting. Use narrower percentages (±1-2%).

### Problem: Integer truncation (e.g., min=max)

**Solution**: This happens when `parameter × percentage` is too small. Either:
- Increase the percentage
- Accept that small parameters have limited search space

---

## Summary

**Before**: One global percentage applied to all parameters
```c
#define SEARCH_PERCENT_1H 0.05  // All parameters use ±5%
```

**Now**: Individual control per parameter
```c
#define SEARCH_PERCENT_FAST_LOW_1H 0.02     // ±2%
#define SEARCH_PERCENT_SLOW_LOW_1H 0.02     // ±2%
#define SEARCH_PERCENT_LOW_PCT_1H 0.15      // ±15%
// ... and 7 more
```

**Benefit**: Fine-grained control → faster optimization + better exploration where it matters.
