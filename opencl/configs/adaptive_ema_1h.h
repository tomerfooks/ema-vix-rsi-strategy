/**
 * Adaptive EMA Strategy Configuration - 1 Hour Timeframe
 * 
 * This configuration is optimized for 1-hour candles.
 * Adjust ranges based on your backtest results and market conditions.
 * 
 * Total combinations = (fast_low * slow_low * fast_med * slow_med * fast_high * 
 *                       slow_high * atr * vol * low_pct * high_pct)
 * Current: ~1.5M combinations (fast with GPU)
 */

#ifndef CONFIG_ADAPTIVE_EMA_1H_H
#define CONFIG_ADAPTIVE_EMA_1H_H

// Low Volatility EMA Parameters
#define FAST_LENGTH_LOW_MIN 11
#define FAST_LENGTH_LOW_MAX 16
#define SLOW_LENGTH_LOW_MIN 72
#define SLOW_LENGTH_LOW_MAX 87

// Medium Volatility EMA Parameters
#define FAST_LENGTH_MED_MIN 20
#define FAST_LENGTH_MED_MAX 28
#define SLOW_LENGTH_MED_MIN 89
#define SLOW_LENGTH_MED_MAX 108

// High Volatility EMA Parameters
#define FAST_LENGTH_HIGH_MIN 35
#define FAST_LENGTH_HIGH_MAX 47
#define SLOW_LENGTH_HIGH_MIN 106
#define SLOW_LENGTH_HIGH_MAX 132

// ATR (Average True Range) Length
#define ATR_LENGTH_MIN 11
#define ATR_LENGTH_MAX 18

// Volatility Lookback Period
#define VOLATILITY_LENGTH_MIN 62
#define VOLATILITY_LENGTH_MAX 78

// Volatility Percentile Thresholds
#define LOW_VOL_PERCENTILE_MIN 22
#define LOW_VOL_PERCENTILE_MAX 32
#define HIGH_VOL_PERCENTILE_MIN 58
#define HIGH_VOL_PERCENTILE_MAX 71

// Default Values (center of ranges)
#define DEFAULT_FAST_LOW 10
#define DEFAULT_SLOW_LOW 84
#define DEFAULT_FAST_MED 20
#define DEFAULT_SLOW_MED 102
#define DEFAULT_FAST_HIGH 39
#define DEFAULT_SLOW_HIGH 124
#define DEFAULT_ATR_LENGTH 13
#define DEFAULT_VOLATILITY_LENGTH 79
#define DEFAULT_LOW_VOL_PERCENTILE 22
#define DEFAULT_HIGH_VOL_PERCENTILE 68

#endif // CONFIG_ADAPTIVE_EMA_1H_H
