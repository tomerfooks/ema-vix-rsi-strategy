/*
 * OpenCL GPU-accelerated Adaptive EMA Strategy v1 Optimizer
 * Usage: ./optimize <TICKER> <INTERVAL>
 * Example: ./optimize GOOG 1h
 * 
 * Compilation:
 *   make STRATEGY=adaptive_ema_v1
 */

#ifdef __APPLE__
#include <OpenCL/opencl.h>
#else
#include <CL/cl.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <ctype.h>

#define STRATEGY_NAME "adaptive_ema_v1"

// Include v1 strategy config files
#include "config_1h.h"
#include "config_4h.h"
#include "config_1d.h"

typedef struct {
    int fast_length_low_min, fast_length_low_max;
    int slow_length_low_min, slow_length_low_max;
    int fast_length_med_min, fast_length_med_max;
    int slow_length_med_min, slow_length_med_max;
    int fast_length_high_min, fast_length_high_max;
    int slow_length_high_min, slow_length_high_max;
    int atr_length_min, atr_length_max;
    int volatility_length_min, volatility_length_max;
    int low_vol_percentile_min, low_vol_percentile_max;
    int high_vol_percentile_min, high_vol_percentile_max;
} Config;

// Forward declarations
void export_results_to_json(const char* ticker, const char* interval, const char* strategy,
                            float* best_params, float* best_results, float* trade_log,
                            time_t* timestamps, float* closes, int num_candles,
                            float buy_hold_return);
void generate_html_report(const char* json_filename, const char* ticker, 
                         const char* interval, const char* strategy,
                         const char* results_dir, const char* timestamp_str);

// Load configuration based on interval
void load_config(const char* interval, Config* config) {
    // Now reads from strategy config headers (config_1h.h, config_4h.h, config_1d.h)
    // Edit those files to change parameters instead of editing this file!
    
    if (strcmp(interval, "1h") == 0) {
        #ifdef USE_PERCENT_RANGE_1H
            float percent = SEARCH_PERCENT_1H;
            int default_fast_low = FAST_LOW_1H;
            int default_slow_low = SLOW_LOW_1H;
            int default_fast_med = FAST_MED_1H;
            int default_slow_med = SLOW_MED_1H;
            int default_fast_high = FAST_HIGH_1H;
            int default_slow_high = SLOW_HIGH_1H;
            int default_atr = ATR_LENGTH_1H;
            int default_vol = VOL_LENGTH_1H;
            int default_low_pct = LOW_VOL_PCT_1H;
            int default_high_pct = HIGH_VOL_PCT_1H;
            
            config->fast_length_low_min = (int)(default_fast_low * (1 - percent));
            config->fast_length_low_max = (int)(default_fast_low * (1 + percent));
            config->slow_length_low_min = (int)(default_slow_low * (1 - percent));
            config->slow_length_low_max = (int)(default_slow_low * (1 + percent));
            config->fast_length_med_min = (int)(default_fast_med * (1 - percent));
            config->fast_length_med_max = (int)(default_fast_med * (1 + percent));
            config->slow_length_med_min = (int)(default_slow_med * (1 - percent));
            config->slow_length_med_max = (int)(default_slow_med * (1 + percent));
            config->fast_length_high_min = (int)(default_fast_high * (1 - percent));
            config->fast_length_high_max = (int)(default_fast_high * (1 + percent));
            config->slow_length_high_min = (int)(default_slow_high * (1 - percent));
            config->slow_length_high_max = (int)(default_slow_high * (1 + percent));
            config->atr_length_min = (int)(default_atr * (1 - percent));
            config->atr_length_max = (int)(default_atr * (1 + percent));
            config->volatility_length_min = (int)(default_vol * (1 - percent));
            config->volatility_length_max = (int)(default_vol * (1 + percent));
            config->low_vol_percentile_min = (int)(default_low_pct * (1 - percent));
            config->low_vol_percentile_max = (int)(default_low_pct * (1 + percent));
            config->high_vol_percentile_min = (int)(default_high_pct * (1 - percent));
            config->high_vol_percentile_max = (int)(default_high_pct * (1 + percent));
        #else
            fprintf(stderr, "⚠️  Warning: Fixed range mode not implemented. Enable USE_PERCENT_RANGE_1H in config_1h.h\n");
            exit(1);
        #endif
    } else if (strcmp(interval, "4h") == 0) {
        #ifdef USE_PERCENT_RANGE_4H
            float percent = SEARCH_PERCENT_4H;
            int default_fast_low = FAST_LOW_4H;
            int default_slow_low = SLOW_LOW_4H;
            int default_fast_med = FAST_MED_4H;
            int default_slow_med = SLOW_MED_4H;
            int default_fast_high = FAST_HIGH_4H;
            int default_slow_high = SLOW_HIGH_4H;
            int default_atr = ATR_LENGTH_4H;
            int default_vol = VOL_LENGTH_4H;
            int default_low_pct = LOW_VOL_PCT_4H;
            int default_high_pct = HIGH_VOL_PCT_4H;
            
            config->fast_length_low_min = (int)(default_fast_low * (1 - percent));
            config->fast_length_low_max = (int)(default_fast_low * (1 + percent));
            config->slow_length_low_min = (int)(default_slow_low * (1 - percent));
            config->slow_length_low_max = (int)(default_slow_low * (1 + percent));
            config->fast_length_med_min = (int)(default_fast_med * (1 - percent));
            config->fast_length_med_max = (int)(default_fast_med * (1 + percent));
            config->slow_length_med_min = (int)(default_slow_med * (1 - percent));
            config->slow_length_med_max = (int)(default_slow_med * (1 + percent));
            config->fast_length_high_min = (int)(default_fast_high * (1 - percent));
            config->fast_length_high_max = (int)(default_fast_high * (1 + percent));
            config->slow_length_high_min = (int)(default_slow_high * (1 - percent));
            config->slow_length_high_max = (int)(default_slow_high * (1 + percent));
            config->atr_length_min = (int)(default_atr * (1 - percent));
            config->atr_length_max = (int)(default_atr * (1 + percent));
            config->volatility_length_min = (int)(default_vol * (1 - percent));
            config->volatility_length_max = (int)(default_vol * (1 + percent));
            config->low_vol_percentile_min = (int)(default_low_pct * (1 - percent));
            config->low_vol_percentile_max = (int)(default_low_pct * (1 + percent));
            config->high_vol_percentile_min = (int)(default_high_pct * (1 - percent));
            config->high_vol_percentile_max = (int)(default_high_pct * (1 + percent));
        #else
            fprintf(stderr, "⚠️  Warning: Fixed range mode not implemented. Enable USE_PERCENT_RANGE_4H in config_4h.h\n");
            exit(1);
        #endif
    } else { // 1d
        #ifdef USE_PERCENT_RANGE_1D
            float percent = SEARCH_PERCENT_1D;
            int default_fast_low = FAST_LOW_1D;
            int default_slow_low = SLOW_LOW_1D;
            int default_fast_med = FAST_MED_1D;
            int default_slow_med = SLOW_MED_1D;
            int default_fast_high = FAST_HIGH_1D;
            int default_slow_high = SLOW_HIGH_1D;
            int default_atr = ATR_LENGTH_1D;
            int default_vol = VOL_LENGTH_1D;
            int default_low_pct = LOW_VOL_PCT_1D;
            int default_high_pct = HIGH_VOL_PCT_1D;
            
            config->fast_length_low_min = (int)(default_fast_low * (1 - percent));
            config->fast_length_low_max = (int)(default_fast_low * (1 + percent));
            config->slow_length_low_min = (int)(default_slow_low * (1 - percent));
            config->slow_length_low_max = (int)(default_slow_low * (1 + percent));
            config->fast_length_med_min = (int)(default_fast_med * (1 - percent));
            config->fast_length_med_max = (int)(default_fast_med * (1 + percent));
            config->slow_length_med_min = (int)(default_slow_med * (1 - percent));
            config->slow_length_med_max = (int)(default_slow_med * (1 + percent));
            config->fast_length_high_min = (int)(default_fast_high * (1 - percent));
            config->fast_length_high_max = (int)(default_fast_high * (1 + percent));
            config->slow_length_high_min = (int)(default_slow_high * (1 - percent));
            config->slow_length_high_max = (int)(default_slow_high * (1 + percent));
            config->atr_length_min = (int)(default_atr * (1 - percent));
            config->atr_length_max = (int)(default_atr * (1 + percent));
            config->volatility_length_min = (int)(default_vol * (1 - percent));
            config->volatility_length_max = (int)(default_vol * (1 + percent));
            config->low_vol_percentile_min = (int)(default_low_pct * (1 - percent));
            config->low_vol_percentile_max = (int)(default_low_pct * (1 + percent));
            config->high_vol_percentile_min = (int)(default_high_pct * (1 - percent));
            config->high_vol_percentile_max = (int)(default_high_pct * (1 + percent));
        #else
            fprintf(stderr, "⚠️  Warning: Fixed range mode not implemented. Enable USE_PERCENT_RANGE_1D in config_1d.h\n");
            exit(1);
        #endif
    }
}

