# OpenCL GPU Trading Strategy Optimizer

**GPU-accelerated strategy backtesting and parameter optimization for any OpenCL-compatible GPU**

Compatible with: AMD Radeon, Intel GPUs, NVIDIA, Apple Silicon (M1/M2/M3)

---

## 🚀 Quick Start

### Run Optimization (Automated)

```bash
./run.sh TICKER INTERVAL [CANDLES]
```

**Examples:**
```bash
./run.sh QQQ 1h          # 1-hour, 300 candles (default)
./run.sh AAPL 4h         # 4-hour, 270 candles (default)
./run.sh SPY 1d          # Daily, 150 candles (default)
./run.sh GOOG 1h 500     # 1-hour, custom 500 candles
```

The script automatically:
1. Fetches market data from Yahoo Finance
2. Compiles the optimizer
3. Runs GPU optimization
4. Shows best parameters and trade log

---

## 📁 Project Structure

```
opencl/
├── run.sh                  # Automated workflow script
├── optimize.c              # Main optimizer (**EDIT PARAMS HERE**)
├── fetch_data.py           # Data fetcher (Yahoo Finance)
├── Makefile                # Build configuration
├── data/                   # Downloaded market data (CSV)
└── strategies/             # Strategy modules (future use)
    └── adaptive_ema_v1/
        ├── config_1h.h     # 1-hour parameter definitions
        ├── config_4h.h     # 4-hour parameter definitions
        ├── config_1d.h     # Daily parameter definitions
        └── kernel.cl       # OpenCL GPU kernel
```

---

## 🎯 Strategy: Adaptive EMA v1

**Description**: EMA crossover strategy with adaptive periods based on market volatility

**Volatility Regimes:**
- **Low Volatility**: Shorter EMAs for faster trend-following
- **Medium Volatility**: Balanced EMA periods
- **High Volatility**: Longer EMAs for conservative entries

**Entry**: Fast EMA crosses above Slow EMA  
**Exit**: Fast EMA crosses below Slow EMA

---

## ⚙️ Tweaking Parameters (Min/Max Ranges)

### Understanding Min/Max System

The optimizer tests **all combinations** of parameters within min/max ranges:

```c
int default_fast_low = 13;    // Center value
float percent = 0.05;         // ±5% search range

// Automatically calculates:
min_fast_low = 13 * (1 - 0.05) = 12.35 → 12
max_fast_low = 13 * (1 + 0.05) = 13.65 → 13
// Tests: 12, 13 (2 values)
```

**All parameters expand similarly:**
- 10 parameters with ±5% each = ~20 million combinations
- GPU tests all combinations in seconds

### Step-by-Step: Tweaking Parameters

#### 1. Open the optimizer file
```bash
nano optimize.c
# Or use your preferred editor: vim, code, etc.
```

#### 2. Navigate to your timeframe section

**Parameter locations:**
- **1h interval**: Lines 53-90
- **4h interval**: Lines 91-128  
- **1d interval**: Lines 129-166

#### 3. Modify default values (centers of search ranges)

```c
if (strcmp(interval, "1h") == 0) {
    // === TWEAK THESE DEFAULTS ===
    int default_fast_low = 13;      // Fast EMA - Low Volatility
    int default_slow_low = 79;      // Slow EMA - Low Volatility
    int default_fast_med = 24;      // Fast EMA - Medium Volatility
    int default_slow_med = 97;      // Slow EMA - Medium Volatility
    int default_fast_high = 41;     // Fast EMA - High Volatility
    int default_slow_high = 119;    // Slow EMA - High Volatility
    int default_atr = 15;           // ATR Length
    int default_vol = 70;           // Volatility Lookback Period
    int default_low_pct = 27;       // Low Volatility Percentile
    int default_high_pct = 64;      // High Volatility Percentile
    
    // === TWEAK SEARCH RANGE (min/max width) ===
    float percent = 0.05;  // ±5% from defaults
    // This creates:
    // min = default * 0.95
    // max = default * 1.05
}
```

#### 4. Adjust search range percentage

