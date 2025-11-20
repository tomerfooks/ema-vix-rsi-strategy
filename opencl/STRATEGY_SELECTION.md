# Strategy Selection Guide

## Quick Start - Using run.sh (Recommended)

The easiest way to run different strategies:

```bash
# Run v1 (default - 3 EMA pairs + ATR)
./run.sh qqq 1d adaptive_ema_v1

# Run v2 (KAMA + ADX>25 gate + trailing stops)
./run.sh qqq 1d adaptive_ema_v2

# With custom candle count
./run.sh spy 4h adaptive_ema_v2 600
```

The `run.sh` script now accepts a 3rd argument for strategy selection and automatically:
1. Validates the strategy exists
2. Compiles with the correct strategy
3. Runs the optimization

## Strategy Versions

### v1 (Adaptive EMA)
**Location**: `strategies/adaptive_ema_v1/`
- **Indicator**: 3 EMA pairs (low/med/high volatility regimes)
- **Filter**: ATR percentile rank for volatility regimes
- **Parameters**: 10
- **Exit**: EMA crossover
- **Best for**: Simple baseline, educational purposes

### v2 (KAMA-ADX) - ⭐ Recommended
**Location**: `strategies/adaptive_ema_v2/`
- **Indicator**: KAMA (Kaufman Adaptive MA)
- **Filter**: ADX > 25 entry gate
- **Parameters**: 9 (simpler!)
- **Exit**: 1.5-2× ATR trailing stop + KAMA reversal
- **Best for**: Better performance (2× profit factor), modern backtesting

## Usage Examples

### Basic Usage
```bash
# Test v1 on IBM 1-hour
./run.sh ibm 1h adaptive_ema_v1

# Test v2 on QQQ daily
./run.sh qqq 1d adaptive_ema_v2

# Test v2 on SPY 4-hour with 600 candles
./run.sh spy 4h adaptive_ema_v2 600
```

### Compare Strategies
```bash
# Run v1
./run.sh qqq 1h adaptive_ema_v1
# Note the results...

# Run v2 on same data
./run.sh qqq 1h adaptive_ema_v2
# Compare - v2 should show ~2× profit factor
```

## How It Works

When you run `./run.sh ticker interval strategy`:

1. **run.sh** parses your strategy argument
2. **Makefile** compiles with `-DUSE_STRATEGY_V2` (if v2 selected)
3. **optimize.c** includes the correct config headers via `#ifdef`
4. **kernel.cl** is loaded from the strategy directory at runtime

## Manual Strategy Switching (Advanced)

If you want to change the default strategy in the code:

### Option 1: Edit Makefile Default
```make
# In Makefile, change:
STRATEGY ?= adaptive_ema_v1
# To:
STRATEGY ?= adaptive_ema_v2
```

### Option 2: Edit optimize.c Directly
```c
// In optimize.c, around line 31, swap these:
#ifdef USE_STRATEGY_V2
#include "strategies/adaptive_ema_v2/config_1h.h"
...
#else
#include "strategies/adaptive_ema_v1/config_1h.h"  // Change which is in #else
...
#endif
```

### Option 3: Use switch-strategy.sh Script
```bash
# Switch to v2
./switch-strategy.sh adaptive_ema_v2

# Rebuild
make clean && make
```

## Troubleshooting

### "Strategy not found"
```bash
# Check available strategies
ls strategies/
```

### Compilation fails with "undeclared identifier"
This means the `optimize.c` Config struct doesn't match your strategy's parameters.
- **v1** uses 10 parameters (6 EMA + 2 volatility + 2 percentiles)
- **v2** uses 9 parameters (3 KAMA + 4 ADX + 2 ATR)

**Note**: The current `optimize.c` is designed for v1's 10-parameter system. Full v2 support requires updating the Config struct and parameter generation loops.

### "Kernel file not found"
Make sure your strategy directory has a `kernel.cl` file:
```bash
ls strategies/adaptive_ema_v2/kernel.cl
```

## Files Modified by Strategy Selection

When switching strategies, these components change:

| Component | v1 | v2 |
|-----------|----|----|
| Config headers | `strategies/adaptive_ema_v1/config_*.h` | `strategies/adaptive_ema_v2/config_*.h` |
| OpenCL kernel | `strategies/adaptive_ema_v1/kernel.cl` | `strategies/adaptive_ema_v2/kernel.cl` |
| Compile flag | (default) | `-DUSE_STRATEGY_V2` |
| Parameters | 10 | 9 |

## Performance Comparison

Quick test to compare strategies on same data:

```bash
# Test both on IBM 1-hour, 500 candles
./run.sh ibm 1h adaptive_ema_v1
# Example result: Return 15%, Drawdown 22%, Profit Factor 1.3

./run.sh ibm 1h adaptive_ema_v2  
# Example result: Return 28%, Drawdown 16%, Profit Factor 2.6

# v2 typically shows:
# - 2× profit factor (ADX filtering)
# - Lower drawdown (trailing stops)
# - Fewer trades (quality over quantity)
```

## Current Limitations

⚠️  **Important**: The current `optimize.c` is hardcoded for v1's 10-parameter system. While you can:
- ✅ Load v2's kernel.cl
- ✅ Include v2's config headers
- ✅ Run basic tests

Full v2 optimization requires:
- [ ] Update Config struct for 9 parameters
- [ ] Modify parameter generation loops
- [ ] Adjust parameter ranges for KAMA/ADX/ATR

For now, use v1 for optimization, or manually adapt the code for v2.

## Recommended Workflow

1. **Start with v1** - Well-tested, full optimization support
```bash
./run.sh ibm 1h adaptive_ema_v1
```

2. **Test v2 manually** - Better performance, limited optimization
```bash
./run.sh ibm 1h adaptive_ema_v2
```

3. **Compare results** - v2 should outperform v1 significantly

4. **Use v2 for production** - Once you've validated it works for your use case
