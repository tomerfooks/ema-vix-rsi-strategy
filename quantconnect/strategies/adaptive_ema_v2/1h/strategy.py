"""
Adaptive EMA Strategy v2
Ported from OpenCL optimization system

Strategy Logic:
- Single EMA pair (fast/slow) that adapts periods based on volatility
- Uses ATR to measure relative volatility
- High volatility -> Longer periods (more conservative)
- Low volatility -> Shorter periods (more responsive)

Entry: Fast EMA crosses above Slow EMA
Exit: Fast EMA crosses below Slow EMA
"""

import pandas as pd
import numpy as np
from typing import Optional
from ...base_strategy import BaseStrategy


class AdaptiveEMAV2_1H(BaseStrategy):
    """
    Adaptive EMA Strategy v2 - Hourly Timeframe (1H)
    Optimized for hourly bar trading
    
    Parameters:
        fast_base: Base fast EMA period (default: 8)
        slow_base: Base slow EMA period (default: 14)
        fast_mult: Fast EMA multiplier in high volatility (default: 1.6)
        slow_mult: Slow EMA multiplier in high volatility (default: 1.0)
        atr_length: ATR calculation period (default: 12)
        vol_threshold: Volatility percentile threshold (default: 69)
        vol_length: Volatility lookback period (default: 50)
    """
    
    def __init__(self, 
                 fast_base: int = 8,
                 slow_base: int = 14,
                 fast_mult: float = 1.6,
                 slow_mult: float = 1.0,
                 atr_length: int = 12,
                 vol_threshold: int = 69,
                 vol_length: int = 50,
                 **kwargs):
        
        super().__init__(
            fast_base=fast_base,
            slow_base=slow_base,
            fast_mult=fast_mult,
            slow_mult=slow_mult,
            atr_length=atr_length,
            vol_threshold=vol_threshold,
            vol_length=vol_length,
            **kwargs
        )
        
        # Store parameters
        self.fast_base = fast_base
        self.slow_base = slow_base
        self.fast_mult = fast_mult
        self.slow_mult = slow_mult
        self.atr_length = atr_length
        self.vol_threshold = vol_threshold
        self.vol_length = vol_length
        
        # Validate parameters
        if fast_base >= slow_base:
            raise ValueError(f"fast_base ({fast_base}) must be < slow_base ({slow_base})")
        if fast_mult < 1.0 or slow_mult < 1.0:
            raise ValueError("Multipliers must be >= 1.0")
        
        # State for crossover detection
        self.prev_ema_fast = None
        self.prev_ema_slow = None
    
    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range."""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=self.atr_length, adjust=False).mean()
        
        return atr
    
    def calculate_ema(self, series: pd.Series, period: int) -> float:
        """Calculate EMA up to current point."""
        return series.ewm(span=period, adjust=False).mean().iloc[-1]
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators needed for the strategy.
        
        Adds columns:
        - atr: Average True Range
        - relative_volatility: ATR as percentage of price
        - vol_percentile: Current volatility percentile
        - is_high_vol: Boolean flag for high volatility regime
        - fast_period: Adaptive fast EMA period
        - slow_period: Adaptive slow EMA period
        - ema_fast: Fast EMA value
        - ema_slow: Slow EMA value
        """
        # Calculate ATR
        data['atr'] = self.calculate_atr(data)
        
        # Calculate relative volatility (ATR as % of price)
        data['relative_volatility'] = (data['atr'] / data['close']) * 100
        
        # Calculate volatility percentile using rolling window
        data['vol_percentile'] = data['relative_volatility'].rolling(
            window=self.vol_length
        ).apply(
            lambda x: (x < x.iloc[-1]).sum() / len(x) * 100,
            raw=False
        )
        
        # Determine volatility regime
        data['is_high_vol'] = data['vol_percentile'] >= self.vol_threshold
        
        # Calculate adaptive periods
        data['fast_period'] = np.where(
            data['is_high_vol'],
            int(self.fast_base * self.fast_mult),
            self.fast_base
        )
        data['slow_period'] = np.where(
            data['is_high_vol'],
            int(self.slow_base * self.slow_mult),
            self.slow_base
        )
        
        return data
    
    def generate_signals(self, data: pd.DataFrame, idx: int) -> Optional[str]:
        """
        Generate buy/sell signals based on EMA crossover.
        
        Entry: Fast EMA crosses above Slow EMA
        Exit: Fast EMA crosses below Slow EMA
        """
        # Need warmup period
        warmup = max(self.atr_length, self.vol_length) + 10
        if idx < warmup:
            return None
        
        # Get current adaptive periods
        fast_period = int(data.iloc[idx]['fast_period'])
        slow_period = int(data.iloc[idx]['slow_period'])
        
        # Calculate EMAs with adaptive periods
        closes_up_to_now = data['close'].iloc[:idx+1]
        ema_fast = self.calculate_ema(closes_up_to_now, fast_period)
        ema_slow = self.calculate_ema(closes_up_to_now, slow_period)
        
        # Detect crossovers
        signal = None
        
        if self.prev_ema_fast is not None and self.prev_ema_slow is not None:
            # Buy signal: Fast crosses above Slow
            if self.prev_ema_fast <= self.prev_ema_slow and ema_fast > ema_slow:
                signal = 'BUY'
            
            # Sell signal: Fast crosses below Slow
            elif self.prev_ema_fast >= self.prev_ema_slow and ema_fast < ema_slow:
                signal = 'SELL'
        
        # Store for next iteration
        self.prev_ema_fast = ema_fast
        self.prev_ema_slow = ema_slow
        
        return signal
    
    def get_strategy_info(self) -> dict:
        """Return strategy description and parameters."""
        return {
            'name': 'Adaptive EMA v2 - Hourly (1H)',
            'description': 'EMA crossover with volatility-adaptive periods - Hourly timeframe',
            'timeframe': '1H',
            'parameters': {
                'fast_base': self.fast_base,
                'slow_base': self.slow_base,
                'fast_mult': self.fast_mult,
                'slow_mult': self.slow_mult,
                'atr_length': self.atr_length,
                'vol_threshold': self.vol_threshold,
                'vol_length': self.vol_length
            },
            'entry': 'Fast EMA crosses above Slow EMA',
            'exit': 'Fast EMA crosses below Slow EMA',
            'risk_management': 'Longer EMAs in high volatility'
        }


