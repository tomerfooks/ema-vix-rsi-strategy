/**
 * Adaptive EMA Strategy v1 - 1H Configuration
 */

#ifndef ADAPTIVE_EMA_V1_CONFIG_1H_H
#define ADAPTIVE_EMA_V1_CONFIG_1H_H

// ============================================================
// 1H INTERVAL - DEFAULT PARAMETERS
// ============================================================

// Low Volatility Regime
// BASE FAST_LOW_1H = 12, SLOW_LOW_1H = 80
#define FAST_LOW_1H 9
#define SLOW_LOW_1H 21

// Medium Volatility Regime
// BASE FAST_MED_1H = 25, SLOW_MED_1H = 108
#define FAST_MED_1H 9
#define SLOW_MED_1H 21

// High Volatility Regime
// BASE FAST_HIGH_1H = 38, SLOW_HIGH_1H = 120
#define FAST_HIGH_1H 9
#define SLOW_HIGH_1H 21

// Volatility Calculation
// BASE ATR_LENGTH_1H = 14, VOL_LENGTH_1H = 70
#define ATR_LENGTH_1H 11
#define VOL_LENGTH_1H 58
// BASE LOW_VOL_PCT_1H = 25, HIGH_VOL_PCT_1H = 75
#define LOW_VOL_PCT_1H 1
#define HIGH_VOL_PCT_1H 88

// Use percentage-based range for optimization
#define USE_PERCENT_RANGE_1H

// Individual search percentages for each parameter
#define SEARCH_PERCENT_FAST_LOW_1H 0.1
#define SEARCH_PERCENT_SLOW_LOW_1H 0.07
#define SEARCH_PERCENT_FAST_MED_1H 0.12    
#define SEARCH_PERCENT_SLOW_MED_1H 0.04     
#define SEARCH_PERCENT_FAST_HIGH_1H 0.12    
#define SEARCH_PERCENT_SLOW_HIGH_1H 0.03    
#define SEARCH_PERCENT_ATR_1H 0.1
#define SEARCH_PERCENT_VOL_1H 0.04          
#define SEARCH_PERCENT_LOW_PCT_1H 0.05      
#define SEARCH_PERCENT_HIGH_PCT_1H 0.04

// Strategy Settings
#define INITIAL_CAPITAL_1H 10000.0f
#define MIN_TRADES_1H 1
#define MAX_DRAWDOWN_FILTER_1H 50.0f
#define WARMUP_PERIOD_1H 50

#endif // ADAPTIVE_EMA_V1_CONFIG_1
