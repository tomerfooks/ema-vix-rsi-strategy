# Strategy Configuration Files

This directory contains parameter ranges and defaults for the **Adaptive EMA Strategy** across different timeframes.

## Files

- **`adaptive_ema_1h.h`** - 1-hour timeframe configuration
- **`adaptive_ema_4h.h`** - 4-hour timeframe configuration  
- **`adaptive_ema_1d.h`** - Daily timeframe configuration

## How to Modify Ranges

These header files serve as **documentation and reference** for the parameter ranges. The actual values are loaded in `../optimize.c` in the `load_config()` function.

### To change parameter ranges:

1. Edit `/Users/hhh/Projects/ema-vix-rsi-strategy/opencl/optimize.c`
2. Find the `load_config()` function (around line 38-85)
3. Modify the min/max values for your target interval
4. Rebuild: `make clean && make`

### Example:

```c
void load_config(const char* interval, Config* config) {
    if (strcmp(interval, "1h") == 0) {
        config->fast_length_low_min = 13;  // ← Change these
        config->fast_length_low_max = 14;  // ← Change these
        // ... etc
    }
}
```

## Understanding the Parameters

### EMA Parameters
- **Fast/Slow Length Low** - EMA periods for low volatility regime
- **Fast/Slow Length Med** - EMA periods for medium volatility regime
- **Fast/Slow Length High** - EMA periods for high volatility regime

### Volatility Parameters
- **ATR Length** - Period for Average True Range calculation
- **Volatility Length** - Lookback period for volatility measurement
- **Low/High Vol Percentile** - Thresholds for volatility regime classification

## Combination Count

Total combinations = `(fast_low_range * slow_low_range * fast_med_range * 
                       slow_med_range * fast_high_range * slow_high_range * 
                       atr_range * vol_range * low_pct_range * high_pct_range)`

**Current configurations:**
- **1h**: ~1.5M combinations (0.1s on AMD Radeon Pro 555X)
- **4h**: ~1.3M combinations
- **1d**: ~1.1M combinations

## Tips

1. **Start narrow** - Use tight ranges (±2-5 values) for fast iteration
2. **Expand gradually** - Widen ranges once you find promising regions
3. **Monitor combinations** - Keep total combinations under 5M for fast GPU execution
4. **Use defaults** - The DEFAULT_* values in headers show optimal center points

## Performance Impact

**Rounding:** CSV data is rounded to 4 decimal places for better GPU cache performance. This improves speed by ~5-10% with negligible accuracy loss for stock prices.
