# Strategy Framework - Quick Start Guide

## Overview

A modular, extensible backtesting and optimization framework that supports multiple trading strategies with TA-Lib indicators.

## Features

✨ **Modular Strategy Pattern**: Easy to add new strategies  
⚡ **TA-Lib Integration**: High-performance C-based technical indicators  
🎯 **Per-Strategy Configuration**: Each strategy has its own parameters and optimization ranges  
📊 **OHLC Stop Loss**: Uses intrabar low data for realistic stop loss execution  
🔍 **Flexible Optimization**: Quick or exhaustive parameter search  
📈 **Multi-Symbol Support**: Test strategies across different securities  

## Available Strategies

1. **AdaptiveEMAStrategy** - EMA crossover that adapts periods based on volatility regime
2. **RSIStrategy** - Trade RSI oversold/overbought crossovers
3. **MACDStrategy** - MACD line and signal line crossovers

## Quick Start

### Run a Backtest

```bash
# Backtest with default strategy (AdaptiveEMA)
node backtest-new.js

# Test specific ticker with a strategy
node backtest-new.js QQQ
```

### Compare Strategies

```bash
# Compare all strategies on QQQ
node compare-strategies.js
```

### Optimize a Strategy

```bash
# Quick optimization (tests key parameter points)
node optimize-new.js --strategy RSIStrategy

# Exhaustive optimization (full grid search)
node optimize-new.js --strategy MACDStrategy --exhaustive

# Optimize on specific symbols
node optimize-new.js --strategy AdaptiveEMAStrategy --symbols IBM,AAPL,MSFT

# Optimize on different timeframe
node optimize-new.js --strategy RSIStrategy --symbols QQQ,SPY
```

## Creating a New Strategy

1. Create a new file in `strategies/` folder
2. Extend `BaseStrategy` class
3. Add strategy configuration at the top:

```javascript
const STRATEGY_CONFIG = {
  name: 'My Strategy',
  description: 'Strategy description',
  
  defaultParams: {
    myParam: 10,
    initialCapital: 10000,
    commissionPerTrade: 1.0,
    stopLossPercent: 5.0
  },
  
  optimizationRanges: {
    myParam: [5, 20]  // Min, Max
  },
  
  optimization: {
    symbols: ['QQQ', 'SPY'],
    candles: 3000,
    interval: '1h'
  }
};
```

4. Implement required methods:
   - `calculateIndicators(candles)` - Calculate all indicators
   - `getMinimumCandles()` - Return minimum data required
   - `checkEntrySignal(i, indicators, candles, position)` - Entry logic
   - `checkExitSignal(i, indicators, candles, position)` - Exit logic

5. Register in `strategies/index.js`

## Strategy Configuration

Each strategy file contains its configuration at the top:

### defaultParams
Default values for all strategy parameters including risk management (capital, commission, stop loss).

### optimizationRanges
Min/max values for parameters to test during optimization. Format: `[min, max]`

### optimization
Settings for optimization runs:
- `symbols`: Default securities to test
- `candles`: Number of candles to fetch
- `interval`: Timeframe ('1h', '4h', '1d')
- `rangePercent`: Default percentage range if not specified

## Important Notes

### Stop Loss Using OHLC
Stop losses now check the **low** of each candle, not just the close. This provides more realistic exit prices since a stop would be hit intrabar.

### Commission Per Trade
Each trade incurs a configurable commission (default $1). This is deducted from P&L.

### Optimization Modes

**Quick Mode** (default):
- Tests min, default, and max for each parameter
- Fast, good for initial exploration
- Tests ~20-30 combinations

**Exhaustive Mode** (`--exhaustive`):
- Full grid search across parameter space
- Much slower but comprehensive
- Tests hundreds to thousands of combinations

## File Structure

```
js/
├── strategies/
│   ├── BaseStrategy.js          # Base class all strategies extend
│   ├── AdaptiveEMAStrategy.js   # Volatility-adaptive EMA crossover
│   ├── RSIStrategy.js           # RSI oversold/overbought
│   ├── MACDStrategy.js          # MACD crossover
│   └── index.js                 # Strategy registry
├── indicators.js                # TA-Lib indicator wrappers
├── dataFetcher.js              # Yahoo Finance data fetching
├── backtest-new.js             # Backtesting engine
├── optimize-new.js             # Optimization engine
├── compare-strategies.js       # Strategy comparison tool
└── config.js                   # Legacy config (for old backtest.js)
```

## Example Workflow

```bash
# 1. Compare strategies to find best performer
node compare-strategies.js

# 2. Optimize the best strategy
node optimize-new.js --strategy RSIStrategy --symbols QQQ,SPY,AAPL

# 3. Update strategy config with optimized parameters

# 4. Run full backtest with optimized params
node backtest-new.js
```

## Tips

- Start with quick optimization to identify promising parameter regions
- Use exhaustive mode on specific parameters you want to fine-tune
- Test on multiple symbols to avoid overfitting
- Higher granularity in exhaustive mode = longer runtime but better results
- Stop loss of 5% is default - adjust based on your risk tolerance
- Commission matters - $1/trade adds up on high-frequency strategies
