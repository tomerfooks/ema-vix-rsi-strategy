const YahooFinance = require('yahoo-finance2').default;

const yahooFinance = new YahooFinance();

/**
 * Fetch historical data from Yahoo Finance
 */
async function fetchData(ticker, targetCandles = 1500, interval = '1h') {
  try {
    // Calculate days needed based on interval (with buffer for weekends/holidays)
    const daysNeeded = interval === '1h' ? 300 : (interval === '4h' ? 500 : 730);
    
    const queryOptions = { 
      period1: new Date(Date.now() - daysNeeded * 24 * 60 * 60 * 1000),
      interval: interval
    };
    
    const result = await yahooFinance.chart(ticker, queryOptions);
    
    if (!result || !result.quotes || result.quotes.length === 0) {
      throw new Error('No data returned');
    }
    
    const candles = result.quotes
      .filter(bar => bar.close != null && bar.high != null && bar.low != null && bar.open != null)
      .map(bar => ({
        date: bar.date,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        volume: bar.volume || 0
      }));
    
    // Clean data: interpolate outliers using rolling median
    const cleanedCandles = [];
    const windowSize = 10;
    
    for (let i = 0; i < candles.length; i++) {
      if (i < windowSize) {
        cleanedCandles.push(candles[i]);
        continue;
      }
      
      // Get median of last 10 candles
      const recentPrices = candles.slice(i - windowSize, i).map(c => c.close).sort((a, b) => a - b);
      const median = recentPrices[Math.floor(recentPrices.length / 2)];
      
      const currClose = candles[i].close;
      const deviationPercent = Math.abs((currClose - median) / median * 100);
      
      // Interpolate candles that deviate >15% from rolling median (likely bad data)
      if (deviationPercent > 15) {
        const prevClose = cleanedCandles[cleanedCandles.length - 1].close;
        const nextClose = candles[i + 1]?.close || prevClose;
        const interpolated = (prevClose + nextClose) / 2;
        
        console.log(`   ⚠️  Interpolated bad data: ${new Date(candles[i].date).toISOString().slice(0,16)} - Original: $${currClose.toFixed(2)}, Interpolated: $${interpolated.toFixed(2)} (${deviationPercent.toFixed(1)}% deviation from median)`);
        
        cleanedCandles.push({
          ...candles[i],
          close: interpolated,
          open: interpolated,
          high: Math.max(interpolated, candles[i].high),
          low: Math.min(interpolated, candles[i].low)
        });
        continue;
      }
      
      cleanedCandles.push(candles[i]);
    }
    
    // Limit to target number of candles (most recent)
    return cleanedCandles.slice(-targetCandles);
  } catch (error) {
    console.error(`Error fetching data for ${ticker}:`, error.message);
    return null;
  }
}

module.exports = { fetchData };
