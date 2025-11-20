#!/usr/bin/env python3
"""
Verify the backtesting results by manually calculating returns from the trade log
"""
import json
import pandas as pd
import sys

def verify_trades(json_file, csv_file):
    """Verify trade calculations"""
    
    # Load JSON results
    with open(json_file, 'r') as f:
        results = json.load(f)
    
    # Load CSV data
    df = pd.read_csv(csv_file)
    
    print("="*60)
    print("BACKTEST VERIFICATION")
    print("="*60)
    print(f"Ticker: {results['ticker']}")
    print(f"Interval: {results['interval']}")
    print(f"Total Candles: {len(df)}")
    print(f"First Close: ${df['Close'].iloc[0]:.2f}")
    print(f"Last Close: ${df['Close'].iloc[-1]:.2f}")
    
    # Calculate Buy & Hold
    buy_hold_return = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
    print(f"Buy & Hold Return: {buy_hold_return:.2f}%")
    print(f"Reported B&H: {results['performance']['buy_hold_return']:.2f}%")
    
    if abs(buy_hold_return - results['performance']['buy_hold_return']) > 0.1:
        print("⚠️  WARNING: Buy & Hold return mismatch!")
    
    print("\n" + "="*60)
    print("TRADE-BY-TRADE VERIFICATION")
    print("="*60)
    
    # Verify each trade pair
    trades = results['trades']
    capital = 10000.0
    position = 0.0
    entry_price = 0.0
    trade_returns = []
    
    print(f"Initial Capital: ${capital:.2f}")
    print()
    
    for i, trade in enumerate(trades):
        action = trade['action']
        price = trade['price']
        trade_num = trade['trade_number']
        date = trade['date']
        candle_idx = trade['candle_index']
        
        # Verify price matches CSV
        if candle_idx < len(df):
            csv_price = df['Close'].iloc[candle_idx]
            price_diff = abs(csv_price - price)
            if price_diff > 0.01:
                print(f"⚠️  WARNING: Price mismatch at trade #{trade_num}")
                print(f"   JSON: ${price:.2f}, CSV: ${csv_price:.2f}, Diff: ${price_diff:.2f}")
        
        if action == 'BUY':
            # Buy with all available capital
            position = capital / price
            capital = 0.0
            entry_price = price
            print(f"#{trade_num:2d} BUY  @ ${price:6.2f} | Shares: {position:8.4f} | {date}")
            
        elif action == 'SELL':
            # Sell all shares
            capital = position * price
            pnl = ((price - entry_price) / entry_price) * 100
            trade_returns.append(pnl)
            
            reported_pnl = trade.get('pnl_percent', None)
            pnl_match = "✅" if reported_pnl and abs(pnl - reported_pnl) < 0.01 else "⚠️"
            
            print(f"#{trade_num:2d} SELL @ ${price:6.2f} | Capital: ${capital:9.2f} | P&L: {pnl:+6.2f}% {pnl_match}")
            if reported_pnl:
                print(f"     Reported P&L: {reported_pnl:+6.2f}%")
            
            position = 0.0
    
    # Close any remaining position
    if position > 0:
        final_price = df['Close'].iloc[-1]
        capital = position * final_price
        print(f"\n⚠️  Position still open at end! Closing at ${final_price:.2f}")
        print(f"   Final Capital: ${capital:.2f}")
    
    # Calculate total return
    total_return = ((capital - 10000) / 10000) * 100
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Final Capital: ${capital:.2f}")
    print(f"Calculated Return: {total_return:.2f}%")
    print(f"Reported Return: {results['performance']['total_return']:.2f}%")
    print(f"Difference: {abs(total_return - results['performance']['total_return']):.2f}%")
    
    if abs(total_return - results['performance']['total_return']) > 0.5:
        print("\n❌ CRITICAL ERROR: Return calculation mismatch!")
        print("   The backtesting system has a bug.")
    else:
        print("\n✅ Return calculation verified (within tolerance)")
    
    # Count trades
    buy_count = sum(1 for t in trades if t['action'] == 'BUY')
    sell_count = sum(1 for t in trades if t['action'] == 'SELL')
    
    print(f"\nTrade Count: {buy_count} buys, {sell_count} sells")
    print(f"Reported Total Trades: {results['performance']['total_trades']}")
    
    if buy_count != sell_count:
        print(f"⚠️  WARNING: Unmatched trades! {buy_count} buys vs {sell_count} sells")
    
    # Show individual trade returns
    print(f"\nIndividual Trade Returns:")
    for i, ret in enumerate(trade_returns):
        print(f"  Trade {i+1}: {ret:+6.2f}%")
    
    print(f"\nAverage Trade Return: {sum(trade_returns)/len(trade_returns):+.2f}%")
    print(f"Winning Trades: {sum(1 for r in trade_returns if r > 0)}/{len(trade_returns)}")
    print(f"Win Rate: {sum(1 for r in trade_returns if r > 0)/len(trade_returns)*100:.1f}%")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 verify_backtest.py <json_file> <csv_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    csv_file = sys.argv[2]
    
    verify_trades(json_file, csv_file)
