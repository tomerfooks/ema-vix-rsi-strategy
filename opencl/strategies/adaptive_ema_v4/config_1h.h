/**
 * Adaptive EMA Strategy v4 - 1H Configuration
 * 
 * Optimized for 1-hour timeframe with simpler parameter set.
 * Base EMAs adapt via efficiency ratio + ADX/RSI filters.
 */

#ifndef ADAPTIVE_EMA_V4_CONFIG_1H_H
#define ADAPTIVE_EMA_V4_CONFIG_1H_H

#define USE_PERCENT_RANGE_1H

// Default parameter values for 1H interval
#define EMA_FAST_BASE_1H 5
#define EMA_SLOW_BASE_1H 17
#define ADX_LENGTH_1H 10
#define ADX_THRESHOLD_1H 10.0
#define RSI_LENGTH_1H 7
#define RSI_BUY_MAX_1H 69.0
#define RSI_SELL_MIN_1H 37.0
#define EFFICIENCY_LOOKBACK_1H 10

// Search range percentages - focused on catching more trades
#define SEARCH_PERCENT_EMA_FAST_BASE_1H 0     // 7-13
#define SEARCH_PERCENT_EMA_SLOW_BASE_1H 0    // 10-18  
#define SEARCH_PERCENT_ADX_LENGTH_1H 0        // 9-19
#define SEARCH_PERCENT_ADX_THRESHOLD_1H 0     // 9-21
#define SEARCH_PERCENT_RSI_LENGTH_1H 0        // 5-11
#define SEARCH_PERCENT_RSI_BUY_MAX_1H 0       // 62-82
#define SEARCH_PERCENT_RSI_SELL_MIN_1H 0      // 25-45
#define SEARCH_PERCENT_EFFICIENCY_LOOKBACK_1H 0  // 4-12

#endif // ADAPTIVE_EMA_V4_CONFIG_1H_H
