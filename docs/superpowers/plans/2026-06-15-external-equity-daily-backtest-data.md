# External Equity Daily Backtest Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a configurable external US equity daily price source for local backtest data landing while preserving Bitget as the default source.

**Architecture:** Keep the existing backtest/report/web flow. Add a small Yahoo Chart daily client that returns existing `Candle` objects, extend config with `price_source` and `ticker_map`, and route CLI fetch/backtest through a source selector.

**Tech Stack:** Python standard library, pytest, existing static dashboard.

---

## File Structure

- Modify `src/bitget_ai_backtest/config.py`: add `price_source` and `ticker_map` to `BacktestConfig`.
- Create `src/bitget_ai_backtest/equity_client.py`: fetch and parse Yahoo Chart daily candles.
- Modify `src/bitget_ai_backtest/cli.py`: route `fetch` and `backtest` by selected source and preserve source in reports.
- Modify `src/bitget_ai_backtest/reporting.py`: let normalized artifacts write the actual candle source.
- Modify `src/bitget_ai_backtest/web.py`: expose `price_source` in dashboard config.
- Modify `src/bitget_ai_backtest/static/app.js`: show price source in the config chips.
- Create `configs/us_stock_daily_external.json`: first external daily stock pool.
- Add tests in `tests/test_config.py`, `tests/test_equity_client.py`, `tests/test_cli.py`, `tests/test_reporting.py`, `tests/test_static_dashboard_ui.py`.

## Task 1: Config Source Fields

**Files:**
- Modify: `src/bitget_ai_backtest/config.py`
- Test: `tests/test_config.py`

- [x] **Step 1: Add failing config test**

Add a test that expects `price_source` and `ticker_map` to load.

- [x] **Step 2: Run config test to verify it fails**

Run: `python3 -m pytest tests/test_config.py -q`

- [x] **Step 3: Implement config fields**

Add `price_source: str` and `ticker_map: dict[str, str]` to `BacktestConfig`; default `price_source` to `bitget_public`.

- [x] **Step 4: Run config tests**

Run: `python3 -m pytest tests/test_config.py -q`

## Task 2: Yahoo Chart Daily Client

**Files:**
- Create: `src/bitget_ai_backtest/equity_client.py`
- Test: `tests/test_equity_client.py`

- [x] **Step 1: Add failing parser tests**

Test that a Yahoo Chart response converts to sorted `Candle` rows and skips incomplete OHLC rows.

- [x] **Step 2: Run parser tests to verify they fail**

Run: `python3 -m pytest tests/test_equity_client.py -q`

- [x] **Step 3: Implement Yahoo parser and client**

Implement `parse_yahoo_chart_response`, `YahooChartDailyClient.build_chart_url`, and `YahooChartDailyClient.fetch_candles`.

- [x] **Step 4: Run equity client tests**

Run: `python3 -m pytest tests/test_equity_client.py -q`

## Task 3: CLI Source Routing

**Files:**
- Modify: `src/bitget_ai_backtest/cli.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Add failing CLI tests**

Test `fetch --source yahoo_chart_daily` and `backtest` with config `price_source: yahoo_chart_daily`.

- [x] **Step 2: Run selected CLI tests to verify they fail**

Run: `python3 -m pytest tests/test_cli.py::test_fetch_command_writes_yahoo_daily_rows tests/test_cli.py::test_backtest_command_uses_external_equity_source -q`

- [x] **Step 3: Implement source selector**

Add source selection helpers and route `fetch`/`backtest` through Bitget or Yahoo.

- [x] **Step 4: Run selected CLI tests**

Run: `python3 -m pytest tests/test_cli.py::test_fetch_command_writes_yahoo_daily_rows tests/test_cli.py::test_backtest_command_uses_external_equity_source -q`

## Task 4: Preserve Source In Artifacts And Web Config

**Files:**
- Modify: `src/bitget_ai_backtest/reporting.py`
- Modify: `src/bitget_ai_backtest/web.py`
- Modify: `src/bitget_ai_backtest/static/app.js`
- Test: `tests/test_reporting.py`
- Test: `tests/test_web.py`
- Test: `tests/test_static_dashboard_ui.py`

- [x] **Step 1: Add failing source preservation tests**

Test normalized artifacts keep `yahoo_chart_daily`; test dashboard payload includes `price_source`; test static JS has a Chinese price source chip.

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_reporting.py tests/test_web.py tests/test_static_dashboard_ui.py -q`

- [x] **Step 3: Implement source propagation**

Pass source to normalized artifacts, expose source in web payload, render it in config chips.

- [x] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_reporting.py tests/test_web.py tests/test_static_dashboard_ui.py -q`

## Task 5: External Daily Config And Verification

**Files:**
- Create: `configs/us_stock_daily_external.json`

- [x] **Step 1: Add external config**

Use a small stock pool: `NVDAUSDT`, `AMDUSDT`, `TSLAUSDT`, `AAPLUSDT`, `MSFTUSDT`.

- [x] **Step 2: Run full tests**

Run: `python3 -m pytest -q`

- [x] **Step 3: Run external backtest smoke**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/us_stock_daily_external.json \
  --output-dir reports/us-stock-daily-external
```

Expected: report, candles, coverage, decisions, markers are written; coverage source is `yahoo_chart_daily`.

- [x] **Step 4: Do not leave web server running**

No web server is required for this task unless explicitly started in foreground and stopped.
