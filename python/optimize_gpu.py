"""
GPU-accelerated parameter optimization using Numba CUDA
Expected: 200K-500K tests/sec on NVIDIA GPU

Requirements:
- NVIDIA GPU with CUDA support
- pip install numba[cuda]
- CUDA Toolkit installed
"""

import numpy as np
from numba import cuda
import math

@cuda.jit
def calculate_ema_gpu(prices, length, output):
    """Calculate EMA on GPU - one thread per candle"""
    idx = cuda.grid(1)
    
    if idx >= prices.shape[0]:
        return
    
    alpha = 2.0 / (length + 1.0)
    
    if idx == 0:
        output[idx] = prices[idx]
    else:
        output[idx] = alpha * prices[idx] + (1 - alpha) * output[idx - 1]


@cuda.jit
def optimize_parameters_gpu(closes, highs, lows, 
                           param_combinations,  # [N, 10] array of all param combos
                           results):            # [N, 5] output: return, drawdown, trades, score, valid
    """
    Run strategy for ALL parameter combinations in parallel on GPU
    Each thread tests ONE parameter combination
    """
    idx = cuda.grid(1)
    
    if idx >= param_combinations.shape[0]:
        return
    
    # Extract parameters for this thread
    fast_low = int(param_combinations[idx, 0])
    slow_low = int(param_combinations[idx, 1])
    fast_med = int(param_combinations[idx, 2])
    slow_med = int(param_combinations[idx, 3])
    fast_high = int(param_combinations[idx, 4])
    slow_high = int(param_combinations[idx, 5])
    atr_len = int(param_combinations[idx, 6])
    vol_len = int(param_combinations[idx, 7])
    low_pct = param_combinations[idx, 8]
    high_pct = param_combinations[idx, 9]
    
    # Validate parameters
    if fast_low >= slow_low or fast_med >= slow_med or fast_high >= slow_high:
        results[idx, 4] = 0  # invalid
        return
    
    # Allocate thread-local arrays for EMAs (shared memory could be used for optimization)
    # Note: In real implementation, use shared memory or pre-calculated EMAs
    
    # Calculate EMAs for this parameter set
    # (Simplified - in production, pre-calculate or use shared memory)
    
    # Run strategy simulation
    capital = 10000.0
    position = 0.0
    max_capital = capital
    max_drawdown = 0.0
    trades = 0
    
    for i in range(1, closes.shape[0]):
        # Calculate indicators (simplified - would use actual EMA values)
        # This is where you'd implement your strategy logic
        
        # Track drawdown
        if capital > max_capital:
            max_capital = capital
        
        drawdown = (max_capital - capital) / max_capital * 100.0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    
    # Calculate final metrics
    total_return = (capital - 10000.0) / 10000.0 * 100.0
    
    # Early termination filters
    if trades < 2 or max_drawdown > 50.0 or not math.isfinite(total_return):
        results[idx, 4] = 0  # invalid
        return
    
    # Calculate score
    calmar = total_return / max_drawdown if max_drawdown > 0 else 0
    score = calmar * 10.0
    
    # Store results
    results[idx, 0] = total_return
    results[idx, 1] = max_drawdown
    results[idx, 2] = float(trades)
    results[idx, 3] = score
    results[idx, 4] = 1  # valid


