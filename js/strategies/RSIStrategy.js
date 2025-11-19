const BaseStrategy = require('./BaseStrategy');
const { calculateRSI } = require('../indicators');

// ============================================================
// STRATEGY CONFIGURATION
// ============================================================
const STRATEGY_CONFIG = {
  name: 'RSI Strategy',
  description: 'Buy when RSI crosses above oversold, sell when crosses below overbought',
  
  // Default parameters
  defaultParams: {
    rsiPeriod: 14,
    oversoldLevel: 30,
    overboughtLevel: 70,
    
    // Risk Management
    initialCapital: 10000,
    commissionPerTrade: 1.0,
    stopLossPercent: 5.0
  },
  
  // Optimization ranges
  optimizationRanges: {
    rsiPeriod: [10, 20],
    oversoldLevel: [20, 35],
    overboughtLevel: [65, 80]
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
 * RSI Strategy
 * Buy when RSI crosses above oversold level
 * Sell when RSI crosses below overbought level
 */
class RSIStrategy extends BaseStrategy {
  constructor(params) {
    super(params);
    this.name = 'RSI Strategy';
  }

  static getDefaultParams() {
    return STRATEGY_CONFIG.defaultParams;
  }
  
  static getConfig() {
    return STRATEGY_CONFIG;
  }

  calculateIndicators(candles) {
    const closes = candles.map(c => c.close);
    const rsi = calculateRSI(closes, this.params.rsiPeriod);
    
    return { rsi };
  }

  getMinimumCandles() {
    return this.params.rsiPeriod + 50; // Extra buffer for RSI warmup
  }

  getFirstValidIndex(indicators, candles) {
    const startIdx = this.params.rsiPeriod;
    
    // Find first valid RSI value
    for (let i = startIdx; i < indicators.rsi.length; i++) {
      if (isFinite(indicators.rsi[i])) {
        return candles.length - indicators.rsi.length + i;
      }
    }
    
    return startIdx;
  }

  checkEntrySignal(i, indicators, candles, position) {
    if (position) return false;
    
    const rsiIdx = i - (candles.length - indicators.rsi.length);
    if (rsiIdx < 1) return false;
    
    const currentRSI = indicators.rsi[rsiIdx];
    const prevRSI = indicators.rsi[rsiIdx - 1];
    
    if (!isFinite(currentRSI) || !isFinite(prevRSI)) return false;
    
    // Buy when RSI crosses above oversold level
    return prevRSI <= this.params.oversoldLevel && currentRSI > this.params.oversoldLevel;
  }

  checkExitSignal(i, indicators, candles, position) {
    // Check stop loss first
    const stopLossExit = super.checkExitSignal(i, indicators, candles, position);
    if (stopLossExit) return stopLossExit;
    
    const rsiIdx = i - (candles.length - indicators.rsi.length);
    if (rsiIdx < 1) return null;
    
    const currentRSI = indicators.rsi[rsiIdx];
    const prevRSI = indicators.rsi[rsiIdx - 1];
    
    if (!isFinite(currentRSI) || !isFinite(prevRSI)) return null;
    
    // Sell when RSI crosses below overbought level
    const bearishCross = prevRSI >= this.params.overboughtLevel && currentRSI < this.params.overboughtLevel;
    
    if (bearishCross) {
      return {
        price: candles[i].close,
        reason: 'SIGNAL'
      };
    }
    
    return null;
  }

  getDescription() {
    return `${this.name} (Period: ${this.params.rsiPeriod}, Oversold: ${this.params.oversoldLevel}, Overbought: ${this.params.overboughtLevel})`;
  }
}

module.exports = RSIStrategy;
