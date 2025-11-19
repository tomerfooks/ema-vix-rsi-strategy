/**
 * Adaptive EMA Strategy Configuration - 4 Hour Timeframe
 * 
 * This configuration is optimized for 4-hour candles.
 * 4h typically requires slightly shorter periods than 1h for similar responsiveness.
 * 
 * Total combinations = ~1.3M (fast with GPU)
 */

#ifndef CONFIG_ADAPTIVE_EMA_4H_H
#define CONFIG_ADAPTIVE_EMA_4H_H

// Low Volatility EMA Parameters
#define FAST_LENGTH_LOW_MIN 11
#define FAST_LENGTH_LOW_MAX 13
#define SLOW_LENGTH_LOW_MIN 68
#define SLOW_LENGTH_LOW_MAX 74

// Medium Volatility EMA Parameters
#define FAST_LENGTH_MED_MIN 21
#define FAST_LENGTH_MED_MAX 23
#define SLOW_LENGTH_MED_MIN 86
#define SLOW_LENGTH_MED_MAX 92

// High Volatility EMA Parameters
#define FAST_LENGTH_HIGH_MIN 36
#define FAST_LENGTH_HIGH_MAX 39
#define SLOW_LENGTH_HIGH_MIN 106
#define SLOW_LENGTH_HIGH_MAX 112

// ATR (Average True Range) Length
#define ATR_LENGTH_MIN 13
#define ATR_LENGTH_MAX 15

// Volatility Lookback Period
#define VOLATILITY_LENGTH_MIN 64
#define VOLATILITY_LENGTH_MAX 68

// Volatility Percentile Thresholds
#define LOW_VOL_PERCENTILE_MIN 24
#define LOW_VOL_PERCENTILE_MAX 27
#define HIGH_VOL_PERCENTILE_MIN 60
#define HIGH_VOL_PERCENTILE_MAX 63

// Default Values (center of ranges)
#define DEFAULT_FAST_LOW 12
#define DEFAULT_SLOW_LOW 71
#define DEFAULT_FAST_MED 22
#define DEFAULT_SLOW_MED 89
#define DEFAULT_FAST_HIGH 37
#define DEFAULT_SLOW_HIGH 109
#define DEFAULT_ATR_LENGTH 14
#define DEFAULT_VOLATILITY_LENGTH 66
#define DEFAULT_LOW_VOL_PERCENTILE 25
#define DEFAULT_HIGH_VOL_PERCENTILE 61

#endif // CONFIG_ADAPTIVE_EMA_4H_H