// Export results to JSON and HTML
void export_results_to_json(const char* ticker, const char* interval, const char* strategy,
                            float* best_params, float* best_results, float* trade_log,
                            time_t* timestamps, float* closes, int num_candles,
                            float buy_hold_return) {
    
    // Create timestamp for filename
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    char timestamp_str[32];
    strftime(timestamp_str, sizeof(timestamp_str), "%Y%m%d_%H%M%S", tm_info);
    
    // Create results directory if it doesn't exist (with interval subfolder)
    char results_dir[256];
    snprintf(results_dir, sizeof(results_dir), "strategies/%s/results/%s", strategy, interval);
    char mkdir_cmd[512];
    snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir -p %s", results_dir);
    system(mkdir_cmd);
    
    // Create JSON filename
    char json_filename[512];
    snprintf(json_filename, sizeof(json_filename), "%s/%s_%s_%s.json", 
             results_dir, timestamp_str, ticker, interval);
    
    FILE* json_file = fopen(json_filename, "w");
    if (!json_file) {
        fprintf(stderr, "⚠️  Warning: Could not create JSON file: %s\n", json_filename);
        return;
    }
    
    // Write JSON
    fprintf(json_file, "{\n");
    fprintf(json_file, "  \"ticker\": \"%s\",\n", ticker);
    fprintf(json_file, "  \"interval\": \"%s\",\n", interval);
    fprintf(json_file, "  \"strategy\": \"%s\",\n", strategy);
    fprintf(json_file, "  \"timestamp\": \"%s\",\n", timestamp_str);
    fprintf(json_file, "  \"candles\": %d,\n", num_candles);
    
    // Performance metrics
    fprintf(json_file, "  \"performance\": {\n");
    fprintf(json_file, "    \"total_return\": %.2f,\n", best_results[0]);
    fprintf(json_file, "    \"max_drawdown\": %.2f,\n", best_results[1]);
    fprintf(json_file, "    \"calmar_ratio\": %.2f,\n", best_results[2]);
    fprintf(json_file, "    \"total_trades\": %d,\n", (int)best_results[3]);
    fprintf(json_file, "    \"buy_hold_return\": %.2f,\n", buy_hold_return);
    fprintf(json_file, "    \"outperformance\": %.2f\n", best_results[0] - buy_hold_return);
    fprintf(json_file, "  },\n");
    
    // Best parameters
    fprintf(json_file, "  \"parameters\": {\n");
    fprintf(json_file, "    \"fast_low\": %.0f,\n", best_params[0]);
    fprintf(json_file, "    \"slow_low\": %.0f,\n", best_params[1]);
    fprintf(json_file, "    \"fast_med\": %.0f,\n", best_params[2]);
    fprintf(json_file, "    \"slow_med\": %.0f,\n", best_params[3]);
    fprintf(json_file, "    \"fast_high\": %.0f,\n", best_params[4]);
    fprintf(json_file, "    \"slow_high\": %.0f,\n", best_params[5]);
    fprintf(json_file, "    \"atr_length\": %.0f,\n", best_params[6]);
    fprintf(json_file, "    \"volatility_length\": %.0f,\n", best_params[7]);
    fprintf(json_file, "    \"low_vol_percentile\": %.0f,\n", best_params[8]);
    fprintf(json_file, "    \"high_vol_percentile\": %.0f\n", best_params[9]);
    fprintf(json_file, "  },\n");
    
    // Trade log
    fprintf(json_file, "  \"trades\": [\n");
    int trade_count = 0;
    float entry_price = 0.0f;
    
    for (int i = 0; i < 100; i++) {
        int candle_idx = (int)trade_log[i * 3 + 0];
        float price = trade_log[i * 3 + 1];
        int is_buy = (int)trade_log[i * 3 + 2];
        
        if (candle_idx == 0 && price == 0.0f) break;
        
        time_t ts = timestamps[candle_idx];
        struct tm *tm_info_trade = localtime(&ts);
        char date_str[64];
        strftime(date_str, sizeof(date_str), "%Y-%m-%d %H:%M:%S", tm_info_trade);
        
        if (trade_count > 0) fprintf(json_file, ",\n");
        
        fprintf(json_file, "    {\n");
        fprintf(json_file, "      \"trade_number\": %d,\n", ++trade_count);
        fprintf(json_file, "      \"action\": \"%s\",\n", is_buy ? "BUY" : "SELL");
        fprintf(json_file, "      \"price\": %.2f,\n", price);
        fprintf(json_file, "      \"date\": \"%s\",\n", date_str);
        fprintf(json_file, "      \"candle_index\": %d", candle_idx);
        
        if (!is_buy && entry_price > 0) {
            float pnl = ((price - entry_price) / entry_price) * 100.0f;
            fprintf(json_file, ",\n      \"pnl_percent\": %.2f", pnl);
        }
        
        fprintf(json_file, "\n    }");
        
        if (is_buy) {
            entry_price = price;
        }
    }
    
    fprintf(json_file, "\n  ]\n");
    fprintf(json_file, "}\n");
    fclose(json_file);
    
    printf("\n💾 Results saved to: %s\n", json_filename);
    
    // Generate HTML report
    generate_html_report(json_filename, ticker, interval, strategy, results_dir, timestamp_str);
}

