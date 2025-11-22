"""1D timeframe strategy configuration for Adaptive EMA v1"""

from ..base import AdaptiveEmaV1Strategy


def create_strategy(params: dict = None) -> AdaptiveEmaV1Strategy:
    """
    Create 1D Adaptive EMA strategy instance with default parameters
    
    Adjusted for daily timeframe (longer EMAs, longer lookback)
    """
    default_params = {
        'fast_length_low': 8,
        'slow_length_low': 50,
        'fast_length_med': 15,
        'slow_length_med': 70,
        'fast_length_high': 25,
        'slow_length_high': 90,
        'atr_length': 14,
        'volatility_length': 50,
        'low_vol_percentile': 25,
        'high_vol_percentile': 75
    }
    
    if params:
        default_params.update(params)
    
    return AdaptiveEmaV1Strategy(default_params)


__all__ = ['create_strategy']
