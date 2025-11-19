const BaseStrategy = require('./BaseStrategy');
const { calculateMACD } = require('../indicators');

// ============================================================
// STRATEGY CONFIGURATION
// ============================================================
const STRATEGY_CONFIG = {
  name: 'MACD Strategy',
  description: 'Buy on MACD bullish crossover, sell on bearish crossover',
  
  // Default parameters
  defaultParams: {
    fastPeriod: 12,
    slowPeriod: 26,
    signalPeriod: 9,
    
    // Risk Management
    initialCapital: 10000,
    commissionPerTrade: 1.0,
    stopLossPercent: 5.0
  },
  
  // Optimization ranges
  optimizationRanges: {
    fastPeriod: [8, 16],
    slowPeriod: [20, 32],
    signalPeriod: [7, 12]
  },
  
  // Optimization settings
  optimization: {
    symbols: ['QQQ', 'SPY'],
    candles: 3000,
    interval: '1h',
    rangePercent: 0.05
  }
};

/**
 * MACD Strategy
 * Buy when MACD line crosses above signal line
 * Sell when MACD line crosses below signal line
 */
class MACDStrategy extends BaseStrategy {
  constructor(params) {
    super(params);
    this.name = 'MACD Strategy';
  }

  static getDefaultParams() {
    return STRATEGY_CONFIG.defaultParams;
  }
  
  static getConfig() {
    return STRATEGY_CONFIG;
  }

  calculateIndicators(candles) {
    const closes = candles.map(c => c.close);
    const macdData = calculateMACD(closes, this.params.fastPeriod, this.params.slowPeriod, this.params.signalPeriod);
    
    return {
      macd: macdData.macd,
      signal: macdData.signal,
      histogram: macdData.histogram
    };
  }

  getMinimumCandles() {
    return this.params.slowPeriod + this.params.signalPeriod + 50;
  }

  getFirstValidIndex(indicators, candles) {
    const startIdx = this.params.slowPeriod + this.params.signalPeriod;
    
    // Find first valid MACD value
    for (let i = startIdx; i < indicators.macd.length; i++) {
      if (isFinite(indicators.macd[i]) && isFinite(indicators.signal[i])) {
        return candles.length - indicators.macd.length + i;
      }
    }
    
    return startIdx;
  }

  checkEntrySignal(i, indicators, candles, position) {
    if (position) return false;
    
    const macdIdx = i - (candles.length - indicators.macd.length);
    if (macdIdx < 1) return false;
    
    const currentMACD = indicators.macd[macdIdx];
    const currentSignal = indicators.signal[macdIdx];
    const prevMACD = indicators.macd[macdIdx - 1];
    const prevSignal = indicators.signal[macdIdx - 1];
    
    if (!isFinite(currentMACD) || !isFinite(currentSignal) || !isFinite(prevMACD) || !isFinite(prevSignal)) {
      return false;
    }
    
    // Buy when MACD crosses above signal
    return prevMACD <= prevSignal && currentMACD > currentSignal;
  }

  checkExitSignal(i, indicators, candles, position) {
    // Check stop loss first
    const stopLossExit = super.checkExitSignal(i, indicators, candles, position);
    if (stopLossExit) return stopLossExit;
    
    const macdIdx = i - (candles.length - indicators.macd.length);
    if (macdIdx < 1) return null;
    
    const currentMACD = indicators.macd[macdIdx];
    const currentSignal = indicators.signal[macdIdx];
    const prevMACD = indicators.macd[macdIdx - 1];
    const prevSignal = indicators.signal[macdIdx - 1];
    
    if (!isFinite(currentMACD) || !isFinite(currentSignal) || !isFinite(prevMACD) || !isFinite(prevSignal)) {
      return null;
    }
    
    // Sell when MACD crosses below signal
    const bearishCross = prevMACD >= prevSignal && currentMACD < currentSignal;
    
    if (bearishCross) {
      return {
        price: candles[i].close,
        reason: 'SIGNAL'
      };
    }
    
    return null;
  }

  getDescription() {
    return `${this.name} (Fast: ${this.params.fastPeriod}, Slow: ${this.params.slowPeriod}, Signal: ${this.params.signalPeriod})`;
  }
}

module.exports = MACDStrategy;
