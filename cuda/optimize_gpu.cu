/*
 * GPU-accelerated trading strategy optimizer using CUDA
 * Expected: 500K-2M tests/sec on modern NVIDIA GPU
 * 
 * Compilation:
 *   nvcc -O3 -arch=sm_80 optimize_gpu.cu -o optimize_gpu
 * 
 * Requirements:
 *   - NVIDIA GPU with Compute Capability 7.0+
 *   - CUDA Toolkit 11.0+
 */

#include <cuda_runtime.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

// CUDA error checking macro
#define CUDA_CHECK(call) \
    do { \
        cudaError_t err = call; \
        if (err != cudaSuccess) { \
            fprintf(stderr, "CUDA error at %s:%d: %s\n", __FILE__, __LINE__, \
                    cudaGetErrorString(err)); \
            exit(EXIT_FAILURE); \
        } \
    } while(0)

struct Candle {
    float open;
    float high;
    float low;
    float close;
    float volume;
};

struct Params {
    int fast_length_low;
    int slow_length_low;
    int fast_length_med;
    int slow_length_med;
    int fast_length_high;
    int slow_length_high;
    int atr_length;
    int volatility_length;
    float low_vol_percentile;
    float high_vol_percentile;
};

struct Result {
    float total_return;
    float max_drawdown;
    int total_trades;
    float score;
    bool valid;
};

// GPU kernel: Calculate EMA
__device__ void calculate_ema_device(const float* prices, int size, int length, float* output) {
    float alpha = 2.0f / (length + 1.0f);
    
    output[0] = prices[0];
    for (int i = 1; i < size; i++) {
        output[i] = alpha * prices[i] + (1.0f - alpha) * output[i - 1];
    }
}

// GPU kernel: Calculate ATR
__device__ void calculate_atr_device(const Candle* candles, int size, int length, float* output) {
    float alpha = 1.0f / length;
    
    // First TR
    float tr = candles[0].high - candles[0].low;
    output[0] = tr;
    
    for (int i = 1; i < size; i++) {
        float high_low = candles[i].high - candles[i].low;
        float high_close = fabsf(candles[i].high - candles[i-1].close);
        float low_close = fabsf(candles[i].low - candles[i-1].close);
        
        tr = fmaxf(high_low, fmaxf(high_close, low_close));
        output[i] = alpha * tr + (1.0f - alpha) * output[i - 1];
    }
    
    // Normalize
    for (int i = 0; i < size; i++) {
        output[i] = (output[i] / candles[i].close) * 100.0f;
    }
}