```c
float percent = 0.01;  // Narrow: ±1% → ~100K tests, <1 sec
float percent = 0.03;  // Medium: ±3% → ~1M tests, ~1 sec
float percent = 0.05;  // Wide: ±5% → ~20M tests, ~5 sec
float percent = 0.08;  // Very wide: ±8% → 100M+ tests, may crash
```

**Choose based on:**
- **Exploratory**: Use 0.05-0.08 to find good regions
- **Fine-tuning**: Use 0.01-0.03 to refine known-good parameters
- **Production**: Use 0.01 for final optimization

#### 5. Save and test

```bash
./run.sh QQQ 1h   # Auto-compiles and runs with new parameters
```

### Example: Iterative Parameter Tuning

**Iteration 1 - Exploration:**
```c
int default_fast_low = 15;
float percent = 0.08;  // Wide search
```
```bash
./run.sh QQQ 1h
# Result: Best fast_low = 12, Return: 2.1%, Calmar: 0.45
```

**Iteration 2 - Refinement:**
```c
int default_fast_low = 12;  // Use best from iteration 1
float percent = 0.03;       // Narrow search around winner
```
```bash
./run.sh QQQ 1h
# Result: Best fast_low = 11, Return: 2.4%, Calmar: 0.52
```

**Iteration 3 - Validation:**
```c
int default_fast_low = 11;  // Use refined best
float percent = 0.01;       // Very narrow final search
```
```bash
./run.sh SPY 1h    # Test on different ticker
./run.sh QQQ 4h    # Test on different timeframe
```

---

## 🔄 Iterative Testing Workflow

### Complete Iteration Cycle

**Goal**: Find optimal parameters through systematic testing and refinement

#### Step 1: Baseline Test
```bash
./run.sh QQQ 1h
```

**Record baseline metrics:**
```
Test #1 - Baseline (QQQ 1h, defaults)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Parameters: fast_low=13, slow_low=79, percent=0.05
Return: 1.74%
Drawdown: 4.93%
Calmar: 0.35
Trades: 10
```

#### Step 2: Adjust Parameters
```bash
nano optimize.c  # Line 53 for 1h
```

**Change one dimension at a time:**
```c
// Iteration 2: Test faster EMAs
int default_fast_low = 10;   // Was 13
int default_slow_low = 65;   // Was 79
float percent = 0.05;        // Keep same
```

#### Step 3: Re-test
```bash
./run.sh QQQ 1h
```

**Record results:**
```
Test #2 - Faster EMAs (QQQ 1h)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Parameters: fast_low=10, slow_low=65, percent=0.05
Return: 2.45%  ⬆ IMPROVED
Drawdown: 6.12%  ⬇ Worse
Calmar: 0.40  ⬆ IMPROVED
Trades: 15  ⬆ More active
```

#### Step 4: Analyze & Decide

**Decision matrix:**
- ✅ **Better Calmar** → Keep changes
- ❌ **Worse Calmar** → Revert or try opposite direction
- ⚠️ **Mixed results** → Test on another ticker

#### Step 5: Test Different Symbols
```bash
./run.sh SPY 1h
./run.sh AAPL 1h
./run.sh MSFT 1h
```

**Track consistency:**
```
Symbol   Return   Drawdown   Calmar   Trades
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QQQ      2.45%    6.12%      0.40     15
SPY      1.89%    5.34%      0.35     12  ⚠ Lower
AAPL     3.12%    7.88%      0.40     18  ✅ Similar
MSFT     2.67%    6.45%      0.41     16  ✅ Good
```

#### Step 6: Refine Search Range
```c
// Parameters are good, narrow the search
int default_fast_low = 10;   // Keep winning value
int default_slow_low = 65;   // Keep winning value
float percent = 0.02;        // Narrow from 0.05
```

#### Step 7: Test Different Timeframes
```bash
./run.sh QQQ 1h
./run.sh QQQ 4h
./run.sh QQQ 1d
```

**Verify consistency across timeframes**

