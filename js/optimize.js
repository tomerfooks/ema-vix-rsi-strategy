const { fetchData } = require('./dataFetcher');
const strategies = require('./strategies');

/**
 * Generate parameter combinations for optimization
 */
function generateParamCombinations(strategyClass) {
  const config = strategyClass.getConfig();
  const defaultParams = config.defaultParams;
  const ranges = config.optimizationRanges;
  
  const paramSets = [defaultParams]; // Start with default
  
  // Generate combinations by varying one parameter at a time
  for (const [paramName, range] of Object.entries(ranges)) {
    if (!range || range.length !== 2) continue;
    
    const [min, max] = range;
    const defaultValue = defaultParams[paramName];
    
    // Test min, default, and max values
    const testValues = [min, defaultValue, max].filter((v, i, arr) => arr.indexOf(v) === i);
    
    for (const value of testValues) {
      if (value === defaultValue) continue; // Already have default
      
      paramSets.push({
        ...defaultParams,
        [paramName]: value
      });
    }
  }
  
  return paramSets;
}

/**
 * Generate comprehensive parameter grid for exhaustive search
 */
function generateParamGrid(strategyClass, granularity = null, includeParams = null) {
  const config = strategyClass.getConfig();
  const defaultParams = config.defaultParams;
  const ranges = config.optimizationRanges;
  
  const paramArrays = {};
  
  for (const [paramName, range] of Object.entries(ranges)) {
    // Skip if not in includeParams list (when specified)
    if (includeParams && !includeParams.includes(paramName)) continue;
    
    if (!range || range.length !== 2) continue;
    
    const [min, max] = range;
    
    // Generate ALL integer values between min and max (inclusive)
    const values = [];
    for (let value = min; value <= max; value++) {
      values.push(value);
    }
    
    paramArrays[paramName] = values;
  }
  
  // Generate all combinations (cartesian product)
  const keys = Object.keys(paramArrays);
  if (keys.length === 0) return [defaultParams];
  
  console.log(`\n📋 Parameter Grid:`);
  let totalCombinations = 1;
  for (const key of keys) {
    console.log(`   ${key}: ${paramArrays[key].length} values [${paramArrays[key].join(', ')}]`);
    totalCombinations *= paramArrays[key].length;
  }
  console.log(`   Total combinations: ${totalCombinations.toLocaleString()}`);
  
  function cartesian(arrays, index = 0, current = {}) {
    if (index === keys.length) {
      return [{ ...defaultParams, ...current }];
    }
    
    const key = keys[index];
    const results = [];
    
    for (const value of arrays[key]) {
      results.push(...cartesian(arrays, index + 1, { ...current, [key]: value }));
    }
    
    return results;
  }
  
  return cartesian(paramArrays);
}

/**
 * Run optimization for a strategy
 */
