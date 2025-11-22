#!/usr/bin/env python3
"""
Fetch historical market data using Alpaca API
Usage: python3 fetch_data.py TICKER INTERVAL CANDLES
Example: python3 fetch_data.py GOOG 1h 600

Implements 24-hour caching to avoid redundant API calls
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

# Hardcoded Alpaca API credentials
ALPACA_API_KEY = 'PKMAR3VY5HO7ERI6A2EAVIUYM2'
ALPACA_SECRET_KEY = 'e4PcTCF9rhCNnaizeXGQxfhGja2RuF2bbdGq5WyJKs2'


def _get_cache_filename(ticker: str, interval: str, num_candles: int) -> str:
    """
    Generate cache filename with timestamp.
    Format: YYYYMMDD_HHMMSS_TICKER_INTERVAL_CANDLES.csv
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ticker_lower = ticker.lower()
    return f"{timestamp}_{ticker_lower}_{interval}_{num_candles}.csv"


def _check_cache(ticker: str, interval: str, num_candles: int, cache_dir: str = 'data') -> tuple:
    """
    Check for cached data that matches parameters and is less than 24 hours old.
    
    Returns:
        (DataFrame or None, cache_filepath or None)
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return None, None
    
    ticker_lower = ticker.lower()
    
    # Pattern to match: *_TICKER_INTERVAL_CANDLES.csv
    pattern = f"*_{ticker_lower}_{interval}_{num_candles}.csv"
    matching_files = list(cache_path.glob(pattern))
    
    if not matching_files:
        # Also check for files that have more candles than requested (still usable)
        pattern_any = f"*_{ticker_lower}_{interval}_*.csv"
        all_files = list(cache_path.glob(pattern_any))
        
        # Filter for files with >= requested candles
        matching_files = []
        for f in all_files:
            try:
                file_candles = int(f.stem.split('_')[-1])
                if file_candles >= num_candles:
                    matching_files.append(f)
            except (ValueError, IndexError):
                continue
    
    if not matching_files:
        return None, None
    
    # Get the most recent file
    matching_files.sort(reverse=True)  # Sort by filename (timestamp is in the name)
    latest_file = matching_files[0]
    
    # Extract timestamp from filename
    filename = latest_file.name
    try:
        timestamp_str = filename.split('_')[0] + '_' + filename.split('_')[1]
        file_timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
        age_hours = (datetime.now() - file_timestamp).total_seconds() / 3600
        
        if age_hours < 24:
            print(f"📦 Found cached data from {file_timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({age_hours:.1f}h ago)")
            df = pd.read_csv(latest_file)
            
            # If we need fewer candles than cached, just use what we need
            if len(df) > num_candles + 50:  # +50 for warmup
                df = df.tail(num_candles + 50)
                print(f"   Using {len(df)} most recent candles from cache")
            
            return df, latest_file
        else:
            print(f"   Cached data is {age_hours:.1f}h old (>24h), fetching fresh data...")
            # Delete old cache file
            latest_file.unlink()
            # Delete any other old files for this ticker/interval
            for old_file in matching_files:
                try:
                    old_file.unlink()
                except:
                    pass
            return None, None
    except (ValueError, IndexError):
        # Invalid filename format, ignore
        return None, None


def _save_to_cache(df: pd.DataFrame, ticker: str, interval: str, num_candles: int, cache_dir: str = 'data') -> str:
    """
    Save DataFrame to cache with timestamped filename.
    Returns the filepath of the saved cache file.
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    filename = _get_cache_filename(ticker, interval, num_candles)
    filepath = cache_path / filename
    
    df.to_csv(filepath, index=False, header=True)
    return str(filepath)

