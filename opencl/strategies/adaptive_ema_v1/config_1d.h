/**
 * Adaptive EMA Strategy v1 - 1D Configuration
 */

#ifndef ADAPTIVE_EMA_V1_CONFIG_1D_H
#define ADAPTIVE_EMA_V1_CONFIG_1D_H

// ============================================================
// 1D INTERVAL - DEFAULT PARAMETERS
// ============================================================

// Low Volatility Regime
#define FAST_LOW_1D 1
#define SLOW_LOW_1D 6

// Medium Volatility Regime
#define FAST_MED_1D 6
#define SLOW_MED_1D 15

// High Volatility Regime
#define FAST_HIGH_1D 6
#define SLOW_HIGH_1D 22

// Volatility Calculation
#define ATR_LENGTH_1D 5
#define VOL_LENGTH_1D 71
#define LOW_VOL_PCT_1D 7
#define HIGH_VOL_PCT_1D 55

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_1D
#define SEARCH_PERCENT_1D 0.15  // ±15% from defaults

// Strategy Settings
#define INITIAL_CAPITAL_1D 10000.0f
#define MIN_TRADES_1D 1  // Reduced from 2 for short datasets
#define MAX_DRAWDOWN_FILTER_1D 50.0f
#define WARMUP_PERIOD_1D 50

#endif // ADAPTIVE_EMA_V1_CONFIG_1D_H
