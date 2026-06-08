# technical-analysis

Purpose: confirm whether price action supports the news and macro view.

Data scope:

- For the US stock track, use Bitget-listed stock USDT perpetual contract K-lines when available, for example `NVDAUSDT` or `AAPLUSDT`.
- This is contract market data, not traditional US stock spot-market data.
- `15m` K-lines can be used as a technical confirmation input when supported by the Bitget market endpoint / Playbook flow.

First-version focus:

- Trend direction.
- Moving averages / EMA.
- RSI.
- MACD.
- Volatility / ATR.
- Volume or VWAP when available.

Technical analysis is a confirmation layer. Good news without trend confirmation should usually stay neutral or cautiously bullish, not strongly bullish.
