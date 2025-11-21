/**
 * Adaptive EMA Strategy v2 - Configuration
 * 
 * This strategy uses a single EMA pair that adapts based on volatility.
 * In high volatility, the EMAs become slower (longer periods).
 * In low volatility, the EMAs remain at base periods.
 */

#ifndef ADAPTIVE_EMA_V2_CONFIG_H
#define ADAPTIVE_EMA_V2_CONFIG_H

// Strategy name and version
#define STRATEGY_NAME "Adaptive EMA v2"
#define STRATEGY_VERSION "v2.0"

// ============================================================
// 1H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    // Base EMA periods (used in normal/low volatility)
    int fast_base;
    int slow_base;
    
    // Multipliers for high volatility (e.g., 1.5 = 50% longer periods)
    float fast_multiplier;
    float slow_multiplier;
    
    // Volatility settings
    int atr_length;
    int volatility_threshold;  // Percentile (e.g., 70 = top 30% is high vol)
    
    // Search range (percentage)
    float search_percent;
} Strategy_1h_Config;

static const Strategy_1h_Config CONFIG_1H = {
    // Base periods
    .fast_base = 12,
    .slow_base = 26,
    
    // Volatility multipliers (1.5x in high vol)
    .fast_multiplier = 1.5,
    .slow_multiplier = 1.5,
    
    // Volatility detection
    .atr_length = 14,
    .volatility_threshold = 70,  // Top 30% = high volatility
    
    // Search range: ±15%
    .search_percent = 0.15
};

// ============================================================
// 4H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int fast_base;
    int slow_base;
    float fast_multiplier;
    float slow_multiplier;
    int atr_length;
    int volatility_threshold;
    float search_percent;
} Strategy_4h_Config;

static const Strategy_4h_Config CONFIG_4H = {
    .fast_base = 12,
    .slow_base = 26,
    .fast_multiplier = 1.5,
    .slow_multiplier = 1.5,
    .atr_length = 14,
    .volatility_threshold = 70,
    .search_percent = 0.15
};

// ============================================================
// 1D INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int fast_base;
    int slow_base;
    float fast_multiplier;
    float slow_multiplier;
    int atr_length;
    int volatility_threshold;
    float search_percent;
} Strategy_1d_Config;

static const Strategy_1d_Config CONFIG_1D = {
    .fast_base = 12,
    .slow_base = 26,
    .fast_multiplier = 1.5,
    .slow_multiplier = 1.5,
    .atr_length = 14,
    .volatility_threshold = 70,
    .search_percent = 0.15
};

// ============================================================
// COMMON STRATEGY SETTINGS
// ============================================================
#define INITIAL_CAPITAL 10000.0f
#define MIN_TRADES 1
#define MAX_DRAWDOWN_FILTER 50.0f
#define WARMUP_PERIOD 50

// Performance metric weights for scoring
#define SCORE_CALMAR_WEIGHT 10.0f

#endif // ADAPTIVE_EMA_V2_CONFIG_H
