# Bitget Skill Exports

Place sanitized local exports from Bitget Agent Hub skills here when available.

Accepted event `source_type` values:

- `bitget_news_briefing`
- `bitget_macro_analyst`
- `bitget_sentiment_analyst`
- `bitget_technical_analysis`
- `bitget_market_intel`

The `fetch-events` command reads JSON files in this directory before using public news fallback sources.

Do not store API keys, account identifiers, balances, positions, orders, or raw private account snapshots here. JSON files in this directory are ignored by git by default.