#### Step 8: Test Different Candle Counts
```bash
./run.sh QQQ 1h 200   # Less history
./run.sh QQQ 1h 300   # Default
./run.sh QQQ 1h 500   # More history
```

**Check robustness to data length**

### Iteration Template

Copy this for each test cycle:

```
Test #__: _________________ (Ticker: ___, Interval: ___, Candles: ___)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Changes Made:
  - Parameter: old_value → new_value
  - Reason: _________________

Command: ./run.sh ___ ___ ___

Results:
  Return:    ____% (baseline: ___%, change: __%)
  Drawdown:  ____% (baseline: ___%, change: __%)
  Calmar:    ____ (baseline: ____, change: ____)
  Trades:    ____ (baseline: ____, change: ____)

Decision: [KEEP / REVERT / TEST_MORE]
Next Step: _________________
```

### Advanced Iteration Strategies

#### A. Binary Search for Optimal Values
```
Test fast_low = 20 → Calmar: 0.30
Test fast_low = 10 → Calmar: 0.40  ✅ Better
Test fast_low = 5  → Calmar: 0.35  
Optimal range: 8-12
```

#### B. Grid Search with Multiple Tickers
```bash
# Test parameter matrix
for TICKER in QQQ SPY AAPL; do
  for PERCENT in 0.03 0.05 0.07; do
    # Edit optimize.c with each percent
    ./run.sh $TICKER 1h
  done
done
```

#### C. Walk-Forward Testing
```bash
./run.sh QQQ 1h 300   # Recent 300 candles
./run.sh QQQ 1h 500   # Recent 500 candles
./run.sh QQQ 1h 1000  # Recent 1000 candles
# Parameters should perform well across all periods
```

### When to Stop Iterating

✅ **Good stopping points:**
- Calmar Ratio > 1.0 consistently across tickers
- Similar performance on 3+ symbols
- Performance holds on different candle counts
- No significant improvement for 3+ iterations

⚠️ **Warning signs (over-fitting):**
- Perfect results on one ticker, terrible on others
- Performance degrades with more history
- Very high Calmar (>3.0) with few trades (<5)

## 🤖 AI Assistant Instructions

**For AI assistants testing and optimizing this system:**

### Complete Optimization Workflow for LLMs

This section guides you through the iterative process of finding optimal parameters. Follow this systematic approach:

#### Phase 1: Initial Test

```bash
# Test a specific symbol and interval
./run.sh QQQ 1h
```

**What to observe:**
- The HTML report will open showing performance metrics
- Note the optimized parameters in the "Optimized Parameters" section
- Record: Total Return, Max Drawdown, Calmar Ratio, Total Trades

#### Phase 2: Review Results

The optimization outputs TWO files:
1. **JSON file**: `strategies/adaptive_ema_v1/results/TIMESTAMP_SYMBOL_INTERVAL.json`
2. **HTML file**: `strategies/adaptive_ema_v1/results/TIMESTAMP_SYMBOL_INTERVAL.html`

**Open the HTML file** (it avoids CORS issues with embedded data):
- Shows performance metrics at the top
- Displays the optimized parameters
- Shows chart with trade entry/exit points
- Lists all trades with P&L

#### Phase 3: Extract Best Parameters

From the HTML report, copy the optimized parameters:
```
fast_low: 13
slow_low: 82
fast_med: 23
slow_med: 97
fast_high: 41
slow_high: 115
atr_length: 14
volatility_length: 71
low_vol_percentile: 26
high_vol_percentile: 62
```

#### Phase 4: Update Default Parameters

Edit `optimize.c` to use the best parameters as new defaults:

```bash
# Open the file (line 53 for 1h, line 91 for 4h, line 129 for 1d)
nano optimize.c
# Or: code optimize.c
# Or: vim optimize.c
```

**Find the section for your interval and update ALL default values:**

