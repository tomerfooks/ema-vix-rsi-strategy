"""
QuantConnect Cloud Optimization Interface
Deploy strategies to QuantConnect and use their optimization engine
"""

import requests
import json
from typing import Dict, List, Any
import time


class QuantConnectOptimizer:
    """
    Interface to QuantConnect's cloud optimization engine.
    
    Requires QuantConnect account and API credentials.
    """
    
    def __init__(self, user_id: str, api_token: str):
        """
        Initialize QuantConnect API client.
        
        Args:
            user_id: QuantConnect user ID
            api_token: QuantConnect API token
        """
        self.user_id = user_id
        self.api_token = api_token
        self.base_url = "https://www.quantconnect.com/api/v2"
        self.auth = (user_id, api_token)
    
    def create_optimization(
        self,
        project_id: int,
        strategy: str,
        parameters: Dict[str, Dict[str, Any]],
        target: str = "TotalPerformance.PortfolioStatistics.SharpeRatio",
        constraint: str = "",
        estimate_period: str = "2020-01-01",
        end_period: str = "2024-11-18"
    ) -> str:
        """
        Create optimization in QuantConnect cloud.
        
        Args:
            project_id: QuantConnect project ID
            strategy: Strategy code/class name
            parameters: Parameter definitions with min/max/step
                Example: {
                    'fast_base': {'min': 5, 'max': 20, 'step': 1},
                    'slow_base': {'min': 15, 'max': 50, 'step': 5}
                }
            target: Optimization target (maximize this)
            constraint: Optimization constraint
            estimate_period: Backtest start date
            end_period: Backtest end date
        
        Returns:
            Optimization ID
        """
        endpoint = f"{self.base_url}/optimizations/create"
        
        # Build parameter array for QC
        qc_parameters = []
        for name, config in parameters.items():
            qc_parameters.append({
                "name": name,
                "min": config['min'],
                "max": config['max'],
                "step": config.get('step', 1)
            })
        
        payload = {
            "projectId": project_id,
            "name": f"{strategy}_optimization_{int(time.time())}",
            "target": target,
            "targetTo": "max",
            "constraint": constraint,
            "estimatedValue": 0,
            "estimatePeriod": estimate_period,
            "endPeriod": end_period,
            "parameters": qc_parameters
        }
        
        response = requests.post(endpoint, json=payload, auth=self.auth)
        response.raise_for_status()
        
        result = response.json()
        optimization_id = result.get('optimizationId')
        
        print(f"Optimization created: {optimization_id}")
        print(f"Testing {len(qc_parameters)} parameters")
        print(f"Target: {target}")
        
        return optimization_id
    
    def get_optimization_status(self, optimization_id: str) -> Dict:
        """
        Get status of running optimization.
        
        Args:
            optimization_id: Optimization ID
        
        Returns:
            Status dictionary
        """
        endpoint = f"{self.base_url}/optimizations/read"
        params = {"optimizationId": optimization_id}
        
        response = requests.get(endpoint, params=params, auth=self.auth)
        response.raise_for_status()
        
        return response.json()
    
    def get_optimization_results(self, optimization_id: str) -> List[Dict]:
        """
        Get results from completed optimization.
        
        Args:
            optimization_id: Optimization ID
        
        Returns:
            List of results sorted by target metric
        """
        status = self.get_optimization_status(optimization_id)
        
        if status['status'] != 'completed':
            raise ValueError(f"Optimization not complete. Status: {status['status']}")
        
        results = status.get('results', [])
        
        # Sort by target value
        results.sort(key=lambda x: x.get('targetValue', 0), reverse=True)
        
        return results
    
    def wait_for_optimization(
        self,
        optimization_id: str,
        check_interval: int = 30,
        timeout: int = 3600
    ) -> Dict:
        """
        Wait for optimization to complete.
        
        Args:
            optimization_id: Optimization ID
            check_interval: Seconds between status checks
            timeout: Maximum wait time in seconds
        
        Returns:
            Final status dictionary
        """
        start_time = time.time()
        
        print(f"Waiting for optimization {optimization_id}...")
        
        while time.time() - start_time < timeout:
            status = self.get_optimization_status(optimization_id)
            current_status = status['status']
            
            print(f"Status: {current_status}")
            
            if current_status == 'completed':
                print("Optimization completed!")
                return status
            elif current_status == 'error':
                raise RuntimeError(f"Optimization failed: {status.get('error', 'Unknown error')}")
            
            time.sleep(check_interval)
        
        raise TimeoutError(f"Optimization timed out after {timeout} seconds")
    
    def optimize_strategy(
        self,
        project_id: int,
        strategy: str,
        parameters: Dict[str, Dict[str, Any]],
        wait: bool = True
    ) -> Dict:
        """
        Run complete optimization workflow.
        
        Args:
            project_id: QuantConnect project ID
            strategy: Strategy name
            parameters: Parameter definitions
            wait: Wait for completion
        
        Returns:
            Optimization results
        """
        # Create optimization
        opt_id = self.create_optimization(project_id, strategy, parameters)
        
        if not wait:
            return {'optimization_id': opt_id, 'status': 'running'}
        
        # Wait for completion
        self.wait_for_optimization(opt_id)
        
        # Get results
        results = self.get_optimization_results(opt_id)
        
        print()
        print("=" * 70)
        print("TOP 10 RESULTS")
        print("=" * 70)
        
        for i, result in enumerate(results[:10], 1):
            print(f"\n#{i}")
            print(f"  Target Value: {result.get('targetValue', 0):.4f}")
            print(f"  Parameters:")
            for param_name, param_value in result.get('parameterSet', {}).items():
                print(f"    {param_name}: {param_value}")
        
        return {
            'optimization_id': opt_id,
            'status': 'completed',
            'results': results
        }