# QuantConnect Algorithm wrapper
class AdaptiveEMAV2QC:
    """
    QuantConnect-compatible algorithm wrapper.
    Deploy this to QuantConnect Cloud.
    """
    
    def Initialize(self):
        """Initialize algorithm."""
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2024, 12, 31)
        self.SetCash(10000)
        
        # Add equity
        self.symbol = self.AddEquity("QQQ", Resolution.Hour).Symbol
        
        # Strategy parameters (hourly timeframe)
        self.fast_base = 8
        self.slow_base = 14
        self.fast_mult = 1.6
        self.slow_mult = 1.0
        self.atr_length = 12
        self.vol_threshold = 69
        self.vol_length = 50
        
        # Rolling windows for indicators
        self.close_window = RollingWindow[float](200)
        self.high_window = RollingWindow[float](200)
        self.low_window = RollingWindow[float](200)
        
        # State
        self.prev_ema_fast = None
        self.prev_ema_slow = None
    
    def OnData(self, data):
        """Handle new data."""
        if not data.ContainsKey(self.symbol):
            return
        
        bar = data[self.symbol]
        
        # Update rolling windows
        self.close_window.Add(bar.Close)
        self.high_window.Add(bar.High)
        self.low_window.Add(bar.Low)
        
        # Need warmup
        warmup = max(self.atr_length, self.vol_length) + 10
        if not self.close_window.IsReady or self.close_window.Count < warmup:
            return
        
        # Calculate ATR
        atr = self.CalculateATR()
        relative_vol = (atr / bar.Close) * 100
        
        # Calculate volatility percentile
        vol_percentile = self.CalculateVolPercentile(relative_vol)
        
        # Determine adaptive periods
        is_high_vol = vol_percentile >= self.vol_threshold
        fast_period = int(self.fast_base * self.fast_mult) if is_high_vol else self.fast_base
        slow_period = int(self.slow_base * self.slow_mult) if is_high_vol else self.slow_base
        
        # Calculate EMAs
        ema_fast = self.CalculateEMA(fast_period)
        ema_slow = self.CalculateEMA(slow_period)
        
        # Generate signals
        if self.prev_ema_fast is not None and self.prev_ema_slow is not None:
            # Buy signal
            if not self.Portfolio.Invested:
                if self.prev_ema_fast <= self.prev_ema_slow and ema_fast > ema_slow:
                    self.SetHoldings(self.symbol, 1.0)
                    self.Debug(f"BUY @ {bar.Close}")
            
            # Sell signal
            else:
                if self.prev_ema_fast >= self.prev_ema_slow and ema_fast < ema_slow:
                    self.Liquidate(self.symbol)
                    self.Debug(f"SELL @ {bar.Close}")
        
        # Store for next iteration
        self.prev_ema_fast = ema_fast
        self.prev_ema_slow = ema_slow
    
    def CalculateATR(self):
        """Calculate Average True Range."""
        tr_values = []
        for i in range(1, self.atr_length + 1):
            high = self.high_window[i-1]
            low = self.low_window[i-1]
            prev_close = self.close_window[i]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_values.append(tr)
        
        return sum(tr_values) / len(tr_values)
    
    def CalculateVolPercentile(self, current_vol):
        """Calculate volatility percentile."""
        vol_values = []
        for i in range(self.vol_length):
            atr = self.CalculateATRAt(i)
            close = self.close_window[i]
            vol_values.append((atr / close) * 100)
        
        count = sum(1 for v in vol_values if v < current_vol)
        return (count / len(vol_values)) * 100
    
    def CalculateATRAt(self, offset):
        """Calculate ATR at specific offset."""
        tr_values = []
        for i in range(offset + 1, offset + self.atr_length + 1):
            if i >= self.high_window.Count:
                break
            high = self.high_window[i-1]
            low = self.low_window[i-1]
            prev_close = self.close_window[i]
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)
        
        return sum(tr_values) / len(tr_values) if tr_values else 0
    
    def CalculateEMA(self, period):
        """Calculate EMA with given period."""
        closes = [self.close_window[i] for i in range(min(period * 3, self.close_window.Count))]
        closes.reverse()
        
        alpha = 2 / (period + 1)
        ema = closes[0]
        
        for close in closes[1:]:
            ema = alpha * close + (1 - alpha) * ema
        
        return ema
