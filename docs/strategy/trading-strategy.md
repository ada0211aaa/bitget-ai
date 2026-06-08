# Trading Strategy

Strategy theme: daily AI tech stock USDT perpetual strategy.

Asset scope:

- Use Bitget-listed stock USDT perpetual contracts / stock futures.
- Examples use symbols such as `NVDAUSDT`, `MSFTUSDT`, `GOOGLUSDT`, `AMDUSDT`, and `METAUSDT`.
- Do not describe these assets as traditional US stock spot positions.
- The first version should focus on 20-30 AI/technology-related contracts rather than the full stock-contract list.

Candidate pool:

- `NVDAUSDT`
- `MSFTUSDT`
- `GOOGLUSDT`
- `AMDUSDT`
- `METAUSDT`

Actual assets depend on Bitget and Playbook support.

Decision flow:

```text
Collect daily signals
-> hard risk filters
-> score news, macro, technical, event, sentiment, and market-intel signals
-> output one of five views
-> use Playbook for backtest and publishing
```
