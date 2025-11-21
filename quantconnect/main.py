"""
Main entry point for QuantConnect backtesting system
Run strategies locally before deploying to QuantConnect Cloud
"""

import argparse
import sys
from datetime import datetime
import json

from strategies import (
    AdaptiveEMAV2,
    AdaptiveEMAV2_1,
    AdaptiveEMAV2_2,
    AdaptiveEMAVolV1,
    AdaptiveDonchianV1
)
from utils import load_data, align_opencl_data, calculate_metrics, generate_report
from utils.converter import convert_opencl_params


def run_backtest(
    strategy_name: str,
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = '1h',
    use_opencl_data: bool = False,
    **strategy_params
):
    """
    Run a backtest with specified parameters.
    
    Args:
        strategy_name: Name of strategy to run
        symbol: Ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval
        use_opencl_data: Use same data as OpenCL for comparison
        **strategy_params: Strategy-specific parameters
    """
    print("=" * 70)
    print(f"QuantConnect Backtest - {strategy_name}")
    print("=" * 70)
    print(f"Symbol: {symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Interval: {interval}")
    print()
    
    # Load data
    if use_opencl_data:
        print("Loading OpenCL data for comparison...")
        data = align_opencl_data(symbol, interval)
    else:
        data = load_data(symbol, start_date, end_date, interval)
    
    print(f"Loaded {len(data)} bars")
    print()
    
    # Initialize strategy based on name
    strategy_key = strategy_name.lower().replace('_', '').replace('.', '')
    
    if strategy_key == 'adaptiveemav2':
        strategy = AdaptiveEMAV2(**strategy_params)
    elif strategy_key == 'adaptiveemav21':
        strategy = AdaptiveEMAV2_1(**strategy_params)
    elif strategy_key == 'adaptiveemav22':
        strategy = AdaptiveEMAV2_2(**strategy_params)
    elif strategy_key == 'adaptiveemavolv1':
        strategy = AdaptiveEMAVolV1(**strategy_params)
    elif strategy_key == 'adaptivedonchianv1':
        strategy = AdaptiveDonchianV1(**strategy_params)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available: adaptive_ema_v2, adaptive_ema_v2_1, adaptive_ema_v2_2, adaptive_ema_vol_v1, adaptive_donchian_v1")
    
    # Display strategy info
    info = strategy.get_strategy_info()
    print(f"Strategy: {info['name']}")
    print(f"Description: {info['description']}")
    print()
    print("Parameters:")
    for key, value in info['parameters'].items():
        print(f"  {key}: {value}")
    print()
    
    # Run backtest
    print("Running backtest...")
    metrics = strategy.run(data)
    
    # Display results
    print()
    print("=" * 70)
    print("PERFORMANCE METRICS")
    print("=" * 70)
    print(f"Total Return:     {metrics['total_return']:>8.2f}%")
    print(f"Final Capital:    ${metrics['final_capital']:>8,.2f}")
    print(f"Max Drawdown:     {metrics['max_drawdown']:>8.2f}%")
    print(f"Calmar Ratio:     {metrics['calmar_ratio']:>8.2f}")
    print(f"Sharpe Ratio:     {metrics['sharpe_ratio']:>8.2f}")
    print(f"Win Rate:         {metrics['win_rate']:>8.2f}%")
    print(f"Total Trades:     {metrics['num_trades']:>8}")
    print(f"Winning Trades:   {metrics['winning_trades']:>8}")
    print(f"Losing Trades:    {metrics['losing_trades']:>8}")
    print()

    
    # Get trade details
    trades_df = strategy.get_trades_df()
    equity_df = strategy.get_equity_df()
    
    print()
    print("Trade Summary:")
    if len(trades_df) > 0:
        # Create a cleaner display
        display_df = trades_df.copy()
        
        # For BUY trades, replace NaN with empty string for cleaner display
        if 'return' in display_df.columns:
            display_df['return'] = display_df.apply(
                lambda row: f"{row['return']:>7.2f}%" if row['type'] == 'SELL' else '', 
                axis=1
            )
        
        # Format price and capital
        display_df['price'] = display_df['price'].apply(lambda x: f"${x:>8.2f}")
        display_df['capital'] = display_df['capital'].apply(lambda x: f"${x:>10,.2f}")
        
        # Only show relevant columns
        cols = ['timestamp', 'type', 'price', 'capital', 'return']
        display_df = display_df[[col for col in cols if col in display_df.columns]]
        
        print(display_df.to_string(index=False))
        
        # Show winning vs losing trades summary
        sell_trades = trades_df[trades_df['type'] == 'SELL']
        if len(sell_trades) > 0 and 'return' in sell_trades.columns:
            winners = sell_trades[sell_trades['return'] > 0]
            losers = sell_trades[sell_trades['return'] < 0]
            print()
            print(f"Winning Trades: {len(winners)}")
            print(f"Losing Trades:  {len(losers)}")
            if len(winners) > 0:
                print(f"Avg Win:        {winners['return'].mean():>6.2f}%")
            if len(losers) > 0:
                print(f"Avg Loss:       {losers['return'].mean():>6.2f}%")
            print(f"Buy & Hold:       {metrics['buy_hold_return']:>8.2f}%")
            print(f"Alpha:            {metrics['alpha']:>8.2f}%")
            print("=" * 70)
    return metrics, trades_df, equity_df


