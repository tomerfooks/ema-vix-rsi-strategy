/**
 * Adaptive EMA with Volume Strategy v1 - 1H Configuration
 * 
 * Configuration for 1-hour timeframe optimization.
 */

#ifndef ADAPTIVE_EMA_VOL_V1_CONFIG_1H_H
#define ADAPTIVE_EMA_VOL_V1_CONFIG_1H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1H

// Default parameter values for 1H interval
#define FAST_BASE_1H 9
#define SLOW_BASE_1H 10
#define FAST_MULT_1H 1.4
#define SLOW_MULT_1H 1.0
#define ATR_LENGTH_1H 12
#define VOL_THRESHOLD_1H 65
#define ADX_LENGTH_1H 7
#define ADX_THRESHOLD_1H 11
#define RSI_LENGTH_1H 14
#define RSI_TRENDING_MIN_1H 40
#define RSI_TRENDING_MAX_1H 70

// Search range percentages
#define SEARCH_PERCENT_FAST_BASE_1H 0.15
#define SEARCH_PERCENT_SLOW_BASE_1H 0.15
#define SEARCH_PERCENT_FAST_MULT_1H 0.15
#define SEARCH_PERCENT_SLOW_MULT_1H 0.15
#define SEARCH_PERCENT_ATR_1H 0.15
#define SEARCH_PERCENT_VOL_THRESHOLD_1H 0.10
#define SEARCH_PERCENT_ADX_LENGTH_1H 0.15
#define SEARCH_PERCENT_ADX_THRESHOLD_1H 0.20
#define SEARCH_PERCENT_RSI_LENGTH_1H 0.15
#define SEARCH_PERCENT_RSI_TRENDING_MIN_1H 0.15
#define SEARCH_PERCENT_RSI_TRENDING_MAX_1H 0.10

#endif // ADAPTIVE_EMA_VOL_V1_CONFIG_1H_H
