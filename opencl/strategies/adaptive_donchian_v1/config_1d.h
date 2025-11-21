/**
 * Adaptive Donchian Breakout Strategy v1 - 1D Configuration
 * 
 * Configuration for daily timeframe optimization.
 */

#ifndef ADAPTIVE_DONCHIAN_V1_CONFIG_1D_H
#define ADAPTIVE_DONCHIAN_V1_CONFIG_1D_H

// Enable percentage-based range search
#define USE_PERCENT_RANGE_1D

// Default parameter values for 1D interval
#define DONCHIAN_LENGTH_1D 20
#define ATR_LENGTH_1D 14
#define ATR_MULTIPLIER_1D 0.5
#define ADX_LENGTH_1D 14
#define ADX_THRESHOLD_1D 20

// Search range percentages
#define SEARCH_PERCENT_DONCHIAN_LENGTH_1D 0.25
#define SEARCH_PERCENT_ATR_LENGTH_1D 0.20
#define SEARCH_PERCENT_ATR_MULTIPLIER_1D 0.50
#define SEARCH_PERCENT_ADX_LENGTH_1D 0.20
#define SEARCH_PERCENT_ADX_THRESHOLD_1D 0.30

#endif // ADAPTIVE_DONCHIAN_V1_CONFIG_1D_H
