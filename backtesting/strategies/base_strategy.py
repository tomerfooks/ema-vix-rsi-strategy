"""
Base Strategy Class
Provides common functionality for all trading strategies
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime


class BaseStrategy:
    """
    Base class for all trading strategies.
    
    Provides:
    - Trade execution and tracking
    - Performance metrics calculation
    - Equity curve generation
    - Common interface for backtesting
    """
    
    def __init__(self, initial_capital: float = 10000, **kwargs):
        """
        Initialize base strategy.
        
        Args:
            initial_capital: Starting capital for backtesting
            **kwargs: Strategy-specific parameters
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # Number of shares held
        self.entry_price = 0
        
        # Trade tracking
        self.trades = []
        self.equity_curve = []
        
        # Store parameters
        self.params = kwargs
    
    def run(self, data: pd.DataFrame) -> Dict:
        """
        Run backtest on historical data.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            Dictionary with performance metrics
        """
        # Reset state
        self.capital = self.initial_capital
        self.position = 0
        self.entry_price = 0
        self.trades = []
        self.equity_curve = []
        
        # Calculate indicators
        data = self.calculate_indicators(data)
        
        # Initial equity point
        self.equity_curve.append({
            'timestamp': data.iloc[0]['timestamp'],
            'equity': self.capital
        })
        
        # Iterate through data
        for idx in range(len(data)):
            # Generate signal
            signal = self.generate_signals(data, idx)
            
            # Execute trades
            if signal == 'BUY' and self.position == 0:
                self._execute_buy(data.iloc[idx])
            elif signal == 'SELL' and self.position > 0:
                self._execute_sell(data.iloc[idx])
            
            # Update equity curve
            current_equity = self._calculate_equity(data.iloc[idx])
            self.equity_curve.append({
                'timestamp': data.iloc[idx]['timestamp'],
                'equity': current_equity
            })
        
        # Close any open position at end
        if self.position > 0:
            self._execute_sell(data.iloc[-1], force=True)
        
        # Calculate and return metrics
        return self._calculate_metrics(data)
    
    def _execute_buy(self, bar: pd.Series):
        """Execute a buy order."""
        price = bar['close']
        self.position = self.capital / price  # Buy max shares
        self.entry_price = price
        
        self.trades.append({
            'timestamp': bar['timestamp'],
            'type': 'BUY',
            'price': price,
            'shares': self.position,
            'capital': self.capital
        })
    
    def _execute_sell(self, bar: pd.Series, force: bool = False):
        """Execute a sell order."""
        price = bar['close']
        sale_value = self.position * price
        returns = ((price - self.entry_price) / self.entry_price) * 100
        
        self.capital = sale_value
        
        self.trades.append({
            'timestamp': bar['timestamp'],
            'type': 'SELL',
            'price': price,
            'shares': self.position,
            'capital': self.capital,
            'return': returns
        })
        
        self.position = 0
        self.entry_price = 0
    
    def _calculate_equity(self, bar: pd.Series) -> float:
        """Calculate current equity value."""
        if self.position > 0:
            return self.position * bar['close']
        return self.capital
    
    def _calculate_metrics(self, data: pd.DataFrame) -> Dict:
        """Calculate performance metrics."""
        equity_df = pd.DataFrame(self.equity_curve)
        
        # Basic returns
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        # Buy and hold benchmark
        buy_hold_return = ((data.iloc[-1]['close'] - data.iloc[0]['close']) / data.iloc[0]['close']) * 100
        alpha = total_return - buy_hold_return
        
        # Drawdown calculation
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = ((equity_df['equity'] - equity_df['peak']) / equity_df['peak']) * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # Calmar ratio
        calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Sharpe ratio (simplified - using daily returns)
        equity_df['returns'] = equity_df['equity'].pct_change()
        mean_return = equity_df['returns'].mean()
        std_return = equity_df['returns'].std()
        sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return != 0 else 0
        
        # Trade statistics
        trades_df = pd.DataFrame(self.trades)
        sell_trades = trades_df[trades_df['type'] == 'SELL']
        
        num_trades = len(sell_trades)
        winning_trades = len(sell_trades[sell_trades['return'] > 0]) if num_trades > 0 else 0
        losing_trades = len(sell_trades[sell_trades['return'] <= 0]) if num_trades > 0 else 0
        win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'alpha': alpha,
            'final_capital': self.capital,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar_ratio,
            'sharpe_ratio': sharpe_ratio,
            'num_trades': num_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate
        }
    
    def get_trades_df(self) -> pd.DataFrame:
        """Return trades as DataFrame."""
        return pd.DataFrame(self.trades)
    
    def get_equity_df(self) -> pd.DataFrame:
        """Return equity curve as DataFrame."""
        return pd.DataFrame(self.equity_curve)
    
    # Abstract methods - must be implemented by subclasses
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate strategy-specific indicators.
        
        Args:
            data: Raw OHLCV data
            
        Returns:
            Data with indicator columns added
        """
        raise NotImplementedError("Subclass must implement calculate_indicators()")
    
    def generate_signals(self, data: pd.DataFrame, idx: int) -> Optional[str]:
        """
        Generate trading signals.
        
        Args:
            data: DataFrame with OHLCV and indicators
            idx: Current bar index
            
        Returns:
            'BUY', 'SELL', or None
        """
        raise NotImplementedError("Subclass must implement generate_signals()")
    
    def get_strategy_info(self) -> Dict:
        """
        Return strategy description and parameters.
        
        Returns:
            Dictionary with strategy metadata
        """
        raise NotImplementedError("Subclass must implement get_strategy_info()")
