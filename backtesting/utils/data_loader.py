"""
Data loading utilities for backtesting
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional
import os
import glob
from pathlib import Path


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
    cache_dir: str = './data',
    source: str = 'alpaca'
) -> pd.DataFrame:
    """
    Load historical data from Alpaca (preferred) or Yahoo Finance (fallback).
    Caches data locally and reuses if less than 24 hours old.
    
    Args:
        symbol: Ticker symbol
        start_date: Start date (defaults to 1 year ago)
        end_date: End date (defaults to today)
        interval: Data interval
        cache_dir: Directory for cached data
        source: Data source ('alpaca', 'yahoo', or 'auto' for smart selection)
    
    Returns:
        DataFrame with OHLCV data
    """
    # Set default dates
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Create cache directory if it doesn't exist
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    # Check for cached data
    cached_df = _check_cache(symbol, start_date, end_date, interval, cache_dir)
    if cached_df is not None:
        print(f"Using cached data ({len(cached_df)} bars)")
        return cached_df
    
    # Try Alpaca first if source is 'auto' or 'alpaca'
    if source in ['auto', 'alpaca']:
        try:
            from .alpaca_loader import load_alpaca_data
            
            # Check if API keys are available (with hardcoded fallback)
            has_keys = bool(
                os.environ.get('ALPACA_API_KEY', 'PKMAR3VY5HO7ERI6A2EAVIUYM2') and 
                os.environ.get('ALPACA_SECRET_KEY', 'e4PcTCF9rhCNnaizeXGQxfhGja2RuF2bbdGq5WyJKs2')
            )
            
            if has_keys:
                print("Using Alpaca data source...")
                df = load_alpaca_data(symbol, start_date, end_date, interval)
                _save_to_cache(df, symbol, start_date, end_date, interval, cache_dir)
                return df
            elif source == 'alpaca':
                raise ValueError("Alpaca API keys not found. Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables.")
            else:
                print("Alpaca API keys not found, falling back to Yahoo Finance...")
        except ImportError:
            if source == 'alpaca':
                raise ImportError("alpaca-py not installed. Install with: pip install alpaca-py")
            else:
                print("alpaca-py not installed, using Yahoo Finance...")
        except Exception as e:
            if source == 'alpaca':
                raise
            else:
                print(f"Alpaca failed ({e}), falling back to Yahoo Finance...")
    
    # Fall back to Yahoo Finance
    if source in ['auto', 'yahoo']:
        df = download_yahoo_data(symbol, start_date, end_date, interval)
        _save_to_cache(df, symbol, start_date, end_date, interval, cache_dir)
        return df
    
    raise ValueError(f"Unknown data source: {source}. Use 'alpaca', 'yahoo', or 'auto'.")


def _get_cache_filename(symbol: str, start_date: str, end_date: str, interval: str) -> str:
    """
    Generate cache filename with timestamp.
    Format: YYYYMMDD_HHMMSS_SYMBOL_INTERVAL_STARTDATE_ENDDATE.csv
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    symbol_lower = symbol.lower()
    start_clean = start_date.replace('-', '')
    end_clean = end_date.replace('-', '')
    return f"{timestamp}_{symbol_lower}_{interval}_{start_clean}_{end_clean}.csv"


def _check_cache(symbol: str, start_date: str, end_date: str, interval: str, cache_dir: str) -> Optional[pd.DataFrame]:
    """
    Check for cached data that matches parameters and is less than 24 hours old.
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return None
    
    symbol_lower = symbol.lower()
    start_clean = start_date.replace('-', '')
    end_clean = end_date.replace('-', '')
    
    # Pattern to match: *_SYMBOL_INTERVAL_STARTDATE_ENDDATE.csv
    pattern = f"*_{symbol_lower}_{interval}_{start_clean}_{end_clean}.csv"
    matching_files = list(cache_path.glob(pattern))
    
    if not matching_files:
        return None
    
    # Get the most recent file
    matching_files.sort(reverse=True)  # Sort by filename (timestamp is in the name)
    latest_file = matching_files[0]
    
    # Extract timestamp from filename
    filename = latest_file.name
    timestamp_str = filename.split('_')[0] + '_' + filename.split('_')[1]
    
    try:
        file_timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        age_hours = (datetime.now() - file_timestamp).total_seconds() / 3600
        
        if age_hours < 24:
            print(f"Found cached data from {file_timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({age_hours:.1f} hours ago)")
            df = pd.read_csv(latest_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            print(f"Cached data is {age_hours:.1f} hours old (>24h), fetching fresh data...")
            # Delete old cache file
            latest_file.unlink()
            # Delete any other old files for this symbol/interval/date range
            for old_file in matching_files:
                try:
                    old_file.unlink()
                except:
                    pass
            return None
    except (ValueError, IndexError):
        # Invalid filename format, ignore
        return None


def _save_to_cache(df: pd.DataFrame, symbol: str, start_date: str, end_date: str, interval: str, cache_dir: str) -> None:
    """
    Save DataFrame to cache with timestamped filename.
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    filename = _get_cache_filename(symbol, start_date, end_date, interval)
    filepath = cache_path / filename
    
    df.to_csv(filepath, index=False)
    print(f"Cached data saved to {filepath}")


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
