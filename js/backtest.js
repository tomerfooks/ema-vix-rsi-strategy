const { EMA, ATR } = require('technicalindicators');
const { DEFAULT_PARAMS } = require('./config-1h');
const { fetchData } = require('./dataFetcher');

/**
 * Calculate EMA using technicalindicators library
 */
function calculateEMA(prices, period) {
  return EMA.calculate({
    period: period,
    values: prices
  });
}

/**
 * Calculate ATR
 */
function calculateATR(candles, period) {
  const high = candles.map(c => c.high);
  const low = candles.map(c => c.low);
  const close = candles.map(c => c.close);
  
  return ATR.calculate({
    high: high,
    low: low,
    close: close,
    period: period
  });
}

/**
 * Calculate normalized ATR (ATR / close * 100)
 */
function calculateNormalizedATR(candles, atrValues) {
  const normalized = [];
  const offset = candles.length - atrValues.length;
  
  for (let i = 0; i < atrValues.length; i++) {
    const closePrice = candles[offset + i].close;
    normalized.push((atrValues[i] / closePrice) * 100);
  }
  
  return normalized;
}

/**
 * Calculate percentile rank for volatility regime detection
 */
function calculateVolatilityRank(normalizedATR, volatilityLength) {
  const ranks = [];
  
  for (let i = 0; i < normalizedATR.length; i++) {
    const startIdx = Math.max(0, i - volatilityLength + 1);
    const window = normalizedATR.slice(startIdx, i + 1);
    
    if (window.length < 20) {
      ranks.push(0);
      continue;
    }
    
    const currentVol = normalizedATR[i];
    const sorted = [...window].sort((a, b) => a - b);
    
    let rank = 0;
    for (let j = 0; j < sorted.length; j++) {
      if (sorted[j] <= currentVol) {
        rank = (j / sorted.length) * 100;
      }
    }
    
    ranks.push(rank);
  }
  
  return ranks;
}

/**
 * Determine volatility regime
 */
function getVolatilityRegime(volRank, lowVolPercentile, highVolPercentile) {
  if (volRank < lowVolPercentile) return 'LOW';
  if (volRank < highVolPercentile) return 'MEDIUM';
  return 'HIGH';
}

/**
 * Run adaptive EMA crossover strategy
 */
