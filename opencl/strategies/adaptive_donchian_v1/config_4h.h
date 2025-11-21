/**
 * Adaptive Donchian Breakout Strategy v1 - 4H Configuration
 * 
 * Configuration for 4-hour timeframe optimization.
 */

#ifndef ADAPTIVE_DONCHIAN_V1_CONFIG_4H_H
#define ADAPTIVE_DONCHIAN_V1_CONFIG_4H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_4H

// Default parameter values for 4H interval
#define DONCHIAN_LENGTH_4H 20
#define ATR_LENGTH_4H 14
#define ATR_MULTIPLIER_4H 0.5
#define ADX_LENGTH_4H 14
#define ADX_THRESHOLD_4H 20

// Search range percentages
#define SEARCH_PERCENT_DONCHIAN_LENGTH_4H 0.25
#define SEARCH_PERCENT_ATR_LENGTH_4H 0.20
#define SEARCH_PERCENT_ATR_MULTIPLIER_4H 0.50
#define SEARCH_PERCENT_ADX_LENGTH_4H 0.20
#define SEARCH_PERCENT_ADX_THRESHOLD_4H 0.30

#endif // ADAPTIVE_DONCHIAN_V1_CONFIG_4H_H
