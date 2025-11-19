#!/bin/bash
# Quick start script for Python trading system

echo "🚀 Python Trading Strategy - Quick Start"
echo "========================================"
echo ""

# Check if in python directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Run this script from the python/ directory"
    exit 1
fi

# Check Python version
echo "📌 Checking Python version..."
python3 --version

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Test imports
echo ""
echo "🧪 Testing imports..."
python3 -c "import numpy; import pandas; import numba; import yfinance; print('✅ All imports successful!')"

# Run indicator tests
echo ""
echo "🧪 Testing Numba-optimized indicators..."
python3 indicators_numba.py

echo ""
echo "✅ Setup complete! Ready to run optimizations."
echo ""
echo "Try these commands:"
echo "  python3 optimize_numba.py QQQ        # Optimize QQQ"
echo "  python3 backtest_numba.py            # Run backtest"
echo ""
