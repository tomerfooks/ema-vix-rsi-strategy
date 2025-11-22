"""1H timeframe strategy configuration for Adaptive EMA v1"""

from ..base import AdaptiveEmaV1Strategy


def create_strategy(params: dict = None) -> AdaptiveEmaV1Strategy:
    """
    Create 1H Adaptive EMA strategy instance with default parameters
    
    Default parameters match proven Pine Script values:
    - Fast Low: 12, Slow Low: 80 (Low volatility)
    - Fast Med: 25, Slow Med: 108 (Medium volatility)
    - Fast High: 38, Slow High: 120 (High volatility)
    - ATR: 14, Volatility Window: 63
    - Low %ile: 25, High %ile: 73
    """
    default_params = {
        'fast_length_low': 12,
        'slow_length_low': 80,
        'fast_length_med': 25,
        'slow_length_med': 108,
        'fast_length_high': 38,
        'slow_length_high': 120,
        'atr_length': 14,
        'volatility_length': 63,
        'low_vol_percentile': 25,
        'high_vol_percentile': 73
    }
    
    if params:
        default_params.update(params)
    
    return AdaptiveEmaV1Strategy(default_params)


__all__ = ['create_strategy']
