/**
 * Base Strategy Class
 * All trading strategies should extend this class
 */
class BaseStrategy {
  constructor(params) {
    this.params = params;
    this.name = 'BaseStrategy';
  }

  /**
   * Get the default parameters for this strategy
   * @returns {Object} Default parameters
   */
  static getDefaultParams() {
    return {
      initialCapital: 10000,
      commissionPerTrade: 1.0,
      stopLossPercent: 5.0
    };
  }

  /**
   * Calculate all indicators needed for the strategy
   * Must be implemented by child classes
   * @param {Array} candles - Array of OHLCV candles
   * @returns {Object} Object containing all calculated indicators
   */
  calculateIndicators(candles) {
    throw new Error('calculateIndicators() must be implemented by child class');
  }

  /**
   * Get the minimum number of candles required for indicator warmup
   * @returns {number} Minimum candles needed
   */
  getMinimumCandles() {
    throw new Error('getMinimumCandles() must be implemented by child class');
  }

  /**
   * Get the first valid index where strategy can start trading
   * @param {Object} indicators - Calculated indicators
   * @param {Array} candles - Array of candles
   * @returns {number} First valid index
   */
  getFirstValidIndex(indicators, candles) {
    return this.getMinimumCandles() - 1;
  }

  /**
   * Check for entry signal
   * @param {number} i - Current candle index
   * @param {Object} indicators - Calculated indicators
   * @param {Array} candles - Array of candles
   * @param {Object|null} position - Current position (null if no position)
   * @returns {boolean} True if entry signal detected
   */
  checkEntrySignal(i, indicators, candles, position) {
    throw new Error('checkEntrySignal() must be implemented by child class');
  }

    /**
   * Check for exit signal
   * @param {number} i - Current candle index
   * @param {Object} indicators - Calculated indicators
   * @param {Array} candles - Array of candles
   * @param {Object} position - Current position
   * @returns {Object|null} Exit info {price, reason} or null if no exit
   */
  checkExitSignal(i, indicators, candles, position) {
    // Check stop loss only if enabled (stopLossPercent > 0)
    if (this.params.stopLossPercent && this.params.stopLossPercent > 0) {
      const candle = candles[i];
      const stopLossPrice = position.entryPrice * (1 - this.params.stopLossPercent / 100);
      
      // Check if the low of the candle touched or went below stop loss
      if (candle.low <= stopLossPrice) {
        return {
          price: stopLossPrice,
          reason: 'STOP_LOSS'
        };
      }
    }
    
    return null;
  }

  /**
   * Get strategy-specific data to store with position
   * @param {number} i - Current candle index
   * @param {Object} indicators - Calculated indicators
   * @returns {Object} Additional position data
   */
  getPositionData(i, indicators) {
    return {};
  }

  /**
   * Get description of the strategy
   * @returns {string} Strategy description
   */
  getDescription() {
    return this.name;
  }
}

module.exports = BaseStrategy;
