# AI Tech Stock News Signal

## 策略

This Playbook is a signal-only strategy for Bitget-listed stock-linked USDT
perpetual contracts, starting with NVDAUSDT. It is built for the US Stock AI
Trading track: the idea is to combine price trend confirmation with a
news-aware operating style, while keeping the first version deterministic
enough for historical Playbook backtesting.

The current package keeps the historical replay path simple. It uses Bitget
contract candles through the managed Playbook data layer and turns price action
into a cautious long-or-watch signal. News and macro context remain part of the
strategy philosophy and documentation, but the replayable first version does
not use open-ended live LLM reasoning, because that would make a fair historical
backtest hard to reproduce.

## 开仓

The Playbook opens a long signal only when the shorter trend read has clearly
recovered above the slower trend read. This is meant to avoid buying every small
headline move. The strategy waits for confirmation from price action, then emits
an actionable long signal if the historical replay supports the idea.

It does not open short positions in this first version. If the signal is not
clear, it emits watch instead of forcing a trade.

## 平仓

The Playbook closes or retracts the long view when the shorter trend read fades
back below the slower trend read. That means the strategy treats a loss of
momentum as the exit condition. There is no separate live stop loss or take
profit path in this package, because this first version is not allowed to place
orders and is intended for backtest evidence only.

## 参数说明

Subscribers and reviewers should read the package as a conservative demo:

- **trading_symbols** controls which stock-linked contract is replayed.
- **margin_budget** is the strategy-level budget denominator used by the
  platform when it normalizes performance.

The code reads these values from the Playbook manifest so future iterations can
adjust the symbol or budget without changing the whole package shape.

## 回测指标如何读

The Playbook API run can return `total_return_pct`, `max_drawdown_pct`,
`sharpe_ratio`, `win_rate`, and `total_trades`. Treat these as evidence that
the package can run through Bitget Playbook, not as proof that the strategy is
ready for live money.

## 风险

This strategy can underperform when a stock-linked contract chops sideways,
when a major earnings or macro headline gaps through the trend signal, or when
liquidity around tokenized stock contracts is thin. The first version is
deliberately signal-only and backtest-first. It should not be enabled for live
follow trading without a separate approved implementation plan.
