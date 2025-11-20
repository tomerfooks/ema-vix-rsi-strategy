# Makefile for OpenCL GPU optimizer

CC = gcc
CFLAGS = -O3 -Wall
LDFLAGS = -framework OpenCL

TARGET = optimize
SRC = optimize.c

# Default strategy (can be overridden: make STRATEGY=adaptive_ema_v2)
STRATEGY ?= adaptive_ema_v1

# Add strategy-specific defines
ifeq ($(STRATEGY),adaptive_ema_v2)
CFLAGS += -DUSE_STRATEGY_V2
endif

# Add strategy name to compiler flags
CFLAGS += -DSTRATEGY_NAME=\"$(STRATEGY)\"

.PHONY: all clean run-goog run-qqq run-spy

all: $(TARGET)

$(TARGET): $(SRC)
	@echo "🔨 Compiling OpenCL optimizer with strategy: $(STRATEGY)..."
	@$(CC) $(CFLAGS) $(LDFLAGS) $(SRC) -o $(TARGET)
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
