"""
Data loading utilities for backtesting
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import os


def download_yahoo_data(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = '1h'
) -> pd.DataFrame:
    """
    Download historical data from Yahoo Finance.
    
    Args:
        symbol: Ticker symbol (e.g., 'QQQ')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        interval: Data interval ('1h', '1d', '5m', etc.)
    
    Returns:
        DataFrame with OHLCV data
    """
    from datetime import datetime, timedelta
    
    # Yahoo Finance hourly data limitation check
    if interval in ['1h', '60m', '90m']:
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        days_requested = (end_dt - start_dt).days
        
        if days_requested > 729:
            max_start = (end_dt - timedelta(days=729)).strftime('%Y-%m-%d')
            print(f"⚠️  Yahoo Finance limits hourly data to ~730 days")
            print(f"   Adjusting start date from {start_date} to {max_start}")
            start_date = max_start
    
    print(f"Downloading {symbol} data from {start_date} to {end_date} ({interval})...")
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    
    if df.empty:
        raise ValueError(f"No data returned for {symbol}. Try using daily interval (1d) for longer periods.")
    
    # Standardize column names
    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]
    
    # Rename datetime column to timestamp
    if 'datetime' in df.columns:
        df = df.rename(columns={'datetime': 'timestamp'})
    elif 'date' in df.columns:
        df = df.rename(columns={'date': 'timestamp'})
    
    # Select relevant columns
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    print(f"Downloaded {len(df)} bars")
    return df


def load_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = '1h',
    cache_dir: str = './data'
) -> pd.DataFrame:
    """
    Load historical data.
    
    Args:
        symbol: Ticker symbol
        start_date: Start date (defaults to 1 year ago)
        end_date: End date (defaults to today)
        interval: Data interval
        cache_dir: Directory for cached data (unused, kept for compatibility)
    
    Returns:
        DataFrame with OHLCV data
    """
    # Set default dates
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Download data directly without caching
    df = download_yahoo_data(symbol, start_date, end_date, interval)
    
    return df


def load_opencl_data(filepath: str) -> pd.DataFrame:
    """
    Load data from OpenCL data directory.
    
    Args:
        filepath: Path to CSV file in opencl/data/
    
    Returns:
        DataFrame in standard format
    """
    df = pd.read_csv(filepath)
    
    # Standardize format
    if 'Datetime' in df.columns:
        df = df.rename(columns={'Datetime': 'timestamp'})
    
    df.columns = [c.lower() for c in df.columns]
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]


def resample_data(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """
    Resample data to different timeframe.
    
    Args:
        df: OHLCV DataFrame
        interval: Target interval ('1h', '4h', '1d')
    
    Returns:
        Resampled DataFrame
    """
    df = df.set_index('timestamp')
    
    resampled = df.resample(interval).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    return resampled.reset_index()


def align_opencl_data(symbol: str, interval: str, opencl_data_dir: str = '../opencl/data') -> pd.DataFrame:
    """
    Load the exact same data used in OpenCL backtests.
    
    Args:
        symbol: Ticker symbol
        interval: Interval ('1h', '4h', '1d')
        opencl_data_dir: Path to OpenCL data directory
    
    Returns:
        DataFrame matching OpenCL data
    """
    filename = f"{symbol.lower()}_{interval}.csv"
    filepath = os.path.join(opencl_data_dir, filename)
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"OpenCL data file not found: {filepath}")
    
    return load_opencl_data(filepath)
