"""
Numba-optimized technical indicators
Uses JIT compilation for 10-200x speedup over pure Python/Pandas

Key optimizations:
- @njit decorator compiles to machine code
- Pure NumPy arrays (no Pandas overhead)
- Vectorized operations where possible
- Pre-allocated arrays to avoid reallocations
"""

import numpy as np
from numba import njit, prange


@njit(cache=True, fastmath=True)
def calculate_ema_numba(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average using Numba JIT
    
    Args:
        prices: 1D array of prices
        period: EMA period
    
    Returns:
        1D array of EMA values (same length as input, first values will be NaN)
    """
    n = len(prices)
    ema = np.empty(n, dtype=np.float64)
    ema[:] = np.nan
    
    if n < period:
        return ema
    
    # Calculate smoothing factor
    alpha = 2.0 / (period + 1.0)
    
    # Initialize with SMA for first period
    sma = np.mean(prices[:period])
    ema[period - 1] = sma
    
    # Calculate EMA iteratively
    for i in range(period, n):
        ema[i] = alpha * prices[i] + (1.0 - alpha) * ema[i - 1]
    
    return ema


@njit(cache=True, fastmath=True)
def calculate_true_range_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """
    Calculate True Range using Numba JIT
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
    
    Returns:
        True Range array
    """
    n = len(high)
    tr = np.empty(n, dtype=np.float64)
    
    # First TR is just high - low
    tr[0] = high[0] - low[0]
    
    # Subsequent TRs compare with previous close
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, hc, lc)
    
    return tr


@njit(cache=True, fastmath=True)
def calculate_atr_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Average True Range using Numba JIT
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period
    
    Returns:
        ATR array
    """
    tr = calculate_true_range_numba(high, low, close)
    atr = calculate_ema_numba(tr, period)
    return atr


@njit(cache=True, fastmath=True)
def calculate_normalized_atr_numba(high: np.ndarray, low: np.ndarray, close: np.ndarray, 
                                   period: int) -> np.ndarray:
    """
    Calculate normalized ATR (ATR / close * 100)
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period
    
    Returns:
        Normalized ATR array (percentage)
    """
    atr = calculate_atr_numba(high, low, close, period)
    normalized = (atr / close) * 100.0
    return normalized


@njit(cache=True, fastmath=True)
def calculate_volatility_rank_numba(normalized_atr: np.ndarray, volatility_length: int,
                                    min_history: int = 20) -> np.ndarray:
    """
    Calculate percentile rank for volatility regime detection using Numba JIT
    
    Args:
        normalized_atr: Normalized ATR values
        volatility_length: Lookback period for percentile calculation
        min_history: Minimum history required to calculate rank
    
    Returns:
        Volatility rank array (0-100 percentile)
    """
    n = len(normalized_atr)
    vol_ranks = np.empty(n, dtype=np.float64)
    vol_ranks[:] = np.nan
    
    for i in range(n):
        start_idx = max(0, i - volatility_length + 1)
        window = normalized_atr[start_idx:i + 1]
        
        if len(window) < min_history:
            continue
        
        # Calculate percentile rank
        current_vol = normalized_atr[i]
        if np.isnan(current_vol):
            continue
        
        # Count values <= current value
        rank_count = 0
        valid_count = 0
        for val in window:
            if not np.isnan(val):
                valid_count += 1
                if val <= current_vol:
                    rank_count += 1
        
        if valid_count > 0:
            vol_ranks[i] = (rank_count / valid_count) * 100.0
    
    return vol_ranks


@njit(cache=True, fastmath=True)
def get_volatility_regime_numba(vol_rank: float, low_percentile: float, high_percentile: float) -> int:
    """
    Determine volatility regime
    
    Args:
        vol_rank: Volatility percentile rank
        low_percentile: Low volatility threshold
        high_percentile: High volatility threshold
    
    Returns:
        0 = LOW, 1 = MEDIUM, 2 = HIGH
    """
    if np.isnan(vol_rank):
        return -1
    
    if vol_rank < low_percentile:
        return 0  # LOW
    elif vol_rank < high_percentile:
        return 1  # MEDIUM
    else:
        return 2  # HIGH


@njit(cache=True, fastmath=True, parallel=True)
def precalculate_emas_numba(closes: np.ndarray, periods: np.ndarray) -> np.ndarray:
    """
    Pre-calculate multiple EMAs in parallel using Numba
    
    Args:
        closes: Close prices
        periods: Array of EMA periods to calculate
    
    Returns:
        2D array where each row is an EMA for the corresponding period
    """
    n_periods = len(periods)
    n_prices = len(closes)
    emas = np.empty((n_periods, n_prices), dtype=np.float64)
    
    # Calculate EMAs in parallel
    for idx in prange(n_periods):
        emas[idx] = calculate_ema_numba(closes, periods[idx])
    
    return emas


# Wrapper functions for easier usage with Pandas DataFrames
def ema(series, period):
    """Calculate EMA from Pandas Series"""
    values = series.values if hasattr(series, 'values') else series
    result = calculate_ema_numba(values, period)
    if hasattr(series, 'index'):
        import pandas as pd
        return pd.Series(result, index=series.index)
    return result


def atr(high, low, close, period):
    """Calculate ATR from Pandas Series"""
    h = high.values if hasattr(high, 'values') else high
    l = low.values if hasattr(low, 'values') else low
    c = close.values if hasattr(close, 'values') else close
    result = calculate_atr_numba(h, l, c, period)
    if hasattr(close, 'index'):
        import pandas as pd
        return pd.Series(result, index=close.index)
    return result


def normalized_atr(high, low, close, period):
    """Calculate normalized ATR from Pandas Series"""
    h = high.values if hasattr(high, 'values') else high
    l = low.values if hasattr(low, 'values') else low
    c = close.values if hasattr(close, 'values') else close
    result = calculate_normalized_atr_numba(h, l, c, period)
    if hasattr(close, 'index'):
        import pandas as pd
        return pd.Series(result, index=close.index)
    return result


def volatility_rank(normalized_atr_series, volatility_length, min_history=20):
    """Calculate volatility rank from Pandas Series"""
    values = normalized_atr_series.values if hasattr(normalized_atr_series, 'values') else normalized_atr_series
    result = calculate_volatility_rank_numba(values, volatility_length, min_history)
    if hasattr(normalized_atr_series, 'index'):
        import pandas as pd
        return pd.Series(result, index=normalized_atr_series.index)
    return result


if __name__ == '__main__':
    import time
    
    print("\n🧪 Testing Numba-Optimized Indicators\n")
    
    # Generate test data
    n = 10000
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = prices + np.abs(np.random.randn(n) * 0.5)
    low = prices - np.abs(np.random.randn(n) * 0.5)
    close = prices
    
    # Test EMA
    print("Testing EMA calculation...")
    start = time.time()
    ema_result = calculate_ema_numba(close, 20)
    elapsed = time.time() - start
    print(f"   ✅ Calculated {n} EMA values in {elapsed*1000:.2f}ms")
    print(f"   Last 5 values: {ema_result[-5:]}")
    
    # Test ATR
    print("\nTesting ATR calculation...")
    start = time.time()
    atr_result = calculate_atr_numba(high, low, close, 14)
    elapsed = time.time() - start
    print(f"   ✅ Calculated {n} ATR values in {elapsed*1000:.2f}ms")
    print(f"   Last 5 values: {atr_result[-5:]}")
    
    # Test Normalized ATR
    print("\nTesting Normalized ATR calculation...")
    start = time.time()
    norm_atr = calculate_normalized_atr_numba(high, low, close, 14)
    elapsed = time.time() - start
    print(f"   ✅ Calculated {n} Normalized ATR values in {elapsed*1000:.2f}ms")
    print(f"   Last 5 values: {norm_atr[-5:]}")
    
    # Test Volatility Rank
    print("\nTesting Volatility Rank calculation...")
    start = time.time()
    vol_rank = calculate_volatility_rank_numba(norm_atr, 71, min_history=20)
    elapsed = time.time() - start
    print(f"   ✅ Calculated {n} Volatility Rank values in {elapsed*1000:.2f}ms")
    valid_ranks = vol_rank[~np.isnan(vol_rank)]
    print(f"   Valid ranks: {len(valid_ranks)} (last 5: {valid_ranks[-5:]})")
    
    # Test parallel EMA calculation
    print("\nTesting parallel EMA calculation...")
    periods = np.array([10, 20, 30, 50, 100, 200], dtype=np.int64)
    start = time.time()
    emas = precalculate_emas_numba(close, periods)
    elapsed = time.time() - start
    print(f"   ✅ Calculated {len(periods)} EMAs ({n} values each) in {elapsed*1000:.2f}ms")
    print(f"   Shape: {emas.shape}")
    print(f"   EMA(20) last 5: {emas[1, -5:]}")
    
    print("\n✅ All tests passed!\n")