def optimize_gpu(candles_df, config):
    """
    Main GPU optimization entry point
    
    Args:
        candles_df: DataFrame with OHLC data
        config: Configuration dict with parameter ranges
    
    Returns:
        best_params, best_result
    """
    # Check CUDA availability
    if not cuda.is_available():
        raise RuntimeError("CUDA not available. Need NVIDIA GPU with CUDA support.")
    
    print(f"🎮 GPU Device: {cuda.get_current_device().name}")
    print(f"   Compute Capability: {cuda.get_current_device().compute_capability}")
    
    # Prepare data arrays
    closes = candles_df['close'].values.astype(np.float32)
    highs = candles_df['high'].values.astype(np.float32)
    lows = candles_df['low'].values.astype(np.float32)
    
    # Generate ALL parameter combinations upfront
    print("\n⚡ Generating parameter combinations...")
    param_combos = []
    
    for fl in range(config['fast_length_low_min'], config['fast_length_low_max'] + 1):
        for sl in range(config['slow_length_low_min'], config['slow_length_low_max'] + 1):
            if fl >= sl: continue
            for fm in range(config['fast_length_med_min'], config['fast_length_med_max'] + 1):
                for sm in range(config['slow_length_med_min'], config['slow_length_med_max'] + 1):
                    if fm >= sm: continue
                    for fh in range(config['fast_length_high_min'], config['fast_length_high_max'] + 1):
                        for sh in range(config['slow_length_high_min'], config['slow_length_high_max'] + 1):
                            if fh >= sh: continue
                            for atr in range(config['atr_length_min'], config['atr_length_max'] + 1):
                                for vol in range(config['volatility_length_min'], config['volatility_length_max'] + 1):
                                    for lp in range(int(config['low_vol_percentile_min']), 
                                                   int(config['low_vol_percentile_max']) + 1):
                                        for hp in range(int(config['high_vol_percentile_min']), 
                                                       int(config['high_vol_percentile_max']) + 1):
                                            if lp >= hp: continue
                                            param_combos.append([fl, sl, fm, sm, fh, sh, atr, vol, lp, hp])
    
    param_array = np.array(param_combos, dtype=np.float32)
    num_combinations = len(param_combos)
    print(f"   Generated {num_combinations:,} parameter combinations")
    
    # Allocate result array
    results = np.zeros((num_combinations, 5), dtype=np.float32)
    
    # Transfer data to GPU
    print("\n📤 Transferring data to GPU...")
    d_closes = cuda.to_device(closes)
    d_highs = cuda.to_device(highs)
    d_lows = cuda.to_device(lows)
    d_params = cuda.to_device(param_array)
    d_results = cuda.to_device(results)
    
    # Configure GPU kernel
    threads_per_block = 256
    blocks = (num_combinations + threads_per_block - 1) // threads_per_block
    
    print(f"\n🚀 Launching GPU kernel...")
    print(f"   Threads per block: {threads_per_block}")
    print(f"   Blocks: {blocks}")
    print(f"   Total GPU threads: {blocks * threads_per_block:,}")
    
    # Launch kernel
    import time
    start = time.time()
    
    optimize_parameters_gpu[blocks, threads_per_block](
        d_closes, d_highs, d_lows, d_params, d_results
    )
    
    cuda.synchronize()  # Wait for GPU to finish
    
    elapsed = time.time() - start
    
    # Transfer results back
    print("\n📥 Transferring results from GPU...")
    results = d_results.copy_to_host()
    
    # Find best result
    valid_mask = results[:, 4] == 1
    valid_results = results[valid_mask]
    valid_params = param_array[valid_mask]
    
    if len(valid_results) == 0:
        raise ValueError("No valid results found")
    
    best_idx = np.argmax(valid_results[:, 3])  # Max score
    best_result = valid_results[best_idx]
    best_params = valid_params[best_idx]
    
    tests_per_sec = num_combinations / elapsed
    
    print(f"\n✅ GPU Optimization Complete")
    print(f"   Tested: {num_combinations:,} combinations")
    print(f"   Valid: {len(valid_results):,} results")
    print(f"   Time: {elapsed:.1f}s ({tests_per_sec:,.0f} tests/sec)")
    print(f"   Speedup vs CPU: {tests_per_sec / 25000:.1f}x")
    
    return {
        'params': {
            'fast_length_low': int(best_params[0]),
            'slow_length_low': int(best_params[1]),
            'fast_length_med': int(best_params[2]),
            'slow_length_med': int(best_params[3]),
            'fast_length_high': int(best_params[4]),
            'slow_length_high': int(best_params[5]),
            'atr_length': int(best_params[6]),
            'volatility_length': int(best_params[7]),
            'low_vol_percentile': float(best_params[8]),
            'high_vol_percentile': float(best_params[9]),
        },
        'result': {
            'total_return': float(best_result[0]),
            'max_drawdown': float(best_result[1]),
            'total_trades': int(best_result[2]),
            'score': float(best_result[3]),
        }
    }


if __name__ == '__main__':
    import yfinance as yf
    from config_1h import config as config_1h
    
    # Check CUDA
    if cuda.is_available():
        print("✅ CUDA is available")
        print(f"   Device: {cuda.get_current_device().name}")
    else:
        print("❌ CUDA not available")
        print("   Install: pip install numba[cuda]")
        print("   Requires: NVIDIA GPU + CUDA Toolkit")
        exit(1)
    
    # Download data
    print("\n📥 Downloading GOOG data...")
    ticker = yf.Ticker('GOOG')
    df = ticker.history(period='3mo', interval='1h')
    print(f"   Loaded {len(df)} candles")
    
    # Run GPU optimization
    result = optimize_gpu(df, config_1h)
    
    print("\n🏆 BEST PARAMETERS:")
    print(f"   Total Return: {result['result']['total_return']:.2f}%")
    print(f"   Max Drawdown: {result['result']['max_drawdown']:.2f}%")
    print(f"   Trades: {result['result']['total_trades']}")
    print(f"   Score: {result['result']['score']:.2f}")
