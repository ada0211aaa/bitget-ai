# Trading Strategy

Strategy theme: daily AI tech stock / tokenized US stock strategy.

Candidate pool:

- NVDA
- MSFT
- GOOGL
- AMD
- META

Actual assets depend on Bitget Playbook support.

Decision flow:

```text
Collect daily signals
-> hard risk filters
-> score news, macro, technical, event, sentiment, and market-intel signals
-> output one of five views
-> use Playbook for backtest and publishing
```
