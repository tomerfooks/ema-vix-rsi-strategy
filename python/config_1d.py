"""
Configuration for 1-day interval optimization
"""

# Strategy default parameters
DEFAULT_PARAMS = {
    # Low Volatility
    'fast_length_low': 8,
    'slow_length_low': 40,
    
    # Medium Volatility
    'fast_length_med': 15,
    'slow_length_med': 50,
    
    # High Volatility
    'fast_length_high': 20,
    'slow_length_high': 60,
    
    # Volatility Settings
    'volatility_length': 30,
    'atr_length': 10,
    'low_vol_percentile': 25,
    'high_vol_percentile': 70,
    
    # Backtest settings
    'initial_capital': 10000
}

# Optimization Configuration
OPTIMIZATION_CONFIG = {
    'symbols': ['QQQ'],
    'candles': 150,              # ~5 months of daily data
    'interval': '1d',
    'num_workers': None,
    'batch_size': 5000,
    'param_ranges': {
        'fast_length_low': 0.3,
        'slow_length_low': 0.3,
        'fast_length_med': 0.3,
        'slow_length_med': 0.3,
        'fast_length_high': 0.3,
        'slow_length_high': 0.3,
        'atr_length': 0.3,
        'volatility_length': 0.3,
        'low_vol_percentile': 0.3,
        'high_vol_percentile': 0.3
    },
    'range_percent': 0.3,
    'progress_update_interval': 5.0
}
