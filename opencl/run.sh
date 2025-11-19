#!/bin/bash
# OpenCL GPU Optimizer - Automated Workflow
# Usage: ./run.sh <TICKER> <INTERVAL> [CANDLES]
# Examples:
#   ./run.sh GOOG 1h
#   ./run.sh GOOG 1h 1000
#   ./run.sh QQQ 4h 600
#   ./run.sh SPY 1d 500

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_CANDLES=600

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}❌ Error: Missing arguments${NC}"
    echo ""
    echo "Usage: $0 <TICKER> <INTERVAL> [CANDLES]"
    echo ""
    echo "Arguments:"
    echo "  TICKER    Stock ticker (e.g., GOOG, QQQ, SPY)"
    echo "  INTERVAL  Time interval: 1h, 4h, or 1d"
    echo "  CANDLES   Number of candles (optional, default: 600)"
    echo ""
    echo "Examples:"
    echo "  $0 GOOG 1h           # Use default 600 candles"
    echo "  $0 GOOG 1h 1000      # Use 1000 candles"
    echo "  $0 QQQ 4h 600"
    echo "  $0 SPY 1d 500"
    exit 1
fi

TICKER=$1
INTERVAL=$2
CANDLES=${3:-$DEFAULT_CANDLES}

# Validate interval
case "$INTERVAL" in
    1h|4h|1d|1H|4H|1D)
        # Convert to lowercase for consistency
        INTERVAL=$(echo "$INTERVAL" | tr '[:upper:]' '[:lower:]')
        ;;
    *)
        echo -e "${RED}❌ Error: Invalid interval '$INTERVAL'${NC}"
        echo "   Must be one of: 1h, 4h, 1d"
        exit 1
        ;;
esac

# Convert ticker to uppercase
TICKER=$(echo "$TICKER" | tr '[:lower:]' '[:upper:]')

echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 OpenCL GPU Optimizer - Automated Workflow${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Ticker:${NC}   $TICKER"
echo -e "  ${GREEN}Interval:${NC} $INTERVAL"
echo -e "  ${GREEN}Candles:${NC}  $CANDLES"
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

# Step 2: Compile optimizer (if needed)
echo -e "${YELLOW}🔨 Step 2/3: Checking compilation...${NC}"
echo ""

if [ ! -f "optimize" ] || [ "optimize.c" -nt "optimize" ]; then
    echo "   Compiling optimizer..."
    if make; then
        echo -e "${GREEN}✅ Compilation successful${NC}"
    else
        echo -e "${RED}❌ Compilation failed${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Optimizer already compiled (up to date)${NC}"
fi

echo ""

# Step 3: Run optimization
echo -e "${YELLOW}⚡ Step 3/3: Running GPU optimization...${NC}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo ""

if ./optimize "$TICKER" "$INTERVAL"; then
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Optimization completed successfully!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
else
    echo -e "${RED}❌ Optimization failed${NC}"
    exit 1
fi
