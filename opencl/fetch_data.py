#!/usr/bin/env python3
"""
Fetch historical market data using yfinance
Usage: python3 fetch_data.py TICKER INTERVAL CANDLES
Example: python3 fetch_data.py GOOG 1h 600
"""

import sys
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_data(ticker, interval, num_candles):
    """Fetch historical data and save to CSV"""
    
    # Map intervals to yfinance format and calculate period
    # yfinance limits: 1h = 730 days max, 1d = no limit, 4h via 1h data
    interval_map = {
        '1h': ('1h', num_candles / 24, 730, 3500),    # (yf_interval, days_calc, max_days, max_candles)
        '4h': ('1h', num_candles / 6, 730, 875),      # 4h from 1h data, ~875 4h candles max
        '1d': ('1d', num_candles, 18250, 18250)       # ~50 years, effectively unlimited
    }
    
    if interval not in interval_map:
        print(f"❌ Invalid interval: {interval}")
        print("   Valid intervals: 1h, 4h, 1d")
        return False
    
    yf_interval, days_needed, max_days, max_candles = interval_map[interval]
    
    # For 1h/4h intervals, always use maximum available period (730 days)
    # to get as many candles as possible, then limit after fetching
    if interval in ['1h', '4h']:
        print(f"📡 Fetching {ticker} data...")
        print(f"   Interval: {interval}")
        print(f"   Requested: {num_candles} candles")
        print(f"   Fetching maximum available period (730 days)...")
        days_needed = max_days
    else:
        # For daily data, calculate actual days needed
        days_needed = int(min(days_needed * 1.5, max_days)) + 10
        print(f"📡 Fetching {ticker} data...")
        print(f"   Interval: {interval}")
        print(f"   Candles requested: {num_candles}")
    
    try:
        # Fetch data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_needed)
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, interval=yf_interval)
        
        if df.empty:
            print(f"❌ No data returned for {ticker}")
            return False
        
        # Resample for 4h if needed
        if interval == '4h':
            df = df.resample('4h').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
        
        # Limit to requested number of candles
        df = df.tail(num_candles)
        
        # Warn if we got fewer candles than requested
        if len(df) < num_candles and interval in ['1h', '4h']:
            print(f"   ⚠️  Only {len(df)} candles available (yfinance 730-day limit)")
            print(f"   Maximum for {interval}: ~{max_candles} candles")
        
        # Prepare data for CSV
        df['Timestamp'] = df.index.astype(int) // 10**9  # Convert to Unix timestamp
        df = df[['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Create data directory if it doesn't exist
        import os
        os.makedirs('data', exist_ok=True)
        
        # Save to CSV
        ticker_lower = ticker.lower()
        filename = f"data/{ticker_lower}_{interval}.csv"
        df.to_csv(filename, index=False, header=True)
        
        print(f"   ✅ Saved {len(df)} candles to {filename}")
        print(f"   Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
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
