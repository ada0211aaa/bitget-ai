# Project Memory

## Current Project Direction

- This repository is for the Bitget AI Base Camp Hackathon S1, US Stock AI Trading track.
- The first version is Bitget-native and backtest-only.
- Use Bitget Playbook first for natural-language strategy creation, backtesting, publishing, and metrics.
- Use the local Python CLI for public-data backtest evidence before Playbook access is available.
- Use Bitget Agent Hub official skills first for market signals:
  - `news-briefing`
  - `macro-analyst`
  - `technical-analysis`
  - `sentiment-analyst`
  - `market-intel`

## Confirmed Strategy Preferences

- Strategy theme: AI tech stock USDT perpetual contracts listed on Bitget.
- Candidate pool: `NVDAUSDT`, `MSFTUSDT`, `GOOGLUSDT`, `AMDUSDT`, `METAUSDT`, with actual assets constrained by Bitget / Playbook support.
- The first version does not use traditional US stock spot-market data.
- Cadence: daily strategy, not high-frequency news sniping.
- Decision style: hard risk filters first, scoring second.
- Priority: avoid big mistakes and downside first, not chase every rally.
- Output style: five natural-language views: bullish, cautiously bullish, neutral/observe, cautiously bearish, bearish.

## Safety Rules

- Do not commit real Playbook API keys, Bitget API keys, secrets, passphrases, private keys, account IDs, or full account snapshots.
- Do not implement live trading, automatic order placement, scheduled jobs, background tasks, or notifications without explicit user approval.
- First-version evidence must be backtest or simulation records only.

## Local Backtest Commands

- Deterministic fixture demo: `PYTHONPATH=src python3 -m bitget_ai_backtest.cli demo --output-dir reports/local-demo`
- Public-data backtest: `PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest --config configs/default_universe.json --output-dir reports/latest`
- Both commands are backtest-only and do not use API keys or place orders.

## Known Gaps

- Need actual Playbook access and a real backtest before final hackathon submission.
- Need to refine signal weights, thresholds, and mapping from scores to the five output views.
- Need to decide whether the local public-data backtest report is enough for an interim demo before Playbook access.
