# Strategy Documentation

This document describes the trading strategies available in the QuantConnect backtesting system, ported from the OpenCL optimization framework.

## Available Strategies

### 1. Adaptive EMA v2
**Module:** `adaptive_ema_v2.py`

**Description:** Single EMA pair (fast/slow) that adapts periods based on volatility measured by ATR.

**Parameters:**
- `fast_base` (default: 15): Base fast EMA period
- `slow_base` (default: 18): Base slow EMA period
- `fast_mult` (default: 2.0): Fast EMA multiplier in high volatility
- `slow_mult` (default: 1.4): Slow EMA multiplier in high volatility
- `atr_length` (default: 12): ATR calculation period
- `vol_threshold` (default: 65): Volatility percentile threshold (0-100)
- `vol_length` (default: 50): Volatility lookback period

**Entry:** Fast EMA crosses above Slow EMA  
**Exit:** Fast EMA crosses below Slow EMA

---

### 2. Adaptive EMA v2.1
**Module:** `adaptive_ema_v2_1.py`

**Description:** Enhanced version of v2 with ADX trend strength confirmation.

**Parameters:**
- `fast_base` (default: 12): Base fast EMA period
- `slow_base` (default: 26): Base slow EMA period
- `fast_mult` (default: 1.5): Fast EMA multiplier in high volatility
- `slow_mult` (default: 1.5): Slow EMA multiplier in high volatility
- `atr_length` (default: 14): ATR calculation period
- `vol_threshold` (default: 70): Volatility percentile threshold
- `vol_length` (default: 50): Volatility lookback period
- `adx_length` (default: 14): ADX calculation period
- `adx_threshold` (default: 20.0): Minimum ADX for entry

**Entry:** Fast EMA crosses above Slow EMA AND ADX > threshold  
**Exit:** Fast EMA crosses below Slow EMA

**Notes:** More conservative than v2 due to ADX filter. Requires stronger trends.

---

### 3. Adaptive EMA v2.2
**Module:** `adaptive_ema_v2_2.py`

**Description:** Enhanced version with RSI momentum filter and volume confirmation.

**Parameters:**
- `fast_base` (default: 12): Base fast EMA period
- `slow_base` (default: 26): Base slow EMA period
- `fast_mult` (default: 1.5): Fast EMA multiplier in high volatility
- `slow_mult` (default: 1.5): Slow EMA multiplier in high volatility
- `atr_length` (default: 14): ATR calculation period
- `vol_threshold` (default: 70): Volatility percentile threshold
- `vol_length` (default: 50): Volatility lookback period
- `rsi_length` (default: 14): RSI calculation period
- `rsi_threshold` (default: 70): Maximum RSI for entry (avoid overbought)
- `volume_ma_length` (default: 20): Volume MA period

**Entry:** Fast EMA crosses above Slow EMA AND RSI < threshold AND Volume > MA  
**Exit:** Fast EMA crosses below Slow EMA

**Notes:** Prevents entries in overbought conditions and requires volume confirmation.

---

### 4. Adaptive EMA with Volume v1
**Module:** `adaptive_ema_vol_v1.py`

**Description:** Comprehensive strategy combining adaptive EMAs with volume analysis, market regime detection using RSI, and ADX trend confirmation.

**Parameters:**
- `fast_base` (default: 9): Base fast EMA period
- `slow_base` (default: 10): Base slow EMA period
- `fast_mult` (default: 1.4): Fast EMA multiplier in high volatility
- `slow_mult` (default: 1.0): Slow EMA multiplier in high volatility
- `atr_length` (default: 12): ATR calculation period
- `vol_threshold` (default: 65): Volatility percentile threshold
- `vol_length` (default: 50): Volatility lookback period
- `adx_length` (default: 7): ADX calculation period
- `adx_threshold` (default: 11.0): Minimum ADX for entry
- `rsi_length` (default: 14): RSI calculation period
- `rsi_trending_min` (default: 40): Minimum RSI for bullish trend
- `rsi_trending_max` (default: 70): Maximum RSI for bullish trend
- `volume_ma_length` (default: 20): Volume MA period

