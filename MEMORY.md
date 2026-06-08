# Project Memory

## Current Project Direction

- This repository is for the Bitget AI Base Camp Hackathon S1, US Stock AI Trading track.
- The first version is documentation-first and Bitget-native.
- Use Bitget Playbook first for natural-language strategy creation, backtesting, publishing, and metrics.
- Use Bitget Agent Hub official skills first for market signals:
  - `news-briefing`
  - `macro-analyst`
  - `technical-analysis`
  - `sentiment-analyst`
  - `market-intel`

## Confirmed Strategy Preferences

- Strategy theme: AI tech stocks / tokenized US stock assets.
- Candidate pool: NVDA, MSFT, GOOGL, AMD, META, with actual assets constrained by Playbook support.
- Cadence: daily strategy, not high-frequency news sniping.
- Decision style: hard risk filters first, scoring second.
- Priority: avoid big mistakes and downside first, not chase every rally.
- Output style: five natural-language views: bullish, cautiously bullish, neutral/observe, cautiously bearish, bearish.

## Safety Rules

- Do not commit real Playbook API keys, Bitget API keys, secrets, passphrases, private keys, account IDs, or full account snapshots.
- Do not implement live trading, automatic order placement, scheduled jobs, background tasks, or notifications without explicit user approval.
- First-version evidence must be backtest or simulation records only.

## Known Gaps

- Need actual Playbook access and a real backtest before final hackathon submission.
- Need to refine signal weights, thresholds, and mapping from scores to the five output views.
- Need to create the documentation folder skeleton described in the requirements document.
