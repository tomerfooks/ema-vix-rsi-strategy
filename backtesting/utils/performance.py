"""
Performance metrics calculation
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import json
from datetime import datetime


def calculate_metrics(
    equity_curve: pd.Series,
    trades: pd.DataFrame,
    initial_capital: float,
    benchmark_returns: pd.Series = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive performance metrics.
    
    Args:
        equity_curve: Series of equity values over time
        trades: DataFrame of trades with returns
        initial_capital: Starting capital
        benchmark_returns: Optional benchmark returns for comparison
    
    Returns:
        Dictionary of performance metrics
    """
    final_capital = equity_curve.iloc[-1]
    total_return = (final_capital - initial_capital) / initial_capital * 100
    
    # Drawdown analysis
    rolling_max = equity_curve.cummax()
    drawdown = (equity_curve - rolling_max) / rolling_max * 100
    max_drawdown = abs(drawdown.min())
    
    # Trade statistics
    num_trades = len(trades[trades['type'] == 'SELL'])
    
    if num_trades > 0:
        trade_returns = trades[trades['type'] == 'SELL']['return'].values
        winning_trades = (trade_returns > 0).sum()
        losing_trades = (trade_returns < 0).sum()
        win_rate = winning_trades / num_trades * 100
        
        avg_win = trade_returns[trade_returns > 0].mean() if winning_trades > 0 else 0
        avg_loss = trade_returns[trade_returns < 0].mean() if losing_trades > 0 else 0
        
        # Profit factor
        gross_profit = trade_returns[trade_returns > 0].sum()
        gross_loss = abs(trade_returns[trade_returns < 0].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
        
        # Sharpe ratio (annualized, assuming hourly data)
        mean_return = np.mean(trade_returns)
        std_return = np.std(trade_returns)
        sharpe = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
        
        # Sortino ratio (downside deviation)
        downside_returns = trade_returns[trade_returns < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
        sortino = (mean_return / downside_std * np.sqrt(252)) if downside_std > 0 else 0
    else:
        winning_trades = 0
        losing_trades = 0
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
        sharpe = 0
        sortino = 0
    
    # Calmar ratio
    calmar = total_return / max_drawdown if max_drawdown > 0 else 0
    
    # Time-based metrics
    equity_returns = equity_curve.pct_change().dropna()
    volatility = equity_returns.std() * np.sqrt(252) * 100  # Annualized
    
    metrics = {
        'total_return': round(total_return, 2),
        'final_capital': round(final_capital, 2),
        'max_drawdown': round(max_drawdown, 2),
        'calmar_ratio': round(calmar, 2),
        'sharpe_ratio': round(sharpe, 2),
        'sortino_ratio': round(sortino, 2),
        'volatility': round(volatility, 2),
        'num_trades': int(num_trades),
        'winning_trades': int(winning_trades),
        'losing_trades': int(losing_trades),
        'win_rate': round(win_rate, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(profit_factor, 2) if profit_factor != np.inf else 'inf'
    }
    
    # Benchmark comparison
    if benchmark_returns is not None:
        benchmark_total = benchmark_returns.sum()
        alpha = total_return - benchmark_total
        metrics['benchmark_return'] = round(benchmark_total, 2)
        metrics['alpha'] = round(alpha, 2)
    
    return metrics


def generate_report(
    strategy_name: str,
    symbol: str,
    metrics: Dict[str, Any],
    trades: pd.DataFrame,
    equity_curve: pd.DataFrame,
    parameters: Dict[str, Any],
    output_dir: str = './results'
) -> str:
    """
    Generate comprehensive backtest report.
    
    Args:
        strategy_name: Name of the strategy
        symbol: Ticker symbol
        metrics: Performance metrics
        trades: Trades DataFrame
        equity_curve: Equity curve DataFrame
        parameters: Strategy parameters
        output_dir: Output directory
    
    Returns:
        Path to generated report
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{symbol}_{strategy_name}_report.html"
    filepath = os.path.join(output_dir, filename)
    
    # Generate HTML report
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{strategy_name} - {symbol} Backtest Report</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #34495e;
                margin-top: 30px;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 5px;
            }}
            .metrics {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }}
            .metric-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 8px;
                color: white;
            }}
            .metric-card.positive {{
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            }}
            .metric-card.negative {{
                background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
            }}
            .metric-label {{
                font-size: 14px;
                opacity: 0.9;
                margin-bottom: 5px;
            }}
            .metric-value {{
                font-size: 28px;
                font-weight: bold;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ecf0f1;
            }}
            th {{
                background-color: #34495e;
                color: white;
                font-weight: 600;
            }}
            tr:hover {{
                background-color: #f8f9fa;
            }}
            .positive-return {{
                color: #27ae60;
                font-weight: bold;
            }}
            .negative-return {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .params {{
                background-color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .params-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
            }}
            .param-item {{
                background: white;
                padding: 10px;
                border-radius: 4px;
            }}
            .param-name {{
                font-weight: bold;
                color: #7f8c8d;
                font-size: 12px;
            }}
            .param-value {{
                font-size: 16px;
                color: #2c3e50;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 {strategy_name} Backtest Report</h1>
            <p><strong>Symbol:</strong> {symbol} | <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>Performance Metrics</h2>
            <div class="metrics">
                <div class="metric-card {'positive' if metrics['total_return'] > 0 else 'negative'}">
                    <div class="metric-label">Total Return</div>
                    <div class="metric-value">{metrics['total_return']}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Final Capital</div>
                    <div class="metric-value">${metrics['final_capital']:,.0f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Drawdown</div>
                    <div class="metric-value">{metrics['max_drawdown']}%</div>
                </div>
                <div class="metric-card {'positive' if metrics['calmar_ratio'] > 1 else ''}">
                    <div class="metric-label">Calmar Ratio</div>
                    <div class="metric-value">{metrics['calmar_ratio']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{metrics['sharpe_ratio']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{metrics['win_rate']}%</div>
                </div>
            </div>
            
            <h2>Trade Statistics</h2>
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value">{metrics['num_trades']}</div>
                </div>
                <div class="metric-card positive">
                    <div class="metric-label">Winning Trades</div>
                    <div class="metric-value">{metrics['winning_trades']}</div>
                </div>
                <div class="metric-card negative">
                    <div class="metric-label">Losing Trades</div>
                    <div class="metric-value">{metrics['losing_trades']}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value">{metrics.get('profit_factor', 'N/A')}</div>
                </div>
            </div>
            
            <h2>Strategy Parameters</h2>
            <div class="params">
                <div class="params-grid">
    """
    
    for key, value in parameters.items():
        html += f"""
                    <div class="param-item">
                        <div class="param-name">{key}</div>
                        <div class="param-value">{value}</div>
                    </div>
        """
    
    html += """
                </div>
            </div>
            
            <h2>Trade History</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Timestamp</th>
                        <th>Type</th>
                        <th>Price</th>
                        <th>Return</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for idx, trade in trades.iterrows():
        return_str = ""
        return_class = ""
        if trade['type'] == 'SELL' and 'return' in trade:
            ret = trade['return']
            return_class = 'positive-return' if ret > 0 else 'negative-return'
            return_str = f"{ret:.2f}%"
        
        html += f"""
                    <tr>
                        <td>{idx + 1}</td>
                        <td>{trade['timestamp']}</td>
                        <td>{trade['type']}</td>
                        <td>${trade['price']:.2f}</td>
                        <td class="{return_class}">{return_str}</td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    
    with open(filepath, 'w') as f:
        f.write(html)
    
    # Also save JSON report
    json_filename = filename.replace('.html', '.json')
    json_filepath = os.path.join(output_dir, json_filename)
    
    report_data = {
        'strategy': strategy_name,
        'symbol': symbol,
        'timestamp': timestamp,
        'metrics': metrics,
        'parameters': parameters,
        'trades': trades.to_dict('records'),
        'equity_curve': equity_curve.to_dict('records')
    }
    
    with open(json_filepath, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"Report generated: {filepath}")
    print(f"JSON data saved: {json_filepath}")
    
    return filepath


def compare_to_opencl(
    qc_metrics: Dict[str, Any],
    opencl_results_path: str
) -> pd.DataFrame:
    """
    Compare QuantConnect results to OpenCL results.
    
    Args:
        qc_metrics: QuantConnect performance metrics
        opencl_results_path: Path to OpenCL results JSON
    
    Returns:
        Comparison DataFrame
    """
    with open(opencl_results_path, 'r') as f:
        opencl_data = json.load(f)
    
    comparison = pd.DataFrame({
        'Metric': ['Total Return', 'Max Drawdown', 'Calmar Ratio', 'Num Trades'],
        'QuantConnect': [
            qc_metrics['total_return'],
            qc_metrics['max_drawdown'],
            qc_metrics['calmar_ratio'],
            qc_metrics['num_trades']
        ],
        'OpenCL': [
            opencl_data.get('total_return', 'N/A'),
            opencl_data.get('max_drawdown', 'N/A'),
            opencl_data.get('calmar_ratio', 'N/A'),
            opencl_data.get('num_trades', 'N/A')
        ]
    })
    
    comparison['Difference'] = comparison['QuantConnect'] - pd.to_numeric(comparison['OpenCL'], errors='coerce')
    comparison['% Difference'] = (comparison['Difference'] / pd.to_numeric(comparison['OpenCL'], errors='coerce') * 100).round(2)
    
    return comparison
