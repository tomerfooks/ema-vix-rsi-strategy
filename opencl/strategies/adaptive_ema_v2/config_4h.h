/**
 * Adaptive EMA Strategy v2 - 4H Configuration
 * 
 * Configuration for 4-hour timeframe optimization.
 */

#ifndef ADAPTIVE_EMA_V2_CONFIG_4H_H
#define ADAPTIVE_EMA_V2_CONFIG_4H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_4H

// Default parameter values for 4H interval
#define FAST_BASE_4H 12
#define SLOW_BASE_4H 26
#define FAST_MULT_4H 1.5
#define SLOW_MULT_4H 1.5
#define ATR_LENGTH_4H 14
#define VOL_THRESHOLD_4H 70

// Search range percentages
#define SEARCH_PERCENT_FAST_BASE_4H 0.20
#define SEARCH_PERCENT_SLOW_BASE_4H 0.20
#define SEARCH_PERCENT_FAST_MULT_4H 0.20
#define SEARCH_PERCENT_SLOW_MULT_4H 0.20
#define SEARCH_PERCENT_ATR_4H 0.15
#define SEARCH_PERCENT_VOL_THRESHOLD_4H 0.10

#endif // ADAPTIVE_EMA_V2_CONFIG_4H_H
