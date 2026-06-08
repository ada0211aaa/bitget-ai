# Bitget AI Hackathon - US Stock AI Trading

This repository is for a Bitget AI Base Camp Hackathon S1 project in the **US Stock AI Trading** track.

The project direction is a minimal **AI tech stock futures news sentiment strategy** built primarily with Bitget-provided tools:

- Bitget Playbook for natural-language strategy creation, backtesting, publishing, and metrics.
- Bitget Agent Hub skills for news, macro, technical, sentiment, and market-intelligence signals.

The first asset scope is Bitget-listed stock USDT perpetual contracts, such as `NVDAUSDT`, `MSFTUSDT`, and `AAPLUSDT`. This is not a traditional US stock spot-market data project.

The first version is requirements-first and simulation/backtest-only. It does not contain API keys, live trading credentials, or a live execution engine.

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

Outputs:

- `reports/local-demo/backtest-report.md`
- `reports/local-demo/trades.csv`
- `reports/latest/backtest-report.md`
- `reports/latest/trades.csv`

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
