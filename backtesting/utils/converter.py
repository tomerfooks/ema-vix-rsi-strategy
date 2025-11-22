"""
Convert OpenCL strategy configurations to QuantConnect format
"""

import re
from typing import Dict, Any, Optional


def parse_opencl_config(config_path: str) -> Dict[str, Any]:
    """
    Parse OpenCL .h config file to extract parameters.
    
    Args:
        config_path: Path to config_*.h file
    
    Returns:
        Dictionary of parameters
    """
    params = {}
    
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Extract #define statements
    define_pattern = r'#define\s+(\w+)\s+(\S+)'
    matches = re.findall(define_pattern, content)
    
    for name, value in matches:
        # Skip non-parameter defines
        if '_MIN' in name or '_MAX' in name or '_PERCENT' in name:
            continue
        
        # Try to convert to appropriate type
        try:
            if '.' in value:
                params[name.lower()] = float(value)
            else:
                params[name.lower()] = int(value)
        except ValueError:
            params[name.lower()] = value
    
    return params


def convert_opencl_params(config_path: str, strategy_name: str = 'adaptive_ema_v2') -> Dict[str, Any]:
    """
    Convert OpenCL parameters to QuantConnect strategy parameters.
    
    Args:
        config_path: Path to OpenCL config file
        strategy_name: Strategy name for mapping
    
    Returns:
        Dictionary ready for QuantConnect strategy
    """
    raw_params = parse_opencl_config(config_path)
    
    # Strategy-specific mapping
    if 'adaptive_ema' in strategy_name.lower():
        # Map OpenCL parameter names to Python strategy names
        qc_params = {
            'fast_base': raw_params.get('fast_base_1h', raw_params.get('fast_base_4h', raw_params.get('fast_base_1d', 8))),
            'slow_base': raw_params.get('slow_base_1h', raw_params.get('slow_base_4h', raw_params.get('slow_base_1d', 14))),
            'fast_mult': raw_params.get('fast_mult_1h', raw_params.get('fast_mult_4h', raw_params.get('fast_mult_1d', 1.6))),
            'slow_mult': raw_params.get('slow_mult_1h', raw_params.get('slow_mult_4h', raw_params.get('slow_mult_1d', 1.0))),
            'atr_length': raw_params.get('atr_length_1h', raw_params.get('atr_length_4h', raw_params.get('atr_length_1d', 12))),
            'vol_threshold': raw_params.get('vol_threshold_1h', raw_params.get('vol_threshold_4h', raw_params.get('vol_threshold_1d', 69))),
        }
        
        return qc_params
    
    # Return raw params if no specific mapping
    return raw_params


def generate_qc_algorithm(
    strategy_name: str,
    parameters: Dict[str, Any],
    symbol: str = 'QQQ',
    start_date: str = '2023-01-01',
    end_date: str = '2024-12-31'
) -> str:
    """
    Generate QuantConnect algorithm code from parameters.
    
    Args:
        strategy_name: Name of the strategy
        parameters: Strategy parameters
        symbol: Ticker symbol
        start_date: Start date
        end_date: End date
    
    Returns:
        Python code for QuantConnect algorithm
    """
    # Parse dates
    start_parts = start_date.split('-')
    end_parts = end_date.split('-')
    
    code = f'''
# QuantConnect Algorithm - {strategy_name}
# Auto-generated from OpenCL optimization

from AlgorithmImports import *

class {strategy_name.replace('_', '').title()}Algorithm(QCAlgorithm):
    
    def Initialize(self):
        """Initialize algorithm."""
        self.SetStartDate({start_parts[0]}, {start_parts[1]}, {start_parts[2]})
        self.SetEndDate({end_parts[0]}, {end_parts[1]}, {end_parts[2]})
        self.SetCash(10000)
        
        # Add equity
        self.symbol = self.AddEquity("{symbol}", Resolution.Hour).Symbol
        
        # Strategy parameters (optimized from OpenCL)
'''
    
    for key, value in parameters.items():
        code += f'        self.{key} = {value}\n'
    
    code += '''
        
        # Add your strategy logic here
        # See strategies/adaptive_ema_v2.py for full implementation
        
    def OnData(self, data):
        """Handle new data."""
        if not data.ContainsKey(self.symbol):
            return
        
        # Implement your strategy logic
        pass
'''
    
    return code


def create_strategy_file(
    opencl_config_path: str,
    output_path: str,
    strategy_name: str = 'adaptive_ema_v2'
):
    """
    Create a complete QuantConnect strategy file from OpenCL config.
    
    Args:
        opencl_config_path: Path to OpenCL config file
        output_path: Where to save the QC strategy
        strategy_name: Strategy name
    """
    params = convert_opencl_params(opencl_config_path, strategy_name)
    
    with open(output_path, 'w') as f:
        f.write(f"# QuantConnect Strategy: {strategy_name}\n")
        f.write(f"# Generated from: {opencl_config_path}\n\n")
        f.write("# Parameters:\n")
        for key, value in params.items():
            f.write(f"# {key} = {value}\n")
        f.write("\n")
        f.write("# Import and use strategies.adaptive_ema_v2.AdaptiveEMAV2\n")
        f.write("# with these parameters for backtesting.\n")
    
    print(f"Strategy file created: {output_path}")
    print(f"Parameters extracted: {params}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python converter.py <opencl_config_path>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    params = convert_opencl_params(config_path)
    
    print("Extracted Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
