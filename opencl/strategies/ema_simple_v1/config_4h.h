/**
 * Simple EMA Strategy v1 - 4H Configuration
 * 
 * Configuration for 4-hour timeframe optimization.
 * This uses percentage-based search ranges around the default values.
 */

#ifndef EMA_SIMPLE_V1_CONFIG_4H_H
#define EMA_SIMPLE_V1_CONFIG_4H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_4H

// Default parameter values for 4H interval
#define FAST_LENGTH_4H 9
#define SLOW_LENGTH_4H 21

// Search range percentages (0.20 = ±20%)
#define SEARCH_PERCENT_FAST_4H 0.20
#define SEARCH_PERCENT_SLOW_4H 0.20

#endif // EMA_SIMPLE_V1_CONFIG_4H_H
