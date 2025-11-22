"""
Test Adaptive EMA v1 Strategy

Quick test to verify the strategy implementation matches Pine Script behavior
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from strategies.adaptive_ema_v1.base import AdaptiveEmaV1Strategy
from utils.data_loader import load_data


def test_adaptive_ema_v1():
    """Test the strategy with generated data"""
    print("=" * 60)
    print("Testing Adaptive EMA v1 Strategy")
    print("=" * 60)
    
    # Generate sample data for testing
    print("\n📂 Generating sample price data...")
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=500, freq='1H')
    
    # Generate realistic price movement
    returns = np.random.normal(0.001, 0.02, len(dates))
    price = 100 * np.exp(np.cumsum(returns))
    
    # Add some volatility
    high = price * (1 + np.abs(np.random.normal(0, 0.01, len(dates))))
    low = price * (1 - np.abs(np.random.normal(0, 0.01, len(dates))))
    open_price = price * (1 + np.random.normal(0, 0.005, len(dates)))
    volume = np.random.uniform(100000, 1000000, len(dates))
    
    df = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': price,
        'volume': volume
    }, index=dates)
    
    print(f"   ✅ Loaded {len(df)} candles")
    print(f"   Period: {df.index[0]} to {df.index[-1]}")
    
    # Create strategy with proven Pine Script parameters
    params = {
        'fast_length_low': 12,
        'slow_length_low': 80,
        'fast_length_med': 25,
        'slow_length_med': 108,
        'fast_length_high': 38,
        'slow_length_high': 120,
        'atr_length': 14,
        'volatility_length': 63,
        'low_vol_percentile': 25,
        'high_vol_percentile': 73
    }
    
    print(f"\n🎯 Strategy Parameters (Proven Pine Script values):")
    print(f"   Low Vol: {params['fast_length_low']}/{params['slow_length_low']}")
    print(f"   Med Vol: {params['fast_length_med']}/{params['slow_length_med']}")
    print(f"   High Vol: {params['fast_length_high']}/{params['slow_length_high']}")
    print(f"   ATR: {params['atr_length']}, Vol Window: {params['volatility_length']}")
    print(f"   Percentiles: {params['low_vol_percentile']}% - {params['high_vol_percentile']}%")
    
    strategy = AdaptiveEmaV1Strategy(params)
    
    # Generate signals
    print("\n⚙️  Generating signals...")
    df_signals = strategy.generate_signals(df)
    
    # Count signals
    buy_signals = (df_signals['signal'] == 1).sum()
    sell_signals = (df_signals['signal'] == -1).sum()
    
    print(f"   Buy signals: {buy_signals}")
    print(f"   Sell signals: {sell_signals}")
    
    if buy_signals == 0 and sell_signals == 0:
        print("   ⚠️  No signals generated - check data and parameters")
        return
    
    # Simulate trades
    print("\n📊 Simulating trades...")
    initial_capital = 10000
    capital = initial_capital
    position = 0
    entry_price = 0
    trades = []
    
    for i in range(len(df_signals)):
        signal = df_signals['signal'].iloc[i]
        price = df_signals['close'].iloc[i]
        
        if signal == 1 and position == 0:
            # Buy
            position = capital / price
            entry_price = price
            capital = 0
            trades.append({
                'type': 'BUY',
                'date': df_signals.index[i],
                'price': price,
                'position': position
            })
        elif signal == -1 and position > 0:
            # Sell
            capital = position * price
            pnl = ((price - entry_price) / entry_price) * 100
            trades.append({
                'type': 'SELL',
                'date': df_signals.index[i],
                'price': price,
                'pnl': pnl
            })
            position = 0
            entry_price = 0
    
    # Close any open position
    if position > 0:
        final_price = df_signals['close'].iloc[-1]
        capital = position * final_price
        pnl = ((final_price - entry_price) / entry_price) * 100
        trades.append({
            'type': 'SELL',
            'date': df_signals.index[-1],
            'price': final_price,
            'pnl': pnl
        })
    
    # Calculate performance
    final_value = capital
    total_return = ((final_value - initial_capital) / initial_capital) * 100
    num_trades = len([t for t in trades if t['type'] == 'SELL'])
    
    buy_hold_return = ((df_signals['close'].iloc[-1] - df_signals['close'].iloc[0]) / 
                       df_signals['close'].iloc[0]) * 100
    
    print(f"\n🏆 Results:")
    print(f"   Total Trades: {num_trades}")
    print(f"   Final Value: ${final_value:,.2f}")
    print(f"   Total Return: {total_return:.2f}%")
    print(f"   Buy & Hold: {buy_hold_return:.2f}%")
    print(f"   Outperformance: {total_return - buy_hold_return:.2f}%")
    
    if num_trades > 0:
        winning_trades = [t['pnl'] for t in trades if t['type'] == 'SELL' and t['pnl'] > 0]
        losing_trades = [t['pnl'] for t in trades if t['type'] == 'SELL' and t['pnl'] < 0]
        
        print(f"\n📈 Trade Statistics:")
        print(f"   Winning Trades: {len(winning_trades)} ({len(winning_trades)/num_trades*100:.1f}%)")
        print(f"   Losing Trades: {len(losing_trades)} ({len(losing_trades)/num_trades*100:.1f}%)")
        
        if winning_trades:
            print(f"   Avg Win: {sum(winning_trades)/len(winning_trades):.2f}%")
        if losing_trades:
            print(f"   Avg Loss: {sum(losing_trades)/len(losing_trades):.2f}%")
        
        # Show last 5 trades
        print(f"\n📝 Last 5 Trades:")
        for trade in trades[-10:]:
            if trade['type'] == 'BUY':
                print(f"   {trade['date']}: BUY @ ${trade['price']:.2f}")
            else:
                print(f"   {trade['date']}: SELL @ ${trade['price']:.2f} (PnL: {trade['pnl']:.2f}%)")
    
    # Show volatility regime distribution
    regime_counts = df_signals['volatility_regime'].value_counts()
    print(f"\n🌡️  Volatility Regime Distribution:")
    for regime, count in regime_counts.items():
        pct = (count / len(df_signals)) * 100
        print(f"   {regime.capitalize()}: {count} bars ({pct:.1f}%)")
    
    print("\n" + "=" * 60)
    print("✅ Strategy test complete!")
    print("=" * 60)


if __name__ == '__main__':
    test_adaptive_ema_v1()