```c
if (strcmp(interval, "1h") == 0) {
    // Update with values from HTML report
    int default_fast_low = 13;      // From optimized results
    int default_slow_low = 82;      // From optimized results
    int default_fast_med = 23;      // From optimized results
    int default_slow_med = 97;      // From optimized results
    int default_fast_high = 41;     // From optimized results
    int default_slow_high = 115;    // From optimized results
    int default_atr = 14;           // From optimized results
    int default_vol = 71;           // From optimized results
    int default_low_pct = 26;       // From optimized results
    int default_high_pct = 62;      // From optimized results
    
    float percent = 0.05;  // Keep search range or adjust
}
```

**IMPORTANT**: Update ALL 10 parameters with the optimized values from the HTML report.

#### Phase 5: Re-run Optimization

```bash
./run.sh QQQ 1h
```

The optimizer will now search around the new (better) default values.

#### Phase 6: Compare Results

**Track improvement across iterations:**

```
Iteration 1 (Original defaults):
  Return: 8.50%, Drawdown: 6.20%, Calmar: 1.37, Trades: 14

Iteration 2 (Updated with best params from Iter 1):
  Return: 9.00%, Drawdown: 5.59%, Calmar: 1.61, Trades: 16
  ✅ IMPROVED: Better Calmar ratio

Iteration 3 (Updated with best params from Iter 2):
  Return: 9.10%, Drawdown: 5.45%, Calmar: 1.67, Trades: 15
  ✅ IMPROVED: Slightly better
```

#### Phase 7: Validate on Other Symbols

Test the same parameters on different symbols to ensure they're not overfit:

```bash
./run.sh SPY 1h
./run.sh AAPL 1h
./run.sh MSFT 1h
./run.sh GOOGL 1h
```

**Good parameters should perform reasonably well (Calmar > 1.0) on multiple symbols.**

#### Phase 8: Test Different Timeframes

```bash
./run.sh QQQ 4h
./run.sh QQQ 1d
```

Note: 4h and 1d have separate parameter sets in `optimize.c` (lines 91 and 129).

#### Phase 9: Test Different History Lengths

```bash
./run.sh QQQ 1h 300   # Default
./run.sh QQQ 1h 500   # More history
./run.sh QQQ 1h 700   # Even more history
```

**Robust parameters should maintain performance with different data lengths.**

#### Phase 10: Iterate Until Convergence

Repeat Phases 1-6 until:
- ✅ Calmar Ratio stops improving (change < 0.05)
- ✅ Parameters stabilize (similar values across iterations)
- ✅ Performance is consistent across multiple symbols
- ✅ Results are similar with different history lengths

### Complete Example: Full Iteration Cycle

```bash
# === ITERATION 1 ===
./run.sh QQQ 1h
# Results: Return=8.5%, Drawdown=6.2%, Calmar=1.37
# Best params: fast_low=12, slow_low=78, fast_med=22, slow_med=95...

# Edit optimize.c line 53, update all defaults:
# default_fast_low = 12  (was 13)
# default_slow_low = 78  (was 79)
# ... update all 10 parameters

# === ITERATION 2 ===
./run.sh QQQ 1h
# Results: Return=8.8%, Drawdown=5.9%, Calmar=1.49 ✅ IMPROVED
# Best params: fast_low=11, slow_low=76, fast_med=21, slow_med=93...

# Edit optimize.c line 53, update all defaults again
# default_fast_low = 11  (was 12)
# default_slow_low = 76  (was 78)
# ... update all 10 parameters

# === ITERATION 3 ===
./run.sh QQQ 1h
# Results: Return=8.9%, Drawdown=5.8%, Calmar=1.53 ✅ IMPROVED (slightly)
# Best params: fast_low=11, slow_low=75, fast_med=21, slow_med=92...

# Edit optimize.c line 53, update defaults
# default_fast_low = 11  (unchanged)
# default_slow_low = 75  (was 76)
# ... update all 10 parameters

# === ITERATION 4 ===
./run.sh QQQ 1h
# Results: Return=8.9%, Drawdown=5.7%, Calmar=1.56 ✅ IMPROVED (minimal)
# Best params: fast_low=11, slow_low=75, fast_med=21, slow_med=92...
# ✅ Parameters stabilized - ready to validate

# === VALIDATION ===
./run.sh SPY 1h    # Calmar=1.42 ✅ Good
./run.sh AAPL 1h   # Calmar=1.38 ✅ Good
./run.sh MSFT 1h   # Calmar=1.51 ✅ Good

./run.sh QQQ 4h    # Test different timeframe
./run.sh QQQ 1h 500  # Test more history

# ✅ Parameters are validated and ready for production
```

