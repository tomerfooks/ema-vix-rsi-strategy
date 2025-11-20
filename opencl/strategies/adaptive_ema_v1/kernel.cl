/**
 * Adaptive EMA Strategy v1 - OpenCL Kernel
 * 
 * GPU-optimized trading strategy that uses EMA crossovers with
 * adaptive periods based on market volatility.
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
    int param_offset = idx * 10;
    int fast_low = (int)params[param_offset + 0];
    int slow_low = (int)params[param_offset + 1];
    int fast_med = (int)params[param_offset + 2];
    int slow_med = (int)params[param_offset + 3];
    int fast_high = (int)params[param_offset + 4];
    int slow_high = (int)params[param_offset + 5];
    int atr_length = (int)params[param_offset + 6];
    int vol_length = (int)params[param_offset + 7];
    int low_pct = (int)params[param_offset + 8];
    int high_pct = (int)params[param_offset + 9];
    
    // Validate parameter constraints
    if (fast_low >= slow_low || fast_med >= slow_med || fast_high >= slow_high || low_pct >= high_pct) {
        results[idx * 6 + 5] = 0.0f;  // Mark as invalid
        return;
    }
    
    // Pre-calculate ATR
    float atr_values[1024]; // Assume max candles < 1024
    float alpha_atr = 2.0f / (atr_length + 1.0f);
    float atr = 0.0f;
    
    for (int i = 1; i < num_candles; i++) {
        float tr = fmax(highs[i] - lows[i], fmax(fabs(highs[i] - closes[i-1]), fabs(lows[i] - closes[i-1])));
        if (i == 1) {
            atr = tr;
        } else {
            atr = alpha_atr * tr + (1.0f - alpha_atr) * atr;
        }
        if (i >= atr_length) {
            atr_values[i] = atr;
        }
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
    
    // Backtest loop
    for (int i = vol_length + 1; i < num_candles; i++) {
        // Determine volatility regime
        float current_atr = atr_values[i];
        int count = 0;
        for (int j = i - vol_length; j < i; j++) {
            if (atr_values[j] < current_atr) count++;
        }
        float rank_pct = (float)count / vol_length * 100.0f;
        
        int regime = 1; // 0=low, 1=med, 2=high
        if (rank_pct < low_pct) regime = 0;
        else if (rank_pct > high_pct) regime = 2;
        
        // Select EMA lengths based on regime
        int fast_len, slow_len;
        if (regime == 0) {
            fast_len = fast_low;
            slow_len = slow_low;
        } else if (regime == 2) {
            fast_len = fast_high;
            slow_len = slow_high;
        } else {
            fast_len = fast_med;
            slow_len = slow_med;
        }
        
        // Calculate EMAs (simplified, assuming pre-warm)
        float alpha_fast = 2.0f / (fast_len + 1.0f);
        float alpha_slow = 2.0f / (slow_len + 1.0f);
        
        // Ensure we have enough data for EMA calculation
        int start_fast = (i - fast_len >= 0) ? (i - fast_len) : 0;
        int start_slow = (i - slow_len >= 0) ? (i - slow_len) : 0;
        
        // For simplicity, calculate EMAs on the fly (not optimal, but works)
        float ema_fast = closes[start_fast];
        float ema_slow = closes[start_slow];
        for (int k = start_fast + 1; k <= i; k++) {
            ema_fast = alpha_fast * closes[k] + (1.0f - alpha_fast) * ema_fast;
        }
        for (int k = start_slow + 1; k <= i; k++) {
            ema_slow = alpha_slow * closes[k] + (1.0f - alpha_slow) * ema_slow;
        }
        
        // Entry signal: Fast EMA crosses above Slow EMA (actual crossover, not just being above)
        if (position == 0.0f && i > vol_length + 1 && prev_ema_fast <= prev_ema_slow && ema_fast > ema_slow) {
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
        // Exit signal: Fast EMA crosses below Slow EMA (actual crossover)
        else if (position > 0.0f && prev_ema_fast >= prev_ema_slow && ema_fast < ema_slow) {
            float exit_value = position * closes[i];
            float entry_value = 10000.0f * (num_trade_returns == 0 ? 1.0f : (1.0f + trade_returns[num_trade_returns - 1] / 100.0f));
            if (num_trade_returns == 0) entry_value = 10000.0f;
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
        
        // Sharpe ratio = mean return / std dev (annualized approximation)
        sharpe_ratio = (std_dev > 0.0f) ? (mean_return / std_dev) : 0.0f;
    }
    
    // Filter invalid results (relaxed for short datasets)
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
