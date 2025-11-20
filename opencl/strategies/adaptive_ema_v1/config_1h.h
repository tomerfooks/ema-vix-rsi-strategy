/**
 * Adaptive EMA Strategy v1 - 1H Configuration
 */

#ifndef ADAPTIVE_EMA_V1_CONFIG_1H_H
#define ADAPTIVE_EMA_V1_CONFIG_1H_H

// ============================================================
// 1H INTERVAL - DEFAULT PARAMETERS
// ============================================================

// Low Volatility Regime
#define FAST_LOW_1H 5
#define SLOW_LOW_1H 70

// Medium Volatility Regime
#define FAST_MED_1H 14
#define SLOW_MED_1H 78

// High Volatility Regime
#define FAST_HIGH_1H 46
#define SLOW_HIGH_1H 111

// Volatility Calculation
#define ATR_LENGTH_1H 9
#define VOL_LENGTH_1H 70
#define LOW_VOL_PCT_1H 15
#define HIGH_VOL_PCT_1H 65

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_1H

// Individual search percentages for each parameter
#define SEARCH_PERCENT_FAST_LOW_1H 0.05     // ±5% from FAST_LOW_1H
#define SEARCH_PERCENT_SLOW_LOW_1H 0.05     // ±5% from SLOW_LOW_1H
#define SEARCH_PERCENT_FAST_MED_1H 0.05     // ±5% from FAST_MED_1H
#define SEARCH_PERCENT_SLOW_MED_1H 0.05     // ±5% from SLOW_MED_1H
#define SEARCH_PERCENT_FAST_HIGH_1H 0.05    // ±5% from FAST_HIGH_1H
#define SEARCH_PERCENT_SLOW_HIGH_1H 0.05    // ±5% from SLOW_HIGH_1H
#define SEARCH_PERCENT_ATR_1H 0.05          // ±5% from ATR_LENGTH_1H
#define SEARCH_PERCENT_VOL_1H 0.05          // ±5% from VOL_LENGTH_1H
#define SEARCH_PERCENT_LOW_PCT_1H 0.05      // ±5% from LOW_VOL_PCT_1H
#define SEARCH_PERCENT_HIGH_PCT_1H 0.05     // ±5% from HIGH_VOL_PCT_1H

// Strategy Settings
#define INITIAL_CAPITAL_1H 10000.0f
#define MIN_TRADES_1H 1
#define MAX_DRAWDOWN_FILTER_1H 50.0f
#define WARMUP_PERIOD_1H 50

#endif // ADAPTIVE_EMA_V1_CONFIG_1H_H
