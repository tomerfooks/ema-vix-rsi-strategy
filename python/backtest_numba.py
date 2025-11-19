"""
Numba-optimized backtest engine
Uses JIT compilation for the core strategy loop (10-100x speedup)
"""

import numpy as np
import pandas as pd
from numba import njit
from typing import Dict, List, Tuple
import time

from indicators_numba import (
    calculate_ema_numba,
    calculate_normalized_atr_numba,
    calculate_volatility_rank_numba,
    get_volatility_regime_numba
)
from data_fetcher import fetch_data


@njit(cache=True, fastmath=True)
def run_strategy_numba(
    closes: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    ema_low_fast: np.ndarray,
    ema_low_slow: np.ndarray,
    ema_med_fast: np.ndarray,
    ema_med_slow: np.ndarray,
    ema_high_fast: np.ndarray,
    ema_high_slow: np.ndarray,
    vol_ranks: np.ndarray,
    low_vol_percentile: float,
    high_vol_percentile: float,
    initial_capital: float,
    start_idx: int
) -> Tuple[np.ndarray, np.ndarray, float, float, float, int, int]:
    """
    Core strategy loop compiled with Numba for maximum speed
    
    Returns:
        - trade_entries: indices of trade entries
        - trade_exits: indices of trade exits
        - final_equity: final portfolio value
        - max_drawdown: maximum drawdown percentage
        - early_return: return at midpoint (for filtering)
        - total_trades: number of completed trades
        - position_open: 1 if position is still open, 0 otherwise
    """
    n = len(closes)
    
    # Pre-allocate trade arrays (max possible trades = n/2)
    max_trades = n // 2
    trade_entries = np.empty(max_trades, dtype=np.int64)
    trade_exits = np.empty(max_trades, dtype=np.int64)
    trade_entry_prices = np.empty(max_trades, dtype=np.float64)
    trade_exit_prices = np.empty(max_trades, dtype=np.float64)
    trade_shares = np.empty(max_trades, dtype=np.float64)
    
    trade_count = 0
    position_entry_idx = -1
    position_entry_price = 0.0
    position_shares = 0.0
    
    capital = initial_capital
    equity = capital
    peak_equity = capital
    max_drawdown = 0.0
    early_return = 0.0
    mid_point = (n - start_idx) // 2 + start_idx
    
    for i in range(start_idx, n - 1):
        # Skip if volatility rank not available
        if np.isnan(vol_ranks[i]):
            continue
        
        # Determine regime
        regime = get_volatility_regime_numba(vol_ranks[i], low_vol_percentile, high_vol_percentile)
        if regime < 0:
            continue
        
        # Select EMAs based on regime
        if regime == 0:  # LOW
            fast_ema = ema_low_fast[i]
            slow_ema = ema_low_slow[i]
            prev_fast = ema_low_fast[i - 1]
            prev_slow = ema_low_slow[i - 1]
        elif regime == 1:  # MEDIUM
            fast_ema = ema_med_fast[i]
            slow_ema = ema_med_slow[i]
            prev_fast = ema_med_fast[i - 1]
            prev_slow = ema_med_slow[i - 1]
        else:  # HIGH
            fast_ema = ema_high_fast[i]
            slow_ema = ema_high_slow[i]
            prev_fast = ema_high_fast[i - 1]
            prev_slow = ema_high_slow[i - 1]
        
        # Skip if EMAs are NaN
        if np.isnan(fast_ema) or np.isnan(slow_ema) or np.isnan(prev_fast) or np.isnan(prev_slow):
            continue
        
        current_price = closes[i]
        
        # Detect crossovers
        bullish_cross = prev_fast <= prev_slow and fast_ema > slow_ema
        bearish_cross = prev_fast >= prev_slow and fast_ema < slow_ema
        
        # Entry signal
        if bullish_cross and position_entry_idx < 0:
            position_entry_idx = i
            position_entry_price = current_price
            position_shares = equity / current_price
        
        # Exit signal
        elif bearish_cross and position_entry_idx >= 0:
            # Record trade
            trade_entries[trade_count] = position_entry_idx
            trade_exits[trade_count] = i
            trade_entry_prices[trade_count] = position_entry_price
            trade_exit_prices[trade_count] = current_price
            trade_shares[trade_count] = position_shares
            
            # Update equity
            pnl = (current_price - position_entry_price) * position_shares
            equity += pnl
            
            # Reset position
            position_entry_idx = -1
            trade_count += 1
        
        # Update equity curve and drawdown
        current_equity = equity
        if position_entry_idx >= 0:
            current_equity = equity + (current_price - position_entry_price) * position_shares
        
        if current_equity > peak_equity:
            peak_equity = current_equity
        
        drawdown = ((peak_equity - current_equity) / peak_equity) * 100.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
        
        # Track early return
        if i == mid_point:
            early_return = ((current_equity - initial_capital) / initial_capital) * 100.0
    
    # Close final position if still open
    position_open = 0
    if position_entry_idx >= 0:
        final_price = closes[-1]
        trade_entries[trade_count] = position_entry_idx
        trade_exits[trade_count] = n - 1
        trade_entry_prices[trade_count] = position_entry_price
        trade_exit_prices[trade_count] = final_price
        trade_shares[trade_count] = position_shares
        
        pnl = (final_price - position_entry_price) * position_shares
        equity += pnl
        trade_count += 1
        position_open = 1
    
    final_equity = equity
    
    # Trim trade arrays to actual size
    trade_entries = trade_entries[:trade_count]
    trade_exits = trade_exits[:trade_count]
    
    return (trade_entries, trade_exits, final_equity, max_drawdown, 
            early_return, trade_count, position_open)


