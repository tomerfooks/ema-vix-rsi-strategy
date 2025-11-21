/**
 * Adaptive EMA with Volume Strategy v1 - OpenCL Kernel
 * 
 * GPU-optimized trading strategy combining:
 * - Adaptive EMA pairs based on volatility (from v2.1)
 * - Volume analysis for confirmation
 * - Market regime detection using EMA(50,200) + RSI
 * - ADX for trend strength confirmation
 * 
 * Key Features:
 * - Market Regime Detection: EMA(50,200) crossover + RSI to identify trend vs range
 * - Volume Confirmation: Requires above-average volume for entries
 * - Adaptive EMAs: Adjust based on volatility (ATR)
 * - ADX Filter: Only trades in trending markets
 * 
 * Parameters:
 * - fast_base, slow_base: Base EMA periods for trading signals
 * - fast_mult, slow_mult: Multipliers for high volatility
 * - atr_length: Period for ATR calculation
 * - vol_threshold: Percentile threshold for high volatility
 * - adx_length: Period for ADX calculation
 * - adx_threshold: Minimum ADX value required for trade entry
 * - rsi_length: Period for RSI calculation
 * - rsi_trending_min: Minimum RSI for bullish trend (e.g., 40)
 * - rsi_trending_max: Maximum RSI for bullish trend (e.g., 70)
 * - volume_ma_length: Period for volume moving average
 * - volume_threshold: Minimum volume as % of average (e.g., 1.2 = 120%)
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
    
    // Only log trades if this is a single-parameter run
    int should_log = (num_combinations == 1) ? 1 : 0;
    
    // Extract parameters for this combination (11 params now)
    int param_offset = idx * 11;
    int fast_base = (int)params[param_offset + 0];
    int slow_base = (int)params[param_offset + 1];
    float fast_mult = params[param_offset + 2];
    float slow_mult = params[param_offset + 3];
    int atr_length = (int)params[param_offset + 4];
    int vol_threshold = (int)params[param_offset + 5];
    int adx_length = (int)params[param_offset + 6];
    float adx_threshold = params[param_offset + 7];
    int rsi_length = (int)params[param_offset + 8];
    int rsi_trending_min = (int)params[param_offset + 9];
    int rsi_trending_max = (int)params[param_offset + 10];
    
    // Validate parameter constraints
    if (fast_base >= slow_base || fast_mult < 1.0f || slow_mult < 1.0f || 
        adx_threshold < 0.0f || rsi_trending_min >= rsi_trending_max) {
        results[idx * 6 + 5] = 0.0f;  // Mark as invalid
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
    
    for (int i = 0; i < num_candles && i < 2048; i++) {
        adx_values[i] = 0.0f;
    }
    
    float adx = 0.0f;
    for (int i = 1; i < num_candles; i++) {
        float high_diff = highs[i] - highs[i-1];
        float low_diff = lows[i-1] - lows[i];
        
        float plus_dm = (high_diff > low_diff && high_diff > 0.0f) ? high_diff : 0.0f;
        float minus_dm = (low_diff > high_diff && low_diff > 0.0f) ? low_diff : 0.0f;
        
        if (i == 1) {
            plus_dm_smooth = plus_dm;
            minus_dm_smooth = minus_dm;
            atr_adx_smooth = atr_values[i];
        } else {
            plus_dm_smooth = alpha_adx * plus_dm + (1.0f - alpha_adx) * plus_dm_smooth;
            minus_dm_smooth = alpha_adx * minus_dm + (1.0f - alpha_adx) * minus_dm_smooth;
            atr_adx_smooth = alpha_adx * atr_values[i] + (1.0f - alpha_adx) * atr_adx_smooth;
        }
        
        float plus_di = (atr_adx_smooth > 0.0f) ? (plus_dm_smooth / atr_adx_smooth) * 100.0f : 0.0f;
        float minus_di = (atr_adx_smooth > 0.0f) ? (minus_dm_smooth / atr_adx_smooth) * 100.0f : 0.0f;
        
        float di_sum = plus_di + minus_di;
        float dx = (di_sum > 0.0f) ? (fabs(plus_di - minus_di) / di_sum) * 100.0f : 0.0f;
        
        if (i < adx_length) {
            adx = dx;
        } else {
            adx = alpha_adx * dx + (1.0f - alpha_adx) * adx;
        }
        
        adx_values[i] = adx;
    }
    
    // Pre-calculate RSI
    float rsi_values[2048];
    float alpha_rsi = 1.0f / rsi_length;
    float avg_gain = 0.0f;
    float avg_loss = 0.0f;
    
    for (int i = 0; i < num_candles && i < 2048; i++) {
        rsi_values[i] = 50.0f;  // Neutral RSI
    }
    
    for (int i = 1; i < num_candles; i++) {
        float change = closes[i] - closes[i-1];
        float gain = (change > 0.0f) ? change : 0.0f;
        float loss = (change < 0.0f) ? -change : 0.0f;
        
        if (i == 1) {
            avg_gain = gain;
            avg_loss = loss;
        } else {
            avg_gain = alpha_rsi * gain + (1.0f - alpha_rsi) * avg_gain;
            avg_loss = alpha_rsi * loss + (1.0f - alpha_rsi) * avg_loss;
        }
        
        float rs = (avg_loss > 0.0f) ? (avg_gain / avg_loss) : 100.0f;
        float rsi = 100.0f - (100.0f / (1.0f + rs));
        rsi_values[i] = rsi;
    }
    
    // Pre-calculate regime EMAs (50 and 200)
    float ema_50_values[2048];
    float ema_200_values[2048];
    float alpha_50 = 2.0f / 51.0f;
    float alpha_200 = 2.0f / 201.0f;
    
    for (int i = 0; i < num_candles && i < 2048; i++) {
        ema_50_values[i] = closes[0];
        ema_200_values[i] = closes[0];
    }
    
    float ema_50 = closes[0];
    float ema_200 = closes[0];
    
    for (int i = 1; i < num_candles; i++) {
        ema_50 = alpha_50 * closes[i] + (1.0f - alpha_50) * ema_50;
        ema_200 = alpha_200 * closes[i] + (1.0f - alpha_200) * ema_200;
        ema_50_values[i] = ema_50;
        ema_200_values[i] = ema_200;
    }
    
    // Pre-calculate volume moving average
    float volume_ma_values[2048];
    int volume_ma_length = 20;  // Fixed 20-period volume MA
    
    for (int i = 0; i < num_candles && i < 2048; i++) {
        if (i < volume_ma_length) {
            volume_ma_values[i] = volumes[i];
        } else {
            float sum = 0.0f;
            for (int j = 0; j < volume_ma_length; j++) {
                sum += volumes[i - j];
            }
            volume_ma_values[i] = sum / volume_ma_length;
        }
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
    
    // Previous EMA values for crossover detection
    float prev_ema_fast = 0.0f;
    float prev_ema_slow = 0.0f;
    
    // Volatility lookback window
    int vol_length = 50;
    
    // Backtest loop - start after warmup period
    int warmup = 200;  // Need 200 candles for EMA(200)
    warmup = (atr_length > warmup ? atr_length : warmup);
    warmup = (adx_length > warmup ? adx_length : warmup);
    warmup = (rsi_length > warmup ? rsi_length : warmup);
    warmup = (vol_length > warmup ? vol_length : warmup) + 10;
    
    for (int i = warmup; i < num_candles; i++) {
        // Market Regime Detection
        float current_ema_50 = ema_50_values[i];
        float current_ema_200 = ema_200_values[i];
        float current_rsi = rsi_values[i];
        
        // Bullish regime: EMA(50) > EMA(200) AND RSI in trending zone
        int is_bullish_regime = (current_ema_50 > current_ema_200) && 
                                (current_rsi >= rsi_trending_min) && 
                                (current_rsi <= rsi_trending_max);
        
        // Volume confirmation
        float current_volume = volumes[i];
        float avg_volume = volume_ma_values[i];
        float volume_ratio = current_volume / avg_volume;
        int has_volume = (volume_ratio >= 1.0f);  // At least average volume
        
        // Determine volatility regime
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
        
        // Get current ADX value
        float current_adx = adx_values[i];
        
        // Adjust EMA periods based on volatility
        int fast_length = is_high_vol ? (int)(fast_base * fast_mult) : fast_base;
        int slow_length = is_high_vol ? (int)(slow_base * slow_mult) : slow_base;
        
        // Calculate trading EMAs with current periods
        float ema_fast = closes[0];
        float ema_slow = closes[0];
        float alpha_fast = 2.0f / (fast_length + 1.0f);
        float alpha_slow = 2.0f / (slow_length + 1.0f);
        
        for (int j = 1; j <= i; j++) {
            ema_fast = alpha_fast * closes[j] + (1.0f - alpha_fast) * ema_fast;
            ema_slow = alpha_slow * closes[j] + (1.0f - alpha_slow) * ema_slow;
        }
        
        // Entry signal: Fast EMA crosses above Slow EMA 
        // AND ADX above threshold
        // AND Bullish regime
        // AND Volume confirmation
        if (position == 0.0f && i > warmup && 
            prev_ema_fast <= prev_ema_slow && ema_fast > ema_slow && 
            current_adx >= adx_threshold &&
            is_bullish_regime &&
            has_volume) {
            
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
        // Exit signal: Fast EMA crosses below Slow EMA
        else if (position > 0.0f && prev_ema_fast >= prev_ema_slow && ema_fast < ema_slow) {
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
        
        // Store current EMAs for next iteration
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