function runStrategy(candles, params = DEFAULT_PARAMS) {
  const closes = candles.map(c => c.close);
  
  // Calculate ATR and normalized ATR
  const atrValues = calculateATR(candles, params.atrLength);
  const normalizedATR = calculateNormalizedATR(candles, atrValues);
  const volRanks = calculateVolatilityRank(normalizedATR, params.volatilityLength);
  
  // Calculate all EMAs
  const emaLowFast = calculateEMA(closes, params.fastLengthLow);
  const emaLowSlow = calculateEMA(closes, params.slowLengthLow);
  const emaMedFast = calculateEMA(closes, params.fastLengthMed);
  const emaMedSlow = calculateEMA(closes, params.slowLengthMed);
  const emaHighFast = calculateEMA(closes, params.fastLengthHigh);
  const emaHighSlow = calculateEMA(closes, params.slowLengthHigh);
  
  // Align all arrays (offset by the longest EMA period)
  const maxPeriod = Math.max(params.slowLengthLow, params.slowLengthMed, params.slowLengthHigh);
  const startIdx = maxPeriod - 1;
  
  const trades = [];
  let position = null;
  let capital = params.initialCapital;
  let equity = capital;
  
  // Track statistics
  const equityCurve = [];
  let peakEquity = capital;
  let maxDrawdown = 0;
  
  for (let i = startIdx; i < candles.length - 1; i++) {
    const atrIdx = i - (candles.length - normalizedATR.length);
    
    if (atrIdx < 0) continue;
    
    const volRank = volRanks[atrIdx];
    const regime = getVolatilityRegime(volRank, params.lowVolPercentile, params.highVolPercentile);
    
    // Select EMAs based on volatility regime
    let fastEMA, slowEMA;
    const emaOffset = i - startIdx;
    
    if (regime === 'LOW') {
      fastEMA = emaLowFast[emaOffset];
      slowEMA = emaLowSlow[emaOffset];
    } else if (regime === 'MEDIUM') {
      fastEMA = emaMedFast[emaOffset];
      slowEMA = emaMedSlow[emaOffset];
    } else {
      fastEMA = emaHighFast[emaOffset];
      slowEMA = emaHighSlow[emaOffset];
    }
    
    // Get previous EMAs for crossover detection
    const prevFastEMA = regime === 'LOW' ? emaLowFast[emaOffset - 1] :
                       regime === 'MEDIUM' ? emaMedFast[emaOffset - 1] :
                       emaHighFast[emaOffset - 1];
    const prevSlowEMA = regime === 'LOW' ? emaLowSlow[emaOffset - 1] :
                       regime === 'MEDIUM' ? emaMedSlow[emaOffset - 1] :
                       emaHighSlow[emaOffset - 1];
    
    // Detect crossovers
    const bullishCross = prevFastEMA <= prevSlowEMA && fastEMA > slowEMA;
    const bearishCross = prevFastEMA >= prevSlowEMA && fastEMA < slowEMA;
    
    const currentPrice = candles[i].close;
    
    // Entry signal
    if (bullishCross && !position) {
      const shares = equity / currentPrice;
      position = {
        entryPrice: currentPrice,
        entryDate: candles[i].date,
        shares: shares,
        regime: regime
      };
    }
    
    // Exit signal
    if (bearishCross && position) {
      const exitPrice = currentPrice;
      const pnl = (exitPrice - position.entryPrice) * position.shares;
      const pnlPercent = ((exitPrice - position.entryPrice) / position.entryPrice) * 100;
      
      equity += pnl;
      
      trades.push({
        entryDate: position.entryDate,
        exitDate: candles[i].date,
        entryPrice: position.entryPrice,
        exitPrice: exitPrice,
        shares: position.shares,
        pnl: pnl,
        pnlPercent: pnlPercent,
        regime: position.regime
      });
      
      position = null;
    }
    
    // Update equity curve
    let currentEquity = equity;
    if (position) {
      currentEquity = equity + (currentPrice - position.entryPrice) * position.shares;
    }
    
    equityCurve.push(currentEquity);
    
    // Track max drawdown
    if (currentEquity > peakEquity) {
      peakEquity = currentEquity;
    }
    const drawdown = ((peakEquity - currentEquity) / peakEquity) * 100;
    if (drawdown > maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }
  
  // Close any open position at the end
  if (position) {
    const finalPrice = candles[candles.length - 1].close;
    const pnl = (finalPrice - position.entryPrice) * position.shares;
    const pnlPercent = ((finalPrice - position.entryPrice) / position.entryPrice) * 100;
    
    equity += pnl;
    
    trades.push({
      entryDate: position.entryDate,
      exitDate: candles[candles.length - 1].date,
      entryPrice: position.entryPrice,
      exitPrice: finalPrice,
      shares: position.shares,
      pnl: pnl,
      pnlPercent: pnlPercent,
      regime: position.regime
    });
  }
  
  const finalEquity = equity;
  const totalReturn = ((finalEquity - params.initialCapital) / params.initialCapital) * 100;
  
  // Calculate win rate
  const winningTrades = trades.filter(t => t.pnl > 0 && isFinite(t.pnl));
  const losingTrades = trades.filter(t => t.pnl <= 0 && isFinite(t.pnl));
  const validTrades = winningTrades.length + losingTrades.length;
  const winRate = validTrades > 0 ? (winningTrades.length / validTrades) * 100 : 0;
  
  // Calculate average win/loss
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
    winRate: winRate,
    totalReturn: totalReturn,
    finalEquity: finalEquity,
    totalPnL: finalEquity - params.initialCapital,
    maxDrawdown: maxDrawdown,
    avgWin: avgWin,
    avgLoss: avgLoss,
    profitFactor: profitFactor,
    equityCurve: equityCurve
  };
}

/**
 * Calculate buy and hold return
 */
function calculateBuyAndHold(candles, initialCapital) {
  const entryPrice = candles[0].close;
  const exitPrice = candles[candles.length - 1].close;
  const shares = initialCapital / entryPrice;
  const finalValue = shares * exitPrice;
  const totalReturn = ((finalValue - initialCapital) / initialCapital) * 100;
  
  return {
    totalReturn: totalReturn,
    finalValue: finalValue
  };
}

/**
 * Run backtest for a single ticker
 */
