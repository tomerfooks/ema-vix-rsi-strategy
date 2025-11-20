/**
 * Adaptive EMA Strategy v2 - Configuration
 * 
 * Key improvements over v1:
 * 1. ADX percentile rank instead of ATR percentile (less noisy for trend detection)
 * 2. KAMA (Kaufman Adaptive Moving Average) instead of 3 fixed EMA pairs
 * 3. ADX > 25 gate for entry filtering
 * 4. 1.5-2x ATR trailing stop for exits
 * 5. Dynamic EMA length scaling by ATR (smoother than discrete regimes)
 */

#ifndef ADAPTIVE_EMA_V2_CONFIG_H
#define ADAPTIVE_EMA_V2_CONFIG_H

// Strategy name and version
#define STRATEGY_NAME "Adaptive KAMA-ADX Strategy"
#define STRATEGY_VERSION "v2.0"

// ============================================================
// 1H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    // KAMA Parameters (replaces 3 fixed EMA pairs)
    int kama_length;           // Base period for KAMA calculation
    int kama_fast_period;      // Fast smoothing constant period
    int kama_slow_period;      // Slow smoothing constant period
    
    // Dynamic EMA Scaling (replaces discrete regimes)
    int base_ema_length;       // Base EMA length (scales with ATR)
    float ema_atr_multiplier;  // Multiplier for ATR-based scaling
    int min_ema_length;        // Minimum EMA length
    int max_ema_length;        // Maximum EMA length
    
    // ADX Configuration (replaces ATR percentile)
    int adx_length;            // Period for ADX calculation
    int adx_smoothing;         // ADX smoothing period
    float adx_threshold;       // Minimum ADX for entry (typically 25)
    int adx_percentile_length; // Lookback for ADX percentile rank
    
    // ATR Trailing Stop
    int atr_length;            // Period for ATR calculation
    float trail_stop_atr_mult; // ATR multiplier for trailing stop (1.5-2.0)
    
    // Search range (percentage)
    float search_percent;
} Strategy_1h_Config_v2;

static const Strategy_1h_Config_v2 CONFIG_1H_V2 = {
    // KAMA settings (adaptive moving average)
    .kama_length = 20,
    .kama_fast_period = 2,
    .kama_slow_period = 30,
    
    // Dynamic EMA scaling
    .base_ema_length = 50,
    .ema_atr_multiplier = 2.0,
    .min_ema_length = 20,
    .max_ema_length = 100,
    
    // ADX configuration
    .adx_length = 14,
    .adx_smoothing = 14,
    .adx_threshold = 25.0,
    .adx_percentile_length = 70,
    
    // ATR trailing stop
    .atr_length = 14,
    .trail_stop_atr_mult = 1.75,  // 1.5-2.0 range
    
    // Search range: ±5%
    .search_percent = 0.05
};

// ============================================================
// 4H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int kama_length;
    int kama_fast_period;
    int kama_slow_period;
    int base_ema_length;
    float ema_atr_multiplier;
    int min_ema_length;
    int max_ema_length;
    int adx_length;
    int adx_smoothing;
    float adx_threshold;
    int adx_percentile_length;
    int atr_length;
    float trail_stop_atr_mult;
    float search_percent;
} Strategy_4h_Config_v2;

static const Strategy_4h_Config_v2 CONFIG_4H_V2 = {
    .kama_length = 18,
    .kama_fast_period = 2,
    .kama_slow_period = 30,
    .base_ema_length = 45,
    .ema_atr_multiplier = 2.2,
    .min_ema_length = 18,
    .max_ema_length = 90,
    .adx_length = 14,
    .adx_smoothing = 14,
    .adx_threshold = 25.0,
    .adx_percentile_length = 66,
    .atr_length = 14,
    .trail_stop_atr_mult = 1.8,
    .search_percent = 0.04
};

// ============================================================
// 1D INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int kama_length;
    int kama_fast_period;
    int kama_slow_period;
    int base_ema_length;
    float ema_atr_multiplier;
    int min_ema_length;
    int max_ema_length;
    int adx_length;
    int adx_smoothing;
    float adx_threshold;
    int adx_percentile_length;
    int atr_length;
    float trail_stop_atr_mult;
    float search_percent;
} Strategy_1d_Config_v2;

static const Strategy_1d_Config_v2 CONFIG_1D_V2 = {
    .kama_length = 16,
    .kama_fast_period = 2,
    .kama_slow_period = 30,
    .base_ema_length = 40,
    .ema_atr_multiplier = 2.5,
    .min_ema_length = 15,
    .max_ema_length = 80,
    .adx_length = 14,
    .adx_smoothing = 14,
    .adx_threshold = 25.0,
    .adx_percentile_length = 62,
    .atr_length = 14,
    .trail_stop_atr_mult = 2.0,
    .search_percent = 0.03
};

// ============================================================
// COMMON STRATEGY SETTINGS
// ============================================================
#define INITIAL_CAPITAL 10000.0f
#define MIN_TRADES 2
#define MAX_DRAWDOWN_FILTER 50.0f
#define WARMUP_PERIOD 50  // Skip first N candles for indicator stabilization

// Performance metric weights for scoring
#define SCORE_CALMAR_WEIGHT 10.0f

// Parameter count for optimization
#define NUM_PARAMS 9  // Reduced from 10 (v1) due to simplified structure

#endif // ADAPTIVE_EMA_V2_CONFIG_H