### Quick Testing Protocol

```bash
# 1. Run test
./run.sh SYMBOL INTERVAL

# 2. Open HTML file in browser (auto-opens or check strategies/*/results/)
# 3. Copy ALL optimized parameters from "Optimized Parameters" section
# 4. Edit optimize.c (line 53/91/129 based on interval)
# 5. Replace ALL default_* values with optimized values
# 6. Save file
# 7. Repeat from step 1

# Continue until Calmar improvement < 0.05 or parameters stabilize
```

### Important Notes for LLMs

1. **HTML files are self-contained**: They have embedded JSON data to avoid CORS errors. Always use the HTML file to view results.

2. **Update ALL parameters**: Don't cherry-pick. Update all 10 parameters from the optimized results.

3. **Track iterations**: Keep notes of each iteration's results to identify convergence.

4. **File locations**:
   - Main code: `optimize.c`
   - Parameter sections: Lines 53 (1h), 91 (4h), 129 (1d)
   - Results: `strategies/adaptive_ema_v1/results/*.html`

5. **Validation is crucial**: Test on multiple symbols before declaring success.

6. **Diminishing returns**: Don't over-optimize. Stop when improvements are < 5%.

### Systematic Parameter Update Checklist

When updating `optimize.c` after each test:

```c
if (strcmp(interval, "1h") == 0) {
    // ✅ 1. Update Low Volatility EMAs
    int default_fast_low = ____;   // From HTML: fast_low
    int default_slow_low = ____;   // From HTML: slow_low
    
    // ✅ 2. Update Medium Volatility EMAs  
    int default_fast_med = ____;   // From HTML: fast_med
    int default_slow_med = ____;   // From HTML: slow_med
    
    // ✅ 3. Update High Volatility EMAs
    int default_fast_high = ____;  // From HTML: fast_high
    int default_slow_high = ____;  // From HTML: slow_high
    
    // ✅ 4. Update Technical Indicators
    int default_atr = ____;        // From HTML: atr_length
    int default_vol = ____;        // From HTML: volatility_length
    
    // ✅ 5. Update Volatility Thresholds
    int default_low_pct = ____;    // From HTML: low_vol_percentile
    int default_high_pct = ____;   // From HTML: high_vol_percentile
    
    // ✅ 6. Adjust search range if needed
    float percent = 0.05;  // Start with 5%, narrow to 0.02-0.03 for fine-tuning
}
```

### Advanced: Multi-Symbol Optimization

To find parameters that work across multiple symbols:

```bash
# Test each symbol and record Calmar ratios
./run.sh QQQ 1h   # Calmar: 1.61
./run.sh SPY 1h   # Calmar: 1.42
./run.sh AAPL 1h  # Calmar: 1.38
./run.sh MSFT 1h  # Calmar: 1.51

# Average Calmar: 1.48 (good consistency)

# Update optimize.c with params that had best AVERAGE performance
# Then re-test all symbols to verify improvement
```

### When to Stop Optimizing

✅ **Stop when:**
- Calmar improvement between iterations < 0.05
- Parameters don't change for 2+ iterations
- Performance is consistent across 3+ symbols
- Drawdown is acceptable (< 15%)
- Trade count is reasonable (5-20)

⚠️ **Warning signs (over-fitting):**
- Calmar > 3.0 on one symbol, < 0.5 on others
- Parameters change dramatically between iterations
- Very few trades (< 3) or excessive trades (> 30)
- Performance degrades with more historical data

---

## 🆕 Creating a New Strategy

### Strategy Development Workflow

#### Phase 1: Design Strategy Logic

**Define your strategy:**
1. Entry conditions (when to buy)
2. Exit conditions (when to sell)
3. Parameters to optimize
4. Risk management rules

