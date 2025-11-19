"""
Data fetcher with Yahoo Finance integration
Includes data cleaning and outlier interpolation
Matches dataFetcher.js functionality
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def fetch_data(ticker: str, target_candles: int = 1500, interval: str = '1h') -> pd.DataFrame:
    """
    Fetch historical data from Yahoo Finance
    
    Args:
        ticker: Stock symbol
        target_candles: Number of candles to return
        interval: Candle interval ('1h', '4h', '1d')
    
    Returns:
        DataFrame with OHLCV data and DatetimeIndex, or None on error
    """
    try:
        # Calculate period needed based on interval (with buffer for weekends/holidays)
        if interval == '1h':
            period = '300d'  # ~300 days for 1h data
        elif interval == '4h':
            period = '500d'  # ~500 days for 4h data
        else:  # '1d'
            period = '730d'  # ~2 years for daily data
        
        # Fetch data
        df = yf.download(
            ticker, 
            period=period, 
            interval=interval, 
            progress=False,
            auto_adjust=False  # Keep original OHLC
        )
        
        if df.empty:
            print(f"   ❌ No data returned for {ticker}")
            return None
        
        # Ensure proper column names (sometimes yfinance returns multi-index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Standardize column names
        df.columns = [col.capitalize() for col in df.columns]
        
        # Filter rows with valid OHLC data
        df = df.dropna(subset=['Close', 'High', 'Low', 'Open'])
        
        if len(df) == 0:
            print(f"   ❌ No valid data after filtering NaN for {ticker}")
            return None
        
        # Clean data: interpolate outliers using rolling median
        df = _clean_outliers(df)
        
        # Limit to target number of candles (most recent)
        if len(df) > target_candles:
            df = df.iloc[-target_candles:]
        
        return df
        
    except Exception as e:
        print(f"   ❌ Error fetching data for {ticker}: {e}")
        return None


def _clean_outliers(df: pd.DataFrame, window_size: int = 10, threshold_pct: float = 15.0) -> pd.DataFrame:
    """
    Clean data by interpolating outliers using rolling median
    
    Args:
        df: DataFrame with OHLCV data
        window_size: Rolling window size for median calculation
        threshold_pct: Deviation percentage threshold to identify outliers
    
    Returns:
        Cleaned DataFrame
    """
    if len(df) < window_size:
        return df
    
    df_clean = df.copy()
    closes = df_clean['Close'].values
    
    # Calculate rolling median
    rolling_median = pd.Series(closes).rolling(window=window_size, center=False).median()
    
    # Identify and interpolate outliers
    for i in range(window_size, len(closes)):
        median = rolling_median.iloc[i]
        if pd.isna(median):
            continue
            
        current_close = closes[i]
        deviation_pct = abs((current_close - median) / median * 100)
        
        # Interpolate if deviation exceeds threshold
        if deviation_pct > threshold_pct:
            # Use average of previous and next close
            prev_close = closes[i - 1]
            next_close = closes[i + 1] if i + 1 < len(closes) else prev_close
            interpolated = (prev_close + next_close) / 2
            
            print(f"   ⚠️  Interpolated bad data: {df.index[i]} - "
                  f"Original: ${current_close:.2f}, Interpolated: ${interpolated:.2f} "
                  f"({deviation_pct:.1f}% deviation from median)")
            
            # Update all OHLC values
            df_clean.loc[df_clean.index[i], 'Close'] = interpolated
            df_clean.loc[df_clean.index[i], 'Open'] = interpolated
            df_clean.loc[df_clean.index[i], 'High'] = max(interpolated, df_clean.iloc[i]['High'])
            df_clean.loc[df_clean.index[i], 'Low'] = min(interpolated, df_clean.iloc[i]['Low'])
    
    return df_clean


if __name__ == '__main__':
    # Test the data fetcher
    print("\n🧪 Testing Data Fetcher\n")
    
    tickers = ['QQQ', 'SPY']
    
    for ticker in tickers:
        print(f"📥 Fetching {ticker} (1h interval, 100 candles)...")
        df = fetch_data(ticker, target_candles=100, interval='1h')
        
        if df is not None:
            print(f"   ✅ Retrieved {len(df)} candles")
            print(f"   Date Range: {df.index[0]} to {df.index[-1]}")
            print(f"   Columns: {list(df.columns)}")
            print(f"   First row:\n{df.head(1)}\n")
        else:
            print(f"   ❌ Failed to fetch {ticker}\n")