async function backtest(ticker, params = DEFAULT_PARAMS) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`Backtesting ${ticker.toUpperCase()} - 1H Interval`);
  console.log('='.repeat(60));
  
  const candles = await fetchData(ticker, '9000h', '1h');
  
  if (!candles || candles.length < 200) {
    console.log(`❌ Insufficient data for ${ticker}`);
    return null;
  }
  
  console.log(`Fetched ${candles.length} candles`);
  console.log(`Period: ${candles[0].date.toISOString().split('T')[0]} to ${candles[candles.length - 1].date.toISOString().split('T')[0]}`);
  
  // Run strategy
  const results = runStrategy(candles, params);
  
  // Calculate buy and hold
  const buyAndHold = calculateBuyAndHold(candles, params.initialCapital);
  
  // Display results
  console.log(`\n📊 STRATEGY RESULTS`);
  console.log(`Initial Capital: $${params.initialCapital.toFixed(2)}`);
  console.log(`Final Equity: $${results.finalEquity.toFixed(2)}`);
  console.log(`Total P&L: $${results.totalPnL.toFixed(2)} (${results.totalReturn.toFixed(2)}%)`);
  console.log(`Max Drawdown: ${results.maxDrawdown.toFixed(2)}%`);
  
  console.log(`\n📈 TRADE STATISTICS`);
  console.log(`Total Trades: ${results.totalTrades}`);
  console.log(`Winning Trades: ${results.winningTrades} (${results.winRate.toFixed(2)}%)`);
  console.log(`Losing Trades: ${results.losingTrades}`);
  console.log(`Avg Win: $${results.avgWin.toFixed(2)}`);
  console.log(`Avg Loss: $${results.avgLoss.toFixed(2)}`);
  console.log(`Profit Factor: ${isFinite(results.profitFactor) ? results.profitFactor.toFixed(2) : 'N/A'}`);
  
  console.log(`\n📉 BUY & HOLD COMPARISON`);
  console.log(`Buy & Hold Return: ${buyAndHold.totalReturn.toFixed(2)}%`);
  console.log(`Buy & Hold Final Value: $${buyAndHold.finalValue.toFixed(2)}`);
  console.log(`Strategy vs Buy & Hold: ${(results.totalReturn - buyAndHold.totalReturn).toFixed(2)}% ${results.totalReturn > buyAndHold.totalReturn ? '✅' : '❌'}`);
  
  return {
    ticker,
    strategy: results,
    buyAndHold: buyAndHold
  };
}

/**
 * Run backtests on multiple tickers
 */
async function runMultipleBacktests(tickers, params = DEFAULT_PARAMS) {
  const results = [];
  
  for (const ticker of tickers) {
    const result = await backtest(ticker, params);
    if (result) {
      results.push(result);
    }
    // Add small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  // Summary comparison
  console.log(`\n${'='.repeat(60)}`);
  console.log('📊 SUMMARY - ALL TICKERS');
  console.log('='.repeat(60));
  console.log(`\n${'Ticker'.padEnd(10)} ${'Strategy'.padEnd(12)} ${'Buy&Hold'.padEnd(12)} ${'Difference'.padEnd(12)} ${'Win Rate'.padEnd(10)} ${'Trades'}`);
  console.log('-'.repeat(60));
  
  for (const result of results) {
    const stratRet = result.strategy.totalReturn.toFixed(2) + '%';
    const bhRet = result.buyAndHold.totalReturn.toFixed(2) + '%';
    const diff = (result.strategy.totalReturn - result.buyAndHold.totalReturn).toFixed(2) + '%';
    const winRate = result.strategy.winRate.toFixed(1) + '%';
    const trades = result.strategy.totalTrades;
    
    console.log(`${result.ticker.toUpperCase().padEnd(10)} ${stratRet.padEnd(12)} ${bhRet.padEnd(12)} ${diff.padEnd(12)} ${winRate.padEnd(10)} ${trades}`);
  }
  
  return results;
}

// Main execution
if (require.main === module) {
  const tickers = ['QQQ', 'SPY', 'IBM', 'NICE', 'PLU'];
  
  runMultipleBacktests(tickers, DEFAULT_PARAMS)
    .then(() => {
      console.log('\n✅ Backtesting complete!');
    })
    .catch(error => {
      console.error('Error running backtests:', error);
    });
}

module.exports = {
  runStrategy,
  backtest,
  runMultipleBacktests,
  calculateBuyAndHold,
  DEFAULT_PARAMS
};
