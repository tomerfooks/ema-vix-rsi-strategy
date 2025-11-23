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
    
    # For standard filename compatibility
    ticker_lower = ticker.lower()
    standard_filename = f"data/{ticker_lower}_{interval}.csv"
    
    # Check if standard file exists and is recent enough
    if os.path.exists(standard_filename):
        try:
            df_existing = pd.read_csv(standard_filename)
            if len(df_existing) > 0 and 'Timestamp' in df_existing.columns:
                last_timestamp = df_existing['Timestamp'].iloc[-1]
                last_date = pd.to_datetime(last_timestamp, unit='s')
                yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
                
                # Check if data is up to yesterday
                if last_date.date() >= yesterday.date():
                    print(f"📦 Found existing data in {standard_filename}")
                    print(f"   {len(df_existing)} candles available")
                    print(f"   Date range: {pd.to_datetime(df_existing['Timestamp'].iloc[0], unit='s').strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
                    
                    # If we need fewer candles, just use what we need
                    if len(df_existing) >= num_candles + 50:
                        print(f"   ✅ Data is current and sufficient")
                        return True
                    else:
                        print(f"   ⚠️  Data exists but only has {len(df_existing)} candles (need {num_candles + 50})")
                else:
                    print(f"   ⚠️  Data exists but is outdated (last: {last_date.strftime('%Y-%m-%d')})")
        except Exception as e:
            print(f"   ⚠️  Error reading existing file: {e}")
    
    # Add warmup period buffer (50 candles needed for indicators)
    WARMUP_PERIOD = 50
    num_candles_with_warmup = num_candles + WARMUP_PERIOD
    
    # Check cache first (for timestamped files)
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
        '15m': (TimeFrame(15, TimeFrameUnit.Minute), num_candles_with_warmup / 96),
        '1h': (TimeFrame(1, TimeFrameUnit.Hour), num_candles_with_warmup / 24),
        '4h': (TimeFrame(4, TimeFrameUnit.Hour), num_candles_with_warmup / 6),
        '1d': (TimeFrame(1, TimeFrameUnit.Day), num_candles_with_warmup)
    }
    
    if interval not in interval_map:
        print(f"❌ Invalid interval: {interval}")
        print("   Valid intervals: 15m, 1h, 4h, 1d")
        return False
    
    timeframe, days_needed = interval_map[interval]
    
    # Calculate date range
    # For 15m data, fetch all available data from 2016 to yesterday
    # For other intervals, use the existing logic
    end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)  # Yesterday
    
    if interval == '15m':
        # For 15m, always fetch from 2016 to yesterday (all available data)
        start_date = datetime(2016, 1, 1)
        print(f"📡 Fetching ALL {ticker} {interval} data from Alpaca (SIP feed)...")
    else:
        # For other intervals, calculate based on requested candles
        days_needed = int(days_needed * 1.8) + 30
        start_date = max(
            end_date - timedelta(days=days_needed),
            datetime(2016, 1, 1)
        )
        print(f"📡 Fetching {ticker} data from Alpaca...")
    
    print(f"   Interval: {interval}")
    print(f"   Requested: {num_candles} candles (+{WARMUP_PERIOD} warmup)")
    print(f"   Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        # Initialize Alpaca client
        # Use SIP feed for 15m data (has historical data from 2016)
        # Use IEX feed for other intervals (free tier friendly)
        use_sip = (interval == '15m')
        
        client = StockHistoricalDataClient(
            ALPACA_API_KEY, 
            ALPACA_SECRET_KEY,
            url_override="https://data.alpaca.markets"
        )
        
        # Create request
        feed_type = 'sip' if use_sip else 'iex'
        request_params = StockBarsRequest(
            symbol_or_symbols=ticker,
            timeframe=timeframe,
            start=start_date,
            end=end_date,
            limit=10000,  # Maximum allowed on free tier
            adjustment='split',
            feed=feed_type
        )
        
        # Fetch data (may need multiple requests for 15m data)
        all_dfs = []
        current_start = start_date
        
        while current_start < end_date:
            request_params = StockBarsRequest(
                symbol_or_symbols=ticker,
                timeframe=timeframe,
                start=current_start,
                end=end_date,
                limit=10000,
                adjustment='split',
                feed=feed_type
            )
            
            bars = client.get_stock_bars(request_params)
            
            if ticker not in bars.data or len(bars.df) == 0:
                if len(all_dfs) == 0:
                    print(f"❌ No data returned for {ticker}")
                    return False
                else:
                    # We got some data in previous chunks, break
                    break
            
            # Convert to DataFrame
            df_chunk = bars.df
            
            # Alpaca returns MultiIndex DataFrame, flatten it
            if isinstance(df_chunk.index, pd.MultiIndex):
                df_chunk = df_chunk.reset_index()
                if 'symbol' in df_chunk.columns:
                    df_chunk = df_chunk[df_chunk['symbol'] == ticker].drop('symbol', axis=1)
            else:
                df_chunk = df_chunk.reset_index()
            
            # Standardize column names
            df_chunk.columns = [c.lower() for c in df_chunk.columns]
            
            # Rename timestamp column
            if 'timestamp' not in df_chunk.columns:
                for col in ['datetime', 'date', 'index']:
                    if col in df_chunk.columns:
                        df_chunk = df_chunk.rename(columns={col: 'timestamp'})
                        break
            
            # Ensure timestamp is datetime
            df_chunk['timestamp'] = pd.to_datetime(df_chunk['timestamp'])
            if df_chunk['timestamp'].dt.tz is not None:
                df_chunk['timestamp'] = df_chunk['timestamp'].dt.tz_localize(None)
            
            all_dfs.append(df_chunk)
            
            # Check if we got less than the limit (means we got all data)
            if len(df_chunk) < 10000:
                break
            
            # Update start date for next chunk (add 1 second to avoid duplicates)
            current_start = df_chunk['timestamp'].iloc[-1] + timedelta(seconds=1)
            print(f"   Fetched {len(df_chunk)} bars, continuing from {current_start.strftime('%Y-%m-%d')}...")
        
        # Combine all chunks
        if len(all_dfs) == 0:
            print(f"❌ No data returned for {ticker}")
            return False
        
        df = pd.concat(all_dfs, ignore_index=True)
        
        # Remove duplicates based on timestamp
        df = df.drop_duplicates(subset=['timestamp'], keep='first')
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Set timestamp as index
        df = df.set_index('timestamp')
        
        # For non-15m intervals, limit to requested number of candles (including warmup)
        # For 15m, keep all data
        if interval != '15m':
            df = df.tail(num_candles_with_warmup)
        
        # Warn if we got fewer candles than requested (only for non-15m)
        if interval != '15m' and len(df) < num_candles_with_warmup:
            print(f"   ⚠️  Only {len(df)} candles available")
        
        print(f"   ✅ Retrieved {len(df)} total bars")
        
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
        
        # Save to cache with timestamped filename (only if not 15m with all data)
        if interval != '15m':
            cache_filepath = _save_to_cache(df, ticker, interval, num_candles_with_warmup)
            print(f"   📦 Cached as {cache_filepath}")
        
        # Always save to standard filename for OpenCL compatibility
        ticker_lower = ticker.lower()
        filename = f"data/{ticker_lower}_{interval}.csv"
        df.to_csv(filename, index=False, header=True)
        
        print(f"   ✅ Saved {len(df)} candles to {filename}")
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
