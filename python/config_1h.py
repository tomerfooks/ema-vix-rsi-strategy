"""
Configuration for 1-hour interval optimization
Matches JS config-1h.js structure
"""

# Strategy default parameters from strategy-1h.pine
DEFAULT_PARAMS = {
    # Low Volatility
    'fast_length_low': 13,
    'slow_length_low': 70,
    
    # Medium Volatility
    'fast_length_med': 23,
    'slow_length_med': 98,
    
    # High Volatility
    'fast_length_high': 43,
    'slow_length_high': 122,
    
    # Volatility Settings
    'volatility_length': 69,
    'atr_length': 15,
    'low_vol_percentile': 28,
    'high_vol_percentile': 64,
    
    # Backtest settings
    'initial_capital': 10000
}

# Optimization Configuration
OPTIMIZATION_CONFIG = {
    # Data settings
    'symbols': ['QQQ'],           # Symbols to optimize (can be list)
    'candles': 300,               # Number of candles to fetch
    'interval': '1h',             # Candle interval: '1h', '4h', '1d'
    
    # Multiprocessing settings
    'num_workers': None,          # None = use all CPU cores, or specify number (e.g., 4, 8)
    'batch_size': 5000,           # Number of parameter combinations per worker batch
    
    # Parameter ranges - control each parameter individually
    # Options: None = use range_percent, float = use as percentage, [min, max] = explicit range
    'param_ranges': {
        'fast_length_low': 0.05,      # 0.03 = ±3% from default (14) = [13, 14, 15]
        'slow_length_low': 0.03,      # 0.03 = ±3% from default (80) = [77, 78, ..., 83]
        'fast_length_med': 0.05,      # Or: [20, 30] to test all integers 20-30
        'slow_length_med': 0.03,      # Or: None to use range_percent
        'fast_length_high': 0.05,
        'slow_length_high': 0.03,
        'atr_length': 0.03,          # 0.01 = ±1% from default (16) = [16, 17]
        'volatility_length': 0.02,
        'low_vol_percentile': 0.02,
        'high_vol_percentile': 0.03
    },
    'range_percent': 0.05,         # ±5% from default values (used when param_ranges[param] is None)
    
    # Performance
    'progress_update_interval': 5.0  # Console update interval in seconds
}
