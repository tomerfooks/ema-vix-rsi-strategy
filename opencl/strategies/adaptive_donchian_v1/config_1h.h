/**
 * Adaptive Donchian Breakout Strategy v1 - 1H Configuration
 * 
 * Configuration for 1-hour timeframe optimization.
 * Uses percentage-based search ranges around default values.
 */

#ifndef ADAPTIVE_DONCHIAN_V1_CONFIG_1H_H
#define ADAPTIVE_DONCHIAN_V1_CONFIG_1H_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1H

// Default parameter values for 1H interval
#define DONCHIAN_LENGTH_1H 20
#define ATR_LENGTH_1H 14
#define ATR_MULTIPLIER_1H 0.5
#define ADX_LENGTH_1H 14
#define ADX_THRESHOLD_1H 20

// Search range percentages
#define SEARCH_PERCENT_DONCHIAN_LENGTH_1H 0.25
#define SEARCH_PERCENT_ATR_LENGTH_1H 0.20
#define SEARCH_PERCENT_ATR_MULTIPLIER_1H 0.50
#define SEARCH_PERCENT_ADX_LENGTH_1H 0.20
#define SEARCH_PERCENT_ADX_THRESHOLD_1H 0.30

#endif // ADAPTIVE_DONCHIAN_V1_CONFIG_1H_H
