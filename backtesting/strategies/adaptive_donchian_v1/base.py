"""
Adaptive Donchian Breakout Strategy v1
Ported from OpenCL optimization system

Strategy Logic:
- Donchian Channel breakout detection
- ATR-based threshold adjustment for filtering false breakouts
- ADX confirmation for trend strength
- Buy when price breaks above the Donchian high (with filters)
- Sell when price breaks below the Donchian low

Entry: Price > Donchian High + (ATR * multiplier) AND ADX > threshold
Exit: Price < Donchian Low
"""

import pandas as pd
import numpy as np
from typing import Optional
from ..base_strategy import BaseStrategy


class AdaptiveDonchianV1(BaseStrategy):
    """
    Adaptive Donchian Breakout Strategy v1 - QuantConnect Implementation
    
    Parameters:
        donchian_length: Period for Donchian Channel calculation (default: 20)
        atr_length: ATR calculation period (default: 14)
        atr_multiplier: Multiplier for ATR threshold (default: 0.5)
        adx_length: ADX calculation period (default: 14)
        adx_threshold: Minimum ADX for entry (default: 20)
    """
    
    def __init__(self, 
                 donchian_length: int = 20,
                 atr_length: int = 14,
                 atr_multiplier: float = 0.0,
                 adx_length: int = 14,
                 adx_threshold: float = 0.0,
                 **kwargs):
        
        super().__init__(
            donchian_length=donchian_length,
            atr_length=atr_length,
            atr_multiplier=atr_multiplier,
            adx_length=adx_length,
            adx_threshold=adx_threshold,
            **kwargs
        )
        
        # Store parameters
        self.donchian_length = donchian_length
        self.atr_length = atr_length
        self.atr_multiplier = atr_multiplier
        self.adx_length = adx_length
        self.adx_threshold = adx_threshold
        
        # Validate parameters
        if donchian_length < 5:
            raise ValueError("Donchian length must be >= 5")
        if atr_length < 5:
            raise ValueError("ATR length must be >= 5")
        if atr_multiplier < 0:
            raise ValueError("ATR multiplier must be >= 0")
        if adx_threshold < 0:
            raise ValueError("ADX threshold must be >= 0")
    
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
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators needed for the strategy.
        
        Adds columns:
        - donchian_high: Highest high over donchian_length periods
        - donchian_low: Lowest low over donchian_length periods
        - atr: Average True Range
        - adx: Average Directional Index
        - breakout_threshold: Price threshold for valid breakout (Donchian High + ATR * multiplier)
        """
        # Calculate Donchian Channel
        data['donchian_high'] = data['high'].rolling(window=self.donchian_length).max()
        data['donchian_low'] = data['low'].rolling(window=self.donchian_length).min()
        
        # Calculate ATR
        data['atr'] = self.calculate_atr(data)
        
        # Calculate ADX
        data['adx'] = self.calculate_adx(data)
        
        # Calculate breakout threshold (Donchian High + ATR * multiplier)
        data['breakout_threshold'] = data['donchian_high'] + (data['atr'] * self.atr_multiplier)
        
        return data
    
    def generate_signals(self, data: pd.DataFrame, idx: int) -> Optional[str]:
        """
        Generate buy/sell signals based on Donchian breakouts with filters.
        
        Entry: High > Donchian High + (ATR * multiplier) AND ADX > threshold
        Exit: Low < Donchian Low
        """
        # Need warmup period
        warmup = max(self.donchian_length, self.atr_length, self.adx_length) + 10
        if idx < warmup:
            return None
        
        current_bar = data.iloc[idx]
        high = current_bar['high']
        low = current_bar['low']
        
        # Use previous bar's Donchian values to avoid lookahead bias
        prev_bar = data.iloc[idx-1]
        donchian_high = prev_bar['donchian_high']
        donchian_low = prev_bar['donchian_low']
        breakout_threshold = prev_bar['breakout_threshold']
        adx = current_bar['adx']
        
        signal = None
        
        # Buy signal: High breaks above threshold with ADX confirmation
        if self.position == 0:
            if high > breakout_threshold and adx >= self.adx_threshold:
                signal = 'BUY'
        
        # Sell signal: Low breaks below Donchian Low
        elif self.position > 0:
            if low < donchian_low:
                signal = 'SELL'
        
        return signal
    
    def get_strategy_info(self) -> dict:
        """Return strategy description and parameters."""
        return {
            'name': 'Adaptive Donchian v1',
            'description': 'Donchian Channel breakout with ATR-based threshold and ADX confirmation',
            'parameters': {
                'donchian_length': self.donchian_length,
                'atr_length': self.atr_length,
                'atr_multiplier': self.atr_multiplier,
                'adx_length': self.adx_length,
                'adx_threshold': self.adx_threshold
            },
            'entry': 'Price > Donchian High + (ATR * multiplier) AND ADX > threshold',
            'exit': 'Price < Donchian Low',
            'risk_management': 'ATR-based breakout filter, ADX trend strength confirmation'
        }
