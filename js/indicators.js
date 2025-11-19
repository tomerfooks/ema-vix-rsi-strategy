const talib = require('talib');

/**
 * Indicator abstraction layer using TA-Lib
 * Provides consistent interface for all technical indicators
 */

/**
 * Calculate EMA (Exponential Moving Average)
 */
function calculateEMA(prices, period) {
  const result = talib.execute({
    name: 'EMA',
    startIdx: 0,
    endIdx: prices.length - 1,
    inReal: prices,
    optInTimePeriod: period
  });
  
  if (result.error) {
    throw new Error(`EMA calculation error: ${result.error}`);
  }
  
  return result.result.outReal;
}

/**
 * Calculate SMA (Simple Moving Average)
 */
function calculateSMA(prices, period) {
  const result = talib.execute({
    name: 'SMA',
    startIdx: 0,
    endIdx: prices.length - 1,
    inReal: prices,
    optInTimePeriod: period
  });
  
  if (result.error) {
    throw new Error(`SMA calculation error: ${result.error}`);
  }
  
  return result.result.outReal;
}

/**
 * Calculate ATR (Average True Range)
 */
function calculateATR(high, low, close, period) {
  const result = talib.execute({
    name: 'ATR',
    startIdx: 0,
    endIdx: high.length - 1,
    high: high,
    low: low,
    close: close,
    optInTimePeriod: period
  });
  
  if (result.error) {
    throw new Error(`ATR calculation error: ${result.error}`);
  }
  
  return result.result.outReal;
}

/**
 * Calculate RSI (Relative Strength Index)
 */
function calculateRSI(prices, period) {
  const result = talib.execute({
    name: 'RSI',
    startIdx: 0,
    endIdx: prices.length - 1,
    inReal: prices,
    optInTimePeriod: period
  });
  
  if (result.error) {
    throw new Error(`RSI calculation error: ${result.error}`);
  }
  
  return result.result.outReal;
}

/**
 * Calculate MACD (Moving Average Convergence Divergence)
 */
function calculateMACD(prices, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
  const result = talib.execute({
    name: 'MACD',
    startIdx: 0,
    endIdx: prices.length - 1,
    inReal: prices,
    optInFastPeriod: fastPeriod,
    optInSlowPeriod: slowPeriod,
    optInSignalPeriod: signalPeriod
  });
  
  if (result.error) {
    throw new Error(`MACD calculation error: ${result.error}`);
  }
  
  return {
    macd: result.result.outMACD,
    signal: result.result.outMACDSignal,
    histogram: result.result.outMACDHist
  };
}

/**
 * Calculate Bollinger Bands
 */
function calculateBollingerBands(prices, period = 20, stdDev = 2) {
  const result = talib.execute({
    name: 'BBANDS',
    startIdx: 0,
    endIdx: prices.length - 1,
    inReal: prices,
    optInTimePeriod: period,
    optInNbDevUp: stdDev,
    optInNbDevDn: stdDev,
    optInMAType: 0  // SMA
  });
  
  if (result.error) {
    throw new Error(`Bollinger Bands calculation error: ${result.error}`);
  }
  
  return {
    upper: result.result.outRealUpperBand,
    middle: result.result.outRealMiddleBand,
    lower: result.result.outRealLowerBand
  };
}

/**
 * Calculate Stochastic Oscillator
 */
function calculateStochastic(high, low, close, kPeriod = 14, dPeriod = 3, slowingPeriod = 3) {
  const result = talib.execute({
    name: 'STOCH',
    startIdx: 0,
    endIdx: high.length - 1,
    high: high,
    low: low,
    close: close,
    optInFastK_Period: kPeriod,
    optInSlowK_Period: slowingPeriod,
    optInSlowK_MAType: 0,
    optInSlowD_Period: dPeriod,
    optInSlowD_MAType: 0
  });
  
  if (result.error) {
    throw new Error(`Stochastic calculation error: ${result.error}`);
  }
  
  return {
    k: result.result.outSlowK,
    d: result.result.outSlowD
  };
}

/**
 * Calculate ADX (Average Directional Index)
 */
function calculateADX(high, low, close, period = 14) {
  const result = talib.execute({
    name: 'ADX',
    startIdx: 0,
    endIdx: high.length - 1,
    high: high,
    low: low,
    close: close,
    optInTimePeriod: period
  });
  
  if (result.error) {
    throw new Error(`ADX calculation error: ${result.error}`);
  }
  
  return result.result.outReal;
}

/**
 * Calculate normalized ATR (ATR / close * 100)
 */
function calculateNormalizedATR(candles, atrPeriod) {
  const high = candles.map(c => c.high);
  const low = candles.map(c => c.low);
  const close = candles.map(c => c.close);
  
  const atrValues = calculateATR(high, low, close, atrPeriod);
  const normalized = [];
  const offset = candles.length - atrValues.length;
  
  for (let i = 0; i < atrValues.length; i++) {
    const closePrice = candles[offset + i].close;
    normalized.push((atrValues[i] / closePrice) * 100);
  }
  
  return normalized;
}

module.exports = {
  calculateEMA,
  calculateSMA,
  calculateATR,
  calculateRSI,
  calculateMACD,
  calculateBollingerBands,
  calculateStochastic,
  calculateADX,
  calculateNormalizedATR
};