def compare_to_opencl(strategy_name: str, symbol: str, interval: str, **strategy_params):
    """
    Run backtest and compare to OpenCL results.
    
    Args:
        strategy_name: Strategy name
        symbol: Ticker symbol
        interval: Data interval
        **strategy_params: Strategy parameters
    """
    print("=" * 70)
    print("COMPARISON MODE: QuantConnect vs OpenCL")
    print("=" * 70)
    print()
    
    # Run QC backtest with OpenCL data
    metrics, _, _ = run_backtest(
        strategy_name=strategy_name,
        symbol=symbol,
        start_date='2020-01-01',
        end_date='2024-12-31',
        interval=interval,
        use_opencl_data=True,
        **strategy_params
    )
    
    # Try to load OpenCL results
    import os
    opencl_results_dir = f'../opencl/strategies/{strategy_name}/results/{symbol.lower()}/{interval}'
    
    if os.path.exists(opencl_results_dir):
        # Find most recent result
        files = [f for f in os.listdir(opencl_results_dir) if f.endswith('.json')]
        if files:
            latest = sorted(files)[-1]
            opencl_path = os.path.join(opencl_results_dir, latest)
            
            with open(opencl_path, 'r') as f:
                opencl_metrics = json.load(f)
            
            print()
            print("=" * 70)
            print("COMPARISON RESULTS")
            print("=" * 70)
            print(f"{'Metric':<20} {'QuantConnect':>15} {'OpenCL':>15} {'Diff':>15}")
            print("-" * 70)
            
            for key in ['total_return', 'max_drawdown', 'calmar_ratio', 'num_trades']:
                qc_val = metrics.get(key, 'N/A')
                ocl_val = opencl_metrics.get(key, 'N/A')
                
                if isinstance(qc_val, (int, float)) and isinstance(ocl_val, (int, float)):
                    diff = qc_val - ocl_val
                    print(f"{key:<20} {qc_val:>15.2f} {ocl_val:>15.2f} {diff:>15.2f}")
                else:
                    print(f"{key:<20} {str(qc_val):>15} {str(ocl_val):>15} {'N/A':>15}")
            
            print("=" * 70)
    else:
        print()
        print("⚠️  No OpenCL results found for comparison")
        print(f"   Expected at: {opencl_results_dir}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='QuantConnect Backtesting System')
    
    parser.add_argument('--strategy', type=str, default='adaptive_ema_v2',
                       help='Strategy name (default: adaptive_ema_v2)')
    parser.add_argument('--symbol', type=str, default='QQQ',
                       help='Ticker symbol (default: QQQ)')
    parser.add_argument('--start', type=str, default='2023-01-01',
                       help='Start date YYYY-MM-DD (default: 2023-01-01)')
    parser.add_argument('--end', type=str, default='2024-12-31',
                       help='End date YYYY-MM-DD (default: 2024-12-31)')
    parser.add_argument('--interval', type=str, default='1h',
                       help='Data interval (default: 1h)')
    
    # Strategy parameters (optimized defaults)
    parser.add_argument('--fast-base', type=int, default=15,
                       help='Fast EMA base period (default: 15)')
    parser.add_argument('--slow-base', type=int, default=18,
                       help='Slow EMA base period (default: 18)')
    parser.add_argument('--fast-mult', type=float, default=2.0,
                       help='Fast EMA multiplier (default: 2.0)')
    parser.add_argument('--slow-mult', type=float, default=1.4,
                       help='Slow EMA multiplier (default: 1.4)')
    parser.add_argument('--atr-length', type=int, default=12,
                       help='ATR period (default: 12)')
    parser.add_argument('--vol-threshold', type=int, default=65,
                       help='Volatility threshold (default: 65)')
    
    # Modes
    parser.add_argument('--compare', action='store_true',
                       help='Compare to OpenCL results')
    parser.add_argument('--from-opencl', type=str,
                       help='Load parameters from OpenCL config file')
    
    args = parser.parse_args()
    
    # Load parameters from OpenCL if specified
    strategy_params = {
        'fast_base': args.fast_base,
        'slow_base': args.slow_base,
        'fast_mult': args.fast_mult,
        'slow_mult': args.slow_mult,
        'atr_length': args.atr_length,
        'vol_threshold': args.vol_threshold,
    }
    
    if args.from_opencl:
        print(f"Loading parameters from: {args.from_opencl}")
        opencl_params = convert_opencl_params(args.from_opencl, args.strategy)
        strategy_params.update(opencl_params)
        print("Parameters loaded from OpenCL config")
        print()
    
    # Run in appropriate mode
    if args.compare:
        compare_to_opencl(
            strategy_name=args.strategy,
            symbol=args.symbol,
            interval=args.interval,
            **strategy_params
        )
    else:
        run_backtest(
            strategy_name=args.strategy,
            symbol=args.symbol,
            start_date=args.start,
            end_date=args.end,
            interval=args.interval,
            **strategy_params
        )


if __name__ == '__main__':
    main()
