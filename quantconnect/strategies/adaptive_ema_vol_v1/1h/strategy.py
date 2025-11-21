"""
Adaptive EMA with Volume Strategy v1
Ported from OpenCL optimization system

Strategy Logic:
- Adaptive EMA pairs based on volatility (from v2.1)
- Volume analysis for confirmation
- Market regime detection using RSI
- ADX for trend strength confirmation

Entry: Fast EMA crosses above Slow EMA AND ADX > threshold AND RSI in trending range AND Volume > MA
Exit: Fast EMA crosses below Slow EMA
"""

import pandas as pd
import numpy as np
from typing import Optional
from ...base_strategy import BaseStrategy


class AdaptiveEMAVolV1(BaseStrategy):
    """
    Adaptive EMA with Volume Strategy v1 - QuantConnect Implementation
    
    Parameters:
        fast_base: Base fast EMA period (default: 9)
        slow_base: Base slow EMA period (default: 10)
        fast_mult: Fast EMA multiplier in high volatility (default: 1.4)
        slow_mult: Slow EMA multiplier in high volatility (default: 1.0)
        atr_length: ATR calculation period (default: 12)
        vol_threshold: Volatility percentile threshold (default: 65)
        vol_length: Volatility lookback period (default: 50)
        adx_length: ADX calculation period (default: 7)
        adx_threshold: Minimum ADX for entry (default: 11.0)
        rsi_length: RSI calculation period (default: 14)
        rsi_trending_min: Minimum RSI for bullish trend (default: 40)
        rsi_trending_max: Maximum RSI for bullish trend (default: 70)
        volume_ma_length: Volume MA period (default: 20)
    """
    
    def __init__(self, 
                 fast_base: int = 8,
                 slow_base: int = 12,
                 fast_mult: float = 1.6,
                 slow_mult: float = 1.2,
                 atr_length: int = 12,
                 vol_threshold: int = 60,
                 vol_length: int = 50,
                 adx_length: int = 7,
                 adx_threshold: float = 8.0,
                 rsi_length: int = 14,
                 rsi_trending_min: int = 35,
                 rsi_trending_max: int = 75,
                 volume_ma_length: int = 20,
                 **kwargs):
        
        super().__init__(
            fast_base=fast_base,
            slow_base=slow_base,
            fast_mult=fast_mult,
            slow_mult=slow_mult,
            atr_length=atr_length,
            vol_threshold=vol_threshold,
            vol_length=vol_length,
            adx_length=adx_length,
            adx_threshold=adx_threshold,
            rsi_length=rsi_length,
            rsi_trending_min=rsi_trending_min,
            rsi_trending_max=rsi_trending_max,
            volume_ma_length=volume_ma_length,
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
        self.adx_length = adx_length
        self.adx_threshold = adx_threshold
        self.rsi_length = rsi_length
        self.rsi_trending_min = rsi_trending_min
        self.rsi_trending_max = rsi_trending_max
        self.volume_ma_length = volume_ma_length
        
        # Validate parameters
        if fast_base >= slow_base:
            raise ValueError(f"fast_base ({fast_base}) must be < slow_base ({slow_base})")
        if fast_mult < 1.0 or slow_mult < 1.0:
            raise ValueError("Multipliers must be >= 1.0")
        if adx_threshold < 0:
            raise ValueError("ADX threshold must be >= 0")
        if rsi_trending_min >= rsi_trending_max:
            raise ValueError("RSI trending_min must be < trending_max")
        
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
    
    def calculate_adx(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average Directional Index."""
        high = data['high']
        low = data['low']
        
        # Calculate directional movement
        high_diff = high.diff()
        low_diff = -low.diff()
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        # Smooth directional movements
        plus_dm_smooth = pd.Series(plus_dm, index=data.index).ewm(span=self.adx_length, adjust=False).mean()
        minus_dm_smooth = pd.Series(minus_dm, index=data.index).ewm(span=self.adx_length, adjust=False).mean()
        
        # Calculate ATR for ADX
        atr = self.calculate_atr(data)
        
        # Calculate directional indicators
        plus_di = 100 * plus_dm_smooth / atr
        minus_di = 100 * minus_dm_smooth / atr
        
        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # Calculate ADX (smoothed DX)
        adx = dx.ewm(span=self.adx_length, adjust=False).mean()
        
        return adx
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Relative Strength Index."""
        close = data['close']
        delta = close.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.rsi_length).mean()
        avg_loss = loss.rolling(window=self.rsi_length).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
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
        - adx: Average Directional Index
        - rsi: Relative Strength Index
        - volume_ma: Volume moving average
        - fast_period: Adaptive fast EMA period
        - slow_period: Adaptive slow EMA period
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
        
        # Calculate ADX
        data['adx'] = self.calculate_adx(data)
        
        # Calculate RSI
        data['rsi'] = self.calculate_rsi(data)
        
        # Calculate volume MA
        data['volume_ma'] = data['volume'].rolling(window=self.volume_ma_length).mean()
        
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
        Generate buy/sell signals based on EMA crossover with multiple confirmations.
        
        Entry: Fast EMA crosses above Slow EMA AND ADX > threshold AND RSI in trending range AND Volume > MA
        Exit: Fast EMA crosses below Slow EMA
        """
        # Need warmup period
        warmup = max(self.atr_length, self.vol_length, self.adx_length, 
                     self.rsi_length, self.volume_ma_length) + 10
        if idx < warmup:
            return None
        
        # Get current adaptive periods
        fast_period = int(data.iloc[idx]['fast_period'])
        slow_period = int(data.iloc[idx]['slow_period'])
        
        # Get current indicators
        adx = data.iloc[idx]['adx']
        rsi = data.iloc[idx]['rsi']
        volume = data.iloc[idx]['volume']
        volume_ma = data.iloc[idx]['volume_ma']
        
        # Calculate EMAs with adaptive periods
        closes_up_to_now = data['close'].iloc[:idx+1]
        ema_fast = self.calculate_ema(closes_up_to_now, fast_period)
        ema_slow = self.calculate_ema(closes_up_to_now, slow_period)
        
        # Detect crossovers
        signal = None
        
        if self.prev_ema_fast is not None and self.prev_ema_slow is not None:
            # Buy signal: Fast crosses above Slow with all confirmations
            if self.prev_ema_fast <= self.prev_ema_slow and ema_fast > ema_slow:
                if (adx >= self.adx_threshold and 
                    self.rsi_trending_min <= rsi <= self.rsi_trending_max and 
                    volume > volume_ma):
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
            'name': 'Adaptive EMA with Volume v1',
            'description': 'EMA crossover with volatility-adaptive periods, ADX, RSI and volume filters',
            'parameters': {
                'fast_base': self.fast_base,
                'slow_base': self.slow_base,
                'fast_mult': self.fast_mult,
                'slow_mult': self.slow_mult,
                'atr_length': self.atr_length,
                'vol_threshold': self.vol_threshold,
                'vol_length': self.vol_length,
                'adx_length': self.adx_length,
                'adx_threshold': self.adx_threshold,
                'rsi_length': self.rsi_length,
                'rsi_trending_min': self.rsi_trending_min,
                'rsi_trending_max': self.rsi_trending_max,
                'volume_ma_length': self.volume_ma_length
            },
            'entry': 'Fast EMA crosses above Slow EMA AND ADX > threshold AND RSI in trending range AND Volume > MA',
            'exit': 'Fast EMA crosses below Slow EMA',
            'risk_management': 'Longer EMAs in high volatility, ADX filter, RSI range, volume confirmation'
        }
