/**
 * Adaptive EMA Strategy Configuration - 1 Day Timeframe
 * 
 * This configuration is optimized for daily candles.
 * Daily timeframes typically use shorter EMA periods for better signal generation.
 * 
 * Total combinations = ~1.1M (fast with GPU)
 */

#ifndef CONFIG_ADAPTIVE_EMA_1D_H
#define CONFIG_ADAPTIVE_EMA_1D_H

// Low Volatility EMA Parameters
#define FAST_LENGTH_LOW_MIN 10
#define FAST_LENGTH_LOW_MAX 11
#define SLOW_LENGTH_LOW_MIN 58
#define SLOW_LENGTH_LOW_MAX 63

// Medium Volatility EMA Parameters
#define FAST_LENGTH_MED_MIN 19
#define FAST_LENGTH_MED_MAX 21
#define SLOW_LENGTH_MED_MIN 78
#define SLOW_LENGTH_MED_MAX 84

// High Volatility EMA Parameters
#define FAST_LENGTH_HIGH_MIN 32
#define FAST_LENGTH_HIGH_MAX 35
#define SLOW_LENGTH_HIGH_MIN 96
#define SLOW_LENGTH_HIGH_MAX 102

// ATR (Average True Range) Length
#define ATR_LENGTH_MIN 12
#define ATR_LENGTH_MAX 14

// Volatility Lookback Period
#define VOLATILITY_LENGTH_MIN 60
#define VOLATILITY_LENGTH_MAX 64

// Volatility Percentile Thresholds
#define LOW_VOL_PERCENTILE_MIN 23
#define LOW_VOL_PERCENTILE_MAX 25
#define HIGH_VOL_PERCENTILE_MIN 58
#define HIGH_VOL_PERCENTILE_MAX 61

// Default Values (center of ranges)
#define DEFAULT_FAST_LOW 10
#define DEFAULT_SLOW_LOW 60
#define DEFAULT_FAST_MED 20
#define DEFAULT_SLOW_MED 81
#define DEFAULT_FAST_HIGH 33
#define DEFAULT_SLOW_HIGH 99
#define DEFAULT_ATR_LENGTH 13
#define DEFAULT_VOLATILITY_LENGTH 62
#define DEFAULT_LOW_VOL_PERCENTILE 24
#define DEFAULT_HIGH_VOL_PERCENTILE 59

#endif // CONFIG_ADAPTIVE_EMA_1D_H
