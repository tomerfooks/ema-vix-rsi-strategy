/**
 * Simple EMA Strategy v1 - 1D Configuration
 * 
 * Configuration for daily timeframe optimization.
 * This uses percentage-based search ranges around the default values.
 */

#ifndef EMA_SIMPLE_V1_CONFIG_1D_H
#define EMA_SIMPLE_V1_CONFIG_1D_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1D

// Default parameter values for 1D interval
#define FAST_LENGTH_1D 9
#define SLOW_LENGTH_1D 21

// Search range percentages (0.20 = ±20%)
#define SEARCH_PERCENT_FAST_1D 0.20
#define SEARCH_PERCENT_SLOW_1D 0.20

#endif // EMA_SIMPLE_V1_CONFIG_1D_H
