# QuantConnect Backtesting System

Professional-grade backtesting verification for strategies developed in the OpenCL optimizer.

## Purpose

This system allows you to:
1. **Verify** strategies optimized in OpenCL on a professional platform
2. **Paper trade** strategies before live deployment
3. **Access institutional-grade data** and execution modeling
4. **Generate regulatory-compliant** performance reports

## Structure

```
quantconnect/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── main.py                      # Strategy runner & tester
├── strategies/                  # Strategy implementations
│   ├── __init__.py
│   ├── base_strategy.py         # Base strategy class
│   ├── adaptive_ema_v2.py       # Ported from OpenCL
│   └── adaptive_ema_v4.py       # Add more strategies
├── utils/                       # Helper utilities
│   ├── __init__.py
│   ├── data_loader.py           # Load historical data
│   ├── performance.py           # Performance metrics
│   └── converter.py             # OpenCL -> QC converter
├── data/                        # Local data for testing
│   └── .gitkeep
├── results/                     # Backtest results
│   └── .gitkeep
└── notebooks/                   # Jupyter notebooks for analysis
    └── analyze_results.ipynb
```

## Quick Start

### 1. Install Dependencies

```bash
cd quantconnect
pip install -r requirements.txt
```

### 2. Test a Strategy Locally

```bash
# Run with default parameters
python main.py --strategy adaptive_ema_v2 --symbol QQQ --start 2023-01-01 --end 2024-12-31

# Run with custom parameters
python main.py --strategy adaptive_ema_v2 --symbol QQQ --fast-base 8 --slow-base 14 --fast-mult 1.6
```

### 3. Deploy to QuantConnect Cloud

```bash
# Upload strategy to your QC account
python main.py --deploy adaptive_ema_v2 --project-id 12345678
```

## Strategy Porting Guide

To port a strategy from OpenCL:

1. **Extract optimized parameters** from OpenCL results
2. **Use the converter** utility:
   ```bash
   python -m utils.converter --input ../opencl/strategies/adaptive_ema_v2/config_1h.h
   ```
3. **Review generated strategy** in `strategies/` folder
4. **Test locally** before deploying to QC

## Performance Comparison

Compare OpenCL vs QuantConnect results:

```bash
python main.py --compare --strategy adaptive_ema_v2 --symbol QQQ
```

This will:
- Run backtest on same date range as OpenCL
- Compare metrics side-by-side
- Generate comparison report

## Features

### Local Backtesting
- Uses `yfinance` for free historical data
- Implements realistic commission models
- Calculates professional metrics (Sharpe, Sortino, Calmar)
- Generates detailed trade logs

### QuantConnect Integration
- Deploy strategies to QC cloud with one command
- Access institutional data quality
- Use QC's research environment
- Paper trade before going live

### Analysis Tools
- Jupyter notebooks for deep analysis
- Performance visualization
- Parameter sensitivity analysis
- Walk-forward testing framework

## Configuration

Edit `config.json` to set:
- Commission models
- Slippage assumptions
- Initial capital
- Data providers
- QuantConnect API keys

## Next Steps

1. **Verify OpenCL strategies** work correctly in QC
2. **Run walk-forward tests** to validate robustness
3. **Paper trade** best strategies
4. **Deploy to live** after paper trading success

## Resources

- [QuantConnect Docs](https://www.quantconnect.com/docs)
- [Strategy Examples](./strategies/)
- [Performance Analysis](./notebooks/)
