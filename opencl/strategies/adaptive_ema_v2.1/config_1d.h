/**
 * Adaptive EMA Strategy v2.1 - 1D Configuration
 * 
 * Configuration for daily timeframe optimization.
 * Added ADX confirmation for trend strength filtering.
 */

#ifndef ADAPTIVE_EMA_V2_1_CONFIG_1D_H
#define ADAPTIVE_EMA_V2_1_CONFIG_1D_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1D

// Default parameter values for 1D interval
#define FAST_BASE_1D 8
#define SLOW_BASE_1D 22
#define FAST_MULT_1D 1.5
#define SLOW_MULT_1D 1.2
#define ATR_LENGTH_1D 10
#define VOL_THRESHOLD_1D 65
#define ADX_LENGTH_1D 12
#define ADX_THRESHOLD_1D 17

// Search range percentages
#define SEARCH_PERCENT_FAST_BASE_1D 0.20
#define SEARCH_PERCENT_SLOW_BASE_1D 0.1
#define SEARCH_PERCENT_FAST_MULT_1D 0.15
#define SEARCH_PERCENT_SLOW_MULT_1D 0.2
#define SEARCH_PERCENT_ATR_1D 0.15
#define SEARCH_PERCENT_VOL_THRESHOLD_1D 0.03
#define SEARCH_PERCENT_ADX_LENGTH_1D 0.20
#define SEARCH_PERCENT_ADX_THRESHOLD_1D 0.12

#endif // ADAPTIVE_EMA_V2_1_CONFIG_1D_
