#!/bin/bash
# Strategy selection script for OpenCL optimizer
# Usage: ./switch-strategy.sh <strategy_name>
# Example: ./switch-strategy.sh adaptive_ema_v2

if [ $# -lt 1 ]; then
    echo "Usage: $0 <strategy_name>"
    echo ""
    echo "Available strategies:"
    ls -d strategies/adaptive_ema_* 2>/dev/null | xargs -n1 basename || echo "  No strategies found"
    echo ""
    echo "Current strategy (in optimize.c):"
    grep "#include \"strategies/" optimize.c | head -1
    exit 1
fi

STRATEGY=$1

# Check if strategy exists
if [ ! -d "strategies/$STRATEGY" ]; then
    echo "❌ Error: Strategy '$STRATEGY' not found"
    echo ""
    echo "Available strategies:"
    ls -d strategies/adaptive_ema_* 2>/dev/null | xargs -n1 basename
    exit 1
fi

echo "🔄 Switching to strategy: $STRATEGY"
echo ""

# Create backup
cp optimize.c optimize.c.backup

# Update the include statements
if [ "$STRATEGY" = "adaptive_ema_v2" ]; then
    # Switch to v2
    sed -i '' 's|#include "strategies/adaptive_ema_v1/|#include "strategies/adaptive_ema_v2/|g' optimize.c
    sed -i '' 's|// v1 strategy (default)|// v2 strategy|g' optimize.c
    echo "✅ Switched includes to v2"
elif [ "$STRATEGY" = "adaptive_ema_v1" ]; then
    # Switch to v1
    sed -i '' 's|#include "strategies/adaptive_ema_v2/|#include "strategies/adaptive_ema_v1/|g' optimize.c
    sed -i '' 's|// v2 strategy|// v1 strategy (default)|g' optimize.c
    echo "✅ Switched includes to v1"
else
    echo "⚠️  Unknown strategy: $STRATEGY"
    echo "   You may need to manually edit optimize.c"
    exit 1
fi

echo ""
echo "📝 Note: optimize.c has been updated"
echo "   Run 'make clean && make' to recompile"
echo ""
echo "Or use the run script directly:"
echo "   ./run.sh <ticker> <interval> $STRATEGY"
