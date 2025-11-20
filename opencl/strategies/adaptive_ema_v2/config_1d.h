/**
 * Adaptive KAMA-ADX Strategy v2 - 1D Configuration
 * 
 * Optimized parameters for daily timeframe
 */

#ifndef ADAPTIVE_EMA_V2_CONFIG_1D_H
#define ADAPTIVE_EMA_V2_CONFIG_1D_H

// ============================================================
// 1D INTERVAL - DEFAULT PARAMETERS
// ============================================================

// KAMA Parameters (Kaufman Adaptive Moving Average)
#define KAMA_LENGTH_1D 16
#define KAMA_FAST_1D 2
#define KAMA_SLOW_1D 30

// ADX Configuration (trend strength)
#define ADX_LENGTH_1D 14
#define ADX_SMOOTHING_1D 14
#define ADX_THRESHOLD_1D 25.0f      // Entry gate: ADX must be > 25
#define ADX_PCT_LENGTH_1D 62        // Lookback for ADX percentile rank

// ATR Trailing Stop
#define ATR_LENGTH_1D 14
#define TRAIL_STOP_ATR_MULT_1D 2.0f  // 1.5-2.0 range, 2.0 for daily

// Dynamic EMA Scaling
#define BASE_EMA_LENGTH_1D 40
#define EMA_ATR_MULTIPLIER_1D 2.5f
#define MIN_EMA_LENGTH_1D 15
#define MAX_EMA_LENGTH_1D 80

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_1D
#define SEARCH_PERCENT_1D 0.03  // ±3% from defaults

// Strategy Settings
#define INITIAL_CAPITAL_1D 10000.0f
#define MIN_TRADES_1D 2
#define MAX_DRAWDOWN_FILTER_1D 50.0f
#define WARMUP_PERIOD_1D 50

// Parameter count for GPU kernel
#define NUM_PARAMS_1D 9

#endif // ADAPTIVE_EMA_V2_CONFIG_1D_H
