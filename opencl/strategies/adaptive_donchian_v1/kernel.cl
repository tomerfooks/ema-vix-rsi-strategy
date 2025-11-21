/**
 * Adaptive Donchian Breakout Strategy v1 - OpenCL Kernel
 * 
 * GPU-optimized trading strategy using Donchian Channel breakouts
 * with ATR-based position adjustment and ADX confirmation.
 * 
 * Key Features:
 * - Donchian Channel (20-period by default) for breakout detection
 * - ATR-based threshold adjustment for filtering false breakouts
 * - ADX confirmation: Only takes trades when trend strength is above threshold
 * - Buy when price breaks above the Donchian high
 * - Sell when price breaks below the Donchian low
 * 
 * Parameters:
 * - donchian_length: Period for Donchian Channel calculation (default: 20)
 * - atr_length: Period for ATR calculation
 * - atr_multiplier: Multiplier for ATR threshold (e.g., 0.5 = half ATR added to breakout)
 * - adx_length: Period for ADX calculation
 * - adx_threshold: Minimum ADX value required for trade entry
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
    
    // Only log trades if this is a single-parameter run
    int should_log = (num_combinations == 1) ? 1 : 0;
    
    // Extract parameters for this combination (5 params)
    int param_offset = idx * 5;
    int donchian_length = (int)params[param_offset + 0];
    int atr_length = (int)params[param_offset + 1];
    float atr_multiplier = params[param_offset + 2];
    int adx_length = (int)params[param_offset + 3];
    float adx_threshold = params[param_offset + 4];
    
    // Validate parameter constraints
    if (donchian_length < 5 || atr_length < 5 || atr_multiplier < 0.0f || adx_threshold < 0.0f) {
        results[idx * 6 + 5] = 0.0f;  // Mark as invalid
        return;
    }
    
    // Pre-calculate ATR
    float atr_values[2048]; // Support up to 2048 candles
    float alpha_atr = 2.0f / (atr_length + 1.0f);
    float atr = 0.0f;
    
    // Initialize all ATR values to 0
    for (int i = 0; i < num_candles && i < 2048; i++) {
        atr_values[i] = 0.0f;
    }
    
    for (int i = 1; i < num_candles; i++) {
        float tr = fmax(highs[i] - lows[i], 
                       fmax(fabs(highs[i] - closes[i-1]), 
                            fabs(lows[i] - closes[i-1])));
        if (i == 1) {
            atr = tr;
        } else {
            atr = alpha_atr * tr + (1.0f - alpha_atr) * atr;
        }
        atr_values[i] = atr;
    }
    
    // Pre-calculate ADX
    float adx_values[2048];
    float alpha_adx = 2.0f / (adx_length + 1.0f);
    float plus_dm_smooth = 0.0f;
    float minus_dm_smooth = 0.0f;
    float atr_adx_smooth = 0.0f;
    
    // Initialize all ADX values to 0
    for (int i = 0; i < num_candles && i < 2048; i++) {
        adx_values[i] = 0.0f;
    }
    
    float adx = 0.0f;
    for (int i = 1; i < num_candles; i++) {
        // Calculate directional movement
        float high_diff = highs[i] - highs[i-1];
        float low_diff = lows[i-1] - lows[i];
        
        float plus_dm = (high_diff > low_diff && high_diff > 0.0f) ? high_diff : 0.0f;
        float minus_dm = (low_diff > high_diff && low_diff > 0.0f) ? low_diff : 0.0f;
        
        // Smooth directional movements and ATR
        if (i == 1) {
            plus_dm_smooth = plus_dm;
            minus_dm_smooth = minus_dm;
            atr_adx_smooth = atr_values[i];
        } else {
            plus_dm_smooth = alpha_adx * plus_dm + (1.0f - alpha_adx) * plus_dm_smooth;
            minus_dm_smooth = alpha_adx * minus_dm + (1.0f - alpha_adx) * minus_dm_smooth;
            atr_adx_smooth = alpha_adx * atr_values[i] + (1.0f - alpha_adx) * atr_adx_smooth;
        }
        
        // Calculate directional indicators
        float plus_di = (atr_adx_smooth > 0.0f) ? (plus_dm_smooth / atr_adx_smooth) * 100.0f : 0.0f;
        float minus_di = (atr_adx_smooth > 0.0f) ? (minus_dm_smooth / atr_adx_smooth) * 100.0f : 0.0f;
        
        // Calculate DX and ADX
        float di_sum = plus_di + minus_di;
        float dx = (di_sum > 0.0f) ? (fabs(plus_di - minus_di) / di_sum) * 100.0f : 0.0f;
        
        if (i < adx_length) {
            adx = dx;  // Initial ADX is just DX
        } else {
            adx = alpha_adx * dx + (1.0f - alpha_adx) * adx;
        }
        
        adx_values[i] = adx;
    }
    
    // Trading state
    float capital = 10000.0f;
    float position = 0.0f;
    float max_capital = capital;
    float max_drawdown = 0.0f;
    int trades = 0;
    int signals = 0;
    
    // For Sharpe ratio calculation
    float trade_returns[100];
    int num_trade_returns = 0;
    
    // Backtest loop - start after warmup period
    int warmup = (donchian_length > atr_length ? donchian_length : atr_length);
    warmup = (adx_length > warmup ? adx_length : warmup) + 5;
    
    for (int i = warmup; i < num_candles; i++) {
        // Calculate Donchian Channel high and low
        float donchian_high = highs[i - donchian_length];
        float donchian_low = lows[i - donchian_length];
        
        for (int j = i - donchian_length + 1; j < i; j++) {
            if (highs[j] > donchian_high) donchian_high = highs[j];
            if (lows[j] < donchian_low) donchian_low = lows[j];
        }
        
        // Get current ATR and ADX
        float current_atr = atr_values[i];
        float current_adx = adx_values[i];
        
        // Apply ATR-based threshold
        float breakout_threshold = current_atr * atr_multiplier;
        float buy_level = donchian_high + breakout_threshold;
        float sell_level = donchian_low - breakout_threshold;
        
        // Entry signal: Price breaks above Donchian high AND ADX is above threshold
        if (position == 0.0f && highs[i] > buy_level && current_adx >= adx_threshold) {
            position = capital / closes[i];
            capital = 0.0f;
            
            // Log trade
            if (should_log && signals < 100) {
                trade_log[signals * 3 + 0] = (float)i;
                trade_log[signals * 3 + 1] = closes[i];
                trade_log[signals * 3 + 2] = 1.0f;  // Buy
            }
            signals++;
        }
        // Exit signal: Price breaks below Donchian low
        else if (position > 0.0f && lows[i] < sell_level) {
            float exit_value = position * closes[i];
            float entry_value = 10000.0f;
            
            // Calculate cumulative entry value
            if (num_trade_returns > 0) {
                for (int t = 0; t < num_trade_returns; t++) {
                    entry_value *= (1.0f + trade_returns[t] / 100.0f);
                }
            }
            
            float trade_return = (exit_value - entry_value) / entry_value * 100.0f;
            
            // Store trade return
            if (num_trade_returns < 100) {
                trade_returns[num_trade_returns++] = trade_return;
            }
            
            capital = exit_value;
            
            // Log trade
            if (should_log && signals < 100) {
                trade_log[signals * 3 + 0] = (float)i;
                trade_log[signals * 3 + 1] = closes[i];
                trade_log[signals * 3 + 2] = 0.0f;  // Sell
            }
            position = 0.0f;
            signals++;
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
    
    // Calculate Sharpe ratio
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
        
        // Store results
        results[idx * 6 + 0] = total_return;
        results[idx * 6 + 1] = max_drawdown;
        results[idx * 6 + 2] = (float)trades;
        results[idx * 6 + 3] = calmar * 10.0f;  // Score
        results[idx * 6 + 4] = sharpe_ratio;
        results[idx * 6 + 5] = 1.0f;            // Valid flag
    }
}
