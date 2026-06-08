# Folder Structure

The first confirmed requirements phase used documentation folders only. The implementation phase now adds a small local backtest CLI while keeping live trading, Web/API, notifications, and schedulers out of scope.

```text
configs/
├── default_universe.json
│
src/
└── bitget_ai_backtest/
    ├── cli.py
    ├── config.py
    ├── bitget_client.py
    ├── indicators.py
    ├── strategy.py
    ├── backtester.py
    ├── reporting.py
    └── models.py
│
tests/
├── fixtures/
└── test_*.py
│
reports/
├── local-demo/
└── latest/
│
docs/
├── architecture/
├── bitget-skills/
├── strategy/
├── playbook/
├── devlog/
├── security/
├── requirements/
└── ai-sessions/
```

No API keys, live execution engine, Web/API service, notification service, database, or scheduler is included.