def run_strategy(df: pd.DataFrame, params: Dict) -> Dict:
    """
    Run adaptive EMA crossover strategy (Python wrapper for Numba core)
    
    Args:
        df: DataFrame with OHLCV data
        params: Strategy parameters
    
    Returns:
        Dictionary with results
    """
    # Extract arrays
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    
    # Calculate volatility metrics
    normalized_atr = calculate_normalized_atr_numba(
        highs, lows, closes, params['atr_length']
    )
    vol_ranks = calculate_volatility_rank_numba(
        normalized_atr, params['volatility_length']
    )
    
    # Calculate all EMAs
    ema_low_fast = calculate_ema_numba(closes, params['fast_length_low'])
    ema_low_slow = calculate_ema_numba(closes, params['slow_length_low'])
    ema_med_fast = calculate_ema_numba(closes, params['fast_length_med'])
    ema_med_slow = calculate_ema_numba(closes, params['slow_length_med'])
    ema_high_fast = calculate_ema_numba(closes, params['fast_length_high'])
    ema_high_slow = calculate_ema_numba(closes, params['slow_length_high'])
    
    # Determine start index
    max_period = max(
        params['slow_length_low'],
        params['slow_length_med'],
        params['slow_length_high']
    )
    start_idx = max_period - 1
    
    # Run strategy (Numba-compiled)
    (trade_entries, trade_exits, final_equity, max_drawdown,
     early_return, total_trades, position_open) = run_strategy_numba(
        closes, highs, lows,
        ema_low_fast, ema_low_slow,
        ema_med_fast, ema_med_slow,
        ema_high_fast, ema_high_slow,
        vol_ranks,
        params['low_vol_percentile'],
        params['high_vol_percentile'],
        params['initial_capital'],
        start_idx
    )
    
    # Calculate trade statistics
    trades = []
    for i in range(len(trade_entries)):
        entry_idx = trade_entries[i]
        exit_idx = trade_exits[i]
        entry_price = closes[entry_idx]
        exit_price = closes[exit_idx]
        
        # Calculate shares and PnL
        # This is approximate since we don't store shares in the Numba loop
        # but good enough for statistics
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100.0
        
        trades.append({
            'entry_date': df.index[entry_idx],
            'exit_date': df.index[exit_idx],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_percent': pnl_pct
        })
    
    # Calculate statistics
    total_return = ((final_equity - params['initial_capital']) / params['initial_capital']) * 100.0
    
    winning_trades = [t for t in trades if t['pnl_percent'] > 0]
    losing_trades = [t for t in trades if t['pnl_percent'] <= 0]
    
    win_rate = (len(winning_trades) / total_trades * 100.0) if total_trades > 0 else 0.0
    
    avg_win_pct = np.mean([t['pnl_percent'] for t in winning_trades]) if winning_trades else 0.0
    avg_loss_pct = np.mean([t['pnl_percent'] for t in losing_trades]) if losing_trades else 0.0
    
    total_win_pnl = sum([t['pnl_percent'] for t in winning_trades])
    total_loss_pnl = abs(sum([t['pnl_percent'] for t in losing_trades]))
    
    profit_factor = (total_win_pnl / total_loss_pnl) if total_loss_pnl > 0 else (
        np.inf if total_win_pnl > 0 else 0.0
    )
    
    return {
        'trades': trades,
        'total_trades': total_trades,
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'total_return': total_return,
        'final_equity': final_equity,
        'total_pnl': final_equity - params['initial_capital'],
        'max_drawdown': max_drawdown,
        'avg_win': avg_win_pct,
        'avg_loss': avg_loss_pct,
        'profit_factor': profit_factor,
        'early_return': early_return
    }


