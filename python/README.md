# Python Backtesting & Optimization System

High-performance backtesting and parameter optimization for the Adaptive Volatility EMA Crossover Strategy.

## Features

- **Vectorized Operations**: Uses NumPy/Pandas for fast numerical computations
- **Smart Caching**: Pre-calculates EMAs and caches ATR to avoid redundant calculations
- **Early Termination**: Filters out poor parameter combinations quickly
- **±5% Parameter Search**: Tests variations around proven default parameters

## Setup

1. Activate virtual environment:
```bash
source ../.venv/bin/activate
```

2. Install dependencies:
```bash
pip install yfinance pandas numpy
```

## Usage

### Simple Backtest
```bash
python backtest.py
```

### Parameter Optimization
```bash
# Single ticker (QQQ)
python optimize.py QQQ

# Multiple tickers
python optimize.py QQQ SPY IBM

# Full search (slower, more comprehensive)
python optimize.py QQQ --full
```

## Performance

**Current benchmarks (300 candles, QQQ):**
- Python: ~600 tests/sec (1.6ms per test)
- JavaScript: ~5,550 tests/sec (0.18ms per test)  
- **JS is 9x faster** due to V8 engine loop optimizations

**For 26,244 parameter combinations (±5% ranges):**
- Python: ~43 seconds
- JavaScript: ~5 seconds

Both are fast enough for practical use. Python could be further optimized by vectorizing the trading simulation loop, but the current performance is acceptable.

## Configuration

Edit `backtest.py` to modify:
- `num_candles`: Default 300 (set lower for faster testing)
- `interval`: '1h', '4h', or '1d'
- Default parameters in `DEFAULT_PARAMS`

## Output

Optimization results are saved to JSON files:
- `optimization-results-python-smart-{timestamp}.json`

Results include:
- Best parameters for each ticker
- Performance metrics (return, Sharpe, Calmar, profit factor)
- Buy & Hold comparison
- Trade statistics

## Performance

With ±5% ranges and 300 candles:
- ~1,000-10,000 parameter combinations tested
- Typical runtime: 30 seconds to 2 minutes per ticker
- Speed: 50-200 tests/second (depending on hardware)

## Files

- `backtest.py` - Core backtesting engine
- `optimize.py` - Parameter optimization system  
- `indicators.py` - EMA and ATR implementations
