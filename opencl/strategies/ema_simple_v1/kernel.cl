/**
 * Simple EMA Strategy v1 - OpenCL Kernel
 * 
 * GPU-optimized trading strategy using a simple EMA crossover (default: 21/9)
 * No volatility adjustments - pure trend following.
 * 
 * Buy: When fast EMA crosses above slow EMA
 * Sell: When fast EMA crosses below slow EMA
 */

__kernel void optimize_strategy(
    __global const float* closes,
    __global const float* highs,
    __global const float* lows,
    int num_candles,
    __global const float* params,
    __global float* results,
    int num_combinations,
    __global float* trade_log
) {
    int idx = get_global_id(0);
    if (idx >= num_combinations) return;
    
    // Only log trades if this is a single-parameter run (num_combinations == 1)
    int should_log = (num_combinations == 1) ? 1 : 0;
    
    // Extract parameters for this combination
    int param_offset = idx * 2;
    int fast_length = (int)params[param_offset + 0];
    int slow_length = (int)params[param_offset + 1];
    
    // Validate parameter constraints
    if (fast_length >= slow_length) {
        results[idx * 6 + 5] = 0.0f;  // Mark as invalid
        return;
    }
    
    // Trading state
    float capital = 10000.0f;
    float position = 0.0f;
    float max_capital = capital;
    float max_drawdown = 0.0f;
    int trades = 0;              // Count of round-trip trades (buy+sell pair)
    int signals = 0;             // Count of individual signals (for logging)
    
    // For Sharpe ratio calculation
    float trade_returns[100];    // Store returns for each completed trade
    int num_trade_returns = 0;
    
    // Previous EMA values for crossover detection
    float prev_ema_fast = 0.0f;
    float prev_ema_slow = 0.0f;
    
    // Calculate EMA alpha values
    float alpha_fast = 2.0f / (fast_length + 1.0f);
    float alpha_slow = 2.0f / (slow_length + 1.0f);
    
    // Backtest loop
    for (int i = 1; i < num_candles; i++) {
        // Calculate EMAs by recalculating from history
        float ema_fast = closes[0];
        float ema_slow = closes[0];
        
        for (int j = 1; j <= i; j++) {
            ema_fast = alpha_fast * closes[j] + (1.0f - alpha_fast) * ema_fast;
            ema_slow = alpha_slow * closes[j] + (1.0f - alpha_slow) * ema_slow;
        }
        
        // Entry signal: Fast EMA crosses above Slow EMA
        if (position == 0.0f && i > 1 && prev_ema_fast <= prev_ema_slow && ema_fast > ema_slow) {
            position = capital / closes[i];
            capital = 0.0f;
            
            // Log trade only if this is a single-parameter backtest
            if (should_log && signals < 100) {
                trade_log[signals * 3 + 0] = (float)i;      // Candle index
                trade_log[signals * 3 + 1] = closes[i];     // Entry price
                trade_log[signals * 3 + 2] = 1.0f;          // Buy signal
            }
            signals++;
        }
        // Exit signal: Fast EMA crosses below Slow EMA
        else if (position > 0.0f && prev_ema_fast >= prev_ema_slow && ema_fast < ema_slow) {
            float exit_value = position * closes[i];
            float entry_value = 10000.0f;
            
            // Calculate cumulative capital for proper entry value
            if (num_trade_returns > 0) {
                for (int t = 0; t < num_trade_returns; t++) {
                    entry_value *= (1.0f + trade_returns[t] / 100.0f);
                }
            }
            
            float trade_return = (exit_value - entry_value) / entry_value * 100.0f;
            
            // Store trade return for Sharpe calculation
            if (num_trade_returns < 100) {
                trade_returns[num_trade_returns++] = trade_return;
            }
            
            capital = exit_value;
            
            // Log trade only if this is a single-parameter backtest
            if (should_log && signals < 100) {
                trade_log[signals * 3 + 0] = (float)i;
                trade_log[signals * 3 + 1] = closes[i];
                trade_log[signals * 3 + 2] = 0.0f;          // Sell signal
            }
            position = 0.0f;
            signals++;
            trades++;  // Count completed round-trip trade
        }
        
        // Store current EMAs for next iteration's crossover detection
        prev_ema_fast = ema_fast;
        prev_ema_slow = ema_slow;
        
        // Track drawdown
        float current_value = capital + position * closes[i];
        if (current_value > max_capital) max_capital = current_value;
        float drawdown = (max_capital - current_value) / max_capital * 100.0f;
        if (drawdown > max_drawdown) max_drawdown = drawdown;
    }
    
    // Close any open position
    if (position > 0.0f) {
        capital = position * closes[num_candles - 1];
    }
    
    // Calculate performance metrics
    float total_return = (capital - 10000.0f) / 10000.0f * 100.0f;
    
    // Calculate Sharpe ratio (assuming risk-free rate = 0)
    float sharpe_ratio = 0.0f;
    if (num_trade_returns > 1) {
        // Calculate mean return
        float mean_return = 0.0f;
        for (int i = 0; i < num_trade_returns; i++) {
            mean_return += trade_returns[i];
        }
        mean_return /= num_trade_returns;
        
        // Calculate standard deviation of returns
        float variance = 0.0f;
        for (int i = 0; i < num_trade_returns; i++) {
            float diff = trade_returns[i] - mean_return;
            variance += diff * diff;
        }
        variance /= num_trade_returns;
        float std_dev = sqrt(variance);
        
        // Sharpe ratio = mean return / std dev
        sharpe_ratio = (std_dev > 0.0f) ? (mean_return / std_dev) : 0.0f;
    }
    
    // Filter invalid results
    if (trades < 1 || max_drawdown > 50.0f || !isfinite(total_return)) {
        results[idx * 6 + 5] = 0.0f;
    } else {
        float calmar = max_drawdown > 0 ? total_return / max_drawdown : 0.0f;
        
        // Store results
        results[idx * 6 + 0] = total_return;
        results[idx * 6 + 1] = max_drawdown;
        results[idx * 6 + 2] = (float)trades;
        results[idx * 6 + 3] = calmar * 10.0f;  // Score
        results[idx * 6 + 4] = sharpe_ratio;
        results[idx * 6 + 5] = 1.0f;            // Valid flag
    }
}
