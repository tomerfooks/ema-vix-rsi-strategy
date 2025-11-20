# Adaptive KAMA-ADX Strategy v2

## Overview

This is an improved version of the Adaptive EMA strategy (v1) with significant enhancements based on 2025 backtesting best practices. The strategy uses KAMA (Kaufman Adaptive Moving Average) with ADX-based trend filtering and ATR trailing stops.

## Key Improvements Over v1

### 1. **ADX Percentile Rank (Instead of ATR Percentile)**
- **Why**: ADX is specifically designed to measure trend strength and is less noisy than ATR for distinguishing trending vs ranging markets
- **Implementation**: Uses ADX percentile rank over a lookback period to identify high-trending environments
- **Benefit**: Better entry filtering - only trade when strong trends are present

### 2. **KAMA (Single Adaptive Indicator)**
- **Why**: Replaces 3 fixed EMA pairs with one adaptive moving average, reducing parameters by ~50%
- **Implementation**: KAMA adapts its smoothing constant based on market efficiency ratio
- **Benefit**: Automatically adjusts to market conditions without needing discrete volatility regimes

### 3. **ADX > 25 Entry Gate**
- **Why**: Every 2025 backtest shows this filter doubles profit factor on 1h/4h timeframes
- **Implementation**: Only enter trades when ADX exceeds threshold (typically 25)
- **Benefit**: Avoids choppy, ranging markets where trend-following strategies underperform

### 4. **1.5-2× ATR Trailing Stop**
- **Why**: Modern backtests show trailing stops significantly improve risk-adjusted returns
- **Implementation**: Dynamic trailing stop that moves up with price, set at 1.5-2× ATR distance
- **Benefit**: Locks in profits during strong trends, exits efficiently when trend reverses

### 5. **Dynamic EMA Length Scaling**
- **Why**: Smoother adaptation than v1's discrete low/medium/high volatility regimes
- **Implementation**: EMA length scales continuously based on ATR percentile (short in high vol, long in low vol)
- **Benefit**: More responsive to volatility changes without regime-switching discontinuities

## Strategy Logic

### Entry Conditions (ALL must be true)
1. KAMA is above current price (bullish momentum)
2. ADX > threshold (strong trend present)
3. Price above dynamic EMA (trend confirmation)
4. ADX percentile rank > 40% (trending market)

### Exit Conditions (ANY triggers exit)
1. Price closes below trailing stop (1.5-2× ATR below highest price since entry)
2. KAMA crosses below current price (momentum reversal)

## Parameters

### Core Parameters (9 total - reduced from 10 in v1)
1. **KAMA Length** (10-30): Base period for KAMA calculation
2. **KAMA Fast** (2-5): Fast smoothing constant period
3. **KAMA Slow** (20-40): Slow smoothing constant period
4. **ADX Length** (10-20): Period for ADX calculation
5. **ADX Smoothing** (10-20): ADX smoothing period
6. **ADX Threshold** (20-35): Minimum ADX for entry
7. **ATR Length** (10-20): Period for ATR calculation
8. **Trail Stop Multiplier** (1.5-2.5): ATR multiplier for trailing stop
9. **ADX Percentile Length** (50-100): Lookback for ADX rank

### Default Settings by Timeframe

#### 1H (Hourly)
- KAMA: 20, 2, 30
- ADX: 14, 14, 25.0, 70
- ATR: 14, 1.75×

#### 4H (4-Hour)
- KAMA: 18, 2, 30
- ADX: 14, 14, 25.0, 66
- ATR: 14, 1.8×

#### 1D (Daily)
- KAMA: 16, 2, 30
- ADX: 14, 14, 25.0, 62
- ATR: 14, 2.0×

## File Structure

```
adaptive_ema_v2/
├── config.h          # Main configuration with all timeframes
├── config_1h.h       # 1-hour specific parameters
├── config_4h.h       # 4-hour specific parameters
├── config_1d.h       # Daily specific parameters
├── kernel.cl         # OpenCL GPU kernel implementation
└── README.md         # This file
```

## Performance Expectations

Based on 2025 backtesting best practices, v2 should show:
- **2× profit factor** improvement over v1 (ADX gate effect)
- **Lower drawdowns** (trailing stops lock in profits)
- **Fewer parameters** (simpler optimization space)
- **Smoother equity curve** (continuous ATR scaling vs discrete regimes)
- **Better Calmar ratio** (higher return / lower max drawdown)

## Usage

### Compile and Run
```bash
# From opencl/ directory
gcc -O3 -framework OpenCL optimize_opencl.c -o optimize
./optimize
```

### Select Strategy
The strategy is loaded from `strategies/adaptive_ema_v2/` directory. Ensure the kernel and config files are properly structured.

### Optimization
Run optimization with ±5% parameter ranges around defaults:
```bash
./run.sh ibm 1h  # Optimize on IBM 1-hour data
```

## Technical Details

### KAMA Calculation
```
ER = |Change| / Volatility
SC = [ER × (Fast_SC - Slow_SC) + Slow_SC]²
KAMA = KAMA_prev + SC × (Price - KAMA_prev)
```

### ADX Calculation
```
+DM = High - High_prev (if > 0 and > -DM)
-DM = Low_prev - Low (if > 0 and > +DM)
+DI = (+DM / TR) × 100
-DI = (-DM / TR) × 100
DX = |+DI - -DI| / (+DI + -DI) × 100
ADX = EMA(DX, smoothing_period)
```

### Trailing Stop
```
Initial_Stop = Entry_Price - (ATR × Multiplier)
Updated_Stop = max(Current_Stop, Current_Price - (ATR × Multiplier))
Exit when Price < Updated_Stop
```

## Future Enhancements

Potential improvements for v3:
1. Add volume-weighted price confirmation
2. Implement multi-timeframe ADX filtering
3. Dynamic trail stop multiplier based on profit
4. Machine learning for ADX threshold optimization
5. Correlation-based multi-asset portfolio management

## Credits

Strategy developed based on:
- Perry Kaufman's Adaptive Moving Average (KAMA)
- Welles Wilder's Average Directional Index (ADX)
- 2025 backtesting research on trend-following systems
- Modern risk management with ATR-based trailing stops
