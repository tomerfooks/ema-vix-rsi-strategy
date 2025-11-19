# Optimization Command Usage Examples

## Basic Usage

Run optimization for a specific ticker and interval:

```bash
# Optimize QQQ on 1-day interval
node optimize.js QQQ 1d

# Optimize SPY on 1-hour interval
node optimize.js SPY 1h

# Optimize AAPL on 4-hour interval
node optimize.js AAPL 4h
```

## Advanced Usage

Use the `--full` flag for comprehensive search (slower but more thorough):

```bash
# Full optimization for QQQ on 1-day interval
node optimize.js QQQ 1d --full

# Full optimization for SPY on 1-hour interval
node optimize.js SPY 1h --full
```

## Default Behavior

If no arguments are provided, it uses the config file's default settings:

```bash
# Uses symbols and interval from config-1h.js (default)
node optimize.js
```

## Available Intervals

- `1h` - 1-hour candles (uses config-1h.js)
- `4h` - 4-hour candles (uses config-4h.js)
- `1d` - 1-day candles (uses config-1d.js)

## Config Files

Each interval has its own configuration file with optimized default parameters:

- `config-1h.js` - Hourly interval settings
- `config-4h.js` - 4-hour interval settings
- `config-1d.js` - Daily interval settings

You can edit these files to adjust:
- Default EMA lengths for different volatility regimes
- ATR and volatility calculation parameters
- Optimization ranges and search parameters
- Number of candles to fetch
- Worker thread settings

## Examples

```bash
# Quick optimization of QQQ on daily timeframe
node optimize.js QQQ 1d

# Comprehensive optimization of multiple tickers on hourly timeframe
node optimize.js SPY 1h --full

# Optimize with default config settings (QQQ on 1h from config-1h.js)
node optimize.js
```
