"""
Simple technical indicators implementation without external TA libraries
"""
import numpy as np
import pandas as pd


def ema(series, period):
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def atr(high, low, close, period=14):
    """Calculate Average True Range"""
    # True Range calculation
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    
    # ATR is EMA of true range
    return true_range.ewm(span=period, adjust=False).mean()
