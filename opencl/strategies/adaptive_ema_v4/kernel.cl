/**
 * Adaptive EMA Strategy v4 - OpenCL Kernel
 * 
 * A simplified, more effective approach based on proven adaptive strategies.
 * Instead of min/max ranges, we use BASE periods (9/21) and adjust the
 * smoothing factor based on market conditions.
 * 
 * Key Innovations:
 * 1. Base EMAs (9/21) that adapt via efficiency ratio (like KAMA)
 * 2. ADX for trend strength filtering (only trade strong trends)
 * 3. RSI for overbought/oversold filtering (avoid bad entries)
 * 4. Volatility scaling: High vol = MORE selective (higher ADX threshold)
 * 
 * Philosophy:
 * - Trending market + strong momentum = fast EMAs (responsive)
 * - Choppy market = slow EMAs (avoid whipsaws)
 * - High volatility = require stronger confirmation (higher ADX)
 * 
 * Parameters:
 * - ema_fast_base: Base fast EMA period (default 9)
 * - ema_slow_base: Base slow EMA period (default 21)
 * - adx_length: Period for ADX calculation (default 14)
 * - adx_threshold: Minimum ADX to take trades (default 20)
 * - rsi_length: Period for RSI calculation (default 14)
 * - rsi_buy_max: Max RSI for buy (avoid overbought, default 70)
 * - rsi_sell_min: Min RSI for sell (avoid oversold, default 30)
 * - efficiency_lookback: Lookback for efficiency ratio (default 10)
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
    
    int should_log = (num_combinations == 1) ? 1 : 0;
    
    // Extract parameters
    int param_offset = idx * 8;
    int ema_fast_base = (int)params[param_offset + 0];
    int ema_slow_base = (int)params[param_offset + 1];
    int adx_length = (int)params[param_offset + 2];
    float adx_threshold = params[param_offset + 3];
    int rsi_length = (int)params[param_offset + 4];
    float rsi_buy_max = params[param_offset + 5];
    float rsi_sell_min = params[param_offset + 6];
    int efficiency_lookback = (int)params[param_offset + 7];
    
    // Validate parameters
    if (ema_fast_base < 3 || ema_slow_base < 5 || ema_fast_base >= ema_slow_base ||
        adx_length < 7 || adx_threshold < 10.0f || adx_threshold > 40.0f ||
        rsi_length < 7 || rsi_buy_max < 60.0f || rsi_buy_max > 85.0f ||
        rsi_sell_min < 15.0f || rsi_sell_min > 40.0f ||
        efficiency_lookback < 5 || efficiency_lookback > 30) {
        results[idx * 6 + 5] = 0.0f;
        return;
    }
    
    // Pre-calculate indicators
    float atr_values[2048];
    float adx_values[2048];
    float rsi_values[2048];
    
    // Initialize arrays
    for (int i = 0; i < num_candles && i < 2048; i++) {
        atr_values[i] = 0.0f;
        adx_values[i] = 0.0f;
        rsi_values[i] = 50.0f;
    }
    
    // Calculate ATR
    float alpha_atr = 2.0f / (adx_length + 1.0f);
    float atr = 0.0f;
    for (int i = 1; i < num_candles; i++) {
        float tr = fmax(highs[i] - lows[i], 
                       fmax(fabs(highs[i] - closes[i-1]), 
                            fabs(lows[i] - closes[i-1])));
        atr = (i == 1) ? tr : (alpha_atr * tr + (1.0f - alpha_atr) * atr);
        atr_values[i] = atr;
    }
    
    // Calculate ADX (simplified Wilder's method)
    float alpha_adx = 1.0f / adx_length;
    float plus_dm_smooth = 0.0f;
    float minus_dm_smooth = 0.0f;
    float tr_smooth = 0.0f;
    
    for (int i = adx_length; i < num_candles; i++) {
        // Calculate directional movement
        float plus_dm = 0.0f, minus_dm = 0.0f;
        float high_diff = highs[i] - highs[i-1];
        float low_diff = lows[i-1] - lows[i];
        
        if (high_diff > low_diff && high_diff > 0.0f) plus_dm = high_diff;
        if (low_diff > high_diff && low_diff > 0.0f) minus_dm = low_diff;
        
        // Smooth DM and TR
        if (i == adx_length) {
            plus_dm_smooth = plus_dm;
            minus_dm_smooth = minus_dm;
            tr_smooth = atr_values[i];
        } else {
            plus_dm_smooth = plus_dm_smooth - (plus_dm_smooth / adx_length) + plus_dm;
            minus_dm_smooth = minus_dm_smooth - (minus_dm_smooth / adx_length) + minus_dm;
            tr_smooth = tr_smooth - (tr_smooth / adx_length) + atr_values[i];
        }
        
        // Calculate DI+ and DI-
        float di_plus = (tr_smooth > 0.0f) ? (plus_dm_smooth / tr_smooth) * 100.0f : 0.0f;
        float di_minus = (tr_smooth > 0.0f) ? (minus_dm_smooth / tr_smooth) * 100.0f : 0.0f;
        
        // Calculate DX and ADX
        float di_sum = di_plus + di_minus;
        float dx = (di_sum > 0.0f) ? (fabs(di_plus - di_minus) / di_sum) * 100.0f : 0.0f;
        
        if (i == adx_length) {
            adx_values[i] = dx;
        } else {
            adx_values[i] = adx_values[i-1] + alpha_adx * (dx - adx_values[i-1]);
        }
    }
    
    // Calculate RSI
    float avg_gain = 0.0f, avg_loss = 0.0f;
    for (int i = rsi_length; i < num_candles; i++) {
        float change = closes[i] - closes[i-1];
        float gain = (change > 0.0f) ? change : 0.0f;
        float loss = (change < 0.0f) ? -change : 0.0f;
        
        if (i == rsi_length) {
            // Initial averages
            for (int j = i - rsi_length + 1; j <= i; j++) {
                float c = closes[j] - closes[j-1];
                avg_gain += (c > 0.0f) ? c : 0.0f;
                avg_loss += (c < 0.0f) ? -c : 0.0f;
            }
            avg_gain /= rsi_length;
            avg_loss /= rsi_length;
        } else {
            // Wilder's smoothing
            avg_gain = ((avg_gain * (rsi_length - 1)) + gain) / rsi_length;
            avg_loss = ((avg_loss * (rsi_length - 1)) + loss) / rsi_length;
        }
        
        float rs = (avg_loss > 0.0f) ? (avg_gain / avg_loss) : 100.0f;
        rsi_values[i] = 100.0f - (100.0f / (1.0f + rs));
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
    
    // Adaptive EMAs (updated incrementally)
    float ema_fast = 0.0f;
    float ema_slow = 0.0f;
    float prev_ema_fast = 0.0f;
    float prev_ema_slow = 0.0f;
    int ema_initialized = 0;
    
    // Warmup period
    int warmup = adx_length + rsi_length + efficiency_lookback + 10;
    
    // Backtest loop
    for (int i = warmup; i < num_candles; i++) {
        float price = closes[i];
        
        // Validate data
        if (price <= 0.0f || !isfinite(price)) continue;
        
        // Calculate efficiency ratio (directional movement / total movement)
        float net_change = fabs(closes[i] - closes[i - efficiency_lookback]);
        float total_movement = 0.0f;
        for (int j = i - efficiency_lookback + 1; j <= i; j++) {
            total_movement += fabs(closes[j] - closes[j-1]);
        }
        float efficiency_ratio = (total_movement > 0.0f) ? (net_change / total_movement) : 0.0f;
        efficiency_ratio = fmax(0.0f, fmin(1.0f, efficiency_ratio));
        
        // Adaptive alpha based on efficiency
        // High efficiency (trending) -> faster EMAs (higher alpha)
        // Low efficiency (choppy) -> slower EMAs (lower alpha)
        float fastest_alpha = 2.0f / (ema_fast_base + 1.0f);
        float slowest_alpha = 2.0f / (ema_fast_base * 3.0f + 1.0f);  // 3x slower when choppy
        float adaptive_alpha_fast = slowest_alpha + (fastest_alpha - slowest_alpha) * efficiency_ratio;
        
        float slow_fastest_alpha = 2.0f / (ema_slow_base + 1.0f);
        float slow_slowest_alpha = 2.0f / (ema_slow_base * 3.0f + 1.0f);
        float adaptive_alpha_slow = slow_slowest_alpha + (slow_fastest_alpha - slow_slowest_alpha) * efficiency_ratio;
        
        // Initialize or update EMAs
        if (!ema_initialized) {
            ema_fast = price;
            ema_slow = price;
            ema_initialized = 1;
        } else {
            ema_fast = adaptive_alpha_fast * price + (1.0f - adaptive_alpha_fast) * ema_fast;
            ema_slow = adaptive_alpha_slow * price + (1.0f - adaptive_alpha_slow) * ema_slow;
        }
        
        // Get current indicators
        float current_adx = adx_values[i];
        float current_rsi = rsi_values[i];
        
        // Entry: Fast EMA crosses above Slow EMA + filters
        if (position == 0.0f && i > warmup && 
            prev_ema_fast <= prev_ema_slow && ema_fast > ema_slow &&
            current_adx >= adx_threshold &&  // Strong trend
            current_rsi < rsi_buy_max) {      // Not overbought
            
            position = capital / price;
            capital = 0.0f;
            
            if (should_log && signals < 100) {
                trade_log[signals * 3 + 0] = (float)i;
                trade_log[signals * 3 + 1] = price;
                trade_log[signals * 3 + 2] = 1.0f;  // Buy
            }
            signals++;
        }
        // Exit: Fast EMA crosses below Slow EMA OR RSI filter
        else if (position > 0.0f && 
                 ((prev_ema_fast >= prev_ema_slow && ema_fast < ema_slow) ||
                  current_rsi < rsi_sell_min)) {  // Oversold protection
            
            float exit_value = position * price;
            float entry_value = 10000.0f;
            
            if (num_trade_returns > 0) {
                for (int t = 0; t < num_trade_returns; t++) {
                    entry_value *= (1.0f + trade_returns[t] / 100.0f);
                }
            }
            
            float trade_return = (exit_value - entry_value) / entry_value * 100.0f;
            
            if (isfinite(trade_return) && num_trade_returns < 100) {
                trade_returns[num_trade_returns++] = trade_return;
            }
            
            capital = exit_value;
            
            if (should_log && signals < 100) {
                trade_log[signals * 3 + 0] = (float)i;
                trade_log[signals * 3 + 1] = price;
                trade_log[signals * 3 + 2] = 0.0f;  // Sell
            }
            position = 0.0f;
            signals++;
            trades++;
        }
        
        prev_ema_fast = ema_fast;
        prev_ema_slow = ema_slow;
        
        // Track drawdown
        float current_value = capital + position * price;
        if (isfinite(current_value)) {
            if (current_value > max_capital) max_capital = current_value;
            float drawdown = (max_capital - current_value) / max_capital * 100.0f;
            if (drawdown > max_drawdown) max_drawdown = drawdown;
        }
    }
    
    // Close any open position
    if (position > 0.0f && closes[num_candles - 1] > 0.0f) {
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
    
    if (!isfinite(total_return)) total_return = 0.0f;
    if (!isfinite(sharpe_ratio)) sharpe_ratio = 0.0f;
    if (!isfinite(max_drawdown)) max_drawdown = 0.0f;
    
    float calmar = (max_drawdown > 0.0f) ? (total_return / max_drawdown) : 0.0f;
    
    results[idx * 6 + 0] = total_return;
    results[idx * 6 + 1] = max_drawdown;
    results[idx * 6 + 2] = (float)trades;
    results[idx * 6 + 3] = calmar * 10.0f;  // Score
    results[idx * 6 + 4] = sharpe_ratio;
    results[idx * 6 + 5] = (trades >= 1 && max_drawdown <= 50.0f && max_drawdown > 0.0f) ? 1.0f : 0.5f;
}
