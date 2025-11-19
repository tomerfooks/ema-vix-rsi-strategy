const BaseStrategy = require('./BaseStrategy');
const { calculateEMA, calculateNormalizedATR } = require('../indicators');

// ============================================================
// STRATEGY CONFIGURATION
// ============================================================
const STRATEGY_CONFIG = {
  name: 'Adaptive EMA Crossover',
  description: 'Adjusts EMA periods based on volatility regime (Low/Medium/High)',
  
  // Default parameters
  defaultParams: {
    // Low Volatility
    fastLengthLow: 14,
    slowLengthLow: 80,
    
    // Medium Volatility
    fastLengthMed: 25,
    slowLengthMed: 98,
    
    // High Volatility
    fastLengthHigh: 43,
    slowLengthHigh: 120,
    
    // Volatility Settings
    volatilityLength: 71,
    atrLength: 16,
    lowVolPercentile: 28,
    highVolPercentile: 66,
    
    // Risk Management
    initialCapital: 10000,
    commissionPerTrade: 1.0,
    stopLossPercent: 0  // Set to 0 to disable stop loss, or percentage like 5.0 for 5%
  },
  
  // Optimization ranges - used by optimizer
  optimizationRanges: {
    fastLengthLow: [13, 16],      // Min, Max
    slowLengthLow: [78, 82],
    fastLengthMed: [23, 26],
    slowLengthMed: [95, 100],
    fastLengthHigh: [41, 44],
    slowLengthHigh: [118, 122],
    volatilityLength: [67, 73],
    atrLength: [13, 18],
    lowVolPercentile: [28, 32],
    highVolPercentile: [67, 72]
  },
  
  // Optimization settings
  optimization: {
    symbols: ['QQQ'],      // Symbols to optimize
    candles: 1000,                 // Number of candles to fetch
    interval: '1h',                // Candle interval
    rangePercent: 0.03            // ±3% from default if range not specified
  }
};

/**
 * Adaptive EMA Crossover Strategy
 * Adjusts EMA periods based on volatility regime (Low/Medium/High)
 */
class AdaptiveEMAStrategy extends BaseStrategy {
  constructor(params) {
    super(params);
    this.name = 'Adaptive EMA Crossover';
  }

  static getDefaultParams() {
    return STRATEGY_CONFIG.defaultParams;
  }
  
  static getConfig() {
    return STRATEGY_CONFIG;
  }

  /**
   * Calculate percentile rank for volatility regime detection
   */
  calculateVolatilityRank(normalizedATR, volatilityLength, minHistoryLength = 20) {
    const ranks = [];
    
    for (let i = 0; i < normalizedATR.length; i++) {
      const startIdx = Math.max(0, i - volatilityLength + 1);
      const window = normalizedATR.slice(startIdx, i + 1);
      
      if (window.length < minHistoryLength) {
        ranks.push(null);
        continue;
      }
      
      const currentVol = normalizedATR[i];
      const sorted = [...window].sort((a, b) => a - b);
      const rankCount = sorted.filter(v => v <= currentVol).length;
      const rank = (rankCount / sorted.length) * 100;
      
      ranks.push(rank);
    }
    
    return ranks;
  }

  /**
   * Determine volatility regime
   */
  getVolatilityRegime(volRank) {
    if (volRank < this.params.lowVolPercentile) return 'LOW';
    if (volRank < this.params.highVolPercentile) return 'MEDIUM';
    return 'HIGH';
  }

  calculateIndicators(candles) {
    const closes = candles.map(c => c.close);
    
    // Calculate volatility
    const normalizedATR = calculateNormalizedATR(candles, this.params.atrLength);
    const volRanks = this.calculateVolatilityRank(normalizedATR, this.params.volatilityLength);
    
    // Calculate all EMAs
    const emaLowFast = calculateEMA(closes, this.params.fastLengthLow);
    const emaLowSlow = calculateEMA(closes, this.params.slowLengthLow);
    const emaMedFast = calculateEMA(closes, this.params.fastLengthMed);
    const emaMedSlow = calculateEMA(closes, this.params.slowLengthMed);
    const emaHighFast = calculateEMA(closes, this.params.fastLengthHigh);
    const emaHighSlow = calculateEMA(closes, this.params.slowLengthHigh);
    
    return {
      normalizedATR,
      volRanks,
      emaLowFast,
      emaLowSlow,
      emaMedFast,
      emaMedSlow,
      emaHighFast,
      emaHighSlow
    };
  }

  getMinimumCandles() {
    return Math.max(
      this.params.slowLengthLow,
      this.params.slowLengthMed,
      this.params.slowLengthHigh
    ) + this.params.volatilityLength + 20;
  }

