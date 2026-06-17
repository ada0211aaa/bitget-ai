# Changelog

## 2026-06-17

- Added a 30-day per-symbol news library flow under `data/news/<SYMBOL>/` with raw events, AI-ready events, and coverage metadata.
- Added technical candidate observation rows and chart markers so the dashboard can show watch points separately from real buy/sell backtest markers.
- Added `fetch-news-library`, `backtest --news-library`, and dashboard payload support for news coverage and candidate diagnostics.
- Added an `aggressive_news` research decision mode so recent true news can produce real buy markers while no-news days remain observe-only.
- Added external news collectors for daily-stock-analysis archives, SEC EDGAR filings, and Google News date-window search for two-year backtest news coverage.

## 2026-06-15

- Added a configurable `yahoo_chart_daily` external US equity daily source for long-horizon local backtests.
- Added `configs/us_stock_daily_external.json` for NVDAUSDT, AMDUSDT, TSLAUSDT, AAPLUSDT, and MSFTUSDT daily research backtests.
- Preserved actual candle source in candles, coverage, and normalized `data/market` artifacts.
- Added dashboard display of the selected price source.
- Added public-news aliases for AAPL/Apple/iPhone and TSLA/Tesla.
- Added structured AI news fields, MA20/MA50 daily confirmation, sell rule A, and chart marker support for news-gated daily backtests.
- Expanded daily news matching to 72 hours so weekend and after-close events can carry into the next daily session.

## 2026-06-08

- Added a local backtest-only Python CLI for Bitget stock USDT perpetual public candles.
- Added deterministic fixture demo and public-data reports under `reports/`.
- Clarified that the first asset scope is Bitget-listed stock USDT perpetual contracts, not traditional US stock spot-market data.
- Added root-rules-inspired requirements coverage: run modes, dry-run boundary, failure premortem, and documentation folder responsibilities.
- Kept the first version Playbook-first, backtest/simulation-only, and without live trading.

## 2026-06-09

- Added `.env.example` with the single Playbook API key placeholder needed by the current project.
- Documented that current backtest code does not require account, position, or trading credentials.
- Added a real Bitget Playbook API client and CLI flow for list, upload, backtest run, and run polling.
- Added a signal-only NVDAUSDT Playbook package under `playbooks/ai-tech-stock-news-signal/`.
- Recorded a completed Playbook API backtest summary under `reports/playbook/playbook-report.md`.

## 2026-06-07

- Initialized the Bitget AI Hackathon repository.
- Added project rules, README, `.gitignore`, and the first requirements draft.
- Added architecture diagram and layered architecture tree for the requirements document.
