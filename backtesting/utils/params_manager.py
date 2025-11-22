"""
Parameter management for saving and loading strategy parameters.
"""

import json
import os
from typing import Optional, Dict, Any
from pathlib import Path


class ParamsManager:
    """Manager for strategy parameters."""
    
    def __init__(self, base_dir: str = "strategies"):
        """
        Initialize params manager.
        
        Args:
            base_dir: Base directory for strategy folders
        """
        self.base_dir = Path(base_dir)
    
    def get_params_path(self, strategy: str, interval: str, symbol: str) -> Path:
        """
        Get path to parameters file.
        
        Args:
            strategy: Strategy name (e.g., 'adaptive_ema_v2_1')
            interval: Time interval (e.g., '1h', '1d')
            symbol: Ticker symbol (e.g., 'QQQ')
        
        Returns:
            Path to params file
        """
        return self.base_dir / strategy / interval / f"params_{symbol}.json"
    
    def load_params(self, strategy: str, interval: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Load parameters from file.
        
        Args:
            strategy: Strategy name
            interval: Time interval
            symbol: Ticker symbol
        
        Returns:
            Dictionary of parameters or None if not found
        """
        params_path = self.get_params_path(strategy, interval, symbol)
        
        if not params_path.exists():
            return None
        
        try:
            with open(params_path, 'r') as f:
                data = json.load(f)
            
            # Return just the parameters section
            return data.get('parameters', {})
        except Exception as e:
            print(f"Error loading parameters from {params_path}: {e}")
            return None
    
    def save_params(self, 
                   strategy: str, 
                   interval: str, 
                   symbol: str,
                   parameters: Dict[str, Any],
                   performance: Dict[str, float],
                   backtest_period: Dict[str, Any],
                   notes: str = "") -> bool:
        """
        Save parameters to file.
        
        Args:
            strategy: Strategy name
            interval: Time interval
            symbol: Ticker symbol
            parameters: Dictionary of strategy parameters
            performance: Dictionary of performance metrics
            backtest_period: Dictionary with start, end, candles
            notes: Optional notes about optimization
        
        Returns:
            True if saved successfully, False otherwise
        """
        params_path = self.get_params_path(strategy, interval, symbol)
        
        # Create directory if it doesn't exist
        params_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data structure
        data = {
            'symbol': symbol,
            'interval': interval,
            'strategy': strategy,
            'parameters': parameters,
            'performance': performance,
            'backtest_period': backtest_period,
            'updated': '2025-11-21',
            'notes': notes
        }
        
        try:
            with open(params_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving parameters to {params_path}: {e}")
            return False


def load_strategy_params(strategy: str, interval: str, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to load strategy parameters.
    
    Args:
        strategy: Strategy name
        interval: Time interval
        symbol: Ticker symbol
    
    Returns:
        Dictionary of parameters or None if not found
    """
    manager = ParamsManager()
    return manager.load_params(strategy, interval, symbol)


def save_strategy_params(strategy: str,
                         interval: str,
                         symbol: str,
                         parameters: Dict[str, Any],
                         performance: Dict[str, float],
                         backtest_period: Dict[str, Any],
                         notes: str = "") -> bool:
    """
    Convenience function to save strategy parameters.
    
    Args:
        strategy: Strategy name
        interval: Time interval
        symbol: Ticker symbol
        parameters: Dictionary of strategy parameters
        performance: Dictionary of performance metrics
        backtest_period: Dictionary with start, end, candles
        notes: Optional notes
    
    Returns:
        True if saved successfully
    """
    manager = ParamsManager()
    return manager.save_params(
        strategy=strategy,
        interval=interval,
        symbol=symbol,
        parameters=parameters,
        performance=performance,
        backtest_period=backtest_period,
        notes=notes
    )
