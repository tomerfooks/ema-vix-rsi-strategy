# Adaptive Donchian Breakout Strategy v1

## Overview

The Adaptive Donchian Breakout Strategy v1 is a GPU-accelerated trading strategy that uses Donchian Channel breakouts with ATR-based threshold adjustments and ADX trend strength confirmation.

## Strategy Logic

### Core Concept

The Donchian Channel is a volatility indicator consisting of:
- **Upper Band**: Highest high over N periods
- **Lower Band**: Lowest low over N periods

This strategy trades breakouts of these channels with additional filters:

### Entry Rules

**Long Entry (BUY):**
- Price breaks above the Donchian high + (ATR × multiplier)
- ADX is above the minimum threshold (trend strength confirmation)

**Exit (SELL):**
- Price breaks below the Donchian low - (ATR × multiplier)

### Key Features

1. **Donchian Channel (20-period default)**
   - Classic breakout indicator
   - Identifies consolidation and breakout points
   - Adaptive to timeframe

2. **ATR-Based Threshold**
   - Filters false breakouts by requiring price to exceed channel by ATR × multiplier
   - Higher ATR multiplier = more conservative (fewer false signals, may miss some moves)
   - Lower ATR multiplier = more aggressive (catches more moves, more false signals)

3. **ADX Confirmation**
   - Only enters trades when ADX is above threshold
   - Ensures sufficient trend strength
   - Helps avoid choppy, range-bound conditions

## Parameters

The strategy optimizes 5 parameters:

| Parameter | Description | Default (1h) | Range |
|-----------|-------------|--------------|-------|
| `donchian_length` | Period for Donchian Channel | 20 | 15-25 |
| `atr_length` | Period for ATR calculation | 14 | 11-17 |
| `atr_multiplier` | Multiplier for ATR threshold | 0.5 | 0.25-0.75 |
| `adx_length` | Period for ADX calculation | 14 | 11-17 |
| `adx_threshold` | Minimum ADX for entry | 20 | 14-26 |

## Usage

### Compile the strategy:
```bash
cd opencl
make STRATEGY=adaptive_donchian_v1
```

### Run optimization:
```bash
./run.sh <TICKER> <INTERVAL> adaptive_donchian_v1 [MAX_COMBINATIONS]
```

Example:
```bash
./run.sh QQQ 1h adaptive_donchian_v1 5000
```

### Available intervals:
- `1h` - 1-hour candles
- `4h` - 4-hour candles  
- `1d` - Daily candles

## Configuration

Configuration files for each timeframe:
- `config_1h.h` - 1-hour settings
- `config_4h.h` - 4-hour settings
- `config_1d.h` - Daily settings

Each config defines:
- Default parameter values
- Search range percentages for optimization
- Enable/disable percentage-based ranges

## Performance Metrics

The optimizer reports:
- **Total Return**: Overall profit/loss percentage
- **Max Drawdown**: Largest peak-to-trough decline
- **Calmar Ratio**: Return / Max Drawdown (risk-adjusted performance)
- **Sharpe Ratio**: Risk-adjusted return based on trade volatility
- **Total Trades**: Number of completed round-trip trades
- **Outperformance**: Strategy return vs Buy & Hold

## Output

Results are saved to:
```
strategies/adaptive_donchian_v1/results/<ticker>/<interval>/
```

For each run:
- **JSON file**: Complete results and trade log
- **HTML report**: Interactive visualization with charts

## Strategy Characteristics

**Best suited for:**
- Trending markets
- Breakout trading
- Medium to long-term holds
- Strong directional moves

**Performs poorly in:**
- Choppy, range-bound markets
- Low volatility environments
- Frequent whipsaws

**Risk Considerations:**
- Can experience large drawdowns during false breakouts
- May miss early trend entries (waits for breakout confirmation)
- ADX filter reduces trade frequency

## Technical Implementation

- **Language**: OpenCL (GPU-accelerated)
- **Platform**: Apple Silicon M1/M2/M3, AMD Radeon
- **Optimization**: Exhaustive parameter search
- **Backtesting**: Single-pass with all combinations tested in parallel

## Advantages vs Traditional EMA

1. **Breakout Focus**: Captures strong directional moves
2. **Volatility Adaptive**: ATR-based thresholds adjust to market conditions
3. **Trend Confirmation**: ADX filter reduces false signals
4. **Clear Entry/Exit**: Objective channel breakout levels

## Future Enhancements

Potential improvements:
- Multiple timeframe confirmation
- Volume-based filters
- Dynamic position sizing based on ATR
- Trailing stops based on Donchian midline
- Mean reversion mode for range-bound markets
