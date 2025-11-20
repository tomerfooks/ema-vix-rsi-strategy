/**
 * Adaptive KAMA-ADX Strategy v2 - OpenCL Kernel
 * 
 * GPU-optimized trading strategy with key improvements:
 * 1. ADX percentile rank (less noisy than ATR for trend detection)
 * 2. KAMA (Kaufman Adaptive Moving Average) - single adaptive indicator
 * 3. ADX > 25 gate for entry filtering
 * 4. 1.5-2x ATR trailing stop for exits
 * 5. Dynamic EMA length scaling by ATR (smoother than discrete regimes)
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
    int param_offset = idx * 9;
    int kama_length = (int)params[param_offset + 0];
    int kama_fast = (int)params[param_offset + 1];
    int kama_slow = (int)params[param_offset + 2];
    int adx_length = (int)params[param_offset + 3];
    int adx_smooth = (int)params[param_offset + 4];
    float adx_threshold = params[param_offset + 5];
    int atr_length = (int)params[param_offset + 6];
    float trail_atr_mult = params[param_offset + 7];
    int adx_pct_length = (int)params[param_offset + 8];
    
    // Validate parameter constraints
    if (kama_fast >= kama_slow || adx_threshold < 15.0f || adx_threshold > 40.0f ||
        trail_atr_mult < 1.0f || trail_atr_mult > 3.0f) {
        results[idx * 5 + 4] = 0.0f;  // Mark as invalid
        return;
    }
    
    // Pre-calculate ATR (for trailing stops and dynamic scaling)
    float atr_values[2048];
    float alpha_atr = 2.0f / (atr_length + 1.0f);
    float atr = 0.0f;
    
    for (int i = 1; i < num_candles && i < 2048; i++) {
        float tr = fmax(highs[i] - lows[i], 
                       fmax(fabs(highs[i] - closes[i-1]), 
                            fabs(lows[i] - closes[i-1])));
        if (i == 1) {
            atr = tr;
        } else {
            atr = alpha_atr * tr + (1.0f - alpha_atr) * atr;
        }
        if (i >= atr_length) {
            atr_values[i] = atr;
        }
    }
    
    // Pre-calculate ADX
    float adx_values[2048];
    float dx_buffer[2048];
    
    // Calculate directional movement and true range
    for (int i = 1; i < num_candles && i < 2048; i++) {
        float up_move = highs[i] - highs[i-1];
        float down_move = lows[i-1] - lows[i];
        
        float plus_dm = (up_move > down_move && up_move > 0) ? up_move : 0.0f;
        float minus_dm = (down_move > up_move && down_move > 0) ? down_move : 0.0f;
        
        float tr = fmax(highs[i] - lows[i], 
                       fmax(fabs(highs[i] - closes[i-1]), 
                            fabs(lows[i] - closes[i-1])));
        
        // Smooth DM and TR
        if (i == 1) {
            dx_buffer[i] = 0.0f;
        } else if (i >= adx_length) {
            // Simple smoothing for DI calculation
            float plus_di = (tr > 0) ? (plus_dm / tr) * 100.0f : 0.0f;
            float minus_di = (tr > 0) ? (minus_dm / tr) * 100.0f : 0.0f;
            float di_sum = plus_di + minus_di;
            
            if (di_sum > 0) {
                dx_buffer[i] = fabs(plus_di - minus_di) / di_sum * 100.0f;
            } else {
                dx_buffer[i] = 0.0f;
            }
        }
    }
    
    // Smooth DX to get ADX
    float alpha_adx = 2.0f / (adx_smooth + 1.0f);
    float adx = 0.0f;
    for (int i = adx_length; i < num_candles && i < 2048; i++) {
        if (i == adx_length) {
            adx = dx_buffer[i];
        } else {
            adx = alpha_adx * dx_buffer[i] + (1.0f - alpha_adx) * adx;
        }
        adx_values[i] = adx;
    }
    
    // Calculate KAMA (Kaufman Adaptive Moving Average)
    float kama = closes[kama_length];
    float fast_sc = 2.0f / (kama_fast + 1.0f);
    float slow_sc = 2.0f / (kama_slow + 1.0f);
    
    // Trading state
    float capital = 10000.0f;
    float position = 0.0f;
    float entry_price = 0.0f;
    float trail_stop = 0.0f;
    float max_capital = capital;
    float max_drawdown = 0.0f;
    int trades = 0;
    
    int warmup = fmax(kama_length, fmax(adx_length + adx_smooth, atr_length)) + 10;
    
    // Backtest loop
    for (int i = warmup; i < num_candles && i < 2048; i++) {
        // Calculate KAMA efficiency ratio
        float change = fabs(closes[i] - closes[i - kama_length]);
        float volatility = 0.0f;
        for (int j = 0; j < kama_length; j++) {
            volatility += fabs(closes[i - j] - closes[i - j - 1]);
        }
        
        float er = (volatility > 0) ? change / volatility : 0.0f;
        float smooth = er * (fast_sc - slow_sc) + slow_sc;
        float sc = smooth * smooth;
        
        // Update KAMA
        kama = kama + sc * (closes[i] - kama);
        
        // Get ADX percentile rank
        float current_adx = adx_values[i];
        int count = 0;
        int lookback = fmin(adx_pct_length, i - warmup);
        for (int j = 1; j <= lookback; j++) {
            if (adx_values[i - j] < current_adx) count++;
        }
        float adx_rank_pct = (lookback > 0) ? ((float)count / lookback * 100.0f) : 50.0f;
        
        // Dynamic EMA length based on ATR percentile (for alternative trend confirmation)
        float current_atr = atr_values[i];
        int atr_count = 0;
        for (int j = 1; j <= lookback; j++) {
            if (atr_values[i - j] < current_atr) atr_count++;
        }
        float atr_pct = (lookback > 0) ? ((float)atr_count / lookback) : 0.5f;
        
        // Scale EMA: shorter in high vol (atr_pct high), longer in low vol
        int dynamic_ema_len = 30 + (int)(atr_pct * 40.0f); // Range 30-70
        
        // Calculate dynamic EMA for trend confirmation
        float alpha_ema = 2.0f / (dynamic_ema_len + 1.0f);
        float ema = closes[i - dynamic_ema_len];
        for (int k = i - dynamic_ema_len + 1; k <= i; k++) {
            ema = alpha_ema * closes[k] + (1.0f - alpha_ema) * ema;
        }
        
        // Entry Logic: KAMA crosses above price, ADX > threshold, price above EMA
        if (position == 0.0f && 
            kama > closes[i] * 1.001f &&  // KAMA slightly above price (bullish)
            current_adx > adx_threshold &&  // Strong trend (ADX gate)
            closes[i] > ema &&  // Price above dynamic EMA
            adx_rank_pct > 40.0f) {  // ADX in upper range (trending market)
            
            position = capital / closes[i];
            entry_price = closes[i];
            capital = 0.0f;
            
            // Set initial trailing stop
            trail_stop = entry_price - (trail_atr_mult * current_atr);
            
            // Log trade for first parameter set only
            if (idx == 0 && trades < 100) {
                trade_log[trades * 3 + 0] = (float)i;
                trade_log[trades * 3 + 1] = closes[i];
                trade_log[trades * 3 + 2] = 1.0f;  // Buy signal
            }
            trades++;
        }
        // Exit Logic: Trailing stop hit OR KAMA crosses below price
        else if (position > 0.0f) {
            // Update trailing stop (move up only)
            float new_stop = closes[i] - (trail_atr_mult * current_atr);
            if (new_stop > trail_stop) {
                trail_stop = new_stop;
            }
            
            // Check exit conditions
            if (closes[i] < trail_stop || kama < closes[i] * 0.999f) {
                capital = position * closes[i];
                
                if (idx == 0 && trades < 100) {
                    trade_log[trades * 3 + 0] = (float)i;
                    trade_log[trades * 3 + 1] = closes[i];
                    trade_log[trades * 3 + 2] = 0.0f;  // Sell signal
                }
                position = 0.0f;
                trades++;
            }
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
    
    // Filter invalid results
    if (trades < 2 || max_drawdown > 50.0f || !isfinite(total_return)) {
        results[idx * 5 + 4] = 0.0f;
    } else {
        float calmar = max_drawdown > 0 ? total_return / max_drawdown : 0.0f;
        float profit_factor = total_return > 0 ? 2.0f : 1.0f; // Simplified
        
        // Enhanced scoring: Calmar + profit factor bonus
        float score = calmar * 10.0f + profit_factor;
        
        // Store results
        results[idx * 5 + 0] = total_return;
        results[idx * 5 + 1] = max_drawdown;
        results[idx * 5 + 2] = (float)trades;
        results[idx * 5 + 3] = score;
        results[idx * 5 + 4] = 1.0f;  // Valid flag
    }
}
