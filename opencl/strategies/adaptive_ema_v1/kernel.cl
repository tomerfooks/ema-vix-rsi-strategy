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
        results[idx * 5 + 4] = 0.0f;  // Mark as invalid
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
    int trades = 0;
    
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
        
        // For simplicity, calculate EMAs on the fly (not optimal, but works)
        float ema_fast = closes[i - fast_len];
        float ema_slow = closes[i - slow_len];
        for (int k = i - fast_len + 1; k <= i; k++) {
            ema_fast = alpha_fast * closes[k] + (1.0f - alpha_fast) * ema_fast;
        }
        for (int k = i - slow_len + 1; k <= i; k++) {
            ema_slow = alpha_slow * closes[k] + (1.0f - alpha_slow) * ema_slow;
        }
        
        // Entry signal: Fast EMA crosses above Slow EMA
        if (position == 0.0f && ema_fast > ema_slow && i > 50) {
            position = capital / closes[i];
            capital = 0.0f;
            
            // Log trade for first parameter set only
            if (idx == 0 && trades < 100) {
                trade_log[trades * 3 + 0] = (float)i;      // Candle index
                trade_log[trades * 3 + 1] = closes[i];     // Entry price
                trade_log[trades * 3 + 2] = 1.0f;          // Buy signal
            }
            trades++;
        }
        // Exit signal: Fast EMA crosses below Slow EMA
        else if (position > 0.0f && ema_fast < ema_slow) {
            capital = position * closes[i];
            
            if (idx == 0 && trades < 100) {
                trade_log[trades * 3 + 0] = (float)i;
                trade_log[trades * 3 + 1] = closes[i];
                trade_log[trades * 3 + 2] = 0.0f;          // Sell signal
            }
            position = 0.0f;
            trades++;
        }
        
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
    
    // Filter invalid results (relaxed for short datasets)
    if (trades < 1 || max_drawdown > 50.0f || !isfinite(total_return)) {
        results[idx * 5 + 4] = 0.0f;
    } else {
        float calmar = max_drawdown > 0 ? total_return / max_drawdown : 0.0f;
        
        // Store results
        results[idx * 5 + 0] = total_return;
        results[idx * 5 + 1] = max_drawdown;
        results[idx * 5 + 2] = (float)trades;
        results[idx * 5 + 3] = calmar * 10.0f;  // Score
        results[idx * 5 + 4] = 1.0f;            // Valid flag
    }
}
