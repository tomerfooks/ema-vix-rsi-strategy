/*
 * OpenCL GPU-accelerated Adaptive EMA Strategy v2.1 Optimizer
 * Usage: ./optimize <TICKER> <INTERVAL>
 * Example: ./optimize GOOG 1h
 * 
 * Compilation:
 *   make STRATEGY=adaptive_ema_v2.1
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

#define STRATEGY_NAME "adaptive_ema_v2.1"
#define MAX_COMBINATIONS 15000000

// Include strategy config files
#include "config_1h.h"
#include "config_4h.h"
#include "config_1d.h"

typedef struct {
    int fast_base_min, fast_base_max;
    int slow_base_min, slow_base_max;
    float fast_mult_min, fast_mult_max;
    float slow_mult_min, slow_mult_max;
    int atr_length_min, atr_length_max;
    int vol_threshold_min, vol_threshold_max;
    int adx_length_min, adx_length_max;
    float adx_threshold_min, adx_threshold_max;
} Config;

// Forward declarations
void export_results_to_json(const char* ticker, const char* interval, const char* strategy,
                            float* best_params, float* best_results, float* trade_log,
                            long long* timestamps, float* closes, int num_candles,
                            float buy_hold_return);
void generate_html_report(const char* json_filename, const char* ticker, 
                         const char* interval, const char* strategy,
                         const char* results_dir, const char* timestamp_str);

// Load configuration based on interval
void load_config(const char* interval, Config* config) {
    if (strcmp(interval, "1h") == 0) {
        #ifdef USE_PERCENT_RANGE_1H
            int def_fast_base = FAST_BASE_1H;
            int def_slow_base = SLOW_BASE_1H;
            float def_fast_mult = FAST_MULT_1H;
            float def_slow_mult = SLOW_MULT_1H;
            int def_atr = ATR_LENGTH_1H;
            int def_vol_thresh = VOL_THRESHOLD_1H;
            int def_adx_length = ADX_LENGTH_1H;
            float def_adx_thresh = ADX_THRESHOLD_1H;
            
            config->fast_base_min = (int)(def_fast_base * (1 - SEARCH_PERCENT_FAST_BASE_1H));
            config->fast_base_max = (int)(def_fast_base * (1 + SEARCH_PERCENT_FAST_BASE_1H));
            config->slow_base_min = (int)(def_slow_base * (1 - SEARCH_PERCENT_SLOW_BASE_1H));
            config->slow_base_max = (int)(def_slow_base * (1 + SEARCH_PERCENT_SLOW_BASE_1H));
            config->fast_mult_min = def_fast_mult * (1 - SEARCH_PERCENT_FAST_MULT_1H);
            config->fast_mult_max = def_fast_mult * (1 + SEARCH_PERCENT_FAST_MULT_1H);
            config->slow_mult_min = def_slow_mult * (1 - SEARCH_PERCENT_SLOW_MULT_1H);
            config->slow_mult_max = def_slow_mult * (1 + SEARCH_PERCENT_SLOW_MULT_1H);
            config->atr_length_min = (int)(def_atr * (1 - SEARCH_PERCENT_ATR_1H));
            config->atr_length_max = (int)(def_atr * (1 + SEARCH_PERCENT_ATR_1H));
            config->vol_threshold_min = (int)(def_vol_thresh * (1 - SEARCH_PERCENT_VOL_THRESHOLD_1H));
            config->vol_threshold_max = (int)(def_vol_thresh * (1 + SEARCH_PERCENT_VOL_THRESHOLD_1H));
            config->adx_length_min = (int)(def_adx_length * (1 - SEARCH_PERCENT_ADX_LENGTH_1H));
            config->adx_length_max = (int)(def_adx_length * (1 + SEARCH_PERCENT_ADX_LENGTH_1H));
            config->adx_threshold_min = def_adx_thresh * (1 - SEARCH_PERCENT_ADX_THRESHOLD_1H);
            config->adx_threshold_max = def_adx_thresh * (1 + SEARCH_PERCENT_ADX_THRESHOLD_1H);
        #else
            fprintf(stderr, "⚠️  Warning: Fixed range mode not implemented. Enable USE_PERCENT_RANGE_1H\n");
            exit(1);
        #endif
    } else if (strcmp(interval, "4h") == 0) {
        #ifdef USE_PERCENT_RANGE_4H
            int def_fast_base = FAST_BASE_4H;
            int def_slow_base = SLOW_BASE_4H;
            float def_fast_mult = FAST_MULT_4H;
            float def_slow_mult = SLOW_MULT_4H;
            int def_atr = ATR_LENGTH_4H;
            int def_vol_thresh = VOL_THRESHOLD_4H;
            int def_adx_length = ADX_LENGTH_4H;
            float def_adx_thresh = ADX_THRESHOLD_4H;
            
            config->fast_base_min = (int)(def_fast_base * (1 - SEARCH_PERCENT_FAST_BASE_4H));
            config->fast_base_max = (int)(def_fast_base * (1 + SEARCH_PERCENT_FAST_BASE_4H));
            config->slow_base_min = (int)(def_slow_base * (1 - SEARCH_PERCENT_SLOW_BASE_4H));
            config->slow_base_max = (int)(def_slow_base * (1 + SEARCH_PERCENT_SLOW_BASE_4H));
            config->fast_mult_min = def_fast_mult * (1 - SEARCH_PERCENT_FAST_MULT_4H);
            config->fast_mult_max = def_fast_mult * (1 + SEARCH_PERCENT_FAST_MULT_4H);
            config->slow_mult_min = def_slow_mult * (1 - SEARCH_PERCENT_SLOW_MULT_4H);
            config->slow_mult_max = def_slow_mult * (1 + SEARCH_PERCENT_SLOW_MULT_4H);
            config->atr_length_min = (int)(def_atr * (1 - SEARCH_PERCENT_ATR_4H));
            config->atr_length_max = (int)(def_atr * (1 + SEARCH_PERCENT_ATR_4H));
            config->vol_threshold_min = (int)(def_vol_thresh * (1 - SEARCH_PERCENT_VOL_THRESHOLD_4H));
            config->vol_threshold_max = (int)(def_vol_thresh * (1 + SEARCH_PERCENT_VOL_THRESHOLD_4H));
            config->adx_length_min = (int)(def_adx_length * (1 - SEARCH_PERCENT_ADX_LENGTH_4H));
            config->adx_length_max = (int)(def_adx_length * (1 + SEARCH_PERCENT_ADX_LENGTH_4H));
            config->adx_threshold_min = def_adx_thresh * (1 - SEARCH_PERCENT_ADX_THRESHOLD_4H);
            config->adx_threshold_max = def_adx_thresh * (1 + SEARCH_PERCENT_ADX_THRESHOLD_4H);
        #else
            fprintf(stderr, "⚠️  Warning: Fixed range mode not implemented. Enable USE_PERCENT_RANGE_4H\n");
            exit(1);
        #endif
    } else { // 1d
        #ifdef USE_PERCENT_RANGE_1D
            int def_fast_base = FAST_BASE_1D;
            int def_slow_base = SLOW_BASE_1D;
            float def_fast_mult = FAST_MULT_1D;
            float def_slow_mult = SLOW_MULT_1D;
            int def_atr = ATR_LENGTH_1D;
            int def_vol_thresh = VOL_THRESHOLD_1D;
            int def_adx_length = ADX_LENGTH_1D;
            float def_adx_thresh = ADX_THRESHOLD_1D;
            
            config->fast_base_min = (int)(def_fast_base * (1 - SEARCH_PERCENT_FAST_BASE_1D));
            config->fast_base_max = (int)(def_fast_base * (1 + SEARCH_PERCENT_FAST_BASE_1D));
            config->slow_base_min = (int)(def_slow_base * (1 - SEARCH_PERCENT_SLOW_BASE_1D));
            config->slow_base_max = (int)(def_slow_base * (1 + SEARCH_PERCENT_SLOW_BASE_1D));
            config->fast_mult_min = def_fast_mult * (1 - SEARCH_PERCENT_FAST_MULT_1D);
            config->fast_mult_max = def_fast_mult * (1 + SEARCH_PERCENT_FAST_MULT_1D);
            config->slow_mult_min = def_slow_mult * (1 - SEARCH_PERCENT_SLOW_MULT_1D);
            config->slow_mult_max = def_slow_mult * (1 + SEARCH_PERCENT_SLOW_MULT_1D);
            config->atr_length_min = (int)(def_atr * (1 - SEARCH_PERCENT_ATR_1D));
            config->atr_length_max = (int)(def_atr * (1 + SEARCH_PERCENT_ATR_1D));
            config->vol_threshold_min = (int)(def_vol_thresh * (1 - SEARCH_PERCENT_VOL_THRESHOLD_1D));
            config->vol_threshold_max = (int)(def_vol_thresh * (1 + SEARCH_PERCENT_VOL_THRESHOLD_1D));
            config->adx_length_min = (int)(def_adx_length * (1 - SEARCH_PERCENT_ADX_LENGTH_1D));
            config->adx_length_max = (int)(def_adx_length * (1 + SEARCH_PERCENT_ADX_LENGTH_1D));
            config->adx_threshold_min = def_adx_thresh * (1 - SEARCH_PERCENT_ADX_THRESHOLD_1D);
            config->adx_threshold_max = def_adx_thresh * (1 + SEARCH_PERCENT_ADX_THRESHOLD_1D);
        #else
            fprintf(stderr, "⚠️  Warning: Fixed range mode not implemented. Enable USE_PERCENT_RANGE_1D\n");
            exit(1);
        #endif
    }
}

// Export results to JSON and HTML
void export_results_to_json(const char* ticker, const char* interval, const char* strategy,
                            float* best_params, float* best_results, float* trade_log,
                            long long* timestamps, float* closes, int num_candles,
                            float buy_hold_return) {
    
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    char timestamp_str[32];
    strftime(timestamp_str, sizeof(timestamp_str), "%Y%m%d_%H%M%S", tm_info);
    
    char ticker_lower[64];
    strcpy(ticker_lower, ticker);
    for (char* p = ticker_lower; *p; p++) *p = tolower(*p);
    
    char results_dir[256];
    snprintf(results_dir, sizeof(results_dir), "strategies/%s/results/%s/%s", strategy, ticker_lower, interval);
    char mkdir_cmd[512];
    snprintf(mkdir_cmd, sizeof(mkdir_cmd), "mkdir -p %s", results_dir);
    system(mkdir_cmd);
    
    char json_filename[512];
    snprintf(json_filename, sizeof(json_filename), "%s/%s_%s_%s.json", 
             results_dir, timestamp_str, ticker, interval);
    
    FILE* json_file = fopen(json_filename, "w");
    if (!json_file) {
        fprintf(stderr, "⚠️  Warning: Could not create JSON file: %s\n", json_filename);
        return;
    }
    
    fprintf(json_file, "{\n");
    fprintf(json_file, "  \"ticker\": \"%s\",\n", ticker);
    fprintf(json_file, "  \"interval\": \"%s\",\n", interval);
    fprintf(json_file, "  \"strategy\": \"%s\",\n", strategy);
    fprintf(json_file, "  \"timestamp\": \"%s\",\n", timestamp_str);
    fprintf(json_file, "  \"candles\": %d,\n", num_candles);
    
    fprintf(json_file, "  \"performance\": {\n");
    fprintf(json_file, "    \"total_return\": %.2f,\n", best_results[0]);
    fprintf(json_file, "    \"max_drawdown\": %.2f,\n", best_results[1]);
    fprintf(json_file, "    \"calmar_ratio\": %.2f,\n", best_results[0] / best_results[1]);
    fprintf(json_file, "    \"sharpe_ratio\": %.2f,\n", best_results[4]);
    fprintf(json_file, "    \"total_trades\": %d,\n", (int)best_results[2]);
    fprintf(json_file, "    \"buy_hold_return\": %.2f,\n", buy_hold_return);
    fprintf(json_file, "    \"outperformance\": %.2f\n", best_results[0] - buy_hold_return);
    fprintf(json_file, "  },\n");
    
    fprintf(json_file, "  \"parameters\": {\n");
    fprintf(json_file, "    \"fast_base\": %.0f,\n", best_params[0]);
    fprintf(json_file, "    \"slow_base\": %.0f,\n", best_params[1]);
    fprintf(json_file, "    \"fast_multiplier\": %.2f,\n", best_params[2]);
    fprintf(json_file, "    \"slow_multiplier\": %.2f,\n", best_params[3]);
    fprintf(json_file, "    \"atr_length\": %.0f,\n", best_params[4]);
    fprintf(json_file, "    \"volatility_threshold\": %.0f,\n", best_params[5]);
    fprintf(json_file, "    \"adx_length\": %.0f,\n", best_params[6]);
    fprintf(json_file, "    \"adx_threshold\": %.2f\n", best_params[7]);
    fprintf(json_file, "  },\n");
    
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
        
        if (is_buy) entry_price = price;
    }
    
    fprintf(json_file, "\n  ]\n");
    fprintf(json_file, "}\n");
    fclose(json_file);
    
    printf("\n💾 Results saved to: %s\n", json_filename);
    generate_html_report(json_filename, ticker, interval, strategy, results_dir, timestamp_str);
}

// Generate HTML report
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
    
    FILE* json_file = fopen(json_filename, "r");
    if (!json_file) {
        fprintf(stderr, "⚠️  Warning: Could not read JSON file: %s\n", json_filename);
        fclose(html_file);
        return;
    }
    
    fseek(json_file, 0, SEEK_END);
    long json_size = ftell(json_file);
    fseek(json_file, 0, SEEK_SET);
    
    char* json_content = malloc(json_size + 1);
    if (!json_content) {
        fclose(json_file);
        fclose(html_file);
        return;
    }
    
    fread(json_content, 1, json_size, json_file);
    json_content[json_size] = '\0';
    fclose(json_file);
    
    char ticker_lower[32];
    strcpy(ticker_lower, ticker);
    for (int i = 0; ticker_lower[i]; i++) ticker_lower[i] = tolower(ticker_lower[i]);
    
    char csv_path[512];
    snprintf(csv_path, sizeof(csv_path), "../../../data/%s_%s.csv", ticker_lower, interval);
    
    fprintf(html_file, "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n");
    fprintf(html_file, "  <meta charset=\"UTF-8\">\n");
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
    
    fprintf(html_file, "  <script>\n");
    fprintf(html_file, "    const embeddedData = %s;\n", json_content);
    fprintf(html_file, "    async function loadResults() {\n");
    fprintf(html_file, "      const data = embeddedData;\n");
    fprintf(html_file, "      const metricsDiv = document.getElementById('metrics');\n");
    fprintf(html_file, "      const metrics = [\n");
    fprintf(html_file, "        { label: 'Total Return', value: data.performance.total_return, suffix: '%%', colorClass: data.performance.total_return > 0 ? 'positive' : 'negative' },\n");
    fprintf(html_file, "        { label: 'Max Drawdown', value: data.performance.max_drawdown, suffix: '%%', colorClass: 'negative' },\n");
    fprintf(html_file, "        { label: 'Calmar Ratio', value: data.performance.calmar_ratio, suffix: '', colorClass: 'neutral' },\n");
    fprintf(html_file, "        { label: 'Sharpe Ratio', value: data.performance.sharpe_ratio, suffix: '', colorClass: 'neutral' },\n");
    fprintf(html_file, "        { label: 'Total Trades', value: data.performance.total_trades, suffix: '', colorClass: 'neutral' },\n");
    fprintf(html_file, "        { label: 'Buy & Hold', value: data.performance.buy_hold_return, suffix: '%%', colorClass: data.performance.buy_hold_return > 0 ? 'positive' : 'negative' },\n");
    fprintf(html_file, "        { label: 'Outperformance', value: data.performance.outperformance, suffix: '%%', colorClass: data.performance.outperformance > 0 ? 'positive' : 'negative' }\n");
    fprintf(html_file, "      ];\n");
    fprintf(html_file, "      metricsDiv.innerHTML = metrics.map(m => `<div class=\"metric-card\"><div class=\"metric-label\">${m.label}</div><div class=\"metric-value ${m.colorClass}\">${m.value.toFixed(2)}${m.suffix}</div></div>`).join('');\n");
    fprintf(html_file, "      const paramsDiv = document.getElementById('parameters');\n");
    fprintf(html_file, "      const params = Object.entries(data.parameters).map(([key, value]) => `<div class=\"param-item\"><div class=\"param-name\">${key.replace(/_/g, ' ')}</div><div class=\"param-value\">${value}</div></div>`).join('');\n");
    fprintf(html_file, "      paramsDiv.innerHTML = `<div class=\"param-grid\">${params}</div>`;\n");
    fprintf(html_file, "      const tradesTable = document.getElementById('tradesTable');\n");
    fprintf(html_file, "      const tradesHTML = `<thead><tr><th>#</th><th>Action</th><th>Price</th><th>Date</th><th>P&L</th></tr></thead><tbody>${data.trades.map(t => `<tr><td>${t.trade_number}</td><td class=\"${t.action.toLowerCase()}\">${t.action}</td><td>$${t.price.toFixed(2)}</td><td>${t.date}</td><td class=\"${t.pnl_percent ? (t.pnl_percent > 0 ? 'positive' : 'negative') : ''}\">${t.pnl_percent ? (t.pnl_percent > 0 ? '+' : '') + t.pnl_percent.toFixed(2) + '%%' : '-'}</td></tr>`).join('')}</tbody>`;\n");
    fprintf(html_file, "      tradesTable.innerHTML = tradesHTML;\n");
    fprintf(html_file, "      const tradeMarkers = data.trades.map(t => ({ date: t.date.split(' ')[0], price: t.price, action: t.action }));\n");
    fprintf(html_file, "      const ctx = document.getElementById('priceChart').getContext('2d');\n");
    fprintf(html_file, "      new Chart(ctx, {\n");
    fprintf(html_file, "        type: 'line',\n");
    fprintf(html_file, "        data: { labels: tradeMarkers.map(t => t.date), datasets: [{ label: 'Trade Prices', data: tradeMarkers.map(t => t.price), borderColor: '#60a5fa', backgroundColor: 'rgba(96, 165, 250, 0.1)', borderWidth: 2, pointRadius: 4, pointBackgroundColor: tradeMarkers.map(t => t.action === 'BUY' ? '#34d399' : '#f87171'), pointBorderColor: tradeMarkers.map(t => t.action === 'BUY' ? '#34d399' : '#f87171'), tension: 0.1 }] },\n");
    fprintf(html_file, "        options: { responsive: true, maintainAspectRatio: true, aspectRatio: 2.5, plugins: { legend: { labels: { color: '#e4e4e7' } }, tooltip: { mode: 'index', intersect: false, callbacks: { label: function(context) { const trade = tradeMarkers[context.dataIndex]; return `${trade.action}: $${trade.price.toFixed(2)}`; } } } }, scales: { x: { ticks: { color: '#9ca3af', maxTicksLimit: 12 }, grid: { color: '#374151' } }, y: { ticks: { color: '#9ca3af' }, grid: { color: '#374151' } } } }\n");
    fprintf(html_file, "      });\n");
    fprintf(html_file, "    }\n    loadResults();\n");
    fprintf(html_file, "  </script>\n</body>\n</html>\n");
    
    free(json_content);
    fclose(html_file);
    printf("📊 HTML report saved to: %s\n", html_filename);
}

// Load CSV data
int load_csv(const char* filename, float** closes, float** highs, float** lows, long long** timestamps) {
    FILE* file = fopen(filename, "r");
    if (!file) {
        fprintf(stderr, "❌ Error: Could not open %s\n", filename);
        return -1;
    }
    
    int count = 0;
    char line[1024];
    fgets(line, sizeof(line), file);
    
    while (fgets(line, sizeof(line), file)) count++;
    
    rewind(file);
    fgets(line, sizeof(line), file);
    
    *closes = malloc(count * sizeof(float));
    *highs = malloc(count * sizeof(float));
    *lows = malloc(count * sizeof(float));
    *timestamps = malloc(count * sizeof(long long));
    
    int i = 0;
    while (fgets(line, sizeof(line), file) && i < count) {
        long long timestamp;
        float open, high, low, close, volume;
        sscanf(line, "%lld,%f,%f,%f,%f,%f", &timestamp, &open, &high, &low, &close, &volume);
        
        (*closes)[i] = roundf(close * 10000.0f) / 10000.0f;
        (*highs)[i] = roundf(high * 10000.0f) / 10000.0f;
        (*lows)[i] = roundf(low * 10000.0f) / 10000.0f;
        (*timestamps)[i] = timestamp;
        i++;
    }
    
    fclose(file);
    return count;
}

// Load OpenCL kernel
char* load_kernel_source(const char* strategy_dir) {
    char kernel_path[512];
    snprintf(kernel_path, sizeof(kernel_path), "strategies/%s/kernel.cl", strategy_dir);
    
    FILE* file = fopen(kernel_path, "r");
    if (!file) {
        fprintf(stderr, "❌ Error: Could not open kernel file: %s\n", kernel_path);
        exit(1);
    }
    
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);
    
    char* source = malloc(file_size + 1);
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

int main(int argc, char** argv) {
    if (argc < 3 || argc > 4) {
        printf("Usage: %s <TICKER> <INTERVAL> [nosave]\n", argv[0]);
        printf("Example: %s GOOG 1h\n", argv[0]);
        printf("\nIntervals: 1h, 4h, 1d\n");
        printf("Strategy: %s\n", STRATEGY_NAME);
        return 1;
    }
    
    char* ticker = argv[1];
    char* interval = argv[2];
    int save_results = 1;
    
    if (argc == 4 && strcmp(argv[3], "nosave") == 0) {
        save_results = 0;
        printf("\n⚠️  Running in NO-SAVE mode\n");
    }
    
    for (char* p = ticker; *p; p++) *p = toupper(*p);
    for (char* p = interval; *p; p++) *p = tolower(*p);
    
    printf("\n🎮 OpenCL GPU Parameter Optimization System\n");
    printf("   Ticker: %s\n", ticker);
    printf("   Interval: %s\n", interval);
    printf("   Strategy: %s (Volatility-Adaptive EMA with ADX)\n", STRATEGY_NAME);
    printf("   Tech: Apple Silicon / AMD Radeon + OpenCL\n\n");
    
    printf("📦 Loading strategy kernel...\n");
    char* kernel_source = load_kernel_source(STRATEGY_NAME);
    printf("\n");
    
    Config config;
    load_config(interval, &config);
    
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
        printf("\n💡 To fetch data, run: python3 fetch_data.py %s %s 600\n\n", ticker, interval);
        return 1;
    }
    
    printf("   ✅ Loaded %d candles\n\n", num_candles);
    printf("============================================================\n");
    printf("🔧 Optimizing %s - Adaptive EMA v2.1 (with ADX)\n", ticker);
    printf("============================================================\n\n");
    printf("⚡ Calculating parameter space size...\n");
    
    // Calculate ranges
    int fb_range = config.fast_base_max - config.fast_base_min + 1;
    int sb_range = config.slow_base_max - config.slow_base_min + 1;
    int atr_range = config.atr_length_max - config.atr_length_min + 1;
    int vt_range = config.vol_threshold_max - config.vol_threshold_min + 1;
    int adx_len_range = config.adx_length_max - config.adx_length_min + 1;
    
    // For float multipliers and ADX threshold, sample at 0.1 increments
    int fm_steps = (int)((config.fast_mult_max - config.fast_mult_min) / 0.1f) + 1;
    int sm_steps = (int)((config.slow_mult_max - config.slow_mult_min) / 0.1f) + 1;
    int adx_thresh_steps = (int)((config.adx_threshold_max - config.adx_threshold_min) / 1.0f) + 1;
    
    printf("   Parameter ranges:\n");
    printf("     Fast Base: %d-%d (%d values)\n", config.fast_base_min, config.fast_base_max, fb_range);
    printf("     Slow Base: %d-%d (%d values)\n", config.slow_base_min, config.slow_base_max, sb_range);
    printf("     Fast Mult: %.1f-%.1f (%d values)\n", config.fast_mult_min, config.fast_mult_max, fm_steps);
    printf("     Slow Mult: %.1f-%.1f (%d values)\n", config.slow_mult_min, config.slow_mult_max, sm_steps);
    printf("     ATR Length: %d-%d (%d values)\n", config.atr_length_min, config.atr_length_max, atr_range);
    printf("     Vol Threshold: %d-%d (%d values)\n", config.vol_threshold_min, config.vol_threshold_max, vt_range);
    printf("     ADX Length: %d-%d (%d values)\n", config.adx_length_min, config.adx_length_max, adx_len_range);
    printf("     ADX Threshold: %.0f-%.0f (%d values)\n", config.adx_threshold_min, config.adx_threshold_max, adx_thresh_steps);
    
    // Count valid combinations (fast_base < slow_base)
    int num_combinations = 0;
    for (int fb = config.fast_base_min; fb <= config.fast_base_max; fb++) {
        for (int sb = config.slow_base_min; sb <= config.slow_base_max; sb++) {
            if (fb >= sb) continue;
            for (float fm = config.fast_mult_min; fm <= config.fast_mult_max; fm += 0.1f) {
                for (float sm = config.slow_mult_min; sm <= config.slow_mult_max; sm += 0.1f) {
                    for (int atr = config.atr_length_min; atr <= config.atr_length_max; atr++) {
                        for (int vt = config.vol_threshold_min; vt <= config.vol_threshold_max; vt++) {
                            for (int adx_len = config.adx_length_min; adx_len <= config.adx_length_max; adx_len++) {
                                for (float adx_thresh = config.adx_threshold_min; adx_thresh <= config.adx_threshold_max; adx_thresh += 1.0f) {
                                    num_combinations++;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    printf("\n   Total valid combinations: %d\n", num_combinations);
    
    if (num_combinations > MAX_COMBINATIONS) {
        printf("\n❌ ERROR: Too many combinations (%d > %d)\n", num_combinations, MAX_COMBINATIONS);
        printf("   Reduce search ranges in config_%s.h\n\n", interval);
        free(closes); free(highs); free(lows); free(timestamps); free(kernel_source);
        return 1;
    }
    
    printf("   ✅ Parameter space is within limits\n\n");
    
    // Initialize OpenCL
    cl_int err;
    cl_platform_id platform;
    clGetPlatformIDs(1, &platform, NULL);
    
    cl_uint num_devices;
    clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, 0, NULL, &num_devices);
    cl_device_id* devices = malloc(num_devices * sizeof(cl_device_id));
    clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, num_devices, devices, NULL);
    
    cl_device_id device = devices[0];
    int device_priority = 0;
    
    for (int i = 0; i < num_devices; i++) {
        char name[128];
        clGetDeviceInfo(devices[i], CL_DEVICE_NAME, sizeof(name), name, NULL);
        
        int priority = strstr(name, "Apple M") || strstr(name, "Apple") ? 2 : 
                      strstr(name, "Radeon") ? 1 : 0;
        
        if (priority > device_priority) {
            device = devices[i];
            device_priority = priority;
        }
    }
    free(devices);
    
    cl_context context = clCreateContext(NULL, 1, &device, NULL, NULL, &err);
    cl_command_queue queue = clCreateCommandQueue(context, device, 0, &err);
    
    cl_ulong global_mem;
    size_t max_work_group_size;
    cl_uint compute_units;
    clGetDeviceInfo(device, CL_DEVICE_GLOBAL_MEM_SIZE, sizeof(cl_ulong), &global_mem, NULL);
    clGetDeviceInfo(device, CL_DEVICE_MAX_WORK_GROUP_SIZE, sizeof(size_t), &max_work_group_size, NULL);
    clGetDeviceInfo(device, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(cl_uint), &compute_units, NULL);
    
    const char* kernel_source_const = kernel_source;
    cl_program program = clCreateProgramWithSource(context, 1, &kernel_source_const, NULL, &err);
    clBuildProgram(program, 1, &device, "-cl-fast-relaxed-math", NULL, NULL);
    cl_kernel kernel = clCreateKernel(program, "optimize_strategy", &err);
    
    // Allocate parameter array (8 params per combination)
    float* h_params = malloc(num_combinations * 8 * sizeof(float));
    int idx = 0;
    
    for (int fb = config.fast_base_min; fb <= config.fast_base_max; fb++) {
        for (int sb = config.slow_base_min; sb <= config.slow_base_max; sb++) {
            if (fb >= sb) continue;
            for (float fm = config.fast_mult_min; fm <= config.fast_mult_max; fm += 0.1f) {
                for (float sm = config.slow_mult_min; sm <= config.slow_mult_max; sm += 0.1f) {
                    for (int atr = config.atr_length_min; atr <= config.atr_length_max; atr++) {
                        for (int vt = config.vol_threshold_min; vt <= config.vol_threshold_max; vt++) {
                            for (int adx_len = config.adx_length_min; adx_len <= config.adx_length_max; adx_len++) {
                                for (float adx_thresh = config.adx_threshold_min; adx_thresh <= config.adx_threshold_max; adx_thresh += 1.0f) {
                                    h_params[idx * 8 + 0] = fb;
                                    h_params[idx * 8 + 1] = sb;
                                    h_params[idx * 8 + 2] = fm;
                                    h_params[idx * 8 + 3] = sm;
                                    h_params[idx * 8 + 4] = atr;
                                    h_params[idx * 8 + 5] = vt;
                                    h_params[idx * 8 + 6] = adx_len;
                                    h_params[idx * 8 + 7] = adx_thresh;
                                    idx++;
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    float* h_results = malloc(num_combinations * 6 * sizeof(float));
    float* h_trade_log = calloc(1500, sizeof(float));
    
    for (int i = 0; i < num_combinations * 6; i++) h_results[i] = 0.0f;
    
    // Create GPU buffers
    cl_mem d_closes = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR, 
                                     num_candles * sizeof(float), closes, &err);
    cl_mem d_highs = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                    num_candles * sizeof(float), highs, &err);
    cl_mem d_lows = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                   num_candles * sizeof(float), lows, &err);
    cl_mem d_params = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                     num_combinations * 8 * sizeof(float), h_params, &err);
    cl_mem d_results = clCreateBuffer(context, CL_MEM_WRITE_ONLY,
                                      num_combinations * 6 * sizeof(float), NULL, &err);
    cl_mem d_trade_log = clCreateBuffer(context, CL_MEM_WRITE_ONLY, 1500 * sizeof(float), NULL, &err);
    
    // Set kernel arguments
    clSetKernelArg(kernel, 0, sizeof(cl_mem), &d_closes);
    clSetKernelArg(kernel, 1, sizeof(cl_mem), &d_highs);
    clSetKernelArg(kernel, 2, sizeof(cl_mem), &d_lows);
    clSetKernelArg(kernel, 3, sizeof(int), &num_candles);
    clSetKernelArg(kernel, 4, sizeof(cl_mem), &d_params);
    clSetKernelArg(kernel, 5, sizeof(cl_mem), &d_results);
    clSetKernelArg(kernel, 6, sizeof(int), &num_combinations);
    clSetKernelArg(kernel, 7, sizeof(cl_mem), &d_trade_log);
    
    printf("   Compute Units: %d | Max Work Group: %zu\n", compute_units, max_work_group_size);
    printf("   GPU Memory: %.2f GB\n\n", global_mem / (1024.0 * 1024.0 * 1024.0));
    
    size_t local_work_size = device_priority == 2 ? 
        (max_work_group_size >= 1024 ? 1024 : max_work_group_size) :
        device_priority == 1 ? 256 : 128;
    
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
                        num_combinations * 6 * sizeof(float), h_results, 0, NULL, NULL);
    
    // Find best result
    float best_score = -INFINITY;
    int best_idx = -1;
    int valid_count = 0;
    
    for (int i = 0; i < num_combinations; i++) {
        if (h_results[i * 6 + 5] > 0.5f) {
            valid_count++;
            if (h_results[i * 6 + 3] > best_score) {
                best_score = h_results[i * 6 + 3];
                best_idx = i;
            }
        }
    }
    
    printf("\n✅ Optimization Complete\n");
    printf("   Tested: %d combinations\n", num_combinations);
    printf("   Valid: %d results\n", valid_count);
    printf("   Time: %.1fs (%.0f tests/sec)\n\n", elapsed, num_combinations / elapsed);
    
    if (best_idx >= 0) {
        printf("🏆 BEST PARAMETERS FOR %s\n\n", ticker);
        printf("📊 Performance Metrics:\n");
        printf("   Total Return: %.2f%%\n", h_results[best_idx * 6 + 0]);
        printf("   Max Drawdown: %.2f%%\n", h_results[best_idx * 6 + 1]);
        printf("   Calmar Ratio: %.2f\n", h_results[best_idx * 6 + 0] / h_results[best_idx * 6 + 1]);
        printf("   Sharpe Ratio: %.2f\n", h_results[best_idx * 6 + 4]);
        printf("   Total Trades: %.0f\n", h_results[best_idx * 6 + 2]);
        printf("   Score: %.2f\n\n", h_results[best_idx * 6 + 3]);
        
        printf("⚙️  Optimal Parameters:\n");
        printf("   Fast Base: %.0f\n", h_params[best_idx * 8 + 0]);
        printf("   Slow Base: %.0f\n", h_params[best_idx * 8 + 1]);
        printf("   Fast Mult: %.2f\n", h_params[best_idx * 8 + 2]);
        printf("   Slow Mult: %.2f\n", h_params[best_idx * 8 + 3]);
        printf("   ATR Length: %.0f\n", h_params[best_idx * 8 + 4]);
        printf("   Vol Threshold: %.0f%%\n", h_params[best_idx * 8 + 5]);
        printf("   ADX Length: %.0f\n", h_params[best_idx * 8 + 6]);
        printf("   ADX Threshold: %.2f\n", h_params[best_idx * 8 + 7]);
    }
    
    float buy_hold_return = ((closes[num_candles - 1] - closes[0]) / closes[0]) * 100.0f;
    
    // Re-run best params for trade log
    printf("\n============================================================\n");
    printf("📋 TRADE LOG (Best Parameters)\n");
    printf("============================================================\n");
    
    if (best_idx >= 0) {
        printf("   Re-running best parameters to generate accurate trade log...\n\n");
        
        float best_params_only[8];
        for (int i = 0; i < 8; i++) best_params_only[i] = h_params[best_idx * 8 + i];
        
        memset(h_trade_log, 0, 300 * sizeof(float));
        
        cl_mem d_best_params = clCreateBuffer(context, CL_MEM_READ_ONLY | CL_MEM_COPY_HOST_PTR,
                                              8 * sizeof(float), best_params_only, &err);
        cl_mem d_best_results = clCreateBuffer(context, CL_MEM_WRITE_ONLY, 6 * sizeof(float), NULL, &err);
        cl_mem d_best_trade_log = clCreateBuffer(context, CL_MEM_WRITE_ONLY, 1500 * sizeof(float), NULL, &err);
        
        int single_combo = 1;
        clSetKernelArg(kernel, 4, sizeof(cl_mem), &d_best_params);
        clSetKernelArg(kernel, 5, sizeof(cl_mem), &d_best_results);
        clSetKernelArg(kernel, 6, sizeof(int), &single_combo);
        clSetKernelArg(kernel, 7, sizeof(cl_mem), &d_best_trade_log);
        
        size_t single_global = 1;
        clEnqueueNDRangeKernel(queue, kernel, 1, NULL, &single_global, NULL, 0, NULL, NULL);
        clFinish(queue);
        
        float rerun_results[6];
        clEnqueueReadBuffer(queue, d_best_results, CL_TRUE, 0, 6 * sizeof(float), rerun_results, 0, NULL, NULL);
        clEnqueueReadBuffer(queue, d_best_trade_log, CL_TRUE, 0, 1500 * sizeof(float), h_trade_log, 0, NULL, NULL);
        
        for (int i = 0; i < 6; i++) h_results[best_idx * 6 + i] = rerun_results[i];
        
        printf("   ✓ Trade log updated: %.0f round-trip trades\n\n", rerun_results[2]);
        
        clReleaseMemObject(d_best_params);
        clReleaseMemObject(d_best_results);
        clReleaseMemObject(d_best_trade_log);
    }
    
    int trade_count = 0;
    float entry_price = 0.0f;
    
    for (int i = 0; i < 500; i++) {
        int candle_idx = (int)h_trade_log[i * 3 + 0];
        float price = h_trade_log[i * 3 + 1];
        int is_buy = (int)h_trade_log[i * 3 + 2];
        
        if (candle_idx == 0 && price == 0.0f) break;
        
        time_t ts = timestamps[candle_idx];
        struct tm *tm_info = localtime(&ts);
        char date_str[64];
        strftime(date_str, sizeof(date_str), "%Y-%m-%d %H:%M", tm_info);
        
        if (is_buy) {
            printf("   #%d  BUY  @ $%.2f on %s\n", ++trade_count, price, date_str);
            entry_price = price;
        } else {
            float pnl = ((price - entry_price) / entry_price) * 100.0f;
            printf("   #%d  SELL @ $%.2f on %s | P&L: %s%.2f%%\n", 
                   ++trade_count, price, date_str, pnl >= 0 ? "+" : "", pnl);
        }
    }
    printf("   Total trades: %d\n", trade_count);
    
    if (save_results) {
        export_results_to_json(ticker, interval, STRATEGY_NAME, 
                              h_params + (best_idx * 8), 
                              h_results + (best_idx * 6),
                              h_trade_log, timestamps, closes, num_candles,
                              buy_hold_return);
    } else {
        printf("\n⏭️  Skipping results export (nosave mode)\n");
    }
    
    printf("============================================================\n");
    printf("   Buy & Hold Return: %.2f%%\n", buy_hold_return);
    printf("   Strategy Outperformance: %.2f%%\n", h_results[best_idx * 6 + 0] - buy_hold_return);
    printf("\n============================================================\n");
    
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
    free(kernel_source);
    
    return 0;
}
