# EMA-VIX-RSI Trading Strategy

Adaptive EMA crossover trading strategy with volatility regime detection. Optimizes parameters across different market conditions using ATR-based volatility ranking.

## Features

- **Adaptive EMA Parameters**: Automatically adjusts EMA periods based on market volatility (Low/Medium/High regimes)
- **Volatility Regime Detection**: Uses normalized ATR percentile ranking to classify market conditions
- **Advanced Optimization**: Fast parameter optimization with EMA caching and early termination filtering
- **Multiple Timeframes**: Supports 1h, 4h, and 1d intervals
- **Comprehensive Backtesting**: Detailed performance metrics, trade logs, and buy & hold comparison

## Structure

```
ema-vix-rsi-strategy/
├── js/                      # JavaScript implementation
│   ├── backtest.js         # Backtesting engine
│   ├── config.js           # Strategy parameters and optimization config
│   ├── dataFetcher.js      # Yahoo Finance data fetching with outlier filtering
│   ├── optimize.js         # Parameter optimization system
│   └── package.json        # Node.js dependencies
├── python/                  # Python implementation
│   ├── backtest.py         # Python backtesting
│   ├── indicators.py       # Technical indicators
│   ├── optimize.py         # Python optimization
│   └── README.md           # Python-specific docs
└── pine/                    # TradingView Pine Script
    ├── strategy-1h.pine    # 1-hour strategy
    └── strategy-1d.pine    # Daily strategy
```

## Installation

### JavaScript Version

```bash
cd js
npm install
```

### Python Version

```bash
cd python
pip install -r requirements.txt
```

## Usage

### Running Optimization (JavaScript)

```bash
cd js
node optimize.js              # Uses config symbols (QQQ by default)
node optimize.js SPY AAPL     # Optimize specific tickers
node optimize.js --full QQQ   # Full parameter search (slower)
```

### Running Backtest (JavaScript)

```bash
cd js
node backtest.js
```

## Configuration

Edit `js/config.js` to customize:

```javascript
// Default parameters
const DEFAULT_PARAMS = {
  // Low Volatility EMA periods
  fastLengthLow: 14,
  slowLengthLow: 80,
  
  // Medium Volatility EMA periods
  fastLengthMed: 25,
  slowLengthMed: 98,
  
  // High Volatility EMA periods
  fastLengthHigh: 43,
  slowLengthHigh: 120,
  
  // Volatility detection
  volatilityLength: 71,
  atrLength: 16,
  lowVolPercentile: 28,
  highVolPercentile: 66,
  
  initialCapital: 10000
};

// Optimization settings
const OPTIMIZATION_CONFIG = {
  symbols: ['QQQ'],
  candles: 3000,
  interval: '1h',  // '1h', '4h', '1d'
  
  // Per-parameter ranges
  paramRanges: {
    fastLengthLow: 0.03,    // ±3%
    slowLengthLow: 0.03,
    // ... or use [min, max] for explicit range
    // ... or null to use global rangePercent
  },
  rangePercent: 0.05        // Global ±5% (when paramRanges[param] is null)
};
```

## Strategy Logic

1. **Volatility Classification**: Calculate normalized ATR and rank it over a lookback period
2. **Regime Detection**: 
   - Low volatility: percentile < lowVolPercentile (28%)
   - Medium volatility: percentile between low and high thresholds
   - High volatility: percentile > highVolPercentile (66%)
3. **EMA Selection**: Use regime-specific fast/slow EMA periods
4. **Entry Signal**: Bullish crossover (fast EMA crosses above slow EMA)
5. **Exit Signal**: Bearish crossover (fast EMA crosses below slow EMA)

## Performance Features

- **EMA Caching**: Pre-calculates all EMAs once (~850x speedup)
- **ATR Caching**: Caches volatility metrics by ATR/lookback combinations
- **Early Termination**: Filters out poor performers before completion
- **Progress Tracking**: Real-time optimization progress updates
- **Data Quality**: Linear interpolation for outliers (>15% deviation from rolling median)

## Example Results

```
🏆 BEST PARAMETERS FOR QQQ
📊 Performance Metrics:
   Total Return: 37.01%
   Max Drawdown: 4.85%
   Sharpe Ratio: 4.26
   Calmar Ratio: 7.63
   Profit Factor: 7.00
   Win Rate: 82.35%
   Total Trades: 17

📉 Buy & Hold Comparison:
   Buy & Hold Return: 12.71%
   Strategy Outperformance: 24.30% ✅
```

## License

MIT

## Contributing

Feel free to submit issues or pull requests!
