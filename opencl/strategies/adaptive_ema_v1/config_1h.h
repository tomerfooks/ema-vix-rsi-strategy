/**
 * Adaptive EMA Strategy v1 - 1H Configuration
 */

#ifndef ADAPTIVE_EMA_V1_CONFIG_1H_H
#define ADAPTIVE_EMA_V1_CONFIG_1H_H

// ============================================================
// 1H INTERVAL - DEFAULT PARAMETERS
// ============================================================

// Low Volatility Regime
#define FAST_LOW_1H 10
#define SLOW_LOW_1H 71

// Medium Volatility Regime
#define FAST_MED_1H 19
#define SLOW_MED_1H 86

// High Volatility Regime
#define FAST_HIGH_1H 41
#define SLOW_HIGH_1H 122

// Volatility Calculation
#define ATR_LENGTH_1H 13
#define VOL_LENGTH_1H 71
#define LOW_VOL_PCT_1H 16
#define HIGH_VOL_PCT_1H 67

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_1H
#define SEARCH_PERCENT_1H 0.01  // ±1% from defaults

// Strategy Settings
#define INITIAL_CAPITAL_1H 10000.0f
#define MIN_TRADES_1H 1
#define MAX_DRAWDOWN_FILTER_1H 50.0f
#define WARMUP_PERIOD_1H 50

#endif // ADAPTIVE_EMA_V1_CONFIG_1H_H