  getFirstValidIndex(indicators, candles) {
    const maxPeriod = Math.max(
      this.params.slowLengthLow,
      this.params.slowLengthMed,
      this.params.slowLengthHigh
    );
    const startIdx = maxPeriod - 1;
    
    // Find first index where volatility rank is valid
    for (let i = startIdx; i < indicators.volRanks.length; i++) {
      if (indicators.volRanks[i] !== null) {
        return i;
      }
    }
    
    return startIdx;
  }

  /**
   * Get EMA values for a specific regime and index
   */
  getRegimeEMAs(regime, emaOffset, indicators) {
    if (regime === 'LOW') {
      return {
        fast: indicators.emaLowFast[emaOffset],
        slow: indicators.emaLowSlow[emaOffset],
        prevFast: emaOffset > 0 ? indicators.emaLowFast[emaOffset - 1] : indicators.emaLowFast[emaOffset],
        prevSlow: emaOffset > 0 ? indicators.emaLowSlow[emaOffset - 1] : indicators.emaLowSlow[emaOffset]
      };
    } else if (regime === 'MEDIUM') {
      return {
        fast: indicators.emaMedFast[emaOffset],
        slow: indicators.emaMedSlow[emaOffset],
        prevFast: emaOffset > 0 ? indicators.emaMedFast[emaOffset - 1] : indicators.emaMedFast[emaOffset],
        prevSlow: emaOffset > 0 ? indicators.emaMedSlow[emaOffset - 1] : indicators.emaMedSlow[emaOffset]
      };
    } else {
      return {
        fast: indicators.emaHighFast[emaOffset],
        slow: indicators.emaHighSlow[emaOffset],
        prevFast: emaOffset > 0 ? indicators.emaHighFast[emaOffset - 1] : indicators.emaHighFast[emaOffset],
        prevSlow: emaOffset > 0 ? indicators.emaHighSlow[emaOffset - 1] : indicators.emaHighSlow[emaOffset]
      };
    }
  }

  checkEntrySignal(i, indicators, candles, position) {
    if (position) return false; // Already in position
    
    const atrIdx = i - (candles.length - indicators.normalizedATR.length);
    if (atrIdx < 0 || indicators.volRanks[atrIdx] === null) return false;
    
    const volRank = indicators.volRanks[atrIdx];
    const regime = this.getVolatilityRegime(volRank);
    
    const maxPeriod = Math.max(
      this.params.slowLengthLow,
      this.params.slowLengthMed,
      this.params.slowLengthHigh
    );
    const emaOffset = i - (maxPeriod - 1);
    
    const emas = this.getRegimeEMAs(regime, emaOffset, indicators);
    
    if (!isFinite(emas.fast) || !isFinite(emas.slow)) return false;
    
    // Bullish crossover
    return emas.prevFast <= emas.prevSlow && emas.fast > emas.slow;
  }

  checkExitSignal(i, indicators, candles, position) {
    // Check stop loss first
    const stopLossExit = super.checkExitSignal(i, indicators, candles, position);
    if (stopLossExit) return stopLossExit;
    
    // Check bearish crossover using locked regime
    const atrIdx = i - (candles.length - indicators.normalizedATR.length);
    if (atrIdx < 0 || indicators.volRanks[atrIdx] === null) return null;
    
    const maxPeriod = Math.max(
      this.params.slowLengthLow,
      this.params.slowLengthMed,
      this.params.slowLengthHigh
    );
    const emaOffset = i - (maxPeriod - 1);
    
    const emas = this.getRegimeEMAs(position.strategyData.regime, emaOffset, indicators);
    
    if (!isFinite(emas.fast) || !isFinite(emas.slow)) return null;
    
    // Bearish crossover
    const bearishCross = emas.prevFast >= emas.prevSlow && emas.fast < emas.slow;
    
    if (bearishCross) {
      return {
        price: candles[i].close,
        reason: 'SIGNAL'
      };
    }
    
    return null;
  }

  getPositionData(i, indicators, candles) {
    const atrIdx = i - (candles.length - indicators.normalizedATR.length);
    const volRank = indicators.volRanks[atrIdx];
    const regime = this.getVolatilityRegime(volRank);
    
    return { regime };
  }

  getDescription() {
    return `${this.name} (Low: ${this.params.fastLengthLow}/${this.params.slowLengthLow}, Med: ${this.params.fastLengthMed}/${this.params.slowLengthMed}, High: ${this.params.fastLengthHigh}/${this.params.slowLengthHigh})`;
  }
}

module.exports = AdaptiveEMAStrategy;