async function optimizeStrategy(strategyClass, options = {}) {
  const config = strategyClass.getConfig();
  const {
    symbols = config.optimization.symbols,
    candles = config.optimization.candles,
    interval = config.optimization.interval,
    mode = 'quick', // 'quick' or 'exhaustive'
    includeParams = null  // Array of parameter names to optimize (null = all)
  } = options;
  
  console.log(`\n${'='.repeat(70)}`);
  console.log(`🔍 OPTIMIZING: ${config.name}`);
  console.log(`   Mode: ${mode.toUpperCase()}`);
  console.log(`   Symbols: ${symbols.join(', ')}`);
  console.log(`   Candles: ${candles} @ ${interval}`);
  if (includeParams) {
    console.log(`   Optimizing only: ${includeParams.join(', ')}`);
  }
  console.log('='.repeat(70));
  
  // Generate parameter sets
  const paramSets = mode === 'exhaustive' 
    ? generateParamGrid(strategyClass, null, includeParams)
    : generateParamCombinations(strategyClass);
  
  console.log(`\n📊 Testing ${paramSets.length} parameter combinations...`);
  
  // Fetch data for all symbols
  const symbolData = {};
  for (const symbol of symbols) {
    const candlesRequest = interval === '1h' ? `${candles}h` : 
                          interval === '4h' ? `${Math.floor(candles * 4)}h` :
                          `${Math.floor(candles)}d`;
    
    const data = await fetchData(symbol, candlesRequest, interval);
    
    if (data && data.length >= strategyClass.prototype.getMinimumCandles.call({ params: config.defaultParams })) {
      symbolData[symbol] = data;
      console.log(`   ✓ Loaded ${symbol}: ${data.length} candles`);
    } else {
      console.log(`   ✗ Skipped ${symbol}: Insufficient data`);
    }
    
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  const validSymbols = Object.keys(symbolData);
  if (validSymbols.length === 0) {
    console.log('\n❌ No valid data loaded. Aborting optimization.');
    return null;
  }
  
  // Run backtest for each parameter set
  const results = [];
  let completed = 0;
  const startTime = Date.now();
  
  for (const params of paramSets) {
    let totalReturn = 0;
    let totalDrawdown = 0;
    let totalTrades = 0;
    let totalWinRate = 0;
    let totalProfitFactor = 0;
    let validRuns = 0;
    
    for (const symbol of validSymbols) {
      try {
        const strategy = new strategyClass(params);
        const candles = symbolData[symbol];
        
        // Calculate indicators
        const indicators = strategy.calculateIndicators(candles);
        const firstValidIdx = strategy.getFirstValidIndex(indicators, candles);
        
        if (firstValidIdx >= candles.length - 1) continue;
        
        // Run simplified backtest
        const result = runSimpleBacktest(candles, strategy, indicators, firstValidIdx);
        
        if (result.totalTrades > 0) {
          totalReturn += result.totalReturn;
          totalDrawdown += result.maxDrawdown;
          totalTrades += result.totalTrades;
          totalWinRate += result.winRate;
          totalProfitFactor += isFinite(result.profitFactor) ? result.profitFactor : 0;
          validRuns++;
        }
      } catch (error) {
        // Skip invalid parameter combinations
        continue;
      }
    }
    
    if (validRuns > 0) {
      results.push({
        params,
        avgReturn: totalReturn / validRuns,
        avgDrawdown: totalDrawdown / validRuns,
        avgTrades: totalTrades / validRuns,
        avgWinRate: totalWinRate / validRuns,
        avgProfitFactor: totalProfitFactor / validRuns,
        validRuns
      });
    }
    
    completed++;
    
    // Progress update
    if (completed % 10 === 0 || completed === paramSets.length) {
      const elapsed = (Date.now() - startTime) / 1000;
      const rate = completed / elapsed;
      const remaining = (paramSets.length - completed) / rate;
      
      console.log(`   Progress: ${completed}/${paramSets.length} (${(completed/paramSets.length*100).toFixed(1)}%) - ETA: ${remaining.toFixed(0)}s`);
    }
  }
  
  if (results.length === 0) {
    console.log('\n❌ No valid results. Try adjusting parameter ranges.');
    return null;
  }
  
  // Sort by average return
  results.sort((a, b) => b.avgReturn - a.avgReturn);
  
  // Display top results
  console.log(`\n${'='.repeat(70)}`);
  console.log(`🏆 TOP 5 PARAMETER SETS`);
  console.log('='.repeat(70));
  
  for (let i = 0; i < Math.min(5, results.length); i++) {
    const result = results[i];
    console.log(`\n#${i + 1} - Avg Return: ${result.avgReturn.toFixed(2)}%`);
    console.log(`   Avg Drawdown: ${result.avgDrawdown.toFixed(2)}%`);
    console.log(`   Avg Win Rate: ${result.avgWinRate.toFixed(1)}%`);
    console.log(`   Avg Profit Factor: ${result.avgProfitFactor.toFixed(2)}`);
    console.log(`   Avg Trades: ${result.avgTrades.toFixed(0)}`);
    console.log(`   Parameters:`);
    
    // Show only optimization parameters
    for (const [key, value] of Object.entries(result.params)) {
      if (config.optimizationRanges[key]) {
        console.log(`     ${key}: ${value}`);
      }
    }
  }
  
  return results[0];
}

/**
 * Simplified backtest for optimization (faster)
 */
function runSimpleBacktest(candles, strategy, indicators, firstValidIdx) {
  const trades = [];
  let position = null;
  let capital = strategy.params.initialCapital;
  let equity = capital;
  let peakEquity = capital;
  let maxDrawdown = 0;
  
  for (let i = firstValidIdx; i < candles.length - 1; i++) {
    const currentPrice = candles[i].close;
    
    // Entry
    if (!position && strategy.checkEntrySignal(i, indicators, candles, position)) {
      const shares = equity / currentPrice;
      position = {
        entryPrice: currentPrice,
        shares: shares,
        strategyData: strategy.getPositionData(i, indicators, candles)
      };
    }
    
    // Exit
    if (position) {
      const exitSignal = strategy.checkExitSignal(i, indicators, candles, position);
      
      if (exitSignal) {
        const pnl = (exitSignal.price - position.entryPrice) * position.shares - (strategy.params.commissionPerTrade || 0);
        equity += pnl;
        trades.push({ pnl });
        position = null;
      }
    }
    
    // Track drawdown
    const currentEquity = position 
      ? equity + (currentPrice - position.entryPrice) * position.shares - (strategy.params.commissionPerTrade || 0)
      : equity;
    
    if (currentEquity > peakEquity) peakEquity = currentEquity;
    const dd = ((peakEquity - currentEquity) / peakEquity) * 100;
    if (dd > maxDrawdown) maxDrawdown = dd;
  }
  
  // Close open position
  if (position) {
    const finalPrice = candles[candles.length - 1].close;
    const pnl = (finalPrice - position.entryPrice) * position.shares - (strategy.params.commissionPerTrade || 0);
    equity += pnl;
    trades.push({ pnl });
  }
  
  const validTrades = trades.filter(t => isFinite(t.pnl));
  const winningTrades = validTrades.filter(t => t.pnl > 0);
  const losingTrades = validTrades.filter(t => t.pnl <= 0);
  
  const winRate = validTrades.length > 0 ? (winningTrades.length / validTrades.length) * 100 : 0;
  const totalWinPnL = winningTrades.reduce((sum, t) => sum + t.pnl, 0);
  const totalLossPnL = Math.abs(losingTrades.reduce((sum, t) => sum + t.pnl, 0));
  const profitFactor = totalLossPnL > 0 ? totalWinPnL / totalLossPnL : (totalWinPnL > 0 ? Infinity : 0);
  
  return {
    totalReturn: ((equity - strategy.params.initialCapital) / strategy.params.initialCapital) * 100,
    maxDrawdown,
    totalTrades: validTrades.length,
    winRate,
    profitFactor
  };
}

// CLI Interface
if (require.main === module) {
  const args = process.argv.slice(2);
  
  // Parse arguments
  let strategyName = 'AdaptiveEMAStrategy';
  let mode = 'quick';
  let customSymbols = null;
  let includeParams = null;
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--strategy' || args[i] === '-s') {
      strategyName = args[i + 1];
      i++;
    } else if (args[i] === '--exhaustive' || args[i] === '-e') {
      mode = 'exhaustive';
    } else if (args[i] === '--symbols') {
      customSymbols = args[i + 1].split(',');
      i++;
    } else if (args[i] === '--params') {
      includeParams = args[i + 1].split(',');
      i++;
    }
  }
  
  const strategyClass = strategies[strategyName];
  
  if (!strategyClass) {
    console.error(`\n❌ Strategy "${strategyName}" not found.`);
    console.log('\nAvailable strategies:');
    Object.keys(strategies).forEach(name => {
      const config = strategies[name].getConfig();
      console.log(`  - ${name}: ${config.description}`);
    });
    console.log('\nUsage:');
    console.log('  node optimize.js --strategy <name> [options]');
    console.log('\nOptions:');
    console.log('  --exhaustive, -e          Use exhaustive grid search (default: quick)');
    console.log('  --symbols QQQ,SPY         Comma-separated symbols to test');
    console.log('  --params p1,p2            Optimize only specific parameters');
    console.log('\nExamples:');
    console.log('  node optimize.js --strategy RSIStrategy');
    console.log('  node optimize.js --strategy AdaptiveEMAStrategy --exhaustive');
    console.log('  node optimize.js --strategy MACDStrategy --params fastPeriod,slowPeriod');
    process.exit(1);
  }
  
  const options = { mode };
  if (customSymbols) options.symbols = customSymbols;
  if (includeParams) options.includeParams = includeParams;
  
  optimizeStrategy(strategyClass, options)
    .then((best) => {
      if (best) {
        console.log('\n✅ Optimization complete!');
      }
    })
    .catch(error => {
      console.error('\n❌ Optimization failed:', error);
      process.exit(1);
    });
}

module.exports = { optimizeStrategy, generateParamCombinations, generateParamGrid };
