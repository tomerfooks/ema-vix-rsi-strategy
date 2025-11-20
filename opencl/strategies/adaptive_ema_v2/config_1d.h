/**
 * Adaptive EMA Strategy v2 - 1D Configuration
 * 
 * Configuration for daily timeframe optimization.
 */

#ifndef ADAPTIVE_EMA_V2_CONFIG_1D_H
#define ADAPTIVE_EMA_V2_CONFIG_1D_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1D

// Default parameter values for 1D interval
#define FAST_BASE_1D 12
#define SLOW_BASE_1D 26
#define FAST_MULT_1D 1.5
#define SLOW_MULT_1D 1.5
#define ATR_LENGTH_1D 14
#define VOL_THRESHOLD_1D 70

// Search range percentages
#define SEARCH_PERCENT_FAST_BASE_1D 0.20
#define SEARCH_PERCENT_SLOW_BASE_1D 0.20
#define SEARCH_PERCENT_FAST_MULT_1D 0.20
#define SEARCH_PERCENT_SLOW_MULT_1D 0.20
#define SEARCH_PERCENT_ATR_1D 0.15
#define SEARCH_PERCENT_VOL_THRESHOLD_1D 0.10

#endif // ADAPTIVE_EMA_V2_CONFIG_1D_H
