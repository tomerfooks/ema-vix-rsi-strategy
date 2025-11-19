const { backtest } = require('./backtest-new');
const strategies = require('./strategies');
const { STRATEGY_CONFIGS } = require('./config');

async function compareStrategies() {
  const ticker = 'QQQ';
  const strategyNames = ['AdaptiveEMAStrategy', 'RSIStrategy', 'MACDStrategy'];
  const results = [];
  
  console.log(`\n${'='.repeat(70)}`);
  console.log(`🔬 STRATEGY COMPARISON - ${ticker}`);
  console.log('='.repeat(70));
  
  for (const strategyName of strategyNames) {
    const strategyClass = strategies[strategyName];
    const params = STRATEGY_CONFIGS[strategyName];
    
    const result = await backtest(ticker, strategyClass, params, '1h', 3000);
    
    if (result) {
      results.push({
        name: strategyName,
        ...result
      });
    }
    
    // Small delay
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  
  // Comparison table
  console.log(`\n${'='.repeat(70)}`);
  console.log('📊 STRATEGY COMPARISON SUMMARY');
  console.log('='.repeat(70));
  console.log(`${'Strategy'.padEnd(25)} ${'Return'.padEnd(12)} ${'Drawdown'.padEnd(12)} ${'Win Rate'.padEnd(10)} ${'Trades'.padEnd(8)} ${'Profit Factor'}`);
  console.log('-'.repeat(70));
  
  for (const result of results) {
    const ret = result.strategy.totalReturn.toFixed(2) + '%';
    const dd = result.strategy.maxDrawdown.toFixed(2) + '%';
    const wr = result.strategy.winRate.toFixed(1) + '%';
    const trades = result.strategy.totalTrades;
    const pf = isFinite(result.strategy.profitFactor) ? result.strategy.profitFactor.toFixed(2) : 'N/A';
    
    console.log(`${result.name.padEnd(25)} ${ret.padEnd(12)} ${dd.padEnd(12)} ${wr.padEnd(10)} ${String(trades).padEnd(8)} ${pf}`);
  }
  
  // Find best strategy
  const best = results.reduce((best, curr) => 
    curr.strategy.totalReturn > best.strategy.totalReturn ? curr : best
  );
  
  console.log(`\n🏆 Best Strategy: ${best.name} with ${best.strategy.totalReturn.toFixed(2)}% return`);
}

compareStrategies()
  .then(() => console.log('\n✅ Comparison complete!'))
  .catch(error => console.error('Error:', error));
