/**
 * Adaptive KAMA-ADX Strategy v2 - 1H Configuration
 * 
 * Optimized parameters for 1-hour timeframe
 */

#ifndef ADAPTIVE_EMA_V2_CONFIG_1H_H
#define ADAPTIVE_EMA_V2_CONFIG_1H_H

// ============================================================
// 1H INTERVAL - DEFAULT PARAMETERS
// ============================================================

// KAMA Parameters (Kaufman Adaptive Moving Average)
#define KAMA_LENGTH_1H 20
#define KAMA_FAST_1H 2
#define KAMA_SLOW_1H 30

// ADX Configuration (trend strength)
#define ADX_LENGTH_1H 14
#define ADX_SMOOTHING_1H 14
#define ADX_THRESHOLD_1H 25.0f      // Entry gate: ADX must be > 25
#define ADX_PCT_LENGTH_1H 70        // Lookback for ADX percentile rank

// ATR Trailing Stop
#define ATR_LENGTH_1H 14
#define TRAIL_STOP_ATR_MULT_1H 1.75f  // 1.5-2.0 range, 1.75 is balanced

// Dynamic EMA Scaling
#define BASE_EMA_LENGTH_1H 50
#define EMA_ATR_MULTIPLIER_1H 2.0f
#define MIN_EMA_LENGTH_1H 20
#define MAX_EMA_LENGTH_1H 100

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_1H
#define SEARCH_PERCENT_1H 0.02  // ±2% from defaults

// Strategy Settings
#define INITIAL_CAPITAL_1H 10000.0f
#define MIN_TRADES_1H 2
#define MAX_DRAWDOWN_FILTER_1H 50.0f
#define WARMUP_PERIOD_1H 50

// Parameter count for GPU kernel
#define NUM_PARAMS_1H 9

// ============================================================
// COMPATIBILITY LAYER - Map v2 params to v1 optimizer structure
// ============================================================
// The optimizer expects v1-style triple-regime EMA parameters
// Map v2's KAMA/ADX parameters to equivalent v1 parameter names

// Low Volatility Regime (maps to KAMA parameters)
#define FAST_LOW_1H KAMA_FAST_1H
#define SLOW_LOW_1H KAMA_LENGTH_1H

// Medium Volatility Regime (maps to ADX parameters)
#define FAST_MED_1H ADX_LENGTH_1H
#define SLOW_MED_1H ADX_PCT_LENGTH_1H

// High Volatility Regime (maps to EMA scaling parameters)
#define FAST_HIGH_1H MIN_EMA_LENGTH_1H
#define SLOW_HIGH_1H BASE_EMA_LENGTH_1H

// Volatility Calculation (direct mapping)
#define VOL_LENGTH_1H ADX_SMOOTHING_1H
#define LOW_VOL_PCT_1H 20  // Default percentile values
#define HIGH_VOL_PCT_1H 70

#endif // ADAPTIVE_EMA_V2_CONFIG_1H_H