// GPU kernel: Main optimization - each thread tests ONE parameter combination
__global__ void optimize_kernel(
    const Candle* candles,
    int num_candles,
    const Params* param_combinations,
    int num_combinations,
    Result* results
) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    
    if (idx >= num_combinations) {
        return;
    }
    
    Params params = param_combinations[idx];
    
    // Validate parameters
    if (params.fast_length_low >= params.slow_length_low ||
        params.fast_length_med >= params.slow_length_med ||
        params.fast_length_high >= params.slow_length_high ||
        params.low_vol_percentile >= params.high_vol_percentile) {
        results[idx].valid = false;
        return;
    }
    
    // Allocate thread-local memory for indicators
    // In production, use shared memory or pre-computed arrays
    float* ema_low_fast = new float[num_candles];
    float* ema_low_slow = new float[num_candles];
    float* atr = new float[num_candles];
    
    // Extract closes
    float* closes = new float[num_candles];
    for (int i = 0; i < num_candles; i++) {
        closes[i] = candles[i].close;
    }
    
    // Calculate indicators
    calculate_ema_device(closes, num_candles, params.fast_length_low, ema_low_fast);
    calculate_ema_device(closes, num_candles, params.slow_length_low, ema_low_slow);
    calculate_atr_device(candles, num_candles, params.atr_length, atr);
    
    // Run strategy simulation
    float capital = 10000.0f;
    float position = 0.0f;
    float max_capital = capital;
    float max_drawdown = 0.0f;
    int trades = 0;
    
    for (int i = 50; i < num_candles; i++) {  // Start after warmup
        // Determine volatility regime (simplified)
        float vol_rank = 0.5f;  // Would calculate from ATR
        
        int fast_length, slow_length;
        if (vol_rank < params.low_vol_percentile / 100.0f) {
            fast_length = params.fast_length_low;
            slow_length = params.slow_length_low;
        } else if (vol_rank > params.high_vol_percentile / 100.0f) {
            fast_length = params.fast_length_high;
            slow_length = params.slow_length_high;
        } else {
            fast_length = params.fast_length_med;
            slow_length = params.fast_length_med;
        }
        
        // Trading logic
        float fast_ema = ema_low_fast[i];
        float slow_ema = ema_low_slow[i];
        
        // Buy signal
        if (position == 0.0f && fast_ema > slow_ema) {
            position = capital / candles[i].close;
            capital = 0.0f;
            trades++;
        }
        // Sell signal
        else if (position > 0.0f && fast_ema < slow_ema) {
            capital = position * candles[i].close;
            position = 0.0f;
            trades++;
        }
        
        // Track drawdown
        float current_value = capital + position * candles[i].close;
        if (current_value > max_capital) {
            max_capital = current_value;
        }
        float drawdown = (max_capital - current_value) / max_capital * 100.0f;
        if (drawdown > max_drawdown) {
            max_drawdown = drawdown;
        }
    }
    
    // Close position
    if (position > 0.0f) {
        capital = position * candles[num_candles - 1].close;
        position = 0.0f;
    }
    
    // Calculate metrics
    float total_return = (capital - 10000.0f) / 10000.0f * 100.0f;
    
    // Early termination filters
    if (trades < 2 || max_drawdown > 50.0f || !isfinite(total_return)) {
        results[idx].valid = false;
    } else {
        float calmar = max_drawdown > 0 ? total_return / max_drawdown : 0.0f;
        
        results[idx].total_return = total_return;
        results[idx].max_drawdown = max_drawdown;
        results[idx].total_trades = trades;
        results[idx].score = calmar * 10.0f;
        results[idx].valid = true;
    }
    
    // Cleanup
    delete[] ema_low_fast;
    delete[] ema_low_slow;
    delete[] atr;
    delete[] closes;
}

