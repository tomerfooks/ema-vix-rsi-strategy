"""
Parameter Optimization for QuantConnect Strategies
Implements grid search and walk-forward optimization
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from itertools import product
import json
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import os


def grid_search(
    strategy_class,
    data: pd.DataFrame,
    param_grid: Dict[str, List],
    metric: str = 'calmar_ratio',
    n_jobs: int = 4
) -> pd.DataFrame:
    """
    Perform grid search optimization over parameter space.
    
    Args:
        strategy_class: Strategy class to optimize
        data: Historical data
        param_grid: Dictionary of parameter names and values to test
        metric: Metric to optimize ('calmar_ratio', 'sharpe_ratio', 'total_return')
        n_jobs: Number of parallel jobs
    
    Returns:
        DataFrame with all tested combinations and results
    """
    print(f"Grid Search Optimization")
    print(f"Optimizing for: {metric}")
    print("=" * 70)
    
    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    combinations = list(product(*param_values))
    
    print(f"Testing {len(combinations)} parameter combinations...")
    print()
    
    results = []
    
    # Run optimizations
    if n_jobs > 1:
        # Parallel execution
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            futures = {}
            for combo in combinations:
                params = dict(zip(param_names, combo))
                future = executor.submit(_run_single_backtest, strategy_class, data, params)
                futures[future] = params
            
            for i, future in enumerate(as_completed(futures), 1):
                params = futures[future]
                try:
                    metrics = future.result()
                    result = {**params, **metrics}
                    results.append(result)
                    
                    if i % 10 == 0:
                        print(f"Completed {i}/{len(combinations)} tests...")
                except Exception as e:
                    print(f"Error with params {params}: {e}")
    else:
        # Serial execution
        for i, combo in enumerate(combinations, 1):
            params = dict(zip(param_names, combo))
            try:
                metrics = _run_single_backtest(strategy_class, data, params)
                result = {**params, **metrics}
                results.append(result)
                
                if i % 10 == 0:
                    print(f"Completed {i}/{len(combinations)} tests...")
            except Exception as e:
                print(f"Error with params {params}: {e}")
    
    # Convert to DataFrame and sort
    df = pd.DataFrame(results)
    df = df.sort_values(metric, ascending=False)
    
    print()
    print("=" * 70)
    print("Top 10 Parameter Combinations:")
    print("=" * 70)
    print(df.head(10).to_string())
    print()
    
    return df


def _run_single_backtest(strategy_class, data: pd.DataFrame, params: Dict) -> Dict:
    """Run a single backtest with given parameters."""
    strategy = strategy_class(**params)
    metrics = strategy.run(data)
    return metrics


def walk_forward_optimization(
    strategy_class,
    data: pd.DataFrame,
    param_grid: Dict[str, List],
    train_period_days: int = 252,
    test_period_days: int = 63,
    metric: str = 'calmar_ratio'
) -> Dict[str, Any]:
    """
    Perform walk-forward optimization.
    
    Train on one period, test on the next, then roll forward.
    
    Args:
        strategy_class: Strategy class to optimize
        data: Historical data
        param_grid: Parameter grid to search
        train_period_days: Training period length
        test_period_days: Testing period length
        metric: Metric to optimize
    
    Returns:
        Dictionary with walk-forward results
    """
    print("Walk-Forward Optimization")
    print("=" * 70)
    print(f"Train period: {train_period_days} days")
    print(f"Test period: {test_period_days} days")
    print(f"Optimizing for: {metric}")
    print()
    
    results = []
    equity_curve = []
    
    total_bars = len(data)
    current_idx = 0
    window_num = 1
    
    while current_idx + train_period_days + test_period_days <= total_bars:
        print(f"Window {window_num}:")
        print("-" * 70)
        
        # Split data
        train_start = current_idx
        train_end = current_idx + train_period_days
        test_start = train_end
        test_end = test_start + test_period_days
        
        train_data = data.iloc[train_start:train_end].copy()
        test_data = data.iloc[train_start:test_end].copy()  # Include training data for warm-up
        
        print(f"Training: {train_data.iloc[0]['timestamp']} to {train_data.iloc[-1]['timestamp']}")
        print(f"Testing:  {test_data.iloc[train_period_days]['timestamp']} to {test_data.iloc[-1]['timestamp']}")
        
        # Optimize on training data
        train_results = grid_search(strategy_class, train_data, param_grid, metric, n_jobs=1)
        best_params = train_results.iloc[0][list(param_grid.keys())].to_dict()
        
        print(f"Best params: {best_params}")
        print(f"Training {metric}: {train_results.iloc[0][metric]:.2f}")
        
        # Test on out-of-sample data
        strategy = strategy_class(**best_params)
        test_metrics = strategy.run(test_data)
        
        print(f"Testing {metric}: {test_metrics[metric]:.2f}")
        print()
        
        # Store results
        results.append({
            'window': window_num,
            'train_start': train_data.iloc[0]['timestamp'],
            'train_end': train_data.iloc[-1]['timestamp'],
            'test_start': test_data.iloc[train_period_days]['timestamp'],
            'test_end': test_data.iloc[-1]['timestamp'],
            'best_params': best_params,
            'train_metric': train_results.iloc[0][metric],
            'test_metric': test_metrics[metric],
            'test_return': test_metrics['total_return']
        })
        
        # Get equity curve for this window
        test_equity = strategy.get_equity_df()
        test_equity = test_equity.iloc[train_period_days:]  # Only out-of-sample
        equity_curve.extend(test_equity['equity'].tolist())
        
        # Move forward
        current_idx = test_start
        window_num += 1
    
    print("=" * 70)
    print("Walk-Forward Summary")
    print("=" * 70)
    
    results_df = pd.DataFrame(results)
    
    avg_train = results_df['train_metric'].mean()
    avg_test = results_df['test_metric'].mean()
    total_return = ((equity_curve[-1] / 10000) - 1) * 100
    
    print(f"Average Training {metric}: {avg_train:.2f}")
    print(f"Average Testing {metric}: {avg_test:.2f}")
    print(f"Degradation: {((avg_test / avg_train - 1) * 100):.1f}%")
    print(f"Total Walk-Forward Return: {total_return:.2f}%")
    print()
    
    return {
        'results': results_df,
        'equity_curve': equity_curve,
        'avg_train_metric': avg_train,
        'avg_test_metric': avg_test,
        'total_return': total_return
    }


def save_optimization_results(
    results: pd.DataFrame,
    strategy_name: str,
    symbol: str,
    output_dir: str = './results/optimization'
) -> str:
    """
    Display optimization results (no file saving).
    
    Args:
        results: DataFrame with optimization results
        strategy_name: Name of strategy
        symbol: Ticker symbol
        output_dir: Output directory (unused, kept for compatibility)
    
    Returns:
        Empty string (compatibility)
    """
    print("\nOptimization complete - results displayed above")
    return ""


# Example usage
if __name__ == '__main__':
    from strategies import AdaptiveEMAV2
    from utils import load_data
    
    # Load data
    data = load_data('QQQ', '2022-01-01', '2024-11-18', '1d')
    
    # Define parameter grid
    param_grid = {
        'fast_base': [8, 10, 12, 15],
        'slow_base': [18, 21, 24, 30],
        'fast_mult': [1.4, 1.6, 1.8, 2.0],
        'slow_mult': [1.0, 1.2, 1.4, 1.6],
        'vol_threshold': [55, 60, 65, 70, 75]
    }
    
    # Run grid search
    results = grid_search(
        AdaptiveEMAV2,
        data,
        param_grid,
        metric='calmar_ratio',
        n_jobs=4
    )
