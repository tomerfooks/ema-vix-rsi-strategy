"""
Alpaca data loading utilities for backtesting
Provides access to historical data with better limits than yfinance:
- Historical data since 2016
- Up to 10,000 bars per request
- 200 requests/min on free tier
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import os


def download_alpaca_data(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = '1h',
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    limit: int = 10000,
    adjustment: str = 'split'
) -> pd.DataFrame:
    """
    Download historical data from Alpaca Markets API.
    
    Args:
        symbol: Ticker symbol (e.g., 'QQQ')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        interval: Data interval ('1Min', '5Min', '15Min', '1Hour', '1Day', etc.)
                  Alpaca format: [1-59]Min, [1-23]Hour, 1Day, 1Week, [1,2,3,4,6,12]Month
        api_key: Alpaca API key (if not provided, will try env var ALPACA_API_KEY)
        secret_key: Alpaca secret key (if not provided, will try env var ALPACA_SECRET_KEY)
        limit: Maximum number of bars to fetch per request (max: 10000)
        adjustment: Price adjustment ('raw', 'split', 'dividend', 'all')
    
    Returns:
        DataFrame with OHLCV data
    """
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    except ImportError:
        raise ImportError(
            "alpaca-py is required for Alpaca data loading. "
            "Install it with: pip install alpaca-py"
        )
    
    # Get API keys from environment if not provided
    # Hardcoded API keys (fallback if not passed as arguments)
    if api_key is None:
        api_key = os.environ.get('ALPACA_API_KEY', 'PKMAR3VY5HO7ERI6A2EAVIUYM2')
    if secret_key is None:
        secret_key = os.environ.get('ALPACA_SECRET_KEY', 'e4PcTCF9rhCNnaizeXGQxfhGja2RuF2bbdGq5WyJKs2')
    
    if not api_key or not secret_key:
        raise ValueError(
            "Alpaca API credentials required. Either pass them as arguments or set "
            "ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables."
        )
    
    # Convert interval to Alpaca TimeFrame format
    timeframe = _convert_interval_to_timeframe(interval)
    
    # Parse dates
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)
    
    # Validate date range (Alpaca has data since 2016)
    min_date = pd.to_datetime('2016-01-01')
    if start_dt < min_date:
        print(f"⚠️  Alpaca data starts from 2016-01-01")
        print(f"   Adjusting start date from {start_date} to 2016-01-01")
        start_dt = min_date
    
    print(f"Downloading {symbol} data from Alpaca ({start_dt.date()} to {end_dt.date()}, {interval})...")
    
    # Initialize client
    client = StockHistoricalDataClient(api_key, secret_key)
    
    # Create request (use IEX feed for free tier compatibility)
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start_dt,
        end=end_dt,
        limit=limit,
        adjustment=adjustment,
        feed='iex'  # Use IEX feed instead of SIP (free tier compatible)
    )
    
    # Fetch data
    bars = client.get_stock_bars(request_params)
    
    # Convert to DataFrame
    if symbol in bars.data:
        df = bars.df
        
        # Alpaca returns MultiIndex DataFrame, flatten it
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index()
            if 'symbol' in df.columns:
                df = df[df['symbol'] == symbol].drop('symbol', axis=1)
        else:
            df = df.reset_index()
        
        # Standardize column names
        df.columns = [c.lower() for c in df.columns]
        
        # Rename timestamp column
        if 'timestamp' not in df.columns:
            for col in ['datetime', 'date', 'index']:
                if col in df.columns:
                    df = df.rename(columns={col: 'timestamp'})
                    break
        
        # Ensure timestamp is timezone-naive (consistent with yfinance)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if df['timestamp'].dt.tz is not None:
                df['timestamp'] = df['timestamp'].dt.tz_localize(None)
        
        # Select and order columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        available_cols = [col for col in required_cols if col in df.columns]
        df = df[available_cols]
        
        # Remove any NaN values
        df = df.dropna()
        
        print(f"Downloaded {len(df)} bars from Alpaca")
        
        if len(df) == limit:
            print(f"⚠️  Reached limit of {limit} bars. Data may be incomplete.")
            print(f"   Consider fetching data in smaller date ranges or increasing limit.")
        
        return df
    else:
        raise ValueError(f"No data returned for {symbol} from Alpaca")


def _convert_interval_to_timeframe(interval: str):
    """
    Convert common interval formats to Alpaca TimeFrame.
    
    Supports:
    - '1m', '5m', '15m', '30m' -> Minutes
    - '1h', '2h', '4h' -> Hours  
    - '1d' -> Day
    - '1w' -> Week
    - '1M' -> Month
    """
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    
    interval = interval.lower().strip()
    
    # Parse the interval
    if interval.endswith('min') or interval.endswith('m'):
        # Minutes
        value = interval.rstrip('minm')
        if value == '':
            value = '1'
        return TimeFrame(int(value), TimeFrameUnit.Minute)
    
    elif interval.endswith('hour') or interval.endswith('h'):
        # Hours
        value = interval.rstrip('hourh')
        if value == '':
            value = '1'
        return TimeFrame(int(value), TimeFrameUnit.Hour)
    
    elif interval.endswith('d') or interval.endswith('day'):
        # Days
        return TimeFrame(1, TimeFrameUnit.Day)
    
    elif interval.endswith('w') or interval.endswith('week'):
        # Weeks
        return TimeFrame(1, TimeFrameUnit.Week)
    
    elif interval.endswith('mo') or interval.upper().endswith('M'):
        # Months
        value = interval.rstrip('moM')
        if value == '':
            value = '1'
        return TimeFrame(int(value), TimeFrameUnit.Month)
    
    else:
        raise ValueError(
            f"Unsupported interval format: {interval}. "
            f"Supported: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1M"
        )


def load_alpaca_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = '1h',
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    adjustment: str = 'split'
) -> pd.DataFrame:
    """
    Load historical data from Alpaca with smart pagination.
    
    Args:
        symbol: Ticker symbol
        start_date: Start date (defaults to 2 years ago)
        end_date: End date (defaults to today)
        interval: Data interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
        api_key: Alpaca API key (optional if env var set)
        secret_key: Alpaca secret key (optional if env var set)
        adjustment: Price adjustment type
    
    Returns:
        DataFrame with OHLCV data
    """
    # Set default dates
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        # Default to 2 years ago (much better than yfinance's ~730 day limit)
        start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
    
    # Download data
    df = download_alpaca_data(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        interval=interval,
        api_key=api_key,
        secret_key=secret_key,
        limit=10000,  # Use maximum allowed on free tier
        adjustment=adjustment
    )
    
    return df


def test_alpaca_connection(api_key: Optional[str] = None, secret_key: Optional[str] = None) -> bool:
    """
    Test Alpaca API connection.
    
    Args:
        api_key: Alpaca API key (optional if env var set)
        secret_key: Alpaca secret key (optional if env var set)
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        
        # Get API keys (with hardcoded fallback)
        if api_key is None:
            api_key = os.environ.get('ALPACA_API_KEY', 'PKMAR3VY5HO7ERI6A2EAVIUYM2')
        if secret_key is None:
            secret_key = os.environ.get('ALPACA_SECRET_KEY', 'e4PcTCF9rhCNnaizeXGQxfhGja2RuF2bbdGq5WyJKs2')
        
        if not api_key or not secret_key:
            print("❌ API credentials not found")
            return False
        
        # Try to initialize client
        client = StockHistoricalDataClient(api_key, secret_key)
        
        # Try a simple request (use IEX feed for free tier)
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
        
        request = StockBarsRequest(
            symbol_or_symbols='SPY',
            timeframe=TimeFrame(1, TimeFrameUnit.Day),
            start=(datetime.now() - timedelta(days=7)),
            limit=5,
            feed='iex'  # Use IEX feed for free tier
        )
        
        bars = client.get_stock_bars(request)
        
        if bars and len(bars.df) > 0:
            print("✅ Alpaca connection successful!")
            print(f"   Fetched {len(bars.df)} test bars")
            return True
        else:
            print("❌ Connection succeeded but no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Alpaca connection failed: {e}")
        return False


if __name__ == '__main__':
    """Test the Alpaca loader"""
    import sys
    
    print("=" * 70)
    print("Alpaca Data Loader Test")
    print("=" * 70)
    print()
    
    # Test connection
    if not test_alpaca_connection():
        print()
        print("Please set your Alpaca API credentials:")
        print("  export ALPACA_API_KEY='your_key_here'")
        print("  export ALPACA_SECRET_KEY='your_secret_here'")
        print()
        print("Get your free API keys at: https://alpaca.markets/")
        sys.exit(1)
    
    print()
    print("Testing data download...")
    print()
    
    # Test downloading data
    try:
        df = load_alpaca_data(
            symbol='QQQ',
            start_date='2023-01-01',
            end_date='2024-01-01',
            interval='1h'
        )
        
        print()
        print(f"✅ Successfully loaded {len(df)} bars")
        print()
        print("Sample data:")
        print(df.head())
        print()
        print(df.tail())
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        sys.exit(1)
