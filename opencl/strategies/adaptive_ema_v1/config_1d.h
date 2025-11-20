/**
 * Adaptive EMA Strategy v1 - 1D Configuration
 */

#ifndef ADAPTIVE_EMA_V1_CONFIG_1D_H
#define ADAPTIVE_EMA_V1_CONFIG_1D_H

// ============================================================
// 1D INTERVAL - DEFAULT PARAMETERS
// ============================================================

// Low Volatility Regime
// BASE FAST_LOW_1D = 6, SLOW_LOW_1D = 14
#define FAST_LOW_1D 6
#define SLOW_LOW_1D 14

// Medium Volatility Regime
// BASE FAST_MED_1D = 6, SLOW_MED_1D = 19   
#define FAST_MED_1D 6
#define SLOW_MED_1D 19

// High Volatility Regime
// BASE FAST_HIGH_1D = 8, SLOW_HIGH_1D = 27
#define FAST_HIGH_1D 8
#define SLOW_HIGH_1D 27

// Volatility Calculation
// BASE ATR_LENGTH_1D = 13, VOL_LENGTH_1D = 70
#define ATR_LENGTH_1D 13
#define VOL_LENGTH_1D 70
// BASE LOW_VOL_PCT_1D = 25, HIGH_VOL_PCT_1D = 59
#define LOW_VOL_PCT_1D 25
#define HIGH_VOL_PCT_1D 59

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_1D

// Individual search percentages for each parameter
#define SEARCH_PERCENT_FAST_LOW_1D 0.1     // ±15% from FAST_LOW_1D
#define SEARCH_PERCENT_SLOW_LOW_1D 0.1     // ±15% from SLOW_LOW_1D
#define SEARCH_PERCENT_FAST_MED_1D 0.1     // ±15% from FAST_MED_1D
#define SEARCH_PERCENT_SLOW_MED_1D 0.1     // ±15% from SLOW_MED_1D
#define SEARCH_PERCENT_FAST_HIGH_1D 0.1    // ±15% from FAST_HIGH_1D
#define SEARCH_PERCENT_SLOW_HIGH_1D 0.1    // ±15% from SLOW_HIGH_1D
#define SEARCH_PERCENT_ATR_1D 0.1     // ±15% from ATR_LENGTH_1D
#define SEARCH_PERCENT_VOL_1D 0.1          // ±15% from VOL_LENGTH_1D
#define SEARCH_PERCENT_LOW_PCT_1D 0.1      // ±15% from LOW_VOL_PCT_1D
#define SEARCH_PERCENT_HIGH_PCT_1D 0.1     // ±15% from HIGH_VOL_PCT_1D

// Strategy Settings
#define INITIAL_CAPITAL_1D 10000.0f
#define MIN_TRADES_1D 1  // Reduced from 2 for short datasets
#define MAX_DRAWDOWN_FILTER_1D 50.0f
#define WARMUP_PERIOD_1D 50

#endif // ADAPTIVE_EMA_V1_CONFIG_1D_H
