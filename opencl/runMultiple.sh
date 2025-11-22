#!/bin/bash
# OpenCL GPU Optimizer - Multiple Candle Test Workflow
# Usage: ./runMultiple.sh <TICKER> <INTERVAL> <STRATEGY> <CANDLES_LIST> [nosave]
# Examples:
#   ./runMultiple.sh QQQ 1h adaptive_ema_v2.1 "2500 5000 75000 10000 15000"
#   ./runMultiple.sh QQQ 1h adaptive_ema_v2.1 "500 1000 1500 2500 7000 10000 15000" nosave
#   ./runMultiple.sh SPY 4h adaptive_ema_v2 "270 500 1000"

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 4 ]; then
    echo -e "${RED}❌ Error: Missing arguments${NC}"
    echo ""
    echo "Usage: $0 <TICKER> <INTERVAL> <STRATEGY> <CANDLES_LIST> [nosave]"
    echo ""
    echo "Arguments:"
    echo "  TICKER        Stock ticker (e.g., GOOG, QQQ, SPY)"
    echo "  INTERVAL      Time interval: 1h, 4h, or 1d"
    echo "  STRATEGY      Strategy name"
    echo "                Available: adaptive_ema_v1, adaptive_ema_v2, adaptive_ema_v2.1,"
    echo "                          adaptive_ema_v2.2, adaptive_ema_v4, adaptive_donchian_v1,"
    echo "                          adaptive_ema_vol_v1"
    echo "  CANDLES_LIST  Space-separated list of candle counts in quotes"
    echo "  nosave        Skip saving JSON and HTML results (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 QQQ 1h adaptive_ema_v2.1 \"500 1000 1500\""
    echo "  $0 QQQ 1h adaptive_ema_v2.1 \"500 1000 1500 2500 7000\" nosave"
    echo "  $0 SPY 4h adaptive_ema_v2 \"270 500 1000\""
    exit 1
fi

TICKER=$1
INTERVAL=$2
STRATEGY=$3
CANDLES_LIST=$4
NOSAVE_FLAG=""

# Check for nosave flag
if [ $# -ge 5 ] && [ "$5" = "nosave" ]; then
    NOSAVE_FLAG="nosave"
fi

# Validate interval
case "$INTERVAL" in
    1h|1H)
        INTERVAL="1h"
        ;;
    4h|4H)
        INTERVAL="4h"
        ;;
    1d|1D)
        INTERVAL="1d"
        ;;
    *)
        echo -e "${RED}❌ Error: Invalid interval '$INTERVAL'${NC}"
        echo "   Must be one of: 1h, 4h, 1d"
        exit 1
        ;;
esac

# Convert ticker to uppercase
TICKER=$(echo "$TICKER" | tr '[:lower:]' '[:upper:]')

# Convert candles list to array
IFS=' ' read -r -a CANDLES_ARRAY <<< "$CANDLES_LIST"

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  MULTIPLE CANDLE OPTIMIZATION TEST${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Ticker:${NC}     $TICKER"
echo -e "  ${GREEN}Interval:${NC}   $INTERVAL"
echo -e "  ${GREEN}Strategy:${NC}   $STRATEGY"
echo -e "  ${GREEN}Candles:${NC}    ${CANDLES_ARRAY[@]}"
if [ -n "$NOSAVE_FLAG" ]; then
    echo -e "  ${YELLOW}Mode:${NC}       No-save (results won't be saved)"
fi
echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Use virtual environment if it exists, otherwise fall back to python3
if [ -f "../.venv/bin/python" ]; then
    PYTHON_CMD="../.venv/bin/python"
else
    PYTHON_CMD="python3"
fi

# Array to store results
declare -a RESULTS

# Step 1: Compile optimizer once
echo -e "${YELLOW}🔨 Step 1/2: Compiling optimizer...${NC}"
echo ""

if make clean && make STRATEGY="$STRATEGY"; then
    echo -e "${GREEN}✅ Compilation successful${NC}"
else
    echo -e "${RED}❌ Compilation failed${NC}"
    exit 1
fi

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Step 2: Loop through each candle count
TOTAL=${#CANDLES_ARRAY[@]}
CURRENT=0

for CANDLES in "${CANDLES_ARRAY[@]}"; do
    CURRENT=$((CURRENT + 1))
    
    echo -e "${CYAN}⚡ Test $CURRENT/$TOTAL: Running optimization with $CANDLES candles${NC}"
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo ""
    
    # Fetch data for this candle count
    if ! $PYTHON_CMD fetch_data.py "$TICKER" "$INTERVAL" "$CANDLES"; then
        echo -e "${RED}❌ Failed to fetch data for $CANDLES candles${NC}"
        RESULTS+=("$CANDLES candles: FAILED (data fetch)")
        echo ""
        echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
        echo ""
        continue
    fi
    
    echo ""
    
    # Run optimization and capture key metrics
    if OUTPUT=$(./optimize "$TICKER" "$INTERVAL" $NOSAVE_FLAG 2>&1); then
        # Extract metrics from output
        RETURN=$(echo "$OUTPUT" | grep "Total Return:" | awk '{print $3}')
        DRAWDOWN=$(echo "$OUTPUT" | grep "Max Drawdown:" | awk '{print $3}')
        CALMAR=$(echo "$OUTPUT" | grep "Calmar Ratio:" | awk '{print $3}')
        TRADES=$(echo "$OUTPUT" | grep "Total Trades:" | awk '{print $3}')
        OUTPERF=$(echo "$OUTPUT" | grep "Strategy Outperformance:" | awk '{print $3}')
        
        # Store result
        RESULTS+=("$CANDLES: Return=$RETURN, DD=$DRAWDOWN, Calmar=$CALMAR, Trades=$TRADES, Outperf=$OUTPERF")
        
        # Display output
        echo "$OUTPUT"
    else
        echo -e "${RED}❌ Optimization failed for $CANDLES candles${NC}"
        RESULTS+=("$CANDLES candles: FAILED (optimization)")
    fi
    
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo ""
done

# Display summary
echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo -e "${MAGENTA}  SUMMARY OF ALL TESTS${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Ticker:${NC}     $TICKER"
echo -e "${GREEN}Interval:${NC}   $INTERVAL"
echo -e "${GREEN}Strategy:${NC}   $STRATEGY"
echo ""

# Print results table header
printf "%-10s | %-12s | %-10s | %-10s | %-8s | %-12s\n" "Candles" "Return" "Max DD" "Calmar" "Trades" "Outperform"
echo "-----------|--------------|------------|------------|----------|---------------"

# Print each result
for RESULT in "${RESULTS[@]}"; do
    if [[ "$RESULT" == *"FAILED"* ]]; then
        echo "$RESULT"
    else
        CANDLES=$(echo "$RESULT" | cut -d':' -f1)
        RETURN=$(echo "$RESULT" | grep -o "Return=[^,]*" | cut -d'=' -f2)
        DD=$(echo "$RESULT" | grep -o "DD=[^,]*" | cut -d'=' -f2)
        CALMAR=$(echo "$RESULT" | grep -o "Calmar=[^,]*" | cut -d'=' -f2)
        TRADES=$(echo "$RESULT" | grep -o "Trades=[^,]*" | cut -d'=' -f2)
        OUTPERF=$(echo "$RESULT" | grep -o "Outperf=[^,]*" | cut -d'=' -f2)
        
        printf "%-10s | %-12s | %-10s | %-10s | %-8s | %-12s\n" "$CANDLES" "$RETURN" "$DD" "$CALMAR" "$TRADES" "$OUTPERF"
    fi
done

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ All tests completed!${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════${NC}"
echo ""
