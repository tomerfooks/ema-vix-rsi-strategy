const { parentPort, workerData } = require('worker_threads');
const { EMA, ATR } = require('technicalindicators');

/**
 * Calculate volatility metrics (ATR and volatility ranks)
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
 * Pre-calculate EMAs for the given lengths
 */
function precalculateEMAs(closes, emaLengths) {
  const emaCache = {};
  for (const length of emaLengths) {
    emaCache[length] = EMA.calculate({ period: length, values: closes });
  }
  return emaCache;
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
  const returnWeight = 0.35;
  const sharpeWeight = 0.25;
  const calmarWeight = 0.20;
  const profitFactorWeight = 0.10;
  const winRateWeight = 0.10;

  const returnScore = Math.max(0, Math.min(100, result.totalReturn));
  const sharpeScore = Math.max(0, Math.min(100, sharpeRatio * 20));
  const calmarScore = Math.max(0, Math.min(100, calmarRatio * 10));
  const pfScore = Math.max(0, Math.min(100, result.profitFactor * 20));
  const winRateScore = result.winRate;

  const score = 
    returnScore * returnWeight +
    sharpeScore * sharpeWeight +
    calmarScore * calmarWeight +
    pfScore * profitFactorWeight +
    winRateScore * winRateWeight;

  return score;
}

// Worker main execution
const { candles, emaCache, volMetricsCache } = workerData;

// Listen for parameter batches
parentPort.on('message', (data) => {
  const { paramBatch } = data;
  const results = [];

  for (const params of paramBatch) {
    try {
      const result = runStrategyOptimized(candles, emaCache, volMetricsCache, params);
      
      // Early termination filters
      if (!isFinite(result.totalReturn) || 
          result.totalTrades < 2 ||
          result.maxDrawdown > 50 ||
          result.earlyReturn < -20) {
        results.push({ params, result: null, skipped: true });
        continue;
      }

      const sharpeRatio = calculateSharpeRatio(result.equityCurve);
      const calmarRatio = result.maxDrawdown > 0 ? 
        result.totalReturn / result.maxDrawdown : 0;

      const scoredResult = {
        ...result,
        sharpeRatio,
        calmarRatio,
        score: calculateScore(result, sharpeRatio, calmarRatio)
      };

      results.push({ params, result: scoredResult, skipped: false });
    } catch (error) {
      results.push({ params, result: null, skipped: true, error: error.message });
    }
  }

  // Send results back to main thread
  parentPort.postMessage({ results });
});
