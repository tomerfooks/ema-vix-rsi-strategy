// Strategy default parameters for 4-hour interval
const DEFAULT_PARAMS = {
  // Low Volatility
  fastLengthLow: 10,
  slowLengthLow: 60,
  
  // Medium Volatility
  fastLengthMed: 18,
  slowLengthMed: 75,
  
  // High Volatility
  fastLengthHigh: 30,
  slowLengthHigh: 90,
  
  // Volatility Settings
  volatilityLength: 60,
  atrLength: 14,
  lowVolPercentile: 28,
  highVolPercentile: 68,
  
  // Backtest settings
  initialCapital: 10000
};

// Optimization Configuration
const OPTIMIZATION_CONFIG = {
  // Data settings
  symbols: ['QQQ'],           // Symbols to optimize (can be array)
  candles: 270,               // Number of candles to fetch
  interval: '4h',             // Candle interval: '1h', '4h', '1d'
  
  // Worker thread settings
  numWorkers: null,           // null = use all CPU cores, or specify number (e.g., 4, 8)
  batchSize: 5000,            // Number of parameter combinations per worker batch (larger = less overhead)
  
  // Parameter ranges - control each parameter individually
  // Options: null = use rangePercent, number = use as percentage, [min, max] = explicit range
  paramRanges: {
    fastLengthLow: 0.03,      // 0.03 = ±3% from default
    slowLengthLow: 0.02,      // 0.03 = ±3% from default
    fastLengthMed: 0.03,      // Or: [20, 30] to test all integers 20-30
    slowLengthMed: 0.02,      // Or: null to use rangePercent
    fastLengthHigh: 0.04,
    slowLengthHigh: 0.02,
    atrLength: 0.03,          // 0.01 = ±1% from default
    volatilityLength: 0.02,
    lowVolPercentile: 0.02,
    highVolPercentile: 0.02
  },
  rangePercent: 0.05,         // ±5% from default values (used when paramRanges[param] is null)
  
  // Performance
  progressUpdateInterval: 5000 // Console update interval in ms
};

module.exports = { DEFAULT_PARAMS, OPTIMIZATION_CONFIG };