def fetch_data(ticker, interval, num_candles):
    """Fetch historical data from Alpaca and save to CSV (with 24h caching)"""
    
    # Add warmup period buffer (50 candles needed for indicators)
    WARMUP_PERIOD = 50
    num_candles_with_warmup = num_candles + WARMUP_PERIOD
    
    # Check cache first
    cached_df, cache_file = _check_cache(ticker, interval, num_candles_with_warmup)
    if cached_df is not None:
        # Use the standard filename for compatibility with OpenCL code
        ticker_lower = ticker.lower()
        filename = f"data/{ticker_lower}_{interval}.csv"
        
        # If cache file is not the standard filename, copy it
        if str(cache_file) != filename:
            cached_df.to_csv(filename, index=False, header=True)
            print(f"   ✅ Copied to {filename} for OpenCL compatibility")
        else:
            print(f"   ✅ Using {filename}")
        
        # Show date range
        if 'Timestamp' in cached_df.columns:
            first_ts = pd.to_datetime(cached_df['Timestamp'].iloc[0], unit='s')
            last_ts = pd.to_datetime(cached_df['Timestamp'].iloc[-1], unit='s')
            print(f"   Date range: {first_ts.strftime('%Y-%m-%d')} to {last_ts.strftime('%Y-%m-%d')}")
        
        return True
    
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    except ImportError:
        print("❌ alpaca-py is required. Install with: pip install alpaca-py")
        return False
    
    # Map intervals to Alpaca TimeFrame
    interval_map = {
        '1h': (TimeFrame(1, TimeFrameUnit.Hour), num_candles_with_warmup / 24),
        '4h': (TimeFrame(4, TimeFrameUnit.Hour), num_candles_with_warmup / 6),
        '1d': (TimeFrame(1, TimeFrameUnit.Day), num_candles_with_warmup)
    }
    
    if interval not in interval_map:
        print(f"❌ Invalid interval: {interval}")
        print("   Valid intervals: 1h, 4h, 1d")
        return False
    
    timeframe, days_needed = interval_map[interval]
    
    # Calculate date range (Alpaca has data since 2016)
    # Use generous buffer to ensure we get enough candles
    days_needed = int(days_needed * 1.8) + 30
    end_date = datetime.now()  # Get data up to current time
    start_date = max(
        end_date - timedelta(days=days_needed),
        datetime(2016, 1, 1)  # Alpaca data starts from 2016
    )
    
    print(f"📡 Fetching {ticker} data from Alpaca...")
    print(f"   Interval: {interval}")
    print(f"   Requested: {num_candles} candles (+{WARMUP_PERIOD} warmup)")
    print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # Initialize Alpaca client with IEX feed (free tier friendly)
        client = StockHistoricalDataClient(
            ALPACA_API_KEY, 
            ALPACA_SECRET_KEY,
            url_override="https://data.alpaca.markets"  # Use IEX data feed for free tier
        )
        
        # Create request (use IEX feed for free tier)
        request_params = StockBarsRequest(
            symbol_or_symbols=ticker,
            timeframe=timeframe,
            start=start_date,
            end=end_date,
            limit=10000,  # Maximum allowed on free tier
            adjustment='split',
            feed='iex'  # Use IEX feed instead of SIP (free tier compatible)
        )
        
        # Fetch data
        bars = client.get_stock_bars(request_params)
        
        if ticker not in bars.data or len(bars.df) == 0:
            print(f"❌ No data returned for {ticker}")
            return False
        
        # Convert to DataFrame
        df = bars.df
        
        # Alpaca returns MultiIndex DataFrame, flatten it
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index()
            if 'symbol' in df.columns:
                df = df[df['symbol'] == ticker].drop('symbol', axis=1)
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
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        if df['timestamp'].dt.tz is not None:
            df['timestamp'] = df['timestamp'].dt.tz_localize(None)
        
        # Set timestamp as index
        df = df.set_index('timestamp')
        
        # Limit to requested number of candles (including warmup)
        df = df.tail(num_candles_with_warmup)
        
        # Warn if we got fewer candles than requested
        if len(df) < num_candles_with_warmup:
            print(f"   ⚠️  Only {len(df)} candles available")
        
        # Prepare data for CSV
        df['Timestamp'] = df.index.astype(int) // 10**9  # Convert to Unix timestamp
        
        # Rename columns to match expected format (capitalize first letter)
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        df = df[['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Save to cache with timestamped filename
        cache_filepath = _save_to_cache(df, ticker, interval, num_candles_with_warmup)
        
        # Also save to standard filename for OpenCL compatibility
        ticker_lower = ticker.lower()
        filename = f"data/{ticker_lower}_{interval}.csv"
        if cache_filepath != filename:
            df.to_csv(filename, index=False, header=True)
        
        print(f"   ✅ Saved {len(df)} candles to {filename}")
        print(f"   📦 Cached as {cache_filepath}")
        print(f"   Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 fetch_data.py TICKER INTERVAL CANDLES")
        print("Example: python3 fetch_data.py GOOG 1h 600")
        sys.exit(1)
    
    ticker = sys.argv[1].upper()
    interval = sys.argv[2].lower()
    candles = int(sys.argv[3])
    
    success = fetch_data(ticker, interval, candles)
    sys.exit(0 if success else 1)
