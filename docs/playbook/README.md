# Playbook Docs

This folder stores Playbook-facing materials and backtest records.

Do not write real Playbook API keys here.

## Current API Flow

The runnable Playbook package lives at `playbooks/ai-tech-stock-news-signal/`.

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli playbook-backtest --env .env --package-dir playbooks/ai-tech-stock-news-signal --output-dir reports/playbook --poll --poll-interval 5 --max-polls 20
```

The command uses the official Playbook API to upload a draft and run a backtest. It does not publish or enable live execution.
