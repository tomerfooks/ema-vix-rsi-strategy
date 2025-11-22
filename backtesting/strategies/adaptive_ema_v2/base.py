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
from ..base_strategy import BaseStrategy


class AdaptiveEMAV2(BaseStrategy):
    """
    Adaptive EMA Strategy v2 - QuantConnect Implementation
    
    Parameters:
        fast_base: Base fast EMA period (default: 15)
        slow_base: Base slow EMA period (default: 18)
        fast_mult: Fast EMA multiplier in high volatility (default: 2.0)
        slow_mult: Slow EMA multiplier in high volatility (default: 1.4)
        atr_length: ATR calculation period (default: 12)
        vol_threshold: Volatility percentile threshold (default: 65)
        vol_length: Volatility lookback period (default: 50)
    """
    
    def __init__(self, 
                 fast_base: int = 15,
                 slow_base: int = 18,
                 fast_mult: float = 2.0,
                 slow_mult: float = 1.4,
                 atr_length: int = 12,
                 vol_threshold: int = 65,
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
            'name': 'Adaptive EMA v2',
            'description': 'EMA crossover with volatility-adaptive periods',
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
