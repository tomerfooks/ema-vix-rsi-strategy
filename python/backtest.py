import yfinance as yf
import pandas as pd
import numpy as np
from indicators import ema, atr
from datetime import datetime, timedelta

# Strategy parameters from strategy-1h.pine
DEFAULT_PARAMS = {
    # Low Volatility
    'fast_length_low': 14,
    'slow_length_low': 80,
    
    # Medium Volatility
    'fast_length_med': 25,
    'slow_length_med': 98,
    
    # High Volatility
    'fast_length_high': 43,
    'slow_length_high': 120,
    
    # Volatility Settings
    'volatility_length': 71,
    'atr_length': 16,
    'low_vol_percentile': 28,
    'high_vol_percentile': 66,
    
    # Backtest settings
    'initial_capital': 10000
}


def fetch_data(ticker, num_candles=300, interval='1h'):
    """Fetch historical data from Yahoo Finance"""
    try:
        # Request enough data to ensure we get the target number of candles
        # 1h interval: request 60d to get ~1000 hours, then take last num_candles
        if interval == '1h':
            period = '60d'  # Request 60 days
        elif interval == '4h':
            period = '6mo'  # Request 6 months
        else:  # 1d
            period = '2y'  # Request 2 years
        
        # Fetch data
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if df.empty:
            print(f"❌ No data returned for {ticker}")
            return None
        
        # Clean data - remove NaN values
        df = df.dropna()
        
        # Get exactly the requested number of candles (most recent)
        if len(df) > num_candles:
            df = df.iloc[-num_candles:]
        
        print(f"   Retrieved {len(df)} candles (target: {num_candles})")
        
        if len(df) < num_candles:
            print(f"   ⚠️  Warning: Only got {len(df)} candles, requested {num_candles}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error fetching data for {ticker}: {e}")
        return None


def calculate_volatility_rank(normalized_atr, volatility_length):
    """Calculate percentile rank for volatility regime detection"""
    vol_ranks = np.zeros(len(normalized_atr))
    
    for i in range(len(normalized_atr)):
        start_idx = max(0, i - volatility_length + 1)
        window = normalized_atr[start_idx:i + 1]
        
        if len(window) < 20:
            vol_ranks[i] = 0
            continue
        
        # Calculate percentile rank
        current_vol = normalized_atr[i]
        rank = np.sum(window <= current_vol) / len(window) * 100
        vol_ranks[i] = rank
    
    return vol_ranks


def get_volatility_regime(vol_rank, low_percentile, high_percentile):
    """Determine volatility regime"""
    if vol_rank < low_percentile:
        return 'LOW'
    elif vol_rank < high_percentile:
        return 'MEDIUM'
    else:
        return 'HIGH'


