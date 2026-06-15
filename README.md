# Bitget AI Hackathon - US Stock AI Trading

This repository is for a Bitget AI Base Camp Hackathon S1 project in the **US Stock AI Trading** track.

The project direction is a minimal **AI tech stock futures news sentiment strategy** built primarily with Bitget-provided tools:

- Bitget Playbook for natural-language strategy creation, backtesting, publishing, and metrics.
- Bitget Agent Hub skills for news, macro, technical, sentiment, and market-intelligence signals.

The first asset scope is Bitget-listed stock USDT perpetual contracts, such as `NVDAUSDT`, `MSFTUSDT`, and `AAPLUSDT`. This is not a traditional US stock spot-market data project.

The first version is requirements-first and simulation/backtest-only. It does not contain API keys, live trading credentials, or a live execution engine.

## Playbook API Backtest

This repo can now call the official Bitget Playbook control-plane API with the single local `PLAYBOOK_API_KEY` in `.env`.

Run the real Playbook API flow:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli playbook-backtest --env .env --package-dir playbooks/ai-tech-stock-news-signal --output-dir reports/playbook --poll --poll-interval 5 --max-polls 20
```

What it does:

- Packages `playbooks/ai-tech-stock-news-signal/`.
- Uploads the package to `https://api.bitget.com/api/v1/playbook/upload`.
- Starts a Playbook backtest with `POST /api/v1/playbook/run`.
- Polls `GET /api/v1/playbook/run?run_id=...` until completion or timeout.
- Writes a safe summary to `reports/playbook/playbook-report.md`.

It does not publish, enable subscriptions, read positions, or place live orders.

## Local Backtest Demo

This implementation is backtest-only. It uses Bitget public market data or deterministic fixtures. It does not use API keys and cannot place orders.

Run deterministic fixture demo:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli demo --output-dir reports/local-demo
```

Run public-data backtest:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest --config configs/default_universe.json --output-dir reports/latest
```

Fetch news/events for the configured symbols. The first version reads local Bitget Agent Hub skill exports from `data/bitget-skills/` when present, then falls back to public Yahoo Finance RSS. Every event records its source type.

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli fetch-events --config configs/default_universe.json --output data/events/us_stock_events.json
```

Run a backtest with the event file and write per-trade explanations:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest --config configs/default_universe.json --events data/events/us_stock_events.json --output-dir reports/latest
```

Start the local Web demo in the foreground:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web --config configs/default_universe.json --output-dir reports/latest --port 8000
```

Open `http://127.0.0.1:8000` in a browser. Stop the server with `Ctrl+C`.

Outputs:

- `reports/local-demo/backtest-report.md`
- `reports/local-demo/trades.csv`
- `reports/latest/backtest-report.md`
- `reports/latest/trades.csv`
- `reports/latest/trade-explanations.json`
- `data/events/us_stock_events.json`

## Current Documents

- [Project rules](./AGENTS.md)
- [Requirements draft](./docs/requirements/2026-06-07-bitget-playbook-ai-tech-stock-strategy.md)
- [Architecture docs](./docs/architecture/)
- [Bitget skills docs](./docs/bitget-skills/)
- [Strategy docs](./docs/strategy/)
- [Playbook docs](./docs/playbook/)
- [Devlog drafts](./docs/devlog/)
- [Security docs](./docs/security/)
- [AI session recaps](./docs/ai-sessions/)
- [Changelog](./CHANGELOG.md)
- [Project memory](./MEMORY.md)

## Safety Notes

- Do not commit real Playbook API keys, Bitget API keys, secrets, passphrases, private keys, or full account data.
- Use placeholders such as `<PLAYBOOK_API_KEY>` in docs.
- Keep the first demo focused on backtest or simulated trading evidence.