**Example strategies:**
- RSI overbought/oversold
- MACD crossover
- Bollinger Band breakout
- Volume-weighted moving average

#### Phase 2: Create Strategy Folder

```bash
cd strategies
mkdir my_new_strategy_v1
cd my_new_strategy_v1
```

#### Phase 3: Create Configuration Files

**Create `config_1h.h`:**
```c
#ifndef CONFIG_1H_H
#define CONFIG_1H_H

// === YOUR STRATEGY PARAMETERS ===
#define RSI_PERIOD_DEFAULT 14
#define RSI_PERIOD_MIN 10
#define RSI_PERIOD_MAX 20

#define OVERBOUGHT_DEFAULT 70
#define OVERBOUGHT_MIN 65
#define OVERBOUGHT_MAX 80

#define OVERSOLD_DEFAULT 30
#define OVERSOLD_MIN 20
#define OVERSOLD_MAX 35

// Add more parameters as needed

#endif
```

**Copy for other timeframes:**
```bash
cp config_1h.h config_4h.h
cp config_1h.h config_1d.h
# Edit each with timeframe-specific defaults
```

#### Phase 4: Write OpenCL Kernel

**Create `kernel.cl`:**
```c
// YOUR STRATEGY LOGIC HERE
__kernel void backtest_strategy(
    __global const float* high,
    __global const float* low,
    __global const float* close,
    const int data_length,
    
    // Your parameters
    const int rsi_period,
    const int overbought,
    const int oversold,
    
    // Output
    __global float* equity_curve,
    __global int* trades
) {
    int idx = get_global_id(0);
    
    // Initialize
    float cash = 10000.0f;
    int position = 0;
    
    // Loop through bars
    for (int i = rsi_period; i < data_length; i++) {
        // Calculate RSI (your indicator logic)
        float rsi = calculate_rsi(close, i, rsi_period);
        
        // Entry logic
        if (position == 0 && rsi < oversold) {
            position = (int)(cash / close[i]);
            cash -= position * close[i];
        }
        
        // Exit logic
        if (position > 0 && rsi > overbought) {
            cash += position * close[i];
            position = 0;
        }
        
        // Record equity
        equity_curve[i] = cash + (position * close[i]);
    }
}
```

#### Phase 5: Integrate into Main Optimizer

**Edit `optimize.c`:**

1. **Add config includes** (line ~20):
```c
// Strategy configs
#include "strategies/my_new_strategy_v1/config_1h.h"
#include "strategies/my_new_strategy_v1/config_4h.h"
#include "strategies/my_new_strategy_v1/config_1d.h"
```

2. **Update Config struct** (line ~23):
```c
typedef struct {
    // Your new parameters
    int rsi_period;
    int overbought;
    int oversold;
    // Add min/max for each
    int rsi_period_min, rsi_period_max;
    int overbought_min, overbought_max;
    int oversold_min, oversold_max;
} Config;
```

3. **Update load_config()** (line ~47):
```c
if (strcmp(interval, "1h") == 0) {
    config.rsi_period = RSI_PERIOD_DEFAULT;
    config.overbought = OVERBOUGHT_DEFAULT;
    config.oversold = OVERSOLD_DEFAULT;
    
    float percent = 0.05;
    config.rsi_period_min = (int)(config.rsi_period * (1 - percent));
    config.rsi_period_max = (int)(config.rsi_period * (1 + percent));
    // ... repeat for all parameters
}
```

4. **Replace OpenCL kernel string** (line ~195):
```c
const char* kernel_source = 
    #include "strategies/my_new_strategy_v1/kernel.cl"
;
```

5. **Update parameter iteration loops** (line ~330):
```c
for (int rsi = config.rsi_period_min; rsi <= config.rsi_period_max; rsi++) {
    for (int ob = config.overbought_min; ob <= config.overbought_max; ob++) {
        for (int os = config.oversold_min; os <= config.oversold_max; os++) {
            // Set kernel arguments
            clSetKernelArg(kernel, 3, sizeof(int), &rsi);
            clSetKernelArg(kernel, 4, sizeof(int), &ob);
            clSetKernelArg(kernel, 5, sizeof(int), &os);
            
            // Execute and evaluate
            // ... (rest of execution logic)
        }
    }
}
```

