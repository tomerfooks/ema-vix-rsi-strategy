/**
 * Adaptive EMA Strategy v2.2 - OpenCL Kernel
 * 
 * Enhanced strategy combining v2's adaptive EMAs with:
 * - RSI momentum filter (avoids buying overbought, selling oversold)
 * - Volume confirmation (requires above-average volume for entries)
 * 
 * Improvements over v2:
 * - RSI filter prevents bad entries in extreme conditions
 * - Volume filter ensures breakouts have institutional support
 * - Keeps v2's proven adaptive volatility logic
 */

__kernel void optimize_strategy(
    __global const float* closes,
    __global const float* highs,
    __global const float* lows,
    __global const float* volumes,
    int num_candles,
    __global const float* params,
    __global float* results,
    int num_combinations,
    __global float* trade_log
) {
    int idx = get_global_id(0);
    if (idx >= num_combinations) return;
    
    int should_log = (num_combinations == 1) ? 1 : 0;
    
    // Extract parameters (8 total)
    int param_offset = idx * 8;
    int fast_base = (int)params[param_offset + 0];
    int slow_base = (int)params[param_offset + 1];
    float fast_mult = params[param_offset + 2];
    float slow_mult = params[param_offset + 3];
    int atr_length = (int)params[param_offset + 4];
    int vol_threshold = (int)params[param_offset + 5];
    int rsi_length = (int)params[param_offset + 6];
    int rsi_threshold = (int)params[param_offset + 7];
    
    if (fast_base >= slow_base || fast_mult < 1.0f || slow_mult < 1.0f) {
        results[idx * 6 + 5] = 0.0f;
        return;
    }
    
    // Pre-calculate ATR
    float atr_values[2048];
    float alpha_atr = 2.0f / (atr_length + 1.0f);
    float atr = 0.0f;
    
    for (int i = 0; i < num_candles && i < 2048; i++) {
        atr_values[i] = 0.0f;
    }
    
    for (int i = 1; i < num_candles; i++) {
        float tr = fmax(highs[i] - lows[i], 
                       fmax(fabs(highs[i] - closes[i-1]), 
                            fabs(lows[i] - closes[i-1])));
        atr = (i == 1) ? tr : (alpha_atr * tr + (1.0f - alpha_atr) * atr);
        atr_values[i] = atr;
    }
    
    // Pre-calculate RSI
    float rsi_values[2048];
    for (int i = 0; i < num_candles && i < 2048; i++) {
        rsi_values[i] = 50.0f;
    }
    
    float avg_gain = 0.0f;
    float avg_loss = 0.0f;
    
    for (int i = 1; i < num_candles; i++) {
        float change = closes[i] - closes[i-1];
        float gain = (change > 0) ? change : 0.0f;
        float loss = (change < 0) ? -change : 0.0f;
        
        if (i <= rsi_length) {
            avg_gain += gain;
            avg_loss += loss;
            if (i == rsi_length) {
                avg_gain /= rsi_length;
                avg_loss /= rsi_length;
            }
        } else {
            avg_gain = (avg_gain * (rsi_length - 1) + gain) / rsi_length;
            avg_loss = (avg_loss * (rsi_length - 1) + loss) / rsi_length;
        }
        
        if (i >= rsi_length) {
            float rs = (avg_loss > 0) ? (avg_gain / avg_loss) : 100.0f;
            rsi_values[i] = 100.0f - (100.0f / (1.0f + rs));
        }
    }
    
    // Pre-calculate Volume MA
    float vol_ma[2048];
    int vol_ma_period = 20;
    for (int i = 0; i < num_candles && i < 2048; i++) {
        if (i < vol_ma_period) {
            vol_ma[i] = volumes[i];
        } else {
            float sum = 0.0f;
            for (int j = i - vol_ma_period + 1; j <= i; j++) {
                sum += volumes[j];
            }
            vol_ma[i] = sum / vol_ma_period;
        }
    }
    
    // Trading state
    float capital = 10000.0f;
    float position = 0.0f;
    float max_capital = capital;
    float max_drawdown = 0.0f;
    int trades = 0;
    int signals = 0;
    
    float trade_returns[100];
    int num_trade_returns = 0;
    
    float prev_ema_fast = 0.0f;
    float prev_ema_slow = 0.0f;
    
    int vol_length = 50;
    int warmup = 50;
    
    for (int i = warmup; i < num_candles; i++) {
        // Calculate volatility regime
        float current_atr = atr_values[i];
        float price = closes[i];
        float relative_volatility = (current_atr / price) * 100.0f;
        
        int count = 0;
        for (int j = i - vol_length; j < i; j++) {
            float historical_rv = (atr_values[j] / closes[j]) * 100.0f;
            if (historical_rv < relative_volatility) count++;
        }
        float vol_percentile = (float)count / vol_length * 100.0f;
        int is_high_vol = (vol_percentile >= vol_threshold) ? 1 : 0;
        
        // Adjust EMA periods
        int fast_length = is_high_vol ? (int)(fast_base * fast_mult) : fast_base;
        int slow_length = is_high_vol ? (int)(slow_base * slow_mult) : slow_base;
        
        // Calculate EMAs
        float ema_fast = closes[0];
        float ema_slow = closes[0];
        float alpha_fast = 2.0f / (fast_length + 1.0f);
        float alpha_slow = 2.0f / (slow_length + 1.0f);
        
        for (int j = 1; j <= i; j++) {
            ema_fast = alpha_fast * closes[j] + (1.0f - alpha_fast) * ema_fast;
            ema_slow = alpha_slow * closes[j] + (1.0f - alpha_slow) * ema_slow;
        }
        
        // Get indicators
        float rsi = rsi_values[i];
        float current_volume = volumes[i];
        float avg_volume = vol_ma[i];
        
        // Entry: EMA cross up + (RSI not overbought OR strong volume)
        // Changed from AND to OR logic - only need one filter to pass
        if (position == 0.0f && i > warmup) {
            int ema_cross_up = (prev_ema_fast <= prev_ema_slow && ema_fast > ema_slow);
            int rsi_ok = (rsi < (float)rsi_threshold);  // Not overbought
            int volume_ok = (current_volume > avg_volume * 1.05f);  // 5% above average (less strict)
            
            // Use OR logic: enter if EMA crosses AND (RSI is OK OR volume is strong)
            if (ema_cross_up && (rsi_ok || volume_ok)) {
                position = capital / closes[i];
                capital = 0.0f;
                
                if (should_log && signals < 100) {
                    trade_log[signals * 3 + 0] = (float)i;
                    trade_log[signals * 3 + 1] = closes[i];
                    trade_log[signals * 3 + 2] = 1.0f;
                }
                signals++;
            }
        }
        // Exit: EMA cross down
        else if (position > 0.0f && prev_ema_fast >= prev_ema_slow && ema_fast < ema_slow) {
            float exit_value = position * closes[i];
            float entry_value = 10000.0f;
            
            if (num_trade_returns > 0) {
                for (int t = 0; t < num_trade_returns; t++) {
                    entry_value *= (1.0f + trade_returns[t] / 100.0f);
                }
            }
            
            float trade_return = (exit_value - entry_value) / entry_value * 100.0f;
            if (num_trade_returns < 100) {
                trade_returns[num_trade_returns++] = trade_return;
            }
            
            capital = exit_value;
            
            if (should_log && signals < 100) {
                trade_log[signals * 3 + 0] = (float)i;
                trade_log[signals * 3 + 1] = closes[i];
                trade_log[signals * 3 + 2] = 0.0f;
            }
            
            position = 0.0f;
            signals++;
            trades++;
        }
        
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
    
    // Calculate metrics
    float total_return = (capital - 10000.0f) / 10000.0f * 100.0f;
    
    float sharpe_ratio = 0.0f;
    if (num_trade_returns > 1) {
        float mean_return = 0.0f;
        for (int i = 0; i < num_trade_returns; i++) {
            mean_return += trade_returns[i];
        }
        mean_return /= num_trade_returns;
        
        float variance = 0.0f;
        for (int i = 0; i < num_trade_returns; i++) {
            float diff = trade_returns[i] - mean_return;
            variance += diff * diff;
        }
        variance /= num_trade_returns;
        float std_dev = sqrt(variance);
        
        sharpe_ratio = (std_dev > 0.0f) ? (mean_return / std_dev) : 0.0f;
    }
    
    // Filter invalid results
    if (trades < 1 || max_drawdown > 50.0f || !isfinite(total_return)) {
        results[idx * 6 + 5] = 0.0f;
    } else {
        float calmar = max_drawdown > 0 ? total_return / max_drawdown : 0.0f;
        
        results[idx * 6 + 0] = total_return;
        results[idx * 6 + 1] = max_drawdown;
        results[idx * 6 + 2] = (float)trades;
        results[idx * 6 + 3] = calmar * 10.0f;
        results[idx * 6 + 4] = sharpe_ratio;
        results[idx * 6 + 5] = 1.0f;
    }
}
