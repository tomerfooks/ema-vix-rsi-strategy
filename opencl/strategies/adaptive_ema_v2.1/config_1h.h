/**
 * Adaptive EMA Strategy v2.1 - 1H Configuration
 * 
 * Configuration for 1-hour timeframe optimization.
 * Uses percentage-based search ranges around default values.
 * Added ADX confirmation for trend strength filtering.
 */

#ifndef ADAPTIVE_EMA_V2_1_CONFIG_1H_H
#define ADAPTIVE_EMA_V2_1_CONFIG_1H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1H

// Default parameter values for 1H interval
//FAST_BASE_1H = 8
#define FAST_BASE_1H 9
//SLOW_BASE_1H = 13
#define SLOW_BASE_1H 10
//FAST_MULT_1H = 1.6
#define FAST_MULT_1H 1.4
//SLOW_MULT_1H = 1
#define SLOW_MULT_1H 1
//ATR_LENGTH_1H = 12
#define ATR_LENGTH_1H 12
//VOL_THRESHOLD_1H = 63
#define VOL_THRESHOLD_1H 65
//ADX_LENGTH_1H = 14
#define ADX_LENGTH_1H 7
//ADX_THRESHOLD_1H = 2
#define ADX_THRESHOLD_1H 11

// Search range percentages
#define SEARCH_PERCENT_FAST_BASE_1H 0
#define SEARCH_PERCENT_SLOW_BASE_1H 0
#define SEARCH_PERCENT_FAST_MULT_1H 0
#define SEARCH_PERCENT_SLOW_MULT_1H 0
#define SEARCH_PERCENT_ATR_1H 0
#define SEARCH_PERCENT_VOL_THRESHOLD_1H 0
#define SEARCH_PERCENT_ADX_LENGTH_1H 0
#define SEARCH_PERCENT_ADX_THRESHOLD_1H 0

#endif // ADAPTIVE_EMA_V2_1_CONFIG_1H_
