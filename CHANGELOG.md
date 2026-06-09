# Changelog

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
