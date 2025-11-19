const { fetchData } = require('./dataFetcher');
const strategies = require('./strategies');

/**
 * Run strategy using the strategy pattern
 */
function runStrategy(candles, strategy) {
  // Calculate all indicators
  const indicators = strategy.calculateIndicators(candles);
  
  // Get first valid trading index
  const firstValidIdx = strategy.getFirstValidIndex(indicators, candles);
  
  // Validate sufficient data
  if (firstValidIdx >= candles.length - 1) {
    throw new Error('Insufficient data after indicator warmup');
  }
  
  const trades = [];
  let position = null;
  let capital = strategy.params.initialCapital;
  let equity = capital;
  
  // Track statistics
  const equityCurve = [];
  let peakEquity = capital;
  let maxDrawdown = 0;
  
  for (let i = firstValidIdx; i < candles.length - 1; i++) {
    const currentPrice = candles[i].close;
    
    // Check for entry signal
    if (!position && strategy.checkEntrySignal(i, indicators, candles, position)) {
      const shares = equity / currentPrice;
      position = {
        entryPrice: currentPrice,
        entryDate: candles[i].date,
        shares: shares,
        entryIdx: i,
        strategyData: strategy.getPositionData(i, indicators, candles)
      };
    }
    
    // Check for exit signal
    if (position) {
      const exitSignal = strategy.checkExitSignal(i, indicators, candles, position);
      
      if (exitSignal) {
        const exitPrice = exitSignal.price;
        const pnl = (exitPrice - position.entryPrice) * position.shares - (strategy.params.commissionPerTrade || 0);
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
          exitReason: exitSignal.reason,
          ...position.strategyData
        });
        
        position = null;
      }
    }
    
    // Update equity curve
    let currentEquity = equity;
    if (position) {
      const unrealizedPnL = (currentPrice - position.entryPrice) * position.shares - (strategy.params.commissionPerTrade || 0);
      currentEquity = equity + unrealizedPnL;
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
    const pnl = (finalPrice - position.entryPrice) * position.shares - (strategy.params.commissionPerTrade || 0);
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
      exitReason: 'END_OF_DATA',
      ...position.strategyData
    });
  }
  
  const finalEquity = equity;
  const totalReturn = ((finalEquity - strategy.params.initialCapital) / strategy.params.initialCapital) * 100;
  
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
    totalPnL: finalEquity - strategy.params.initialCapital,
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
 * Run backtest for a single ticker with a strategy
 */
async function backtest(ticker, strategyClass, params, interval = '1h', targetCandles = 9000) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`Backtesting ${ticker.toUpperCase()} - ${interval.toUpperCase()} Interval`);
  console.log('='.repeat(60));
  
  // Create strategy instance
  const strategy = new strategyClass(params);
  console.log(`Strategy: ${strategy.getDescription()}`);
  
  // Fetch data
  const candlesRequest = interval === '1h' ? `${targetCandles}h` : 
                        interval === '4h' ? `${Math.floor(targetCandles * 4)}h` :
                        `${Math.floor(targetCandles)}d`;
  
  const candles = await fetchData(ticker, candlesRequest, interval);
  
  // Validate sufficient data
  const requiredCandles = strategy.getMinimumCandles();
  
  if (!candles || candles.length < requiredCandles) {
    console.log(`❌ Insufficient data for ${ticker}. Got ${candles?.length || 0} candles, need at least ${requiredCandles}`);
    return null;
  }
  
  console.log(`Fetched ${candles.length} candles`);
  console.log(`Period: ${candles[0].date.toISOString().split('T')[0]} to ${candles[candles.length - 1].date.toISOString().split('T')[0]}`);
  
  // Run strategy
  const results = runStrategy(candles, strategy);
  
  // Calculate buy and hold
  const buyAndHold = calculateBuyAndHold(candles, strategy.params.initialCapital);
  
  // Display results
  console.log(`\n📊 STRATEGY RESULTS`);
  console.log(`Initial Capital: $${strategy.params.initialCapital.toFixed(2)}`);
  console.log(`Final Equity: $${results.finalEquity.toFixed(2)}`);
  console.log(`Total P&L: $${results.totalPnL.toFixed(2)} (${results.totalReturn.toFixed(2)}%)`);
  console.log(`Max Drawdown: ${results.maxDrawdown.toFixed(2)}%`);
  console.log(`Commission Per Trade: $${(strategy.params.commissionPerTrade || 0).toFixed(2)}`);
  const stopLossText = (strategy.params.stopLossPercent && strategy.params.stopLossPercent > 0) 
    ? `${strategy.params.stopLossPercent.toFixed(2)}%` 
    : 'Disabled';
  console.log(`Stop Loss: ${stopLossText}`);
  
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
async function runMultipleBacktests(tickers, strategyClass, params, interval = '1h', targetCandles = 9000) {
  const results = [];
  
  for (const ticker of tickers) {
    const result = await backtest(ticker, strategyClass, params, interval, targetCandles);
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
  const DEFAULT_STRATEGY = 'AdaptiveEMAStrategy';
  const tickers = ['QQQ', 'SPY', 'IBM', 'NICE'];
  
  const strategyClass = strategies[DEFAULT_STRATEGY];
  
  if (!strategyClass) {
    console.error(`❌ Strategy "${DEFAULT_STRATEGY}" not found. Available: ${Object.keys(strategies).join(', ')}`);
    process.exit(1);
  }
  
  const params = strategyClass.getDefaultParams();
  
  console.log(`\n🎯 Backtesting with ${DEFAULT_STRATEGY}`);
  console.log(`   Using: TA-Lib for indicators`);
  
  runMultipleBacktests(tickers, strategyClass, params)
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
  calculateBuyAndHold
};