# Example usage and helper functions
def create_qc_algorithm_with_optimization(strategy_params: Dict) -> str:
    """
    Generate QuantConnect algorithm code with optimization parameters.
    
    Args:
        strategy_params: Strategy parameter definitions
    
    Returns:
        Python code for QuantConnect algorithm
    """
    code = '''
from AlgorithmImports import *

class OptimizedStrategy(QCAlgorithm):
    
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2024, 11, 18)
        self.SetCash(10000)
        
        # Add equity
        self.symbol = self.AddEquity("QQQ", Resolution.Daily).Symbol
        
        # Optimization parameters
'''
    
    for param_name, config in strategy_params.items():
        code += f'        self.{param_name} = self.GetParameter("{param_name}", {config["min"]})\n'
    
    code += '''
        
        # Indicators
        self.ema_fast = self.EMA(self.symbol, int(self.fast_base), Resolution.Daily)
        self.ema_slow = self.EMA(self.symbol, int(self.slow_base), Resolution.Daily)
        
        # Warm-up
        self.SetWarmUp(100)
    
    def OnData(self, data):
        if self.IsWarmingUp:
            return
        
        if not data.ContainsKey(self.symbol):
            return
        
        # Strategy logic here
        if not self.Portfolio.Invested:
            if self.ema_fast.Current.Value > self.ema_slow.Current.Value:
                self.SetHoldings(self.symbol, 1.0)
        else:
            if self.ema_fast.Current.Value < self.ema_slow.Current.Value:
                self.Liquidate(self.symbol)
'''
    
    return code


if __name__ == '__main__':
    # Example: Optimize strategy on QuantConnect cloud
    
    # Load credentials from config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    qc_config = config.get('quantconnect', {})
    
    if qc_config.get('user_id') and qc_config.get('api_token'):
        optimizer = QuantConnectOptimizer(
            user_id=qc_config['user_id'],
            api_token=qc_config['api_token']
        )
        
        # Define parameters to optimize
        parameters = {
            'fast_base': {'min': 5, 'max': 20, 'step': 1},
            'slow_base': {'min': 15, 'max': 50, 'step': 5},
            'vol_threshold': {'min': 50, 'max': 80, 'step': 5}
        }
        
        # Run optimization
        results = optimizer.optimize_strategy(
            project_id=int(qc_config.get('project_id', 0)),
            strategy='adaptive_ema_v2',
            parameters=parameters,
            wait=True
        )
        
        print(f"\nOptimization complete!")
        print(f"Best parameters: {results['results'][0]['parameterSet']}")
    else:
        print("QuantConnect credentials not configured in config.json")
        print("Add your user_id and api_token to use cloud optimization")
