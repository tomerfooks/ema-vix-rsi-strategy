# Makefile for OpenCL GPU optimizer

CC = gcc
CFLAGS = -O3 -Wall
LDFLAGS = -framework OpenCL

TARGET = optimize

# Default strategy (can be overridden: make STRATEGY=ema_simple_v1)
STRATEGY ?= adaptive_ema_v1

# Strategy-specific source files
ifeq ($(STRATEGY),adaptive_ema_v4)
SRC = strategies/adaptive_ema_v4/optimize.c
STRATEGY_DIR = strategies/adaptive_ema_v4
else ifeq ($(STRATEGY),adaptive_ema_v3)
SRC = strategies/adaptive_ema_v3/optimize.c
STRATEGY_DIR = strategies/adaptive_ema_v3
else ifeq ($(STRATEGY),adaptive_ema_v2.1)
SRC = strategies/adaptive_ema_v2.1/optimize.c
STRATEGY_DIR = strategies/adaptive_ema_v2.1
else ifeq ($(STRATEGY),adaptive_ema_v2)
SRC = strategies/adaptive_ema_v2/optimize.c
STRATEGY_DIR = strategies/adaptive_ema_v2
else ifeq ($(STRATEGY),ema_simple_v1)
SRC = strategies/ema_simple_v1/optimize.c
STRATEGY_DIR = strategies/ema_simple_v1
else
SRC = strategies/adaptive_ema_v1/optimize.c
STRATEGY_DIR = strategies/adaptive_ema_v1
endif

.PHONY: all clean run-goog run-qqq run-spy

all: $(TARGET)

$(TARGET): $(SRC)
	@echo "🔨 Compiling OpenCL optimizer with strategy: $(STRATEGY)..."
	@cd $(STRATEGY_DIR) && $(CC) $(CFLAGS) $(LDFLAGS) -I. optimize.c -o ../../$(TARGET)
	@echo "✅ Build complete: $(TARGET) [$(STRATEGY)]"

clean:
	@echo "🧹 Cleaning..."
	@rm -f $(TARGET) optimize_opencl list_devices
	@echo "✅ Clean complete"

# Quick test targets
run-goog: $(TARGET)
	@echo "🚀 Running optimization on GOOG 1h..."
	@./$(TARGET) GOOG 1h

run-qqq: $(TARGET)
	@echo "🚀 Running optimization on QQQ 1h..."
	@./$(TARGET) QQQ 1h

run-spy: $(TARGET)
	@echo "🚀 Running optimization on SPY 1d..."
	@./$(TARGET) SPY 1d

# Fetch data helpers
fetch-goog:
	@echo "📥 Fetching GOOG data..."
	@cd ../c && python3 fetch_data.py GOOG 1h 600

fetch-qqq:
	@echo "📥 Fetching QQQ data..."
	@cd ../c && python3 fetch_data.py QQQ 1h 600

fetch-spy:
	@echo "📥 Fetching SPY data..."
	@cd ../c && python3 fetch_data.py SPY 1d 500

# Full workflow targets
test-goog: fetch-goog all run-goog

test-qqq: fetch-qqq all run-qqq

test-spy: fetch-spy all run-spy

help:
	@echo "Available targets:"
	@echo "  make all          - Build the optimizer"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make run-goog     - Run optimization on GOOG 1h"
	@echo "  make run-qqq      - Run optimization on QQQ 1h"
	@echo "  make run-spy      - Run optimization on SPY 1d"
	@echo "  make fetch-goog   - Download GOOG data"
	@echo "  make fetch-qqq    - Download QQQ data"
	@echo "  make fetch-spy    - Download SPY data"
	@echo "  make test-goog    - Full workflow (fetch + build + run GOOG)"
	@echo "  make test-qqq     - Full workflow (fetch + build + run QQQ)"
	@echo "  make test-spy     - Full workflow (fetch + build + run SPY)"
	@echo ""
	@echo "Manual usage:"
	@echo "  ./optimize <TICKER> <INTERVAL>"
	@echo "  Example: ./optimize GOOG 1h"
