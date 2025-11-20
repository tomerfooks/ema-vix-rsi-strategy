/**
 * Simple EMA Strategy v1 - 1H Configuration
 * 
 * Configuration for 1-hour timeframe optimization.
 * This uses percentage-based search ranges around the default values.
 */

#ifndef EMA_SIMPLE_V1_CONFIG_1H_H
#define EMA_SIMPLE_V1_CONFIG_1H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1H

// Default parameter values for 1H interval
#define FAST_LENGTH_1H 8
#define SLOW_LENGTH_1H 13

// Search range percentages (0.20 = ±20%)
#define SEARCH_PERCENT_FAST_1H 1
#define SEARCH_PERCENT_SLOW_1H 1

#endif // EMA_SIMPLE_V1_CONFIG_1H_H
