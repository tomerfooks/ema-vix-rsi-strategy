/**
 * Simple EMA Strategy v1 - Configuration
 * 
 * This file contains all parameter settings for the simple EMA crossover strategy.
 * Default: 21-period fast EMA, 9-period slow EMA
 */

#ifndef EMA_SIMPLE_V1_CONFIG_H
#define EMA_SIMPLE_V1_CONFIG_H

// Strategy name and version
#define STRATEGY_NAME "Simple EMA Crossover"
#define STRATEGY_VERSION "v1.0"

// ============================================================
// 1H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    // EMA Lengths
    int fast_length;
    int slow_length;
    
    // Search range (percentage)
    float search_percent;
} Strategy_1h_Config;

static const Strategy_1h_Config CONFIG_1H = {
    // Default: 9 fast, 21 slow (classic golden cross scaled down)
    .fast_length = 9,
    .slow_length = 21,
    
    // Search range: ±20%
    .search_percent = 0.20
};

// ============================================================
// 4H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int fast_length;
    int slow_length;
    float search_percent;
} Strategy_4h_Config;

static const Strategy_4h_Config CONFIG_4H = {
    .fast_length = 9,
    .slow_length = 21,
    .search_percent = 0.20
};

// ============================================================
// 1D INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int fast_length;
    int slow_length;
    float search_percent;
} Strategy_1d_Config;

static const Strategy_1d_Config CONFIG_1D = {
    .fast_length = 9,
    .slow_length = 21,
    .search_percent = 0.20
};

// ============================================================
// COMMON STRATEGY SETTINGS
// ============================================================
#define INITIAL_CAPITAL 10000.0f
#define MIN_TRADES 1
#define MAX_DRAWDOWN_FILTER 50.0f
#define WARMUP_PERIOD 30  // Skip first N candles for EMA stabilization

// Performance metric weights for scoring
#define SCORE_CALMAR_WEIGHT 10.0f

#endif // EMA_SIMPLE_V1_CONFIG_H
