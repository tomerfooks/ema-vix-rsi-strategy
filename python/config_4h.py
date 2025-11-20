"""
Configuration for 4-hour interval optimization
"""

# Strategy default parameters
DEFAULT_PARAMS = {
    # Low Volatility
    'fast_length_low': 12,
    'slow_length_low': 60,
    
    # Medium Volatility
    'fast_length_med': 20,
    'slow_length_med': 75,
    
    # High Volatility
    'fast_length_high': 35,
    'slow_length_high': 95,
    
    # Volatility Settings
    'volatility_length': 50,
    'atr_length': 14,
    'low_vol_percentile': 27,
    'high_vol_percentile': 68,
    
    # Backtest settings
    'initial_capital': 10000
}

# Optimization Configuration
OPTIMIZATION_CONFIG = {
    'symbols': ['QQQ'],
    'candles': 270,
    'interval': '4h',
    'num_workers': None,
    'batch_size': 5000,
    'param_ranges': {
        'fast_length_low': 0.03,
        'slow_length_low': 0.03,
        'fast_length_med': 0.03,
        'slow_length_med': 0.03,
        'fast_length_high': 0.03,
        'slow_length_high': 0.03,
        'atr_length': 0.03,
        'volatility_length': 0.03,
        'low_vol_percentile': 0.02,
        'high_vol_percentile': 0.02
    },
    'range_percent': 0.05,
    'progress_update_interval': 5.0
}