// Generate HTML report with chart
void generate_html_report(const char* json_filename, const char* ticker, 
                         const char* interval, const char* strategy,
                         const char* results_dir, const char* timestamp_str) {
    
    char html_filename[512];
    snprintf(html_filename, sizeof(html_filename), "%s/%s_%s_%s.html", 
             results_dir, timestamp_str, ticker, interval);
    
    FILE* html_file = fopen(html_filename, "w");
    if (!html_file) {
        fprintf(stderr, "⚠️  Warning: Could not create HTML file: %s\n", html_filename);
        return;
    }
    
    // Read JSON file content to embed it
    FILE* json_file = fopen(json_filename, "r");
    if (!json_file) {
        fprintf(stderr, "⚠️  Warning: Could not read JSON file for embedding: %s\n", json_filename);
        fclose(html_file);
        return;
    }
    
    fseek(json_file, 0, SEEK_END);
    long json_size = ftell(json_file);
    fseek(json_file, 0, SEEK_SET);
    
    char* json_content = malloc(json_size + 1);
    if (!json_content) {
        fprintf(stderr, "⚠️  Warning: Could not allocate memory for JSON content\n");
        fclose(json_file);
        fclose(html_file);
        return;
    }
    
    fread(json_content, 1, json_size, json_file);
    json_content[json_size] = '\0';
    fclose(json_file);
    
    // Determine CSV path (relative to HTML location)
    char ticker_lower[32];
    strcpy(ticker_lower, ticker);
    for (int i = 0; ticker_lower[i]; i++) {
        ticker_lower[i] = tolower(ticker_lower[i]);
    }
    
    char csv_path[512];
    snprintf(csv_path, sizeof(csv_path), "../../../data/%s_%s.csv", ticker_lower, interval);
    
    fprintf(html_file, "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n");
    fprintf(html_file, "  <meta charset=\"UTF-8\">\n");
    fprintf(html_file, "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n");
    fprintf(html_file, "  <title>%s %s - %s Results</title>\n", ticker, interval, strategy);
    fprintf(html_file, "  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>\n");
    fprintf(html_file, "  <style>\n");
    fprintf(html_file, "    * { margin: 0; padding: 0; box-sizing: border-box; }\n");
    fprintf(html_file, "    body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0e17; color: #e4e4e7; padding: 20px; }\n");
    fprintf(html_file, "    .container { max-width: 1400px; margin: 0 auto; }\n");
    fprintf(html_file, "    h1 { font-size: 2.5rem; margin-bottom: 10px; color: #60a5fa; }\n");
    fprintf(html_file, "    h2 { font-size: 1.5rem; margin: 30px 0 15px; color: #a78bfa; border-bottom: 2px solid #374151; padding-bottom: 10px; }\n");
    fprintf(html_file, "    .meta { color: #9ca3af; margin-bottom: 30px; font-size: 0.95rem; }\n");
    fprintf(html_file, "    .meta span { margin-right: 20px; }\n");
    fprintf(html_file, "    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }\n");
    fprintf(html_file, "    .metric-card { background: #1e293b; padding: 20px; border-radius: 8px; border-left: 4px solid #60a5fa; }\n");
    fprintf(html_file, "    .metric-label { font-size: 0.85rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.5px; }\n");
    fprintf(html_file, "    .metric-value { font-size: 1.8rem; font-weight: 700; margin-top: 8px; }\n");
    fprintf(html_file, "    .positive { color: #34d399; }\n");
    fprintf(html_file, "    .negative { color: #f87171; }\n");
    fprintf(html_file, "    .neutral { color: #60a5fa; }\n");
    fprintf(html_file, "    .chart-container { background: #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 30px; }\n");
    fprintf(html_file, "    .params { background: #1e293b; padding: 20px; border-radius: 8px; margin-bottom: 30px; }\n");
    fprintf(html_file, "    .param-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }\n");
    fprintf(html_file, "    .param-item { padding: 10px; background: #0f172a; border-radius: 4px; }\n");
    fprintf(html_file, "    .param-name { font-size: 0.8rem; color: #9ca3af; }\n");
    fprintf(html_file, "    .param-value { font-size: 1.1rem; font-weight: 600; color: #e4e4e7; margin-top: 4px; }\n");
    fprintf(html_file, "    .trades-table { width: 100%%; background: #1e293b; border-radius: 8px; overflow: hidden; }\n");
    fprintf(html_file, "    table { width: 100%%; border-collapse: collapse; }\n");
    fprintf(html_file, "    th { background: #0f172a; padding: 12px; text-align: left; font-weight: 600; color: #a78bfa; font-size: 0.85rem; text-transform: uppercase; }\n");
    fprintf(html_file, "    td { padding: 12px; border-top: 1px solid #374151; }\n");
    fprintf(html_file, "    tr:hover { background: #0f172a; }\n");
    fprintf(html_file, "    .buy { color: #34d399; font-weight: 600; }\n");
    fprintf(html_file, "    .sell { color: #f87171; font-weight: 600; }\n");
    fprintf(html_file, "  </style>\n</head>\n<body>\n");
    fprintf(html_file, "  <div class=\"container\">\n");
    fprintf(html_file, "    <h1>%s %s Strategy Results</h1>\n", ticker, interval);
    fprintf(html_file, "    <div class=\"meta\">\n");
    fprintf(html_file, "      <span><strong>Strategy:</strong> %s</span>\n", strategy);
    fprintf(html_file, "      <span><strong>Generated:</strong> %s</span>\n", timestamp_str);
    fprintf(html_file, "      <span><strong>Data:</strong> <a href=\"%s\" style=\"color: #60a5fa;\">%s</a></span>\n", csv_path, csv_path);
    fprintf(html_file, "    </div>\n\n");
    
    fprintf(html_file, "    <h2>Performance Metrics</h2>\n");
    fprintf(html_file, "    <div id=\"metrics\" class=\"metrics\"></div>\n\n");
    
    fprintf(html_file, "    <h2>Price Chart with Trades</h2>\n");
    fprintf(html_file, "    <div class=\"chart-container\">\n");
    fprintf(html_file, "      <canvas id=\"priceChart\"></canvas>\n");
    fprintf(html_file, "    </div>\n\n");
    
    fprintf(html_file, "    <h2>Optimized Parameters</h2>\n");
    fprintf(html_file, "    <div id=\"parameters\" class=\"params\"></div>\n\n");
    
    fprintf(html_file, "    <h2>Trade Log</h2>\n");
    fprintf(html_file, "    <div class=\"trades-table\">\n");
    fprintf(html_file, "      <table id=\"tradesTable\"></table>\n");
    fprintf(html_file, "    </div>\n  </div>\n\n");
    
    // JavaScript to load and display data - with embedded JSON to avoid CORS issues
    fprintf(html_file, "  <script>\n");
    fprintf(html_file, "    const embeddedData = %s;\n", json_content);
    fprintf(html_file, "    \n");
    fprintf(html_file, "    async function loadResults() {\n");
    fprintf(html_file, "      const data = embeddedData;\n\n");
    
    fprintf(html_file, "      const metricsDiv = document.getElementById('metrics');\n");
    fprintf(html_file, "      const metrics = [\n");
    fprintf(html_file, "        { label: 'Total Return', value: data.performance.total_return, suffix: '%%', colorClass: data.performance.total_return > 0 ? 'positive' : 'negative' },\n");
    fprintf(html_file, "        { label: 'Max Drawdown', value: data.performance.max_drawdown, suffix: '%%', colorClass: 'negative' },\n");
    fprintf(html_file, "        { label: 'Calmar Ratio', value: data.performance.calmar_ratio, suffix: '', colorClass: 'neutral' },\n");
    fprintf(html_file, "        { label: 'Total Trades', value: data.performance.total_trades, suffix: '', colorClass: 'neutral' },\n");
    fprintf(html_file, "        { label: 'Buy & Hold', value: data.performance.buy_hold_return, suffix: '%%', colorClass: data.performance.buy_hold_return > 0 ? 'positive' : 'negative' },\n");
    fprintf(html_file, "        { label: 'Outperformance', value: data.performance.outperformance, suffix: '%%', colorClass: data.performance.outperformance > 0 ? 'positive' : 'negative' }\n");
    fprintf(html_file, "      ];\n");
    fprintf(html_file, "      metricsDiv.innerHTML = metrics.map(m => `<div class=\"metric-card\"><div class=\"metric-label\">${m.label}</div><div class=\"metric-value ${m.colorClass}\">${m.value.toFixed(2)}${m.suffix}</div></div>`).join('');\n\n");
    
    fprintf(html_file, "      const paramsDiv = document.getElementById('parameters');\n");
    fprintf(html_file, "      const params = Object.entries(data.parameters).map(([key, value]) => `<div class=\"param-item\"><div class=\"param-name\">${key.replace(/_/g, ' ')}</div><div class=\"param-value\">${value}</div></div>`).join('');\n");
    fprintf(html_file, "      paramsDiv.innerHTML = `<div class=\"param-grid\">${params}</div>`;\n\n");
    
    fprintf(html_file, "      const tradesTable = document.getElementById('tradesTable');\n");
    fprintf(html_file, "      const tradesHTML = `<thead><tr><th>#</th><th>Action</th><th>Price</th><th>Date</th><th>P&L</th></tr></thead><tbody>${data.trades.map(t => `<tr><td>${t.trade_number}</td><td class=\"${t.action.toLowerCase()}\">${t.action}</td><td>$${t.price.toFixed(2)}</td><td>${t.date}</td><td class=\"${t.pnl_percent ? (t.pnl_percent > 0 ? 'positive' : 'negative') : ''}\">${t.pnl_percent ? (t.pnl_percent > 0 ? '+' : '') + t.pnl_percent.toFixed(2) + '%%' : '-'}</td></tr>`).join('')}</tbody>`;\n");
    fprintf(html_file, "      tradesTable.innerHTML = tradesHTML;\n\n");
    
    fprintf(html_file, "      // Generate trade markers for the chart\n");
    fprintf(html_file, "      const tradeMarkers = data.trades.map(t => ({\n");
    fprintf(html_file, "        date: t.date.split(' ')[0],\n");
    fprintf(html_file, "        price: t.price,\n");
    fprintf(html_file, "        action: t.action\n");
    fprintf(html_file, "      }));\n\n");
    
    fprintf(html_file, "      // Create price chart using trade data\n");
    fprintf(html_file, "      const ctx = document.getElementById('priceChart').getContext('2d');\n");
    fprintf(html_file, "      \n");
    fprintf(html_file, "      new Chart(ctx, {\n");
    fprintf(html_file, "        type: 'line',\n");
    fprintf(html_file, "        data: { \n");
    fprintf(html_file, "          labels: tradeMarkers.map(t => t.date), \n");
    fprintf(html_file, "          datasets: [\n");
    fprintf(html_file, "            { \n");
    fprintf(html_file, "              label: 'Trade Prices', \n");
    fprintf(html_file, "              data: tradeMarkers.map(t => t.price), \n");
    fprintf(html_file, "              borderColor: '#60a5fa', \n");
    fprintf(html_file, "              backgroundColor: 'rgba(96, 165, 250, 0.1)', \n");
    fprintf(html_file, "              borderWidth: 2, \n");
    fprintf(html_file, "              pointRadius: 4,\n");
    fprintf(html_file, "              pointBackgroundColor: tradeMarkers.map(t => t.action === 'BUY' ? '#34d399' : '#f87171'),\n");
    fprintf(html_file, "              pointBorderColor: tradeMarkers.map(t => t.action === 'BUY' ? '#34d399' : '#f87171'),\n");
    fprintf(html_file, "              tension: 0.1 \n");
    fprintf(html_file, "            }\n");
    fprintf(html_file, "          ] \n");
    fprintf(html_file, "        },\n");
    fprintf(html_file, "        options: { \n");
    fprintf(html_file, "          responsive: true, \n");
    fprintf(html_file, "          maintainAspectRatio: true, \n");
    fprintf(html_file, "          aspectRatio: 2.5, \n");
    fprintf(html_file, "          plugins: { \n");
    fprintf(html_file, "            legend: { labels: { color: '#e4e4e7' } }, \n");
    fprintf(html_file, "            tooltip: { \n");
    fprintf(html_file, "              mode: 'index', \n");
    fprintf(html_file, "              intersect: false,\n");
    fprintf(html_file, "              callbacks: {\n");
    fprintf(html_file, "                label: function(context) {\n");
    fprintf(html_file, "                  const trade = tradeMarkers[context.dataIndex];\n");
    fprintf(html_file, "                  return `${trade.action}: $${trade.price.toFixed(2)}`;\n");
    fprintf(html_file, "                }\n");
    fprintf(html_file, "              }\n");
    fprintf(html_file, "            } \n");
    fprintf(html_file, "          }, \n");
    fprintf(html_file, "          scales: { \n");
    fprintf(html_file, "            x: { \n");
    fprintf(html_file, "              ticks: { color: '#9ca3af', maxTicksLimit: 12 }, \n");
    fprintf(html_file, "              grid: { color: '#374151' } \n");
    fprintf(html_file, "            }, \n");
    fprintf(html_file, "            y: { \n");
    fprintf(html_file, "              ticks: { color: '#9ca3af' }, \n");
    fprintf(html_file, "              grid: { color: '#374151' } \n");
    fprintf(html_file, "            } \n");
    fprintf(html_file, "          } \n");
    fprintf(html_file, "        }\n");
    fprintf(html_file, "      });\n");
    fprintf(html_file, "    }\n    loadResults();\n");
    fprintf(html_file, "  </script>\n</body>\n</html>\n");
    
    free(json_content);
    fclose(html_file);
    printf("📊 HTML report saved to: %s\n", html_filename);
}

