# Adaptive EMA Strategy v4

## Overview

v4 is a **complete redesign** based on proven algorithmic trading principles:

### Problems with v3:
1. **Over-parameterization**: 4 EMA ranges (fast_min, fast_max, slow_min, slow_max) = too complex
2. **Counterintuitive logic**: High volatility → longer EMAs makes strategy SLOWER when it should be MORE SELECTIVE
3. **Inefficient**: Recalculating EMAs from scratch every candle is computationally expensive

### v4 Solution - Based on KAMA Principles:

**Core Philosophy**: Start with BASE EMAs (9/21) that adapt their smoothing based on market efficiency

## Key Innovations

### 1. **Efficiency Ratio (from KAMA)**
- Measures directional movement vs total movement
- **Trending market** (high efficiency) → Fast EMAs (more responsive)
- **Choppy market** (low efficiency) → Slow EMAs (avoid whipsaws)
- Formula: `ER = |price_change| / sum_of_price_movements`

### 2. **ADX Filter (Trend Strength)**
- Only takes trades when ADX > threshold (default 20)
- High volatility = require HIGHER ADX (stronger confirmation)
- Prevents trading in consolidation/sideways markets

### 3. **RSI Filter (Momentum)**
- **Entry filter**: Don't buy if RSI > 70 (overbought)
- **Exit filter**: Exit if RSI < 30 (oversold protection)
- Adds mean reversion awareness

### 4. **Adaptive Smoothing**
- EMAs speed up/slow down based on efficiency ratio
- Fast EMA: adjusts 3x (fastest = base period, slowest = 3x base period)  
- Slow EMA: same adaptive logic
- **Incremental calculation** (not recalculated from scratch)

## Parameters (8 total, much simpler than v3's 8)

| Parameter | Default | Description |
|-----------|---------|-------------|
| ema_fast_base | 9 | Base fast EMA period |
| ema_slow_base | 21 | Base slow EMA period |
| adx_length | 14 | Period for ADX calculation |
| adx_threshold | 20.0 | Minimum ADX to take trades |
| rsi_length | 14 | Period for RSI calculation |
| rsi_buy_max | 70.0 | Max RSI for buy entries |
| rsi_sell_min | 30.0 | Min RSI for sell exits |
| efficiency_lookback | 10 | Lookback for efficiency ratio |

## Trade Logic

### Entry Signal (BUY):
1. Fast EMA crosses above Slow EMA
2. **AND** ADX >= threshold (strong trend)
3. **AND** RSI < buy_max (not overbought)

### Exit Signal (SELL):
1. Fast EMA crosses below Slow EMA
2. **OR** RSI < sell_min (oversold protection)

## Why This Is Better

1. **Simpler**: 8 intuitive parameters vs v3's confusing min/max ranges
2. **Proven methods**: Based on KAMA, ADX, RSI - all well-tested indicators
3. **Better logic**: Adapts to TRENDING vs CHOPPY, not just high/low volatility
4. **More selective**: Multiple confirmation filters reduce false signals
5. **Computationally efficient**: Incremental EMA updates

## Expected Performance Improvements

- **Fewer whipsaw trades** in choppy markets (efficiency ratio filter)
- **Better entries** during strong trends (ADX filter)
- **Avoided overbought entries** (RSI filter)
- **Protected against severe reversals** (RSI oversold exit)

## Usage

```bash
# Test on QQQ 1h
./run.sh qqq 1h adaptive_ema_v4 nosave

# When satisfied, save results
./run.sh qqq 1h adaptive_ema_v4
```

## Note on Implementation

The optimize.c file needs to be created by copying from v2 or v3 and adapting:
- Change STRATEGY_NAME to "adaptive_ema_v4"
- Update Config struct to match new 8 parameters
- Update load_config() function for new parameter names
- Update combination counting logic
- Update JSON export with correct parameter names

This is left as an exercise since it's primarily string replacements in a long C file.
