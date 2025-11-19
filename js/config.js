// Strategy default parameters from strategy-1h.pine
const DEFAULT_PARAMS = {
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
  
  // Backtest settings
  initialCapital: 10000
};

// Optimization Configuration
const OPTIMIZATION_CONFIG = {
  // Data settings
  symbols: ['QQQ'],           // Symbols to optimize (can be array)
  candles: 2000,              // Number of candles to fetch
  interval: '1h',             // Candle interval: '1h', '4h', '1d'
  
  // Parameter ranges - control each parameter individually
  // Options: null = use rangePercent, number = use as percentage, [min, max] = explicit range
  paramRanges: {
    fastLengthLow: 0.03,      // 0.03 = ±3% from default (14) = [13, 14, 15]
    slowLengthLow: 0.03,      // 0.03 = ±3% from default (80) = [77, 78, ..., 83]
    fastLengthMed: 0.03,      // Or: [20, 30] to test all integers 20-30
    slowLengthMed: 0.03,      // Or: null to use rangePercent
    fastLengthHigh: 0.03,
    slowLengthHigh: 0.03,
    atrLength: 0.02,          // 0.01 = ±1% from default (16) = [16, 17]
    volatilityLength: 0.02,
    lowVolPercentile: 0.02,
    highVolPercentile: 0.02
  },
  rangePercent: 0.05,         // ±5% from default values (used when paramRanges[param] is null)
  
  // Performance
  progressUpdateInterval: 5000 // Console update interval in ms
};

module.exports = { DEFAULT_PARAMS, OPTIMIZATION_CONFIG };
