#!/bin/bash
# Compare all strategies on QQQ 1h with different candle counts
# Usage: ./compare_strategies.sh

set -e

TICKER="qqq"
INTERVAL="1h"
STRATEGIES=( "adaptive_ema_v1" "adaptive_ema_v2" "adaptive_ema_v2.1" "adaptive_ema_v2.2" "adaptive_ema_v4")
CANDLE_COUNTS=(300 500 600 800 1100 1400 1700 2000 2250 2500)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   STRATEGY COMPARISON TEST${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo -e "   Ticker: ${GREEN}${TICKER}${NC}"
echo -e "   Interval: ${GREEN}${INTERVAL}${NC}"
echo -e "   Strategies: ${GREEN}${#STRATEGIES[@]}${NC} (v1, v2, v3, v4)"
echo -e "   Candle Counts: ${GREEN}${#CANDLE_COUNTS[@]}${NC} (600, 1000, 1400, 1700, 2000, 2500)"
echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
echo ""

# Create results directory
RESULTS_DIR="comparison_results"
mkdir -p "$RESULTS_DIR"

# CSV file for results
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CSV_FILE="${RESULTS_DIR}/${TIMESTAMP}_${TICKER}_${INTERVAL}_comparison.csv"

# Write CSV header
echo "Strategy,Candles,Total_Return,Max_Drawdown,Calmar_Ratio,Total_Trades,Score,Buy_Hold_Return,Outperformance" > "$CSV_FILE"

# Counter for progress
TOTAL_TESTS=$((${#STRATEGIES[@]} * ${#CANDLE_COUNTS[@]}))
CURRENT_TEST=0

# Run each strategy with each candle count
for STRATEGY in "${STRATEGIES[@]}"; do
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}   Testing Strategy: ${STRATEGY}${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    for CANDLES in "${CANDLE_COUNTS[@]}"; do
        CURRENT_TEST=$((CURRENT_TEST + 1))
        echo -e "${YELLOW}[${CURRENT_TEST}/${TOTAL_TESTS}]${NC} Testing ${STRATEGY} with ${CANDLES} candles..."
        echo ""
        
        # Fetch data with specific candle count
        echo -e "  ${BLUE}→${NC} Fetching data..."
        if ! ../.venv/bin/python fetch_data.py "$TICKER" "$INTERVAL" "$CANDLES" > /dev/null 2>&1; then
            echo -e "  ${RED}✗ Failed to fetch data${NC}"
            echo "${STRATEGY},${CANDLES},ERROR,,,,,," >> "$CSV_FILE"
            continue
        fi
        
        # Compile with strategy
        echo -e "  ${BLUE}→${NC} Compiling..."
        if ! make clean > /dev/null 2>&1 || ! make STRATEGY="$STRATEGY" > /dev/null 2>&1; then
            echo -e "  ${RED}✗ Compilation failed${NC}"
            echo "${STRATEGY},${CANDLES},ERROR,,,,,," >> "$CSV_FILE"
            continue
        fi
        
        # Run optimization and capture output
        echo -e "  ${BLUE}→${NC} Running test..."
        OUTPUT=$(./optimize "$TICKER" "$INTERVAL" nosave 2>&1 || echo "ERROR")
        
        if [[ "$OUTPUT" == *"ERROR"* ]] || [[ "$OUTPUT" == *"failed"* ]]; then
            echo -e "  ${RED}✗ Test failed${NC}"
            echo "${STRATEGY},${CANDLES},ERROR,,,,,," >> "$CSV_FILE"
            continue
        fi
        
        # Extract metrics from output
        TOTAL_RETURN=$(echo "$OUTPUT" | grep "Total Return:" | grep -oE "[+-]?[0-9]+\.[0-9]+%" | head -1 | tr -d '%')
        MAX_DRAWDOWN=$(echo "$OUTPUT" | grep "Max Drawdown:" | grep -oE "[+-]?[0-9]+\.[0-9]+%" | head -1 | tr -d '%')
        CALMAR_RATIO=$(echo "$OUTPUT" | grep "Calmar Ratio:" | grep -oE "[+-]?[0-9]+\.[0-9]+" | head -1)
        TOTAL_TRADES=$(echo "$OUTPUT" | grep "Total Trades:" | grep -oE "[0-9]+" | head -1)
        SCORE=$(echo "$OUTPUT" | grep "Score:" | grep -oE "[+-]?[0-9]+\.[0-9]+" | head -1)
        BUY_HOLD=$(echo "$OUTPUT" | grep "Buy & Hold Return:" | grep -oE "[+-]?[0-9]+\.[0-9]+%" | head -1 | tr -d '%')
        OUTPERFORMANCE=$(echo "$OUTPUT" | grep "Strategy Outperformance:" | grep -oE "[+-]?[0-9]+\.[0-9]+%" | head -1 | tr -d '%')
        
        # Handle empty values
        TOTAL_RETURN=${TOTAL_RETURN:-0}
        MAX_DRAWDOWN=${MAX_DRAWDOWN:-0}
        CALMAR_RATIO=${CALMAR_RATIO:-0}
        TOTAL_TRADES=${TOTAL_TRADES:-0}
        SCORE=${SCORE:-0}
        BUY_HOLD=${BUY_HOLD:-0}
        OUTPERFORMANCE=${OUTPERFORMANCE:-0}
        
        # Write to CSV
        echo "${STRATEGY},${CANDLES},${TOTAL_RETURN},${MAX_DRAWDOWN},${CALMAR_RATIO},${TOTAL_TRADES},${SCORE},${BUY_HOLD},${OUTPERFORMANCE}" >> "$CSV_FILE"
        
        # Display summary
        echo -e "  ${GREEN}✓${NC} Return: ${TOTAL_RETURN}% | Drawdown: ${MAX_DRAWDOWN}% | Calmar: ${CALMAR_RATIO} | Trades: ${TOTAL_TRADES}"
        echo -e "    Score: ${SCORE} | B&H: ${BUY_HOLD}% | Outperf: ${OUTPERFORMANCE}%"
        echo ""
    done
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   COMPARISON COMPLETE${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "Results saved to: ${CYAN}${CSV_FILE}${NC}"
echo ""

# Generate summary report
echo -e "${YELLOW}Generating summary report...${NC}"
../.venv/bin/python - <<EOF
import csv
import sys

# Read CSV
data = []
with open('${CSV_FILE}', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Total_Return'] != 'ERROR':
            data.append(row)

if not data:
    print("\n${RED}No valid results to analyze${NC}")
    sys.exit(1)

# Group by strategy
strategies = {}
for row in data:
    strategy = row['Strategy']
    if strategy not in strategies:
        strategies[strategy] = []
    strategies[strategy].append(row)

print("\n${CYAN}═══════════════════════════════════════════════════════════════${NC}")
print("${CYAN}                      SUMMARY BY STRATEGY${NC}")
print("${CYAN}═══════════════════════════════════════════════════════════════${NC}\n")

for strategy, rows in sorted(strategies.items()):
    print(f"${MAGENTA}{'─'*63}${NC}")
    print(f"${MAGENTA}  {strategy.upper()}${NC}")
    print(f"${MAGENTA}{'─'*63}${NC}")
    print(f"  {'Candles':<10} {'Return':<10} {'Drawdown':<10} {'Calmar':<8} {'Trades':<8} {'Outperf':<10}")
    print(f"  {'-'*63}")
    
    for row in rows:
        candles = row['Candles']
        ret = float(row['Total_Return'])
        dd = float(row['Max_Drawdown'])
        calmar = float(row['Calmar_Ratio'])
        trades = int(row['Total_Trades'])
        outperf = float(row['Outperformance'])
        
        color = '${GREEN}' if outperf > 0 else '${RED}'
        print(f"  {candles:<10} {ret:>7.2f}%  {dd:>7.2f}%  {calmar:>7.2f}  {trades:>5}    {color}{outperf:>7.2f}%${NC}")
    
    # Calculate averages
    avg_ret = sum(float(r['Total_Return']) for r in rows) / len(rows)
    avg_dd = sum(float(r['Max_Drawdown']) for r in rows) / len(rows)
    avg_calmar = sum(float(r['Calmar_Ratio']) for r in rows) / len(rows)
    avg_trades = sum(int(r['Total_Trades']) for r in rows) / len(rows)
    avg_outperf = sum(float(r['Outperformance']) for r in rows) / len(rows)
    
    print(f"  {'-'*63}")
    print(f"  {'AVERAGE':<10} {avg_ret:>7.2f}%  {avg_dd:>7.2f}%  {avg_calmar:>7.2f}  {avg_trades:>5.1f}    {avg_outperf:>7.2f}%")
    print()

# Find best strategy by average outperformance
best_strategy = max(strategies.items(), key=lambda x: sum(float(r['Outperformance']) for r in x[1]) / len(x[1]))
print(f"${GREEN}═══════════════════════════════════════════════════════════════${NC}")
print(f"${GREEN}  Best Strategy (by avg outperformance): {best_strategy[0]}${NC}")
print(f"${GREEN}═══════════════════════════════════════════════════════════════${NC}\n")

EOF

echo ""
echo -e "Full results in: ${CYAN}${CSV_FILE}${NC}"
echo ""