// Load CSV data (you'll need to fetch this via Python first)
int load_csv(const char* filename, float** closes, float** highs, float** lows, long long** timestamps) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        fprintf(stderr, "❌ Error: Could not open %s\n", filename);
        fprintf(stderr, "   Run: python3 ../c/fetch_data.py %s\n", filename);
        return -1;
    }
    
    // Count lines
    int count = 0;
    char line[1024];
    fgets(line, sizeof(line), file); // Skip header
    
    while (fgets(line, sizeof(line), file)) {
        count++;
    }
    
    rewind(file);
    fgets(line, sizeof(line), file); // Skip header again
    
    *closes = malloc(count * sizeof(float));
    *highs = malloc(count * sizeof(float));
    *lows = malloc(count * sizeof(float));
    *timestamps = malloc(count * sizeof(long long));
    
    int i = 0;
    while (fgets(line, sizeof(line), file) && i < count) {
        long long timestamp;
        float open, high, low, close, volume;
        sscanf(line, "%lld,%f,%f,%f,%f,%f", &timestamp, &open, &high, &low, &close, &volume);
        
        // Round to 4 decimal places for better GPU performance
        // Stock prices rarely need more precision than $0.0001
        (*closes)[i] = roundf(close * 10000.0f) / 10000.0f;
        (*highs)[i] = roundf(high * 10000.0f) / 10000.0f;
        (*lows)[i] = roundf(low * 10000.0f) / 10000.0f;
        (*timestamps)[i] = timestamp;
        i++;
    }
    
    fclose(file);
    return count;
}

