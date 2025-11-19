const { calculateBuyAndHold } = require('./backtest');
const { fetchData } = require('./dataFetcher');
const { DEFAULT_PARAMS, OPTIMIZATION_CONFIG } = require('./config');
const { EMA, ATR } = require('technicalindicators');

/**
 * Generate parameter ranges based on ±X% of default values (from config)
 */
function generateSmartRanges() {
  const percent = OPTIMIZATION_CONFIG.rangePercent;
  const customRanges = OPTIMIZATION_CONFIG.paramRanges || {};
  
  const ranges = {
    fastLengthLow: getParamRange(customRanges.fastLengthLow, DEFAULT_PARAMS.fastLengthLow, percent),
    slowLengthLow: getParamRange(customRanges.slowLengthLow, DEFAULT_PARAMS.slowLengthLow, percent),
    fastLengthMed: getParamRange(customRanges.fastLengthMed, DEFAULT_PARAMS.fastLengthMed, percent),
    slowLengthMed: getParamRange(customRanges.slowLengthMed, DEFAULT_PARAMS.slowLengthMed, percent),
    fastLengthHigh: getParamRange(customRanges.fastLengthHigh, DEFAULT_PARAMS.fastLengthHigh, percent),
    slowLengthHigh: getParamRange(customRanges.slowLengthHigh, DEFAULT_PARAMS.slowLengthHigh, percent),
    atrLength: getParamRange(customRanges.atrLength, DEFAULT_PARAMS.atrLength, percent),
    volatilityLength: getParamRange(customRanges.volatilityLength, DEFAULT_PARAMS.volatilityLength, percent),
    lowVolPercentile: getParamRange(customRanges.lowVolPercentile, DEFAULT_PARAMS.lowVolPercentile, percent, 0, 100),
    highVolPercentile: getParamRange(customRanges.highVolPercentile, DEFAULT_PARAMS.highVolPercentile, percent, 0, 100)
  };
  return ranges;
}

function getParamRange(customValue, defaultValue, defaultPercent, min = 1, max = Infinity) {
  // If null or undefined, use default percentage
  if (customValue === null || customValue === undefined) {
    if (max === Infinity) {
      return generateRange(defaultValue, defaultPercent, min);
    } else {
      return generateRangeFloat(defaultValue, defaultPercent, min, max);
    }
  }
  
  // If it's a number, treat as percentage
  if (typeof customValue === 'number') {
    if (max === Infinity) {
      return generateRange(defaultValue, customValue, min);
    } else {
      return generateRangeFloat(defaultValue, customValue, min, max);
    }
  }
  
  // If it's an array, use generateRangeFromArray
  if (Array.isArray(customValue)) {
    return generateRangeFromArray(customValue);
  }
  
  // Fallback to default
  return generateRange(defaultValue, defaultPercent, min);
}

function generateRangeFromArray(arr) {
  // If [min, max] provided, generate all integers between them
  if (Array.isArray(arr) && arr.length === 2) {
    const [min, max] = arr;
    const range = [];
    for (let i = min; i <= max; i++) {
      range.push(i);
    }
    return range;
  }
  // If full array provided, use as-is
  if (Array.isArray(arr)) {
    return arr;
  }
  // Should not reach here, but return empty array as fallback
  return [];
}

function generateRange(value, percent, min = 1) {
  const lower = Math.max(min, Math.floor(value * (1 - percent)));
  const upper = Math.ceil(value * (1 + percent));
  
  // Generate all integer values in the range
  const range = [];
  for (let i = lower; i <= upper; i++) {
    range.push(i);
  }
  
  return range;
}

function generateRangeFloat(value, percent, min = 0, max = 100) {
  const lower = Math.max(min, Math.floor(value * (1 - percent)));
  const upper = Math.min(max, Math.ceil(value * (1 + percent)));
  
  // Generate all integer values in the range (percentiles are integers)
  const range = [];
  for (let i = lower; i <= upper; i++) {
    range.push(i);
  }
  
  return range;
}

