/**
 * Adaptive KAMA-ADX Strategy v2 - 4H Configuration
 * 
 * Optimized parameters for 4-hour timeframe
 */

#ifndef ADAPTIVE_EMA_V2_CONFIG_4H_H
#define ADAPTIVE_EMA_V2_CONFIG_4H_H

// ============================================================
// 4H INTERVAL - DEFAULT PARAMETERS
// ============================================================

// KAMA Parameters (Kaufman Adaptive Moving Average)
#define KAMA_LENGTH_4H 18
#define KAMA_FAST_4H 2
#define KAMA_SLOW_4H 30

// ADX Configuration (trend strength)
#define ADX_LENGTH_4H 14
#define ADX_SMOOTHING_4H 14
#define ADX_THRESHOLD_4H 25.0f      // Entry gate: ADX must be > 25
#define ADX_PCT_LENGTH_4H 66        // Lookback for ADX percentile rank

// ATR Trailing Stop
#define ATR_LENGTH_4H 14
#define TRAIL_STOP_ATR_MULT_4H 1.8f  // 1.5-2.0 range, 1.8 for 4h

// Dynamic EMA Scaling
#define BASE_EMA_LENGTH_4H 45
#define EMA_ATR_MULTIPLIER_4H 2.2f
#define MIN_EMA_LENGTH_4H 18
#define MAX_EMA_LENGTH_4H 90

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_4H
#define SEARCH_PERCENT_4H 0.04  // ±4% from defaults

// Strategy Settings
#define INITIAL_CAPITAL_4H 10000.0f
#define MIN_TRADES_4H 2
#define MAX_DRAWDOWN_FILTER_4H 50.0f
#define WARMUP_PERIOD_4H 50

// Parameter count for GPU kernel
#define NUM_PARAMS_4H 9

// ============================================================
// COMPATIBILITY LAYER - Map v2 params to v1 optimizer structure
// ============================================================

// Low Volatility Regime (maps to KAMA parameters)
#define FAST_LOW_4H KAMA_FAST_4H
#define SLOW_LOW_4H KAMA_LENGTH_4H

// Medium Volatility Regime (maps to ADX parameters)
#define FAST_MED_4H ADX_LENGTH_4H
#define SLOW_MED_4H ADX_PCT_LENGTH_4H

// High Volatility Regime (maps to EMA scaling parameters)
#define FAST_HIGH_4H MIN_EMA_LENGTH_4H
#define SLOW_HIGH_4H BASE_EMA_LENGTH_4H

// Volatility Calculation
#define VOL_LENGTH_4H ADX_SMOOTHING_4H
#define LOW_VOL_PCT_4H 20
#define HIGH_VOL_PCT_4H 70

#endif // ADAPTIVE_EMA_V2_CONFIG_4H_H
