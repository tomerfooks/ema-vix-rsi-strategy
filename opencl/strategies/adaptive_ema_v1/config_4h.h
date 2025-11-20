/**
 * Adaptive EMA Strategy v1 - 4H Configuration
 */

#ifndef ADAPTIVE_EMA_V1_CONFIG_4H_H
#define ADAPTIVE_EMA_V1_CONFIG_4H_H

// ============================================================
// 4H INTERVAL - DEFAULT PARAMETERS
// ============================================================

// Low Volatility Regime
// BASE FAST_LOW_4H = 12, SLOW_LOW_4H = 71
#define FAST_LOW_4H 12
#define SLOW_LOW_4H 71

// Medium Volatility Regime
// BASE FAST_MED_4H = 25, SLOW_MED_4H = 89
#define FAST_MED_4H 22
#define SLOW_MED_4H 89

// High Volatility Regime
// BASE FAST_HIGH_4H = 37, SLOW_HIGH_4H = 109
#define FAST_HIGH_4H 37
#define SLOW_HIGH_4H 109

// Volatility Calculation
// BASE ATR_LENGTH_4H = 14, VOL_LENGTH_4H = 66
#define ATR_LENGTH_4H 14
#define VOL_LENGTH_4H 66
// BASE LOW_VOL_PCT_4H = 25, HIGH_VOL_PCT_4H = 61
#define LOW_VOL_PCT_4H 25
#define HIGH_VOL_PCT_4H 61

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_4H

// Individual search percentages for each parameter
#define SEARCH_PERCENT_FAST_LOW_4H 0.05     // ±5% from FAST_LOW_4H
#define SEARCH_PERCENT_SLOW_LOW_4H 0.05     // ±5% from SLOW_LOW_4H
#define SEARCH_PERCENT_FAST_MED_4H 0.05     // ±5% from FAST_MED_4H
#define SEARCH_PERCENT_SLOW_MED_4H 0.05     // ±5% from SLOW_MED_4H
#define SEARCH_PERCENT_FAST_HIGH_4H 0.05    // ±5% from FAST_HIGH_4H
#define SEARCH_PERCENT_SLOW_HIGH_4H 0.05    // ±5% from SLOW_HIGH_4H
#define SEARCH_PERCENT_ATR_4H 0.05          // ±5% from ATR_LENGTH_4H
#define SEARCH_PERCENT_VOL_4H 0.05          // ±5% from VOL_LENGTH_4H
#define SEARCH_PERCENT_LOW_PCT_4H 0.05      // ±5% from LOW_VOL_PCT_4H
#define SEARCH_PERCENT_HIGH_PCT_4H 0.05     // ±5% from HIGH_VOL_PCT_4H

// Strategy Settings
#define INITIAL_CAPITAL_4H 10000.0f
#define MIN_TRADES_4H 2
#define MAX_DRAWDOWN_FILTER_4H 50.0f
#define WARMUP_PERIOD_4H 50

#endif // ADAPTIVE_EMA_V1_CONFIG_4H_H
