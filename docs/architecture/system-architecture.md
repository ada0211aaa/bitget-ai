# System Architecture

The current version is not a running service. It is a backtest-only Bitget Playbook strategy project with a small local Python CLI for public-data backtesting.

Main layers:

1. Presentation layer: README, requirements, devlog, showcase materials.
2. Strategy orchestration layer: strategy rules, signal scoring, risk filters, five-view output.
3. Bitget service layer: Playbook, Agent Hub skills, and public stock USDT perpetual candle data.
4. Data and record layer: local backtest reports, trade CSVs, Playbook records, signal snapshots, devlog links.
5. Infrastructure layer: secrets policy, session recaps, verification checklist, future scheduler boundary.

No live trading, Web/API service, database, notification service, or scheduler is included.
