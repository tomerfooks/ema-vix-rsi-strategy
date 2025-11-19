// Strategy default parameters for 1-day interval
const DEFAULT_PARAMS = {
  // Low Volatility
  fastLengthLow: 4,
  slowLengthLow: 16,
  
  // Medium Volatility
  fastLengthMed: 3,
  slowLengthMed: 21,
  
  // High Volatility
  fastLengthHigh: 6,
  slowLengthHigh: 33,
  
  // Volatility Settings
  volatilityLength: 71,
  atrLength: 17,
  lowVolPercentile: 27,
  highVolPercentile: 77,
  
  // Backtest settings
  initialCapital: 10000
};

// Optimization Configuration
const OPTIMIZATION_CONFIG = {
  // Data settings
  symbols: ['QQQ'],           // Symbols to optimize (can be array)
  candles: 500,              // Number of candles to fetch
  interval: '1d',             // Candle interval: '1h', '4h', '1d'
  
  // Worker thread settings
  numWorkers: null,           // null = use all CPU cores, or specify number (e.g., 4, 8)
  batchSize: 5000,            // Number of parameter combinations per worker batch (larger = less overhead)
  
  // Parameter ranges - control each parameter individually
  // Options: null = use rangePercent, number = use as percentage, [min, max] = explicit range
  paramRanges: {
    fastLengthLow: 0.06,      // 0.03 = ±3% from default
    slowLengthLow: 0.05,      // 0.03 = ±3% from default
    fastLengthMed: 0.06,      // Or: [20, 30] to test all integers 20-30
    slowLengthMed: 0.05,      // Or: null to use rangePercent
    fastLengthHigh: 0.06,
    slowLengthHigh: 0.05,
    atrLength: 0.07,          // 0.01 = ±1% from default
    volatilityLength: 0.05,
    lowVolPercentile: 0.05,
    highVolPercentile: 0.05
  },
  rangePercent: 0.05,         // ±5% from default values (used when paramRanges[param] is null)
  
  // Performance
  progressUpdateInterval: 5000 // Console update interval in ms
};

module.exports = { DEFAULT_PARAMS, OPTIMIZATION_CONFIG };
