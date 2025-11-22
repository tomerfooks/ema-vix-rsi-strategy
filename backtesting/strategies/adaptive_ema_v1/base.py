"""
Adaptive EMA Strategy v1 - Base Implementation

Volatility-adaptive EMA crossover strategy that adjusts EMA lengths based on
market volatility regime (low/medium/high). Matches proven Pine Script implementation.

Strategy Logic:
1. Calculate normalized ATR volatility
2. Rank current volatility against historical window (percentile)
3. Select EMA pair based on volatility regime:
   - Low volatility (<25%): Fast EMAs (12/80) for responsiveness
   - Medium volatility (25-73%): Medium EMAs (25/108) for balance
   - High volatility (>73%): Slow EMAs (38/120) for stability
4. Generate signals on EMA crossovers
5. Enter long on bullish crossover, exit on bearish crossover
"""

import pandas as pd
import numpy as np
from ..base_strategy import BaseStrategy


class AdaptiveEmaV1Strategy(BaseStrategy):
    """
    Adaptive Volatility EMA Crossover Strategy
    
    Uses ATR-based volatility percentile ranking to adaptively select
    appropriate EMA lengths for different market conditions.
    """
    
    def __init__(self, params: dict):
        """
        Initialize strategy with parameters
        
        Args:
            params: Dictionary containing strategy parameters:
                - fast_length_low: Fast EMA for low volatility (default: 12)
                - slow_length_low: Slow EMA for low volatility (default: 80)
                - fast_length_med: Fast EMA for medium volatility (default: 25)
                - slow_length_med: Slow EMA for medium volatility (default: 108)
                - fast_length_high: Fast EMA for high volatility (default: 38)
                - slow_length_high: Slow EMA for high volatility (default: 120)
                - atr_length: ATR period (default: 14)
                - volatility_length: Volatility lookback window (default: 63)
                - low_vol_percentile: Low volatility threshold (default: 25)
                - high_vol_percentile: High volatility threshold (default: 73)
        """
        # Initialize base class
        initial_capital = params.pop('initial_capital', 10000)
        super().__init__(initial_capital=initial_capital)
        
        # Extract parameters with defaults matching Pine Script
        self.fast_low = params.get('fast_length_low', 12)
        self.slow_low = params.get('slow_length_low', 80)
        self.fast_med = params.get('fast_length_med', 25)
        self.slow_med = params.get('slow_length_med', 108)
        self.fast_high = params.get('fast_length_high', 38)
        self.slow_high = params.get('slow_length_high', 120)
        
        self.atr_length = params.get('atr_length', 14)
        self.vol_length = params.get('volatility_length', 63)
        self.low_pct = params.get('low_vol_percentile', 25)
        self.high_pct = params.get('high_vol_percentile', 73)
        
        # Validation
        assert self.fast_low < self.slow_low, "Fast EMA must be < Slow EMA (low vol)"
        assert self.fast_med < self.slow_med, "Fast EMA must be < Slow EMA (med vol)"
        assert self.fast_high < self.slow_high, "Fast EMA must be < Slow EMA (high vol)"
        assert self.low_pct < self.high_pct, "Low percentile must be < High percentile"
        
        # Cache for indicators (calculated once per run)
        self.indicators_df = None
    
    def calculate_ema(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()
    
    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Average True Range
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            
        Returns:
            Series of ATR values
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        # True Range is max of the three
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR is EMA of True Range
        atr = tr.ewm(span=self.atr_length, adjust=False).mean()
        
        return atr
    
    def calculate_volatility_percentile(self, normalized_atr: pd.Series) -> pd.Series:
        """
        Calculate volatility percentile rank (matches Pine Script logic)
        
        For each bar, counts how many values in the lookback window are <= current value,
        then calculates percentile as (count / window_size) * 100
        
        Args:
            normalized_atr: Series of normalized ATR values (ATR / close * 100)
            
        Returns:
            Series of percentile ranks (0-100)
        """
        percentiles = pd.Series(index=normalized_atr.index, dtype=float)
        
        for i in range(len(normalized_atr)):
            if i < self.vol_length:
                percentiles.iloc[i] = 50.0  # Default to medium volatility during warmup
                continue
            
            # Get lookback window
            window = normalized_atr.iloc[i - self.vol_length:i]
            current_value = normalized_atr.iloc[i]
            
            # Count values <= current value
            count_below = (window <= current_value).sum()
            
            # Calculate percentile: (count / window_size) * 100
            percentile = (count_below / self.vol_length) * 100.0
            percentiles.iloc[i] = percentile
        
        return percentiles
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators needed for signal generation.
        
        Args:
            data: DataFrame with OHLCV columns
            
        Returns:
            DataFrame with indicators added
        """
        df = data.copy()
        
        # Calculate ATR and normalize by price
        atr = self.calculate_atr(df)
        df['atr'] = atr
        df['normalized_atr'] = (atr / df['close']) * 100
        
        # Calculate volatility percentile rank
        df['vol_percentile'] = self.calculate_volatility_percentile(df['normalized_atr'])
        
        # Calculate all EMAs
        ema_fast_low = self.calculate_ema(df['close'], self.fast_low)
        ema_slow_low = self.calculate_ema(df['close'], self.slow_low)
        ema_fast_med = self.calculate_ema(df['close'], self.fast_med)
        ema_slow_med = self.calculate_ema(df['close'], self.slow_med)
        ema_fast_high = self.calculate_ema(df['close'], self.fast_high)
        ema_slow_high = self.calculate_ema(df['close'], self.slow_high)
        
        # Select EMAs based on volatility regime
        ema_fast_values = []
        ema_slow_values = []
        regime_values = []
        
        for i in range(len(df)):
            pct = df['vol_percentile'].iloc[i]
            
            if pct < self.low_pct:
                # Low volatility - use faster EMAs
                ema_fast_values.append(ema_fast_low.iloc[i])
                ema_slow_values.append(ema_slow_low.iloc[i])
                regime_values.append('low')
            elif pct >= self.high_pct:
                # High volatility - use slower EMAs
                ema_fast_values.append(ema_fast_high.iloc[i])
                ema_slow_values.append(ema_slow_high.iloc[i])
                regime_values.append('high')
            else:
                # Medium volatility - use medium EMAs
                ema_fast_values.append(ema_fast_med.iloc[i])
                ema_slow_values.append(ema_slow_med.iloc[i])
                regime_values.append('medium')
        
        df['ema_fast'] = ema_fast_values
        df['ema_slow'] = ema_slow_values
        df['volatility_regime'] = regime_values
        
        # Cache for use in generate_signals
        self.indicators_df = df
        
        return df
    
    def generate_signals(self, data: pd.DataFrame, idx: int) -> str:
        """
        Generate trading signal at specific index.
        
        Args:
            data: DataFrame with indicators (from calculate_indicators)
            idx: Index to check for signal
            
        Returns:
            'BUY', 'SELL', or None
        """
        # Use cached indicators if available, otherwise calculate
        if self.indicators_df is None:
            df = self.calculate_indicators(data)
        else:
            df = self.indicators_df
        
        # Need at least 2 bars for crossover detection
        if idx < 1:
            return None
        
        # Get current and previous values
        curr_fast = df['ema_fast'].iloc[idx]
        curr_slow = df['ema_slow'].iloc[idx]
        prev_fast = df['ema_fast'].iloc[idx - 1]
        prev_slow = df['ema_slow'].iloc[idx - 1]
        
        # Check for NaN
        if pd.isna(curr_fast) or pd.isna(curr_slow) or pd.isna(prev_fast) or pd.isna(prev_slow):
            return None
        
        # Bullish crossover: fast crosses above slow
        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return 'BUY'
        
        # Bearish crossunder: fast crosses below slow
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return 'SELL'
        
        return None
    
    def get_strategy_name(self) -> str:
        """Return strategy name"""
        return f"Adaptive_EMA_v1_{self.fast_low}_{self.slow_low}_{self.fast_med}_{self.slow_med}_{self.fast_high}_{self.slow_high}"
    
    def get_strategy_info(self) -> dict:
        """Return strategy information for display"""
        return {
            'name': 'Adaptive EMA v1',
            'description': 'Volatility-adaptive EMA crossover with regime detection',
            'parameters': self.get_parameters()
        }
    
    def get_parameters(self) -> dict:
        """Return current strategy parameters"""
        return {
            'fast_length_low': self.fast_low,
            'slow_length_low': self.slow_low,
            'fast_length_med': self.fast_med,
            'slow_length_med': self.slow_med,
            'fast_length_high': self.fast_high,
            'slow_length_high': self.slow_high,
            'atr_length': self.atr_length,
            'volatility_length': self.vol_length,
            'low_vol_percentile': self.low_pct,
            'high_vol_percentile': self.high_pct
        }
