#!/bin/bash
# OpenCL GPU Optimizer - Automated Workflow
# Usage: ./run.sh <TICKER> <INTERVAL> [STRATEGY] [CANDLES|nosave]
# Examples:
#   ./run.sh GOOG 1h
#   ./run.sh GOOG 1h adaptive_ema_v2
#   ./run.sh QQQ 1d adaptive_ema_v1
#   ./run.sh SPY 4h adaptive_ema_v2 600
#   ./run.sh QQQ 1d adaptive_ema_v1 nosave

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}❌ Error: Missing arguments${NC}"
    echo ""
    echo "Usage: $0 <TICKER> <INTERVAL> [STRATEGY] [CANDLES|nosave]"
    echo ""
    echo "Arguments:"
    echo "  TICKER    Stock ticker (e.g., GOOG, QQQ, SPY)"
    echo "  INTERVAL  Time interval: 1h, 4h, or 1d"
    echo "  STRATEGY  Strategy version (optional, default: adaptive_ema_v1)"
    echo "            Options: adaptive_ema_v1, adaptive_ema_v2"
    echo "  CANDLES   Number of candles (optional, defaults: 1h=500, 4h=270, 1d=150)"
    echo "  nosave    Skip saving JSON and HTML results"
    echo ""
    echo "Examples:"
    echo "  $0 GOOG 1h                      # Use v1, default candles"
    echo "  $0 GOOG 1h adaptive_ema_v2      # Use v2, default candles"
    echo "  $0 QQQ 1d adaptive_ema_v1       # Use v1, default candles"
    echo "  $0 SPY 4h adaptive_ema_v2 600   # Use v2, 600 candles"
    echo "  $0 QQQ 1d adaptive_ema_v1 nosave # Use v1, no save results"
    echo ""
    echo "Strategy Comparison:"
    echo "  v1: 3 EMA pairs, ATR percentile, simpler"
    echo "  v2: KAMA + ADX>25 gate + trailing stops, 2× profit factor"
    exit 1
fi

TICKER=$1
INTERVAL=$2
NOSAVE_FLAG=""

# Check if 3rd argument is a strategy name or a number
if [ $# -ge 3 ]; then
    # If it starts with "adaptive_" it's a strategy, otherwise it could be candles or nosave
    if [[ "$3" =~ ^adaptive_ ]]; then
        STRATEGY=$3
        # Check 4th argument for candles or nosave
        if [ $# -ge 4 ]; then
            if [ "$4" = "nosave" ]; then
                NOSAVE_FLAG="nosave"
            else
                CANDLES=$4
            fi
        fi
    elif [ "$3" = "nosave" ]; then
        STRATEGY="adaptive_ema_v1"
        NOSAVE_FLAG="nosave"
    else
        STRATEGY="adaptive_ema_v1"
        CANDLES=$3
    fi
else
    STRATEGY="adaptive_ema_v1"
    CANDLES=""
fi

# Validate strategy
if [ ! -d "strategies/$STRATEGY" ]; then
    echo -e "${RED}❌ Error: Strategy '$STRATEGY' not found${NC}"
    echo ""
    echo "Available strategies:"
    for dir in strategies/adaptive_ema_*; do
        if [ -d "$dir" ]; then
            basename "$dir"
        fi
    done
    exit 1
fi

# Validate interval and set default candles based on timeframe
case "$INTERVAL" in
    1h|1H)
        INTERVAL="1h"
        DEFAULT_CANDLES=500
        ;;
    4h|4H)
        INTERVAL="4h"
        DEFAULT_CANDLES=270
        ;;
    1d|1D)
        INTERVAL="1d"
        DEFAULT_CANDLES=150
        ;;
    *)
        echo -e "${RED}❌ Error: Invalid interval '$INTERVAL'${NC}"
        echo "   Must be one of: 1h, 4h, 1d"
        exit 1
        ;;
esac

CANDLES=${CANDLES:-$DEFAULT_CANDLES}

# Convert ticker to uppercase
TICKER=$(echo "$TICKER" | tr '[:lower:]' '[:upper:]')

echo ""
echo -e "  ${GREEN}Ticker:${NC}   $TICKER"
echo -e "  ${GREEN}Interval:${NC} $INTERVAL"
echo -e "  ${CYAN}Strategy:${NC} $STRATEGY"
echo -e "  ${GREEN}Candles:${NC}  $CANDLES"
if [ -n "$NOSAVE_FLAG" ]; then
    echo -e "  ${YELLOW}Mode:${NC}     No-save (results won't be saved)"
fi
echo ""

# Step 1: Fetch data
echo -e "${YELLOW}📥 Step 1/3: Fetching market data...${NC}"
echo ""

if python3 fetch_data.py "$TICKER" "$INTERVAL" "$CANDLES"; then
    echo ""
    echo -e "${GREEN}✅ Data fetched successfully${NC}"
else
    echo -e "${RED}❌ Failed to fetch data${NC}"
    exit 1
fi

echo ""

# Step 2: Compile optimizer with selected strategy
echo -e "${YELLOW}🔨 Step 2/3: Compiling optimizer with $STRATEGY...${NC}"
echo ""

# Always clean before compiling to ensure config changes are picked up
if make clean && make STRATEGY=$STRATEGY; then
    echo -e "${GREEN}✅ Compilation successful${NC}"
else
    echo -e "${RED}❌ Compilation failed${NC}"
    exit 1
fi

echo ""

# Step 3: Run optimization
echo -e "${YELLOW}⚡ Step 3/3: Running GPU optimization...${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

if ./optimize "$TICKER" "$INTERVAL" $NOSAVE_FLAG; then
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Optimization completed successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
else
    echo -e "${RED}❌ Optimization failed${NC}"
    exit 1
fi