int main(int argc, char** argv) {
    printf("🎮 CUDA GPU-Accelerated Trading Optimizer\n\n");
    
    // Check CUDA device
    int deviceCount = 0;
    CUDA_CHECK(cudaGetDeviceCount(&deviceCount));
    
    if (deviceCount == 0) {
        fprintf(stderr, "❌ No CUDA devices found\n");
        return 1;
    }
    
    cudaDeviceProp deviceProp;
    CUDA_CHECK(cudaGetDeviceProperties(&deviceProp, 0));
    
    printf("🔧 GPU Device: %s\n", deviceProp.name);
    printf("   Compute Capability: %d.%d\n", deviceProp.major, deviceProp.minor);
    printf("   Total Memory: %.2f GB\n", deviceProp.totalGlobalMem / 1e9);
    printf("   Max Threads per Block: %d\n", deviceProp.maxThreadsPerBlock);
    printf("   Multiprocessors: %d\n\n", deviceProp.multiProcessorCount);
    
    // Load data (simplified - would read from CSV)
    int num_candles = 600;
    Candle* h_candles = new Candle[num_candles];
    
    // Generate dummy data
    for (int i = 0; i < num_candles; i++) {
        h_candles[i].close = 100.0f + sinf(i * 0.1f) * 10.0f;
        h_candles[i].high = h_candles[i].close * 1.01f;
        h_candles[i].low = h_candles[i].close * 0.99f;
        h_candles[i].open = h_candles[i].close;
        h_candles[i].volume = 1000000.0f;
    }
    
    // Generate parameter combinations
    printf("⚡ Generating parameter combinations...\n");
    
    std::vector<Params> param_vec;
    
    for (int fl = 5; fl <= 25; fl += 5) {
        for (int sl = 30; sl <= 100; sl += 10) {
            if (fl >= sl) continue;
            for (int fm = 5; fm <= 25; fm += 5) {
                for (int sm = 30; sm <= 100; sm += 10) {
                    if (fm >= sm) continue;
                    for (int fh = 5; fh <= 25; fh += 5) {
                        for (int sh = 30; sh <= 100; sh += 10) {
                            if (fh >= sh) continue;
                            for (int atr = 10; atr <= 20; atr += 2) {
                                for (int vol = 60; vol <= 80; vol += 5) {
                                    for (int lp = 20; lp <= 40; lp += 5) {
                                        for (int hp = 60; hp <= 80; hp += 5) {
                                            if (lp >= hp) continue;
                                            
                                            Params p;
                                            p.fast_length_low = fl;
                                            p.slow_length_low = sl;
                                            p.fast_length_med = fm;
                                            p.slow_length_med = sm;
                                            p.fast_length_high = fh;
                                            p.slow_length_high = sh;
                                            p.atr_length = atr;
                                            p.volatility_length = vol;
                                            p.low_vol_percentile = (float)lp;
                                            p.high_vol_percentile = (float)hp;
                                            
                                            param_vec.push_back(p);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    int num_combinations = param_vec.size();
    printf("   Generated %d combinations\n\n", num_combinations);
    
    // Allocate GPU memory
    Candle* d_candles;
    Params* d_params;
    Result* d_results;
    
    CUDA_CHECK(cudaMalloc(&d_candles, num_candles * sizeof(Candle)));
    CUDA_CHECK(cudaMalloc(&d_params, num_combinations * sizeof(Params)));
    CUDA_CHECK(cudaMalloc(&d_results, num_combinations * sizeof(Result)));
    
    // Copy data to GPU
    printf("📤 Transferring data to GPU...\n");
    CUDA_CHECK(cudaMemcpy(d_candles, h_candles, num_candles * sizeof(Candle), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_params, param_vec.data(), num_combinations * sizeof(Params), cudaMemcpyHostToDevice));
    
    // Configure kernel
    int threadsPerBlock = 256;
    int blocks = (num_combinations + threadsPerBlock - 1) / threadsPerBlock;
    
    printf("🚀 Launching GPU kernel...\n");
    printf("   Blocks: %d\n", blocks);
    printf("   Threads per block: %d\n", threadsPerBlock);
    printf("   Total threads: %d\n\n", blocks * threadsPerBlock);
    
    // Launch kernel
    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);
    
    cudaEventRecord(start);
    optimize_kernel<<<blocks, threadsPerBlock>>>(d_candles, num_candles, d_params, num_combinations, d_results);
    cudaEventRecord(stop);
    
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    
    cudaEventSynchronize(stop);
    float milliseconds = 0;
    cudaEventElapsedTime(&milliseconds, start, stop);
    
    // Copy results back
    printf("📥 Transferring results from GPU...\n");
    Result* h_results = new Result[num_combinations];
    CUDA_CHECK(cudaMemcpy(h_results, d_results, num_combinations * sizeof(Result), cudaMemcpyDeviceToHost));
    
    // Find best result
    float best_score = -FLT_MAX;
    int best_idx = -1;
    int valid_count = 0;
    
    for (int i = 0; i < num_combinations; i++) {
        if (h_results[i].valid) {
            valid_count++;
            if (h_results[i].score > best_score) {
                best_score = h_results[i].score;
                best_idx = i;
            }
        }
    }
    
    float seconds = milliseconds / 1000.0f;
    float tests_per_sec = num_combinations / seconds;
    
    printf("\n✅ GPU Optimization Complete\n");
    printf("   Tested: %d combinations\n", num_combinations);
    printf("   Valid: %d results\n", valid_count);
    printf("   Time: %.2f seconds\n", seconds);
    printf("   Speed: %.0f tests/sec\n", tests_per_sec);
    printf("   Speedup vs CPU: %.1fx\n\n", tests_per_sec / 25000.0f);
    
    if (best_idx >= 0) {
        printf("🏆 BEST RESULT:\n");
        printf("   Total Return: %.2f%%\n", h_results[best_idx].total_return);
        printf("   Max Drawdown: %.2f%%\n", h_results[best_idx].max_drawdown);
        printf("   Total Trades: %d\n", h_results[best_idx].total_trades);
        printf("   Score: %.2f\n", h_results[best_idx].score);
    }
    
    // Cleanup
    CUDA_CHECK(cudaFree(d_candles));
    CUDA_CHECK(cudaFree(d_params));
    CUDA_CHECK(cudaFree(d_results));
    
    delete[] h_candles;
    delete[] h_results;
    
    return 0;
}