def run_strategy(df, params=None):
    """Run adaptive EMA crossover strategy"""
    if params is None:
        params = DEFAULT_PARAMS.copy()
    
    # Extract close prices
    closes = df['Close'].values
    highs = df['High'].values
    lows = df['Low'].values
    
    # Calculate ATR and normalized ATR
    atr_values = atr(df['High'], df['Low'], df['Close'], period=params['atr_length'])
    normalized_atr = (atr_values / closes) * 100
    
    # Calculate volatility ranks
    vol_ranks = calculate_volatility_rank(normalized_atr, params['volatility_length'])
    
    # Calculate all EMAs
    ema_low_fast = ema(df['Close'], params['fast_length_low']).values
    ema_low_slow = ema(df['Close'], params['slow_length_low']).values
    ema_med_fast = ema(df['Close'], params['fast_length_med']).values
    ema_med_slow = ema(df['Close'], params['slow_length_med']).values
    ema_high_fast = ema(df['Close'], params['fast_length_high']).values
    ema_high_slow = ema(df['Close'], params['slow_length_high']).values
    
    # Determine start index (after longest EMA period)
    max_period = max(params['slow_length_low'], params['slow_length_med'], params['slow_length_high'])
    start_idx = max_period
    
    # Initialize tracking variables
    trades = []
    position = None
    capital = params['initial_capital']
    equity = capital
    equity_curve = []
    peak_equity = capital
    max_drawdown = 0
    early_return = 0
    mid_point = len(df) // 2
    
    # Main strategy loop
    for i in range(start_idx, len(df) - 1):
        # Skip if volatility data not ready
        if np.isnan(vol_ranks[i]):
            continue
        
        # Determine regime
        regime = get_volatility_regime(vol_ranks[i], params['low_vol_percentile'], params['high_vol_percentile'])
        
        # Select EMAs based on regime
        if regime == 'LOW':
            fast_ema = ema_low_fast[i]
            slow_ema = ema_low_slow[i]
            prev_fast = ema_low_fast[i - 1]
            prev_slow = ema_low_slow[i - 1]
        elif regime == 'MEDIUM':
            fast_ema = ema_med_fast[i]
            slow_ema = ema_med_slow[i]
            prev_fast = ema_med_fast[i - 1]
            prev_slow = ema_med_slow[i - 1]
        else:  # HIGH
            fast_ema = ema_high_fast[i]
            slow_ema = ema_high_slow[i]
            prev_fast = ema_high_fast[i - 1]
            prev_slow = ema_high_slow[i - 1]
        
        # Skip if NaN
        if np.isnan(fast_ema) or np.isnan(slow_ema):
            continue
        
        # Detect crossovers
        bullish_cross = prev_fast <= prev_slow and fast_ema > slow_ema
        bearish_cross = prev_fast >= prev_slow and fast_ema < slow_ema
        
        current_price = closes[i]
        
        # Entry signal
        if bullish_cross and position is None:
            shares = equity / current_price
            position = {
                'entry_price': current_price,
                'entry_date': df.index[i],
                'shares': shares,
                'regime': regime
            }
        
        # Exit signal
        if bearish_cross and position is not None:
            exit_price = current_price
            pnl = (exit_price - position['entry_price']) * position['shares']
            pnl_percent = ((exit_price - position['entry_price']) / position['entry_price']) * 100
            
            equity += pnl
            
            trades.append({
                'entry_date': position['entry_date'],
                'exit_date': df.index[i],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'shares': position['shares'],
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'regime': position['regime']
            })
            
            position = None
        
        # Update equity curve
        current_equity = equity
        if position is not None:
            current_equity = equity + (current_price - position['entry_price']) * position['shares']
        
        equity_curve.append(current_equity)
        
        # Track max drawdown
        if current_equity > peak_equity:
            peak_equity = current_equity
        drawdown = ((peak_equity - current_equity) / peak_equity) * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
        
        # Track early return for filtering
        if i == mid_point:
            early_return = ((current_equity - params['initial_capital']) / params['initial_capital']) * 100
    
    # Close any open position at the end
    if position is not None:
        final_price = closes[-1]
        pnl = (final_price - position['entry_price']) * position['shares']
        pnl_percent = ((final_price - position['entry_price']) / position['entry_price']) * 100
        
        equity += pnl
        
        trades.append({
            'entry_date': position['entry_date'],
            'exit_date': df.index[-1],
            'entry_price': position['entry_price'],
            'exit_price': final_price,
            'shares': position['shares'],
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'regime': position['regime']
        })
    
    # Calculate statistics
    final_equity = equity
    total_return = ((final_equity - params['initial_capital']) / params['initial_capital']) * 100
    
    # Filter valid trades
    valid_trades = [t for t in trades if np.isfinite(t['pnl'])]
    winning_trades = [t for t in valid_trades if t['pnl'] > 0]
    losing_trades = [t for t in valid_trades if t['pnl'] <= 0]
    
    win_rate = (len(winning_trades) / len(valid_trades) * 100) if valid_trades else 0
    
    avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
    
    total_win_pnl = sum([t['pnl'] for t in winning_trades])
    total_loss_pnl = abs(sum([t['pnl'] for t in losing_trades]))
    
    profit_factor = (total_win_pnl / total_loss_pnl) if total_loss_pnl > 0 else (np.inf if total_win_pnl > 0 else 0)
    
    return {
        'trades': trades,
        'total_trades': len(valid_trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'total_return': total_return,
        'final_equity': final_equity,
        'total_pnl': final_equity - params['initial_capital'],
        'max_drawdown': max_drawdown,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'equity_curve': equity_curve,
        'early_return': early_return
    }


def calculate_buy_and_hold(df, initial_capital):
    """Calculate buy and hold return"""
    entry_price = df['Close'].iloc[0]
    exit_price = df['Close'].iloc[-1]
    shares = initial_capital / entry_price
    final_value = shares * exit_price
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    
    return {
        'total_return': total_return,
        'final_value': final_value
    }


def backtest(ticker, params=None, num_candles=4500, interval='1h'):
    """Run backtest for a single ticker"""
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
    if params is None:
        params = DEFAULT_PARAMS.copy()
    
    results = run_strategy(df, params)
    
    # Calculate buy and hold
    buy_and_hold = calculate_buy_and_hold(df, params['initial_capital'])
    
    # Display results
    print(f"\n📊 STRATEGY RESULTS")
    print(f"Initial Capital: ${params['initial_capital']:.2f}")
    print(f"Final Equity: ${results['final_equity']:.2f}")
    print(f"Total P&L: ${results['total_pnl']:.2f} ({results['total_return']:.2f}%)")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    
    print(f"\n📈 TRADE STATISTICS")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Winning Trades: {results['winning_trades']} ({results['win_rate']:.2f}%)")
    print(f"Losing Trades: {results['losing_trades']}")
    print(f"Avg Win: ${results['avg_win']:.2f}")
    print(f"Avg Loss: ${results['avg_loss']:.2f}")
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


def run_multiple_backtests(tickers, params=None, num_candles=4500, interval='1h'):
    """Run backtests on multiple tickers"""
    results = []
    
    for ticker in tickers:
        result = backtest(ticker, params, num_candles, interval)
        if result:
            results.append(result)
    
    # Summary comparison
    print(f"\n{'=' * 60}")
    print('📊 SUMMARY - ALL TICKERS')
    print('=' * 60)
    print(f"\n{'Ticker':<10} {'Strategy':<12} {'Buy&Hold':<12} {'Difference':<12} {'Win Rate':<10} {'Trades'}")
    print('-' * 60)
    
    for result in results:
        strat_ret = f"{result['strategy']['total_return']:.2f}%"
        bh_ret = f"{result['buy_and_hold']['total_return']:.2f}%"
        diff = f"{result['strategy']['total_return'] - result['buy_and_hold']['total_return']:.2f}%"
        win_rate = f"{result['strategy']['win_rate']:.1f}%"
        trades = result['strategy']['total_trades']
        
        print(f"{result['ticker'].upper():<10} {strat_ret:<12} {bh_ret:<12} {diff:<12} {win_rate:<10} {trades}")
    
    return results


if __name__ == '__main__':
    tickers = ['QQQ', 'SPY', 'IBM', 'NICE']
    
    print("🎯 Python Backtesting System (Vectorized)")
    print("   Using: NumPy, Pandas, TA-Lib")
    print("   Optimizations: Vectorized operations, native C implementations\n")
    
    results = run_multiple_backtests(tickers, params=DEFAULT_PARAMS, num_candles=4500, interval='1h')
    
    print('\n✅ Backtesting complete!')
