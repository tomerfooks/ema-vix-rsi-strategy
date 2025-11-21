/**
 * Adaptive EMA Strategy v2.2 - 1H Configuration
 * 
 * Configuration for 1-hour timeframe optimization.
 * Uses percentage-based search ranges around default values.
 * Added RSI momentum filter and volume confirmation.
 */

#ifndef ADAPTIVE_EMA_V2_2_CONFIG_1H_H
#define ADAPTIVE_EMA_V2_2_CONFIG_1H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1H

// Default parameter values for 1H interval
//FAST_BASE_1H = 8
#define FAST_BASE_1H 8
//SLOW_BASE_1H = 13
#define SLOW_BASE_1H 13
//FAST_MULT_1H = 1.6
#define FAST_MULT_1H 1.7
//SLOW_MULT_1H = 1
#define SLOW_MULT_1H 1.09
//ATR_LENGTH_1H = 12
#define ATR_LENGTH_1H 12
//VOL_THRESHOLD_1H = 63
#define VOL_THRESHOLD_1H 63
//RSI_LENGTH_1H = 14
#define RSI_LENGTH_1H 14
//RSI_THRESHOLD_1H = 70
#define RSI_THRESHOLD_1H 67

// Search range percentages
#define SEARCH_PERCENT_FAST_BASE_1H 0
#define SEARCH_PERCENT_SLOW_BASE_1H 0
#define SEARCH_PERCENT_FAST_MULT_1H 0
#define SEARCH_PERCENT_SLOW_MULT_1H 0
#define SEARCH_PERCENT_ATR_1H 0
#define SEARCH_PERCENT_VOL_THRESHOLD_1H 0
#define SEARCH_PERCENT_RSI_LENGTH_1H 0
#define SEARCH_PERCENT_RSI_THRESHOLD_1H 0

#endif // ADAPTIVE_EMA_V2_2_CONFIG_1H_H