/**
 * Generate parameter combinations for optimization
 */
function* generateParameterCombinations(options = {}) {
  const ranges = options.useSmartRanges ? generateSmartRanges() : {
    fastLengthLow: options.fastEmaRange || [5, 10, 14, 20, 25, 30, 35, 40, 43, 50, 60, 70, 80],
    slowLengthLow: options.slowEmaRange || [20, 30, 40, 50, 60, 70, 80, 90, 98, 100, 120, 140, 160, 180, 200],
    fastLengthMed: options.fastEmaRange || [5, 10, 14, 20, 25, 30, 35, 40, 43, 50, 60, 70, 80],
    slowLengthMed: options.slowEmaRange || [20, 30, 40, 50, 60, 70, 80, 90, 98, 100, 120, 140, 160, 180, 200],
    fastLengthHigh: options.fastEmaRange || [5, 10, 14, 20, 25, 30, 35, 40, 43, 50, 60, 70, 80],
    slowLengthHigh: options.slowEmaRange || [20, 30, 40, 50, 60, 70, 80, 90, 98, 100, 120, 140, 160, 180, 200],
    atrLength: options.atrLengthRange || [10, 14, 16, 20, 25, 30],
    volatilityLength: options.volatilityLengthRange || [50, 60, 71, 80, 100, 120],
    lowVolPercentile: options.lowVolPercentileRange || [20, 25, 28, 30, 33],
    highVolPercentile: options.highVolPercentileRange || [60, 65, 66, 70, 75]
  };

  const total = ranges.fastLengthLow.length * ranges.slowLengthLow.length *
                ranges.fastLengthMed.length * ranges.slowLengthMed.length *
                ranges.fastLengthHigh.length * ranges.slowLengthHigh.length *
                ranges.atrLength.length * ranges.volatilityLength.length *
                ranges.lowVolPercentile.length * ranges.highVolPercentile.length;

  console.log(`\n🔍 Optimization Configuration:`);
  console.log(`   Low Vol EMAs: ${ranges.fastLengthLow.length} fast × ${ranges.slowLengthLow.length} slow = ${ranges.fastLengthLow.length * ranges.slowLengthLow.length} combinations (with fast<slow filter)`);
  console.log(`   Med Vol EMAs: ${ranges.fastLengthMed.length} fast × ${ranges.slowLengthMed.length} slow = ${ranges.fastLengthMed.length * ranges.slowLengthMed.length} combinations (with fast<slow filter)`);
  console.log(`   High Vol EMAs: ${ranges.fastLengthHigh.length} fast × ${ranges.slowLengthHigh.length} slow = ${ranges.fastLengthHigh.length * ranges.slowLengthHigh.length} combinations (with fast<slow filter)`);
  console.log(`   ATR lengths: ${ranges.atrLength.length} values (${ranges.atrLength.join(', ')})`);
  console.log(`   Volatility lookback: ${ranges.volatilityLength.length} values (${ranges.volatilityLength.join(', ')})`);
  console.log(`   Percentile ranges: ${ranges.lowVolPercentile.length} low × ${ranges.highVolPercentile.length} high = ${ranges.lowVolPercentile.length * ranges.highVolPercentile.length} combinations (with low<high filter)`);
  console.log(`   Max possible combinations (before filters): ${total.toLocaleString()}`);
  console.log(`   Note: Actual combinations will be much lower due to fast<slow and low<high filters\n`);

  for (const fastLow of ranges.fastLengthLow) {
    for (const slowLow of ranges.slowLengthLow) {
      if (fastLow >= slowLow) continue;
      
      for (const fastMed of ranges.fastLengthMed) {
        for (const slowMed of ranges.slowLengthMed) {
          if (fastMed >= slowMed) continue;
          
          for (const fastHigh of ranges.fastLengthHigh) {
            for (const slowHigh of ranges.slowLengthHigh) {
              if (fastHigh >= slowHigh) continue;
              
              for (const atrLen of ranges.atrLength) {
                for (const volLen of ranges.volatilityLength) {
                  for (const lowVolPerc of ranges.lowVolPercentile) {
                    for (const highVolPerc of ranges.highVolPercentile) {
                      if (lowVolPerc >= highVolPerc) continue;
                      
                      yield {
                        fastLengthLow: fastLow,
                        slowLengthLow: slowLow,
                        fastLengthMed: fastMed,
                        slowLengthMed: slowMed,
                        fastLengthHigh: fastHigh,
                        slowLengthHigh: slowHigh,
                        atrLength: atrLen,
                        volatilityLength: volLen,
                        lowVolPercentile: lowVolPerc,
                        highVolPercentile: highVolPerc,
                        initialCapital: DEFAULT_PARAMS.initialCapital
                      };
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
}

/**
 * Smart parameter search - uses ±10% from default values
 */
function* generateSmartParameterCombinations() {
  yield* generateParameterCombinations({ useSmartRanges: true });
}

/**
 * Full parameter search - comprehensive but slower
 */
function* generateFullParameterCombinations() {
  const fastEmas = [];
  const slowEmas = [];
  
  // Generate ranges
  for (let i = 5; i <= 80; i += 5) fastEmas.push(i);
  for (let i = 20; i <= 250; i += 10) slowEmas.push(i);
  
  const options = {
    fastEmaRange: fastEmas,
    slowEmaRange: slowEmas,
    atrLengthRange: [10, 12, 14, 16, 18, 20, 25, 30],
    volatilityLengthRange: [40, 50, 60, 71, 80, 100, 120],
    lowVolPercentileRange: [20, 23, 25, 28, 30, 33, 35],
    highVolPercentileRange: [60, 63, 65, 66, 68, 70, 75, 80]
  };
  
  yield* generateParameterCombinations(options);
}

/**
 * Pre-calculate all possible EMAs for optimization
 */
function precalculateEMAs(closes, emaLengths) {
  const emaCache = {};
  for (const length of emaLengths) {
    emaCache[length] = EMA.calculate({ period: length, values: closes });
  }
  return emaCache;
}

/**
 * Calculate ATR and volatility metrics (cached)
 */
function calculateVolatilityMetrics(candles, atrLength, volatilityLength) {
  const high = candles.map(c => c.high);
  const low = candles.map(c => c.low);
  const close = candles.map(c => c.close);
  
  const atrValues = ATR.calculate({ high, low, close, period: atrLength });
  const normalizedATR = [];
  const offset = candles.length - atrValues.length;
  
  for (let i = 0; i < atrValues.length; i++) {
    normalizedATR.push((atrValues[i] / candles[offset + i].close) * 100);
  }
  
  const volRanks = [];
  for (let i = 0; i < normalizedATR.length; i++) {
    const startIdx = Math.max(0, i - volatilityLength + 1);
    const window = normalizedATR.slice(startIdx, i + 1);
    
    if (window.length < 20) {
      volRanks.push(0);
      continue;
    }
    
    const currentVol = normalizedATR[i];
    const sorted = [...window].sort((a, b) => a - b);
    let rank = 0;
    for (let j = 0; j < sorted.length; j++) {
      if (sorted[j] <= currentVol) rank = (j / sorted.length) * 100;
    }
    volRanks.push(rank);
  }
  
  return { normalizedATR, volRanks, offset };
}

/**
 * Optimized strategy runner using pre-calculated EMAs
 */
function runStrategyOptimized(candles, emaCache, volMetricsCache, params) {
  const closes = candles.map(c => c.close);
  
  // Get cached volatility metrics
  const cacheKey = `${params.atrLength}-${params.volatilityLength}`;
  let volMetrics = volMetricsCache[cacheKey];
  if (!volMetrics) {
    volMetrics = calculateVolatilityMetrics(candles, params.atrLength, params.volatilityLength);
    volMetricsCache[cacheKey] = volMetrics;
  }
  
  const { volRanks, offset } = volMetrics;
  
  // Get cached EMAs
  const emaLowFast = emaCache[params.fastLengthLow];
  const emaLowSlow = emaCache[params.slowLengthLow];
  const emaMedFast = emaCache[params.fastLengthMed];
  const emaMedSlow = emaCache[params.slowLengthMed];
  const emaHighFast = emaCache[params.fastLengthHigh];
  const emaHighSlow = emaCache[params.slowLengthHigh];
  
  const maxPeriod = Math.max(
    params.slowLengthLow, params.slowLengthMed, params.slowLengthHigh
  );
  const startIdx = maxPeriod - 1;
  
  const trades = [];
  let position = null;
  let capital = params.initialCapital;
  let equity = capital;
  
  const equityCurve = [];
  let peakEquity = capital;
  let maxDrawdown = 0;
  let earlyReturn = 0;
  const midPoint = Math.floor((candles.length - startIdx) / 2);
  
  for (let i = startIdx; i < candles.length - 1; i++) {
    const atrIdx = i - offset;
    if (atrIdx < 0) continue;
    
    const volRank = volRanks[atrIdx];
    const regime = volRank < params.lowVolPercentile ? 'LOW' :
                   volRank < params.highVolPercentile ? 'MEDIUM' : 'HIGH';
    
    const emaOffset = i - startIdx;
    const fastEMA = regime === 'LOW' ? emaLowFast[emaOffset] :
                    regime === 'MEDIUM' ? emaMedFast[emaOffset] :
                    emaHighFast[emaOffset];
    const slowEMA = regime === 'LOW' ? emaLowSlow[emaOffset] :
                    regime === 'MEDIUM' ? emaMedSlow[emaOffset] :
                    emaHighSlow[emaOffset];
    
    const prevFastEMA = regime === 'LOW' ? emaLowFast[emaOffset - 1] :
                        regime === 'MEDIUM' ? emaMedFast[emaOffset - 1] :
                        emaHighFast[emaOffset - 1];
    const prevSlowEMA = regime === 'LOW' ? emaLowSlow[emaOffset - 1] :
                        regime === 'MEDIUM' ? emaMedSlow[emaOffset - 1] :
                        emaHighSlow[emaOffset - 1];
    
    const bullishCross = prevFastEMA <= prevSlowEMA && fastEMA > slowEMA;
    const bearishCross = prevFastEMA >= prevSlowEMA && fastEMA < slowEMA;
    const currentPrice = candles[i].close;
    
    if (bullishCross && !position) {
      position = {
        entryPrice: currentPrice,
        entryDate: candles[i].date,
        shares: equity / currentPrice,
        regime: regime
      };
    }
    
    if (bearishCross && position) {
      const pnl = (currentPrice - position.entryPrice) * position.shares;
      const pnlPercent = ((currentPrice - position.entryPrice) / position.entryPrice) * 100;
      equity += pnl;
      
      trades.push({
        entryDate: position.entryDate,
        exitDate: candles[i].date,
        entryPrice: position.entryPrice,
        exitPrice: currentPrice,
        shares: position.shares,
        pnl: pnl,
        pnlPercent: pnlPercent,
        regime: position.regime
      });
      position = null;
    }
    
    let currentEquity = equity;
    if (position) {
      currentEquity = equity + (currentPrice - position.entryPrice) * position.shares;
    }
    
    equityCurve.push(currentEquity);
    
    if (currentEquity > peakEquity) peakEquity = currentEquity;
    const drawdown = ((peakEquity - currentEquity) / peakEquity) * 100;
    if (drawdown > maxDrawdown) maxDrawdown = drawdown;
    
    // Track early performance for filtering
    if (emaOffset === midPoint) {
      earlyReturn = ((currentEquity - params.initialCapital) / params.initialCapital) * 100;
    }
  }
  
  if (position) {
    const finalPrice = candles[candles.length - 1].close;
    const pnl = (finalPrice - position.entryPrice) * position.shares;
    equity += pnl;
    trades.push({
      entryDate: position.entryDate,
      exitDate: candles[candles.length - 1].date,
      entryPrice: position.entryPrice,
      exitPrice: finalPrice,
      shares: position.shares,
      pnl: pnl,
      pnlPercent: ((finalPrice - position.entryPrice) / position.entryPrice) * 100,
      regime: position.regime
    });
  }
  
  const finalEquity = equity;
  const totalReturn = ((finalEquity - params.initialCapital) / params.initialCapital) * 100;
  
  const winningTrades = trades.filter(t => t.pnl > 0 && isFinite(t.pnl));
  const losingTrades = trades.filter(t => t.pnl <= 0 && isFinite(t.pnl));
  const validTrades = winningTrades.length + losingTrades.length;
  
  const avgWin = winningTrades.length > 0 ? 
    winningTrades.reduce((sum, t) => sum + t.pnl, 0) / winningTrades.length : 0;
  const avgLoss = losingTrades.length > 0 ? 
    losingTrades.reduce((sum, t) => sum + t.pnl, 0) / losingTrades.length : 0;
  
  const totalWinPnL = winningTrades.reduce((sum, t) => sum + t.pnl, 0);
  const totalLossPnL = Math.abs(losingTrades.reduce((sum, t) => sum + t.pnl, 0));
  const profitFactor = totalLossPnL > 0 ? totalWinPnL / totalLossPnL : (totalWinPnL > 0 ? Infinity : 0);
  
  return {
    trades,
    totalTrades: validTrades,
    winningTrades: winningTrades.length,
    losingTrades: losingTrades.length,
    winRate: validTrades > 0 ? (winningTrades.length / validTrades) * 100 : 0,
    totalReturn,
    finalEquity,
    totalPnL: finalEquity - params.initialCapital,
    maxDrawdown,
    avgWin,
    avgLoss,
    profitFactor,
    equityCurve,
    earlyReturn
  };
}

/**
 * Optimize parameters for a single ticker
 */
async function optimizeTicker(ticker, candles, searchType = 'smart') {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🔧 Optimizing ${ticker.toUpperCase()} - ${searchType.toUpperCase()} Search`);
  console.log(`   Candles: ${candles.length} | Using CLOSE prices only`);
  console.log(`   Date Range: ${candles[0].date.toISOString().slice(0,10)} to ${candles[candles.length - 1].date.toISOString().slice(0,10)}`);
  console.log('='.repeat(60));

  const generator = searchType === 'full' ? 
    generateFullParameterCombinations() : 
    generateSmartParameterCombinations();

  // Pre-calculate all EMAs and cache volatility metrics
  console.log('\n⚡ Pre-calculating EMAs and caching ATR...');
  const emaStartTime = Date.now();
  const closes = candles.map(c => c.close);
  const ranges = generateSmartRanges();
  const allEmaLengths = new Set([
    ...ranges.fastLengthLow, ...ranges.slowLengthLow,
    ...ranges.fastLengthMed, ...ranges.slowLengthMed,
    ...ranges.fastLengthHigh, ...ranges.slowLengthHigh
  ]);
  
  const emaCache = precalculateEMAs(closes, Array.from(allEmaLengths));
  const volMetricsCache = {};
  const emaTime = (Date.now() - emaStartTime) / 1000;
  console.log(`   ✓ Cached ${allEmaLengths.size} EMA lengths in ${emaTime.toFixed(2)}s`);
  console.log('\n🚀 Starting optimization...\n');

  let bestResult = null;
  let bestParams = null;
  let testedCount = 0;
  let validCount = 0;
  let skippedCount = 0;
  const startTime = Date.now();
  let firstTestTime = null;

  let lastProgressUpdate = Date.now();
  const progressInterval = OPTIMIZATION_CONFIG.progressUpdateInterval;

  for (const params of generator) {
    testedCount++;

    try {
      const result = runStrategyOptimized(candles, emaCache, volMetricsCache, params);
      
      // Early termination filters (relaxed for 300 candles)
      if (!isFinite(result.totalReturn) || 
          result.totalTrades < 2 ||  // Reduced from 5 to 2 for shorter timeframe
          result.maxDrawdown > 50 ||
          result.earlyReturn < -20) {  // Relaxed from -10 to -20
        skippedCount++;
        continue;
      }

      validCount++;

      const sharpeRatio = calculateSharpeRatio(result.equityCurve);
      const calmarRatio = result.maxDrawdown > 0 ? 
        result.totalReturn / result.maxDrawdown : 0;

      const scoredResult = {
        ...result,
        sharpeRatio,
        calmarRatio,
        score: calculateScore(result, sharpeRatio, calmarRatio)
      };

      if (!bestResult || scoredResult.score > bestResult.score) {
        bestResult = scoredResult;
        bestParams = params;
      }

      if (Date.now() - lastProgressUpdate > progressInterval) {
        const elapsed = (Date.now() - startTime) / 1000;
        const rate = testedCount / elapsed;
        console.log(`   Progress: ${testedCount.toLocaleString()} tested, ${validCount.toLocaleString()} valid, ${skippedCount.toLocaleString()} filtered | Best: ${bestResult.totalReturn.toFixed(2)}% | ${rate.toFixed(0)}/sec`);
        lastProgressUpdate = Date.now();
      }

    } catch (error) {
      skippedCount++;
      continue;
    }
  }

  const elapsed = (Date.now() - startTime) / 1000;
  
  console.log(`\n✅ Optimization Complete`);
  console.log(`   Tested: ${testedCount.toLocaleString()} combinations`);
  console.log(`   Valid: ${validCount.toLocaleString()} results`);
  console.log(`   Filtered: ${skippedCount.toLocaleString()} (early termination)`);
  console.log(`   Time: ${elapsed.toFixed(1)}s (${(testedCount / elapsed).toFixed(0)} tests/sec)`);
  console.log(`   Avg time per test: ${((elapsed / testedCount) * 1000).toFixed(2)}ms`);
  console.log(`   EMA cache time: ${emaTime.toFixed(2)}s`);
  console.log(`   Actual testing time: ${(elapsed - emaTime).toFixed(2)}s`);
  console.log(`   Speedup: ~${Math.round(allEmaLengths.size * 50)}x faster with EMA caching + caching`);

  if (!bestResult) {
    console.log(`❌ No valid results found for ${ticker}`);
    return null;
  }

  // Display best results
  console.log(`\n🏆 BEST PARAMETERS FOR ${ticker.toUpperCase()}`);
  console.log(`\n📊 Performance Metrics:`);
  console.log(`   Total Return: ${bestResult.totalReturn.toFixed(2)}%`);
  console.log(`   Max Drawdown: ${bestResult.maxDrawdown.toFixed(2)}%`);
  console.log(`   Sharpe Ratio: ${bestResult.sharpeRatio.toFixed(2)}`);
  console.log(`   Calmar Ratio: ${bestResult.calmarRatio.toFixed(2)}`);
  console.log(`   Profit Factor: ${bestResult.profitFactor.toFixed(2)}`);
  console.log(`   Win Rate: ${bestResult.winRate.toFixed(2)}%`);
  console.log(`   Total Trades: ${bestResult.totalTrades}`);
  console.log(`   Score: ${bestResult.score.toFixed(2)}`);

  console.log(`\n⚙️  Optimal Parameters:`);
  console.log(`   Low Volatility:  Fast=${bestParams.fastLengthLow}, Slow=${bestParams.slowLengthLow}`);
  console.log(`   Med Volatility:  Fast=${bestParams.fastLengthMed}, Slow=${bestParams.slowLengthMed}`);
  console.log(`   High Volatility: Fast=${bestParams.fastLengthHigh}, Slow=${bestParams.slowLengthHigh}`);
  console.log(`   ATR Length: ${bestParams.atrLength}`);
  console.log(`   Volatility Lookback: ${bestParams.volatilityLength}`);
  console.log(`   Percentiles: Low=${bestParams.lowVolPercentile}%, High=${bestParams.highVolPercentile}%`);

  // Calculate buy and hold for comparison
  const buyAndHold = calculateBuyAndHold(candles, bestParams.initialCapital);
  console.log(`\n📉 Buy & Hold Comparison:`);
  console.log(`   Buy & Hold Return: ${buyAndHold.totalReturn.toFixed(2)}%`);
  console.log(`   Strategy Outperformance: ${(bestResult.totalReturn - buyAndHold.totalReturn).toFixed(2)}% ${bestResult.totalReturn > buyAndHold.totalReturn ? '✅' : '❌'}`);

  // Display trades
  if (bestResult.trades && bestResult.trades.length > 0) {
    console.log(`\n📝 Trades Taken (${bestResult.trades.length} total):`);
    console.log(`\n${'#'.padEnd(4)} ${'Entry Date'.padEnd(20)} ${'Exit Date'.padEnd(20)} ${'Entry'.padEnd(10)} ${'Exit'.padEnd(10)} ${'P&L'.padEnd(10)} ${'Return'.padEnd(10)} ${'Regime'}`);
    console.log('-'.repeat(100));
    
    bestResult.trades.forEach((trade, idx) => {
      const entryDate = trade.entryDate ? new Date(trade.entryDate).toISOString().slice(0, 16).replace('T', ' ') : 'N/A';
      const exitDate = trade.exitDate ? new Date(trade.exitDate).toISOString().slice(0, 16).replace('T', ' ') : 'N/A';
      const entryPrice = trade.entryPrice.toFixed(2);
      const exitPrice = trade.exitPrice.toFixed(2);
      const pnl = trade.pnl.toFixed(2);
      const returnPct = trade.pnlPercent ? trade.pnlPercent.toFixed(2) : ((trade.exitPrice - trade.entryPrice) / trade.entryPrice * 100).toFixed(2);
      const pnlSign = trade.pnl >= 0 ? '+' : '';
      const returnSign = returnPct >= 0 ? '+' : '';
      
      console.log(
        `${(idx + 1).toString().padEnd(4)} ` +
        `${entryDate.padEnd(20)} ` +
        `${exitDate.padEnd(20)} ` +
        `$${entryPrice.padEnd(9)} ` +
        `$${exitPrice.padEnd(9)} ` +
        `${pnlSign}$${pnl.padEnd(8)} ` +
        `${returnSign}${returnPct}%`.padEnd(10) + ' ' +
        `${trade.regime}`
      );
    });
    
    const totalPnL = bestResult.trades.reduce((sum, t) => sum + t.pnl, 0);
    const winningTrades = bestResult.trades.filter(t => t.pnl > 0);
    const losingTrades = bestResult.trades.filter(t => t.pnl <= 0);
    
    console.log('-'.repeat(100));
    console.log(`Total P&L: $${totalPnL.toFixed(2)} | Winners: ${winningTrades.length} | Losers: ${losingTrades.length}`);
  }
}

/**
 * Calculate Sharpe Ratio from equity curve
 */
function calculateSharpeRatio(equityCurve) {
  if (!equityCurve || equityCurve.length < 2) return 0;

  const returns = [];
  for (let i = 1; i < equityCurve.length; i++) {
    const ret = (equityCurve[i] - equityCurve[i - 1]) / equityCurve[i - 1];
    returns.push(ret);
  }

  const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
  const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
  const stdDev = Math.sqrt(variance);

  if (stdDev === 0) return 0;

  // Annualized Sharpe (assuming hourly data, ~6500 trading hours per year)
  return (avgReturn / stdDev) * Math.sqrt(6500);
}

/**
 * Calculate composite score for ranking strategies
 */
function calculateScore(result, sharpeRatio, calmarRatio) {
  // Weighted scoring system
  const returnWeight = 0.35;
  const sharpeWeight = 0.25;
  const calmarWeight = 0.20;
  const profitFactorWeight = 0.10;
  const winRateWeight = 0.10;

  // Normalize metrics (scale 0-100)
  const returnScore = Math.max(0, Math.min(100, result.totalReturn));
  const sharpeScore = Math.max(0, Math.min(100, sharpeRatio * 20)); // Sharpe 0-5 -> 0-100
  const calmarScore = Math.max(0, Math.min(100, calmarRatio * 10)); // Calmar 0-10 -> 0-100
  const pfScore = Math.max(0, Math.min(100, result.profitFactor * 20)); // PF 0-5 -> 0-100
  const winRateScore = result.winRate;

  const score = 
    returnScore * returnWeight +
    sharpeScore * sharpeWeight +
    calmarScore * calmarWeight +
    pfScore * profitFactorWeight +
    winRateScore * winRateWeight;

  return score;
}

/**
 * Run optimization for multiple tickers
 */
async function optimizeMultipleTickers(tickers, searchType = 'smart') {
  const results = [];
  
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🚀 Starting Multi-Ticker Optimization`);
  console.log(`   Tickers: ${tickers.join(', ')}`);
  console.log(`   Search Type: ${searchType.toUpperCase()}`);
  console.log(`   Optimizations: ±${OPTIMIZATION_CONFIG.rangePercent * 100}% ranges, EMA caching, ATR caching, early termination`);
  console.log('='.repeat(60));

  for (const ticker of tickers) {
    console.log(`\n📥 Fetching data for ${ticker.toUpperCase()}...`);
    const candles = await fetchData(ticker, OPTIMIZATION_CONFIG.candles, OPTIMIZATION_CONFIG.interval);
    
    if (!candles || candles.length < 200) {
      console.log(`❌ Insufficient data for ${ticker}`);
      continue;
    }

    console.log(`   Retrieved ${candles.length} candles`);

    await optimizeTicker(ticker, candles, searchType);

    // Add delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  console.log(`\n${'='.repeat(60)}`);
  console.log('📊 OPTIMIZATION COMPLETE');
  console.log('='.repeat(60));
  console.log('\n✅ Done!\n');
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);
  const searchType = args.includes('--full') ? 'full' : 'smart';
  const tickers = args.filter(arg => !arg.startsWith('--'));
  
  // Use config symbols if no command line args provided
  const tickersToOptimize = tickers.length > 0 ? tickers : OPTIMIZATION_CONFIG.symbols;
  
  console.log(`\n🎯 Parameter Optimization System v2.0`);
  console.log(`   Mode: ${searchType === 'full' ? 'FULL (comprehensive)' : 'SMART (±' + (OPTIMIZATION_CONFIG.rangePercent * 100) + '% from defaults)'}`);  
  console.log(`   Tickers: ${tickersToOptimize.join(', ')}`);
  console.log(`   Candles: ${OPTIMIZATION_CONFIG.candles} (${OPTIMIZATION_CONFIG.interval} interval)`);
  console.log(`   Features: EMA caching, ATR caching, early termination`);
  console.log(`   Use --full flag for comprehensive search`);
  console.log(`   Example: node optimize.js QQQ SPY\n`);  optimizeMultipleTickers(tickersToOptimize, searchType)
    .then(() => {
      console.log('\n✅ Optimization complete!\n');
      process.exit(0);
    })
    .catch(error => {
      console.error('❌ Error during optimization:', error);
      process.exit(1);
    });
}

module.exports = {
  optimizeTicker,
  optimizeMultipleTickers,
  generateParameterCombinations,
  generateSmartParameterCombinations,
  generateFullParameterCombinations
};
