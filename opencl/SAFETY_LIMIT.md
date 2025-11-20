# Parameter Space Safety Limit

## Overview

The optimization system now includes a **15 million combination safety limit** to prevent the computer from freezing or becoming unresponsive when parameter search ranges are too wide.

## How It Works

Before running the optimization, the system:

1. **Calculates parameter ranges** - Shows the min/max values and count for each parameter
2. **Estimates maximum combinations** - Calculates the upper bound (ignoring constraints like fast < slow)
3. **Counts valid combinations** - Counts actual valid combinations respecting all constraints
4. **Checks against limit** - If combinations exceed 15 million, the optimization is aborted

## Example Output

```
⚡ Calculating parameter space size...
   Parameter ranges:
     Fast Low: 6-8 (3 values)
     Slow Low: 86-98 (13 values)
     Fast Med: 16-20 (5 values)
     ... (and 7 more parameters)

   Maximum possible combinations (ignoring constraints): 45000000
   
❌ ERROR: Parameter space is too large!
   Maximum combinations: 45000000
   Safety limit: 15000000 (15 million)
```

## What Triggers the Error

The limit is exceeded when:
- Search percentages are too high (e.g., 0.10 or 10%)
- Too many parameters are being optimized simultaneously
- Default parameter values are very large
- Parameter ranges overlap significantly

## How to Fix

If you see this error, you have several options:

### 1. Reduce Search Percentages

Edit your config file: `strategies/adaptive_ema_v1/config_1h.h`

```c
// Before (too wide)
#define SEARCH_PERCENT_FAST_LOW_1H 0.10    // ±10%

// After (narrower)
#define SEARCH_PERCENT_FAST_LOW_1H 0.03    // ±3%
```

### 2. Focus on Fewer Parameters

Set some parameters to 0% search range:

```c
// Don't optimize these parameters
#define SEARCH_PERCENT_ATR_1H 0.00
#define SEARCH_PERCENT_VOL_1H 0.00
```

### 3. Use Smaller Default Values

```c
// Before
#define FAST_LOW_1H 100    // With ±6% = 94-106 range

// After
#define FAST_LOW_1H 50     // With ±6% = 47-53 range
```

### 4. Optimize in Stages

Instead of optimizing all 10 parameters at once:

**Stage 1:** Optimize EMA periods (6 parameters)
```c
#define SEARCH_PERCENT_FAST_LOW_1H 0.05
#define SEARCH_PERCENT_SLOW_LOW_1H 0.05
// ... other EMA params at 0.05
#define SEARCH_PERCENT_ATR_1H 0.00      // Fixed
#define SEARCH_PERCENT_VOL_1H 0.00      // Fixed
#define SEARCH_PERCENT_LOW_PCT_1H 0.00  // Fixed
#define SEARCH_PERCENT_HIGH_PCT_1H 0.00 // Fixed
```

**Stage 2:** Then optimize volatility parameters using best EMA values

## Math Behind the Limit

With 10 parameters, each with their own range:
- If each parameter has ~10 values
- Total combinations = 10^10 = 10 billion (way too many!)

The constraints (fast < slow, low_pct < high_pct) reduce this significantly, but even with constraints, wide ranges cause exponential growth.

## Safe Configuration Example

Here's a configuration that typically stays under 15M combinations:

```c
// 1H Interval - Safe Configuration
#define FAST_LOW_1H 12
#define SLOW_LOW_1H 80
#define FAST_MED_1H 25
#define SLOW_MED_1H 108
#define FAST_HIGH_1H 38
#define SLOW_HIGH_1H 120
#define ATR_LENGTH_1H 14
#define VOL_LENGTH_1H 70
#define LOW_VOL_PCT_1H 25
#define HIGH_VOL_PCT_1H 75

// Search ranges: ±3% (narrow but effective)
#define SEARCH_PERCENT_FAST_LOW_1H 0.03
#define SEARCH_PERCENT_SLOW_LOW_1H 0.03
#define SEARCH_PERCENT_FAST_MED_1H 0.03
#define SEARCH_PERCENT_SLOW_MED_1H 0.03
#define SEARCH_PERCENT_FAST_HIGH_1H 0.03
#define SEARCH_PERCENT_SLOW_HIGH_1H 0.03
#define SEARCH_PERCENT_ATR_1H 0.03
#define SEARCH_PERCENT_VOL_1H 0.03
#define SEARCH_PERCENT_LOW_PCT_1H 0.03
#define SEARCH_PERCENT_HIGH_PCT_1H 0.03
```

This typically results in ~100K to 5M combinations, which runs smoothly.

## Files Modified

- `opencl/optimize.c` - Main optimizer (universal for all strategies)
- `opencl/strategies/adaptive_ema_v1/optimize.c` - Strategy-specific optimizer

Both files now include identical safety checks.

## Technical Details

The limit is defined as:
```c
#define MAX_COMBINATIONS 15000000
```

This can be adjusted if needed, but 15 million is a reasonable balance between:
- Thoroughness of search
- System stability
- Reasonable execution time (typically 5-30 seconds on GPU)

## Performance Guidelines

| Combinations | Expected Time | System Load |
|--------------|---------------|-------------|
| < 1M         | < 5 seconds   | Light       |
| 1M - 5M      | 5-20 seconds  | Moderate    |
| 5M - 15M     | 20-60 seconds | Heavy       |
| > 15M        | **BLOCKED**   | Dangerous   |
