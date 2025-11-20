/**
 * Adaptive EMA Strategy v2 - 1H Configuration
 * 
 * Configuration for 1-hour timeframe optimization.
 * Uses percentage-based search ranges around default values.
 */

#ifndef ADAPTIVE_EMA_V2_CONFIG_1H_H
#define ADAPTIVE_EMA_V2_CONFIG_1H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1H

// Default parameter values for 1H interval
#define FAST_BASE_1H 5
#define SLOW_BASE_1H 9
#define FAST_MULT_1H 1.9
#define SLOW_MULT_1H 1
#define ATR_LENGTH_1H 14
#define VOL_THRESHOLD_1H 69

// Search range percentages
#define SEARCH_PERCENT_FAST_BASE_1H 0.3
#define SEARCH_PERCENT_SLOW_BASE_1H 0.2
#define SEARCH_PERCENT_FAST_MULT_1H 0.3  // 1.2 to 1.8
#define SEARCH_PERCENT_SLOW_MULT_1H 0.3
#define SEARCH_PERCENT_ATR_1H 0.25
#define SEARCH_PERCENT_VOL_THRESHOLD_1H 0.15  // 63 to 77

#endif // ADAPTIVE_EMA_V2_CONFIG_1H_H
