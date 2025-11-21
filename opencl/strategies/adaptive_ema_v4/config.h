/**
 * Adaptive EMA Strategy v4 - Configuration
 * 
 * Simplified adaptive strategy based on proven principles:
 * - KAMA-style efficiency ratio for adaptive smoothing
 * - ADX for trend strength filtering
 * - RSI for overbought/oversold protection
 * 
 * Philosophy: Base EMAs (9/21) that speed up in trending markets,
 * slow down in choppy markets, with strong confirmation filters.
 */

#ifndef ADAPTIVE_EMA_V4_CONFIG_H
#define ADAPTIVE_EMA_V4_CONFIG_H

#define STRATEGY_NAME "Adaptive EMA v4"
#define STRATEGY_VERSION "v4.0"

// ============================================================
// 1H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int ema_fast_base;      // Base fast EMA period (e.g., 9)
    int ema_slow_base;      // Base slow EMA period (e.g., 21)
    int adx_length;         // Period for ADX calculation
    float adx_threshold;    // Minimum ADX to take trades
    int rsi_length;         // Period for RSI calculation
    float rsi_buy_max;      // Max RSI for buy entries
    float rsi_sell_min;     // Min RSI for sell exits
    int efficiency_lookback;// Lookback for efficiency ratio
    float search_percent;   // Search range percentage
} Strategy_1h_Config;

static const Strategy_1h_Config CONFIG_1H = {
    .ema_fast_base = 9,
    .ema_slow_base = 21,
    .adx_length = 14,
    .adx_threshold = 20.0f,
    .rsi_length = 14,
    .rsi_buy_max = 70.0f,
    .rsi_sell_min = 30.0f,
    .efficiency_lookback = 10,
    .search_percent = 0.20
};

// ============================================================
// 4H INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int ema_fast_base;
    int ema_slow_base;
    int adx_length;
    float adx_threshold;
    int rsi_length;
    float rsi_buy_max;
    float rsi_sell_min;
    int efficiency_lookback;
    float search_percent;
} Strategy_4h_Config;

static const Strategy_4h_Config CONFIG_4H = {
    .ema_fast_base = 9,
    .ema_slow_base = 21,
    .adx_length = 14,
    .adx_threshold = 20.0f,
    .rsi_length = 14,
    .rsi_buy_max = 70.0f,
    .rsi_sell_min = 30.0f,
    .efficiency_lookback = 10,
    .search_percent = 0.20
};

// ============================================================
// 1D INTERVAL CONFIGURATION
// ============================================================
typedef struct {
    int ema_fast_base;
    int ema_slow_base;
    int adx_length;
    float adx_threshold;
    int rsi_length;
    float rsi_buy_max;
    float rsi_sell_min;
    int efficiency_lookback;
    float search_percent;
} Strategy_1d_Config;

static const Strategy_1d_Config CONFIG_1D = {
    .ema_fast_base = 9,
    .ema_slow_base = 21,
    .adx_length = 14,
    .adx_threshold = 20.0f,
    .rsi_length = 14,
    .rsi_buy_max = 70.0f,
    .rsi_sell_min = 30.0f,
    .efficiency_lookback = 10,
    .search_percent = 0.20
};

// ============================================================
// COMMON STRATEGY SETTINGS
// ============================================================
#define INITIAL_CAPITAL 10000.0f
#define MIN_TRADES 1
#define MAX_DRAWDOWN_FILTER 50.0f
#define WARMUP_PERIOD 60

// Performance metric weights
#define SCORE_CALMAR_WEIGHT 10.0f

#endif // ADAPTIVE_EMA_V4_CONFIG_H
