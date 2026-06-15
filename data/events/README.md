# Event Data

Generated news and signal events for the local backtest demo live here.

The first version prefers local Bitget Agent Hub skill exports under `data/bitget-skills/` and falls back to public news feeds when no skill export is present. Do not store API keys, account data, balances, positions, or orders in this directory.

Generate events:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli fetch-events --config configs/default_universe.json --output data/events/us_stock_events.json
```
