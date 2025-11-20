/**
 * Adaptive EMA Strategy v1 - Configuration
 * 
 * This file contains all parameter settings for the adaptive EMA crossover strategy
 * that adjusts EMA periods based on volatility regimes.
 */

#ifndef ADAPTIVE_EMA_V1_CONFIG_H
#define ADAPTIVE_EMA_V1_CONFIG_H

// Strategy name and version
#define STRATEGY_NAME "Adaptive EMA Crossover"
#define STRATEGY_VERSION "v1.0"

// ============================================================
// 1H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    // Low Volatility Regime
    int fast_length_low;
    int slow_length_low;
    
    // Medium Volatility Regime
    int fast_length_med;
    int slow_length_med;
    
    // High Volatility Regime
    int fast_length_high;
    int slow_length_high;
    
    // Volatility Calculation
    int atr_length;
    int volatility_length;
    int low_vol_percentile;
    int high_vol_percentile;
    
    // Search range (percentage)
    float search_percent;
} Strategy_1h_Config;

static const Strategy_1h_Config CONFIG_1H = {
    // Low Vol: Fast trend-following
    .fast_length_low = 13,
    .slow_length_low = 79,
    
    // Medium Vol: Balanced
    .fast_length_med = 24,
    .slow_length_med = 97,
    
    // High Vol: Conservative
    .fast_length_high = 41,
    .slow_length_high = 119,
    
    // Volatility settings
    .atr_length = 15,
    .volatility_length = 70,
    .low_vol_percentile = 27,
    .high_vol_percentile = 64,
    
    // Search range: ±5%
    .search_percent = 0.05
};

// ============================================================
// 4H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int fast_length_low;
    int slow_length_low;
    int fast_length_med;
    int slow_length_med;
    int fast_length_high;
    int slow_length_high;
    int atr_length;
    int volatility_length;
    int low_vol_percentile;
    int high_vol_percentile;
    float search_percent;
} Strategy_4h_Config;

static const Strategy_4h_Config CONFIG_4H = {
    .fast_length_low = 12,
    .slow_length_low = 71,
    .fast_length_med = 22,
    .slow_length_med = 89,
    .fast_length_high = 37,
    .slow_length_high = 109,
    .atr_length = 14,
    .volatility_length = 66,
    .low_vol_percentile = 25,
    .high_vol_percentile = 61,
    .search_percent = 0.04
};

// ============================================================
// 1D INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int fast_length_low;
    int slow_length_low;
    int fast_length_med;
    int slow_length_med;
    int fast_length_high;
    int slow_length_high;
    int atr_length;
    int volatility_length;
    int low_vol_percentile;
    int high_vol_percentile;
    float search_percent;
} Strategy_1d_Config;

static const Strategy_1d_Config CONFIG_1D = {
    .fast_length_low = 10,
    .slow_length_low = 60,
    .fast_length_med = 20,
    .slow_length_med = 81,
    .fast_length_high = 33,
    .slow_length_high = 99,
    .atr_length = 13,
    .volatility_length = 62,
    .low_vol_percentile = 24,
    .high_vol_percentile = 59,
    .search_percent = 0.03
};

// ============================================================
// COMMON STRATEGY SETTINGS
// ============================================================
#define INITIAL_CAPITAL 10000.0f
#define MIN_TRADES 2
#define MAX_DRAWDOWN_FILTER 50.0f
#define WARMUP_PERIOD 50  // Skip first N candles for EMA stabilization

// Performance metric weights for scoring
#define SCORE_CALMAR_WEIGHT 10.0f

#endif // ADAPTIVE_EMA_V1_CONFIG_H