#### Phase 6: Test Your Strategy

```bash
# Compile
make clean
make

# Test
./run.sh QQQ 1h

# Iterate and refine
# Edit parameters in optimize.c
./run.sh QQQ 1h
```

#### Phase 7: Validate

```bash
# Multiple tickers
./run.sh QQQ 1h
./run.sh SPY 1h
./run.sh AAPL 1h

# Multiple timeframes
./run.sh QQQ 1h
./run.sh QQQ 4h
./run.sh QQQ 1d

# Different history lengths
./run.sh QQQ 1h 200
./run.sh QQQ 1h 500
```

### Strategy Template

**Copy this structure:**
```
strategies/
└── my_strategy_v1/
    ├── config_1h.h      # 1-hour parameters
    ├── config_4h.h      # 4-hour parameters  
    ├── config_1d.h      # Daily parameters
    ├── kernel.cl        # OpenCL strategy logic
    └── README.md        # Strategy documentation
```

### Tips for Strategy Development

✅ **Do:**
- Start with 3-5 parameters (avoid over-parameterization)
- Use min/max ranges of ±5-10% for exploration
- Test on liquid symbols (QQQ, SPY, AAPL)
- Validate across multiple timeframes
- Document your strategy logic

❌ **Don't:**
- Add 10+ parameters (overfitting risk)
- Use very wide ranges (>±15%, explosion of combinations)
- Optimize on single ticker only
- Ignore drawdown metrics
- Skip validation step

---

## 📊 Output Interpretation

### Performance Metrics

```
Total Return: 1.74%          # Total profit/loss
Max Drawdown: 4.93%          # Largest peak-to-trough decline
Calmar Ratio: 0.35           # Return / Drawdown (higher is better)
Total Trades: 10             # Number of round-trips
Score: 3.53                  # Calmar * 10 (optimization objective)
```

### Trade Log Example

```
#1  BUY  @ $572.81 (candle 81)
#2  SELL @ $569.54 (candle 98) | P&L: -0.57%    # Loss
#3  BUY  @ $574.33 (candle 120)
#4  SELL @ $592.60 (candle 302) | P&L: +3.18%   # Win
```

### Good vs Bad Parameters

✅ **Good**:
- Calmar Ratio > 1.0
- Max Drawdown < 15%
- 5-15 trades
- Positive vs Buy & Hold

❌ **Bad**:
- Calmar Ratio < 0.3
- Max Drawdown > 25%
- < 3 or > 30 trades
- Large negative returns

---

## 🎮 GPU Performance

**Expected Speed:**
- **Apple Silicon (M1/M2)**: 10-20M tests/sec
- **AMD Radeon Pro**: 5-15M tests/sec
- **Integrated GPU**: 1-5M tests/sec

**Current configs:**
- 1h: ~23M combinations → 1-5 sec
- 4h: ~23M combinations → 1-5 sec
- 1d: ~74K combinations → <1 sec

---

## ⚡ Quick Reference

```bash
# Basic usage
./run.sh QQQ 1h

# Custom candles
./run.sh QQQ 1h 500

# Edit parameters
nano optimize.c     # Lines 45-165

# View last run
cat data/qqq_1h.csv
```

---

## 🐛 Troubleshooting

**"No data returned"**: Check ticker symbol and internet  
**"Too many combinations"**: Reduce `percent` in optimize.c  
**"Compilation failed"**: Check OpenCL availability  
**Slow performance**: Reduce candles or search range  

---

## 📚 Glossary

- **EMA**: Exponential Moving Average - weighted moving average favoring recent prices
- **Calmar Ratio**: Risk-adjusted return (Return / Max Drawdown)
- **Volatility Regime**: Market state (low/med/high volatility)
- **OpenCL**: Cross-platform GPU programming framework
- **Drawdown**: Peak-to-trough decline during trading period