**Entry:** Fast EMA crosses above Slow EMA AND ADX > threshold AND RSI in trending range AND Volume > MA  
**Exit:** Fast EMA crosses below Slow EMA

**Notes:** Most sophisticated EMA strategy with multiple confirmation filters. May generate fewer signals but with higher quality.

---

### 5. Adaptive Donchian v1
**Module:** `adaptive_donchian_v1.py`

**Description:** Donchian Channel breakout strategy with ATR-based threshold adjustment and ADX confirmation.

**Parameters:**
- `donchian_length` (default: 20): Period for Donchian Channel calculation
- `atr_length` (default: 14): ATR calculation period
- `atr_multiplier` (default: 0.5): Multiplier for ATR threshold
- `adx_length` (default: 14): ADX calculation period
- `adx_threshold` (default: 20.0): Minimum ADX for entry

**Entry:** Price > Donchian High + (ATR * multiplier) AND ADX > threshold  
**Exit:** Price < Donchian Low

**Notes:** Breakout strategy that requires strong momentum. May have extended periods without trades in ranging markets. Works best in trending markets. The ATR multiplier filters out weak breakouts.

---

## Usage Examples

### Running a strategy

```bash
# Basic usage
python3 main.py --strategy adaptive_ema_v2 --symbol QQQ --start 2023-01-01 --end 2024-12-31 --interval 1h

# With custom parameters
python3 main.py --strategy adaptive_ema_v2.1 --symbol NVDA \
    --start 2024-01-01 --end 2024-12-31 --interval 1h \
    --fast-base 10 --slow-base 20 --adx-threshold 25

# Test on daily data
python3 main.py --strategy adaptive_ema_v2 --symbol SPY --interval 1d
```

### Strategy Selection Guide

**For trending markets:**
- Adaptive EMA v2.1 (with ADX filter)
- Adaptive Donchian v1

**For balanced approach:**
- Adaptive EMA v2
- Adaptive EMA v2.2

**For high-quality setups (fewer trades):**
- Adaptive EMA with Volume v1 (most filters)
- Adaptive EMA v2.2 (RSI + volume filters)

**For responsive trading:**
- Adaptive EMA v2 (fewer filters, more trades)

## Parameter Optimization

The default parameters are optimized for:
- **Symbol:** QQQ
- **Timeframe:** 1-hour bars
- **Period:** 2023-2025

For different symbols or timeframes, consider running the OpenCL optimization system to find optimal parameters, or adjust parameters based on backtesting results.

### Key Parameter Relationships

**EMA Periods:**
- Smaller = More responsive, more trades, more whipsaws
- Larger = Less responsive, fewer trades, fewer whipsaws
- fast_base should always be < slow_base

**Volatility Multipliers:**
- Higher = More conservative in high volatility (longer periods)
- Lower = More aggressive in high volatility

**ADX Threshold:**
- Higher = Requires stronger trends, fewer trades
- Lower = Allows weaker trends, more trades
- Typical range: 15-25

**RSI Thresholds:**
- Lower = Stricter entry requirements
- Higher = More relaxed entry requirements
- Typical range: 60-80 for rsi_threshold

**Volume Confirmation:**
- Requires volume above moving average
- Helps filter out low-conviction moves

## Performance Metrics

All strategies report:
- **Total Return:** Overall percentage gain/loss
- **Max Drawdown:** Largest peak-to-trough decline
- **Calmar Ratio:** Return / Max Drawdown (higher is better)
- **Sharpe Ratio:** Risk-adjusted return (higher is better)
- **Win Rate:** Percentage of profitable trades
- **Trade Count:** Number of round trips
- **Alpha:** Excess return vs buy-and-hold

## Notes

1. **Warmup Period:** All strategies need a warmup period for indicators to stabilize. The first several bars won't generate signals.

2. **Data Quality:** Ensure you have clean OHLCV data. Volume is required for volume-based strategies.

3. **Overfitting:** Default parameters are optimized on historical data. Be aware of overfitting risk when using optimized parameters.

4. **Comparison to OpenCL:** Python implementations may have slight numerical differences from OpenCL due to floating-point precision and calculation order.

5. **Live Trading:** These strategies are for educational/research purposes. Additional considerations needed for live trading (slippage, commissions, execution risk, etc.).