def calculate_buy_and_hold(df: pd.DataFrame, initial_capital: float) -> Dict:
    """Calculate buy and hold return"""
    entry_price = df['Close'].iloc[0]
    exit_price = df['Close'].iloc[-1]
    shares = initial_capital / entry_price
    final_value = shares * exit_price
    total_return = ((final_value - initial_capital) / initial_capital) * 100.0
    
    return {
        'total_return': total_return,
        'final_value': final_value
    }


def backtest(ticker: str, params: Dict, num_candles: int = 4500, interval: str = '1h') -> Dict:
    """
    Run backtest for a single ticker
    
    Args:
        ticker: Stock symbol
        params: Strategy parameters
        num_candles: Number of candles to fetch
        interval: Candle interval
    
    Returns:
        Dictionary with results
    """
    print(f"\n{'=' * 60}")
    print(f"Backtesting {ticker.upper()} - {interval.upper()} Interval")
    print('=' * 60)
    
    df = fetch_data(ticker, num_candles, interval)
    
    if df is None or len(df) < 200:
        print(f"❌ Insufficient data for {ticker}")
        return None
    
    print(f"Fetched {len(df)} candles")
    print(f"Period: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    
    # Run strategy
    start_time = time.time()
    results = run_strategy(df, params)
    elapsed = time.time() - start_time
    
    # Calculate buy and hold
    buy_and_hold = calculate_buy_and_hold(df, params['initial_capital'])
    
    # Display results
    print(f"\n📊 STRATEGY RESULTS (completed in {elapsed*1000:.2f}ms)")
    print(f"Initial Capital: ${params['initial_capital']:.2f}")
    print(f"Final Equity: ${results['final_equity']:.2f}")
    print(f"Total P&L: ${results['total_pnl']:.2f} ({results['total_return']:.2f}%)")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    
    print(f"\n📈 TRADE STATISTICS")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Winning Trades: {results['winning_trades']} ({results['win_rate']:.2f}%)")
    print(f"Losing Trades: {results['losing_trades']}")
    print(f"Avg Win: {results['avg_win']:.2f}%")
    print(f"Avg Loss: {results['avg_loss']:.2f}%")
    pf_str = f"{results['profit_factor']:.2f}" if np.isfinite(results['profit_factor']) else 'N/A'
    print(f"Profit Factor: {pf_str}")
    
    print(f"\n📉 BUY & HOLD COMPARISON")
    print(f"Buy & Hold Return: {buy_and_hold['total_return']:.2f}%")
    print(f"Buy & Hold Final Value: ${buy_and_hold['final_value']:.2f}")
    diff = results['total_return'] - buy_and_hold['total_return']
    emoji = '✅' if diff > 0 else '❌'
    print(f"Strategy vs Buy & Hold: {diff:.2f}% {emoji}")
    
    return {
        'ticker': ticker,
        'strategy': results,
        'buy_and_hold': buy_and_hold
    }


if __name__ == '__main__':
    from config_1h import DEFAULT_PARAMS
    
    print("\n🎯 Python Backtesting System (Numba-Optimized)")
    print("   Using: NumPy + Numba JIT compilation")
    print("   Expected speedup: 10-100x vs pure Python\n")
    
    tickers = ['QQQ', 'SPY']
    
    for ticker in tickers:
        result = backtest(ticker, DEFAULT_PARAMS, num_candles=1000, interval='1h')
        if result:
            print(f"\n✅ Completed {ticker}")
    
    print('\n✅ Backtesting complete!\n')