// Load OpenCL kernel from file
char* load_kernel_source(const char* strategy_dir) {
    char kernel_path[512];
    snprintf(kernel_path, sizeof(kernel_path), "kernel.cl");
    
    FILE* file = fopen(kernel_path, "r");
    if (!file) {
        fprintf(stderr, "❌ Error: Could not open kernel file: %s\n", kernel_path);
        fprintf(stderr, "   Make sure kernel.cl exists in the strategy directory\n");
        exit(1);
    }
    
    // Get file size
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);
    
    // Allocate and read
    char* source = (char*)malloc(file_size + 1);
    if (!source) {
        fprintf(stderr, "❌ Error: Could not allocate memory for kernel source\n");
        fclose(file);
        exit(1);
    }
    
    size_t read_size = fread(source, 1, file_size, file);
    source[read_size] = '\0';
    
    fclose(file);
    
    printf("✅ Loaded kernel from: %s (%ld bytes)\n", kernel_path, file_size);
    return source;
}

void check_error(cl_int err, const char* operation) {
    if (err != CL_SUCCESS) {
        fprintf(stderr, "Error during %s: %d\n", operation, err);
        exit(1);
    }
}

int main(int argc, char** argv) {
    if (argc < 3 || argc > 4) {
        printf("Usage: %s <TICKER> <INTERVAL> [nosave]\n", argv[0]);
        printf("Example: %s GOOG 1h\n", argv[0]);
        printf("Example: %s GOOG 1h nosave    # Skip saving JSON/HTML\n", argv[0]);
        printf("\nIntervals: 1h, 4h, 1d\n");
        printf("\nCurrent strategy: %s\n", STRATEGY_NAME);
        printf("To change strategy, recompile with: make STRATEGY=adaptive_ema_v2\n");
        return 1;
    }
    
    char* ticker = argv[1];
    char* interval = argv[2];
    int save_results = 1;  // Default: save results
    
    // Check for nosave flag
    if (argc == 4 && strcmp(argv[3], "nosave") == 0) {
        save_results = 0;
        printf("\n⚠️  Running in NO-SAVE mode (results will not be saved)\n");
    }
    
    // Convert to uppercase
    for (char* p = ticker; *p; p++) *p = toupper(*p);
    for (char* p = interval; *p; p++) *p = tolower(*p);
    
    printf("\n");
    printf("🎮 OpenCL GPU Parameter Optimization System\n");
    printf("   Ticker: %s\n", ticker);
    printf("   Interval: %s\n", interval);
    printf("   Strategy: %s\n", STRATEGY_NAME);
    printf("   Tech: Apple Silicon / AMD Radeon + OpenCL\n");
    printf("   Expected speedup: 100-500x faster than CPU\n\n");
    
    // Load OpenCL kernel from strategy directory
    printf("📦 Loading strategy kernel...\n");
    char* kernel_source = load_kernel_source(STRATEGY_NAME);
    printf("\n");
    
    // Load configuration
    Config config;
    load_config(interval, &config);
    
    // Load data from CSV
    char filename[256];
    char ticker_lower[64];
    strcpy(ticker_lower, ticker);
    for (char* p = ticker_lower; *p; p++) *p = tolower(*p);
    
    snprintf(filename, sizeof(filename), "data/%s_%s.csv", ticker_lower, interval);
    
    printf("📂 Loading data from %s...\n", filename);
    
    float *closes, *highs, *lows;
    long long *timestamps;
    int num_candles = load_csv(filename, &closes, &highs, &lows, &timestamps);
    
    if (num_candles < 0) {
        printf("\n💡 To fetch data, run:\n");
        printf("   cd ../c && python3 fetch_data.py %s %s 600\n\n", ticker, interval);
        return 1;
    }
    
    printf("   ✅ Loaded %d candles\n\n", num_candles);
    
    printf("============================================================\n");
    printf("🔧 Optimizing %s - SMART Search\n", ticker);
    printf("   Candles: %d | Auto-detecting GPU...\n", num_candles);
    printf("============================================================\n\n");
    
    // Generate parameter combinations
    printf("⚡ Generating parameter combinations...\n");
    
    int num_combinations = 0;
    for (int fl = config.fast_length_low_min; fl <= config.fast_length_low_max; fl++) {
        for (int sl = config.slow_length_low_min; sl <= config.slow_length_low_max; sl++) {
            if (fl >= sl) continue;
            for (int fm = config.fast_length_med_min; fm <= config.fast_length_med_max; fm++) {
                for (int sm = config.slow_length_med_min; sm <= config.slow_length_med_max; sm++) {
                    if (fm >= sm) continue;
                    for (int fh = config.fast_length_high_min; fh <= config.fast_length_high_max; fh++) {
                        for (int sh = config.slow_length_high_min; sh <= config.slow_length_high_max; sh++) {
                            if (fh >= sh) continue;
                            for (int atr = config.atr_length_min; atr <= config.atr_length_max; atr++) {
                                for (int vol = config.volatility_length_min; vol <= config.volatility_length_max; vol++) {
                                    for (int lp = config.low_vol_percentile_min; lp <= config.low_vol_percentile_max; lp++) {
                                        for (int hp = config.high_vol_percentile_min; hp <= config.high_vol_percentile_max; hp++) {
                                            if (lp >= hp) continue;
                                            num_combinations++;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    printf("   Total combinations: %d\n\n", num_combinations);
    
    // Initialize OpenCL
    cl_int err;
    cl_platform_id platform;
    clGetPlatformIDs(1, &platform, NULL);
    
    // Get all GPU devices and select the best one
    cl_uint num_devices;
    clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, 0, NULL, &num_devices);
    cl_device_id* devices = malloc(num_devices * sizeof(cl_device_id));
    clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, num_devices, devices, NULL);
    
    // Smart device selection: Prefer Apple Silicon > Discrete GPU > Integrated GPU
    cl_device_id device = devices[0];
    char selected_device_name[128] = "";
    int device_priority = 0; // 0=integrated, 1=discrete, 2=Apple Silicon
    
    for (int i = 0; i < num_devices; i++) {
        char name[128];
        clGetDeviceInfo(devices[i], CL_DEVICE_NAME, sizeof(name), name, NULL);
        
        int priority = 0;
        if (strstr(name, "Apple M") || strstr(name, "Apple")) {
            priority = 2; // Apple Silicon (M1/M2/M3) - best performance
        } else if (strstr(name, "Radeon")) {
            priority = 1; // Discrete AMD GPU
        } else {
            priority = 0; // Integrated GPU (Intel UHD, etc)
        }
        
        if (priority > device_priority) {
            device = devices[i];
            device_priority = priority;
            strncpy(selected_device_name, name, sizeof(selected_device_name) - 1);
        }
    }
    free(devices);
    
    cl_context context = clCreateContext(NULL, 1, &device, NULL, NULL, &err);
    cl_command_queue queue = clCreateCommandQueue(context, device, 0, &err);
    
    // Get device info for optimization
    cl_ulong max_mem_alloc, global_mem;
    size_t max_work_group_size;
    cl_uint compute_units;
    clGetDeviceInfo(device, CL_DEVICE_MAX_MEM_ALLOC_SIZE, sizeof(cl_ulong), &max_mem_alloc, NULL);
    clGetDeviceInfo(device, CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(cl_ulong), &global_mem, NULL);
    clGetDeviceInfo(device, CL_DEVICE_MAX_WORK_GROUP_SIZE, sizeof(size_t), &max_work_group_size, NULL);
    clGetDeviceInfo(device, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(cl_uint), &compute_units, NULL);
    
    const char* kernel_source_const = (const char*)kernel_source;
    cl_program program = clCreateProgramWithSource(context, 1, &kernel_source_const, NULL, &err);
    clBuildProgram(program, 1, &device, "-cl-fast-relaxed-math", NULL, NULL);
    cl_kernel kernel = clCreateKernel(program, "optimize_strategy", &err);
    
    // Allocate and populate parameter array
    float* h_params = malloc(num_combinations * 10 * sizeof(float));
    int idx = 0;
    
    for (int fl = config.fast_length_low_min; fl <= config.fast_length_low_max; fl++) {
        for (int sl = config.slow_length_low_min; sl <= config.slow_length_low_max; sl++) {
            if (fl >= sl) continue;
            for (int fm = config.fast_length_med_min; fm <= config.fast_length_med_max; fm++) {
                for (int sm = config.slow_length_med_min; sm <= config.slow_length_med_max; sm++) {
                    if (fm >= sm) continue;
                    for (int fh = config.fast_length_high_min; fh <= config.fast_length_high_max; fh++) {
                        for (int sh = config.slow_length_high_min; sh <= config.slow_length_high_max; sh++) {
                            if (fh >= sh) continue;
                            for (int atr = config.atr_length_min; atr <= config.atr_length_max; atr++) {
                                for (int vol = config.volatility_length_min; vol <= config.volatility_length_max; vol++) {
                                    for (int lp = config.low_vol_percentile_min; lp <= config.low_vol_percentile_max; lp++) {
                                        for (int hp = config.high_vol_percentile_min; hp <= config.high_vol_percentile_max; hp++) {
                                            if (lp >= hp) continue;
                                            h_params[idx * 10 + 0] = fl;
                                            h_params[idx * 10 + 1] = sl;
                                            h_params[idx * 10 + 2] = fm;
                                            h_params[idx * 10 + 3] = sm;
                                            h_params[idx * 10 + 4] = fh;
                                            h_params[idx * 10 + 5] = sh;
                                            h_params[idx * 10 + 6] = atr;
                                            h_params[idx * 10 + 7] = vol;
                                            h_params[idx * 10 + 8] = lp;
                                            h_params[idx * 10 + 9] = hp;
                                            idx++;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    float* h_results = malloc(num_combinations * 5 * sizeof(float));
    float* h_trade_log = calloc(300, sizeof(float)); // Max 100 trades * 3 floats
    
    // Create GPU buffers
    cl_mem d_closes = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR, 
                                     num_candles * sizeof(float), closes, &err);
    cl_mem d_highs = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                    num_candles * sizeof(float), highs, &err);
    cl_mem d_lows = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                   num_candles * sizeof(float), lows, &err);
    cl_mem d_params = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                     num_combinations * 10 * sizeof(float), h_params, &err);
    cl_mem d_results = clCreateBuffer(context, CL_MEM_WRITE_ONLY,
                                      num_combinations * 5 * sizeof(float), NULL, &err);
    cl_mem d_trade_log = clCreateBuffer(context, CL_MEM_WRITE_ONLY,
                                        300 * sizeof(float), NULL, &err);
    
    // Set kernel arguments
    clSetKernelArg(kernel, 0, sizeof(cl_mem), &d_closes);
    clSetKernelArg(kernel, 1, sizeof(cl_mem), &d_highs);
    clSetKernelArg(kernel, 2, sizeof(cl_mem), &d_lows);
    clSetKernelArg(kernel, 3, sizeof(int), &num_candles);
    clSetKernelArg(kernel, 4, sizeof(cl_mem), &d_params);
    clSetKernelArg(kernel, 5, sizeof(cl_mem), &d_results);
    clSetKernelArg(kernel, 6, sizeof(int), &num_combinations);
    clSetKernelArg(kernel, 7, sizeof(cl_mem), &d_trade_log);
    
    // Execute kernel
    printf("   Compute Units: %d | Max Work Group: %zu\n", compute_units, max_work_group_size);
    printf("   GPU Memory: %.2f GB\n\n", global_mem / (1024.0 * 1024.0 * 1024.0));
    
    // Optimize work group size based on device type
    size_t local_work_size;
    if (device_priority == 2) {
        // Apple Silicon - optimal for M1/M2/M3
        local_work_size = (max_work_group_size >= 1024) ? 1024 : max_work_group_size;
    } else if (device_priority == 1) {
        // Discrete GPU (Radeon) - optimal for AMD
        local_work_size = 256;
    } else {
        // Integrated GPU - conservative
        local_work_size = 128;
    }
    
    size_t global_work_size = num_combinations;
    if (global_work_size % local_work_size != 0) {
        global_work_size = ((global_work_size / local_work_size) + 1) * local_work_size;
    }
    
    struct timeval start, end;
    gettimeofday(&start, NULL);
    
    clEnqueueNDRangeKernel(queue, kernel, 1, NULL, &global_work_size, &local_work_size, 0, NULL, NULL);
    clFinish(queue);
    
    gettimeofday(&end, NULL);
    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_usec - start.tv_usec) / 1e6;
    
    // Read results
    clEnqueueReadBuffer(queue, d_results, CL_TRUE, 0, 
                        num_combinations * 5 * sizeof(float), h_results, 0, NULL, NULL);
    clEnqueueReadBuffer(queue, d_trade_log, CL_TRUE, 0,
                        300 * sizeof(float), h_trade_log, 0, NULL, NULL);
    
    // Find best result
    float best_score = -INFINITY;
    int best_idx = -1;
    int valid_count = 0;
    
    for (int i = 0; i < num_combinations; i++) {
        if (h_results[i * 5 + 4] > 0.5f) {
            valid_count++;
            if (h_results[i * 5 + 3] > best_score) {
                best_score = h_results[i * 5 + 3];
                best_idx = i;
            }
        }
    }
    
    double tests_per_sec = num_combinations / elapsed;
    
    printf("\n✅ Optimization Complete\n");
    printf("   Tested: %d combinations\n", num_combinations);
    printf("   Valid: %d results\n", valid_count);
    printf("   Filtered: %d (early termination)\n", num_combinations - valid_count);
    printf("   Time: %.1fs (%.0f tests/sec)\n", elapsed, tests_per_sec);
    printf("   Avg time per test: %.3fms\n\n", (elapsed / num_combinations) * 1000.0);
    
    if (best_idx >= 0) {
        printf("🏆 BEST PARAMETERS FOR %s\n\n", ticker);
        printf("📊 Performance Metrics:\n");
        printf("   Total Return: %.2f%%\n", h_results[best_idx * 5 + 0]);
        printf("   Max Drawdown: %.2f%%\n", h_results[best_idx * 5 + 1]);
        printf("   Calmar Ratio: %.2f\n", h_results[best_idx * 5 + 0] / h_results[best_idx * 5 + 1]);
        printf("   Total Trades: %.0f\n", h_results[best_idx * 5 + 2]);
        printf("   Score: %.2f\n\n", h_results[best_idx * 5 + 3]);
        
        printf("⚙️  Optimal Parameters:\n");
        printf("   Low Vol:  Fast=%.0f, Slow=%.0f\n", 
               h_params[best_idx * 10 + 0], h_params[best_idx * 10 + 1]);
        printf("   Med Vol:  Fast=%.0f, Slow=%.0f\n",
               h_params[best_idx * 10 + 2], h_params[best_idx * 10 + 3]);
        printf("   High Vol: Fast=%.0f, Slow=%.0f\n",
               h_params[best_idx * 10 + 4], h_params[best_idx * 10 + 5]);
        printf("   ATR Length: %.0f\n", h_params[best_idx * 10 + 6]);
        printf("   Volatility Lookback: %.0f\n", h_params[best_idx * 10 + 7]);
        printf("   Percentiles: Low=%.0f%%, High=%.0f%%\n",
               h_params[best_idx * 10 + 8], h_params[best_idx * 10 + 9]);
    }
    
    // Calculate Buy & Hold
    float buy_hold_return = ((closes[num_candles - 1] - closes[0]) / closes[0]) * 100.0f;
    float strategy_outperformance = h_results[best_idx * 5 + 0] - buy_hold_return;
    
    printf("\n============================================================\n");
    printf("📈 PERFORMANCE COMPARISON\n");
    printf("============================================================\n");
    printf("   Buy & Hold Return: %.2f%%\n", buy_hold_return);
    printf("   Strategy Outperformance: %.2f%%\n", strategy_outperformance);
    
    // Display trades from best parameter set
    printf("\n============================================================\n");
    printf("📋 TRADE LOG (Best Parameters)\n");
    printf("============================================================\n");
    int trade_count = 0;
    int entry_idx = -1;
    float entry_price = 0.0f;
    
    for (int i = 0; i < 100; i++) {
        int candle_idx = (int)h_trade_log[i * 3 + 0];
        float price = h_trade_log[i * 3 + 1];
        int is_buy = (int)h_trade_log[i * 3 + 2];
        
        if (candle_idx == 0 && price == 0.0f) break; // End of trades
        
        // Convert timestamp to readable date/time
        time_t ts = (time_t)timestamps[candle_idx];
        struct tm *tm_info = localtime(&ts);
        char date_str[64];
        strftime(date_str, sizeof(date_str), "%Y-%m-%d %H:%M", tm_info);
        
        if (is_buy) {
            printf("   #%d  BUY  @ $%.2f on %s\n", ++trade_count, price, date_str);
            entry_idx = candle_idx;
            entry_price = price;
        } else {
            float pnl = ((price - entry_price) / entry_price) * 100.0f;
            printf("   #%d  SELL @ $%.2f on %s | P&L: %s%.2f%%\n", 
                   ++trade_count, price, date_str,
                   pnl >= 0 ? "+" : "", pnl);
        }
    }
    printf("   Total trades: %d\n", trade_count);
    
    // === EXPORT RESULTS TO JSON AND HTML ===
    if (save_results) {
        export_results_to_json(ticker, interval, STRATEGY_NAME, 
                              h_params + (best_idx * 10), 
                              h_results + (best_idx * 5),
                              h_trade_log, timestamps, closes, num_candles,
                              buy_hold_return);
    } else {
        printf("\n⏭️  Skipping results export (nosave mode)\n");
    }
    
    printf("\n============================================================\n");
    printf("📊 OPTIMIZATION COMPLETE\n");
    printf("============================================================\n\n");
    
    // Cleanup
    clReleaseMemObject(d_closes);
    clReleaseMemObject(d_highs);
    clReleaseMemObject(d_lows);
    clReleaseMemObject(d_params);
    clReleaseMemObject(d_results);
    clReleaseMemObject(d_trade_log);
    clReleaseKernel(kernel);
    clReleaseProgram(program);
    clReleaseCommandQueue(queue);
    clReleaseContext(context);
    
    free(closes);
    free(highs);
    free(lows);
    free(timestamps);
    free(h_params);
    free(h_results);
    free(h_trade_log);
    
    return 0;
}
