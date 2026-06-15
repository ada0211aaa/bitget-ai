from __future__ import annotations

from .conservative_policy import attach_fill, evaluate_conservative_decision
from .events import NewsEvent
from .indicators import max_drawdown
from .models import BacktestResult, Candle, DecisionRecord, Trade
from .strategy import generate_signal


def backtest_symbol(
    symbol: str,
    candles: list[Candle],
    *,
    initial_cash: float,
    trade_fraction: float,
    fee_rate: float,
    macro_mode: str,
    news_bias: str,
    events: list[NewsEvent] | None = None,
) -> BacktestResult:
    cash = initial_cash
    quantity = 0.0
    trades: list[Trade] = []
    decision_records: list[DecisionRecord] = []
    equity_curve: list[float] = []
    last_signal = None

    for index, candle in enumerate(candles):
        history = candles[: index + 1]
        if len(history) >= 3:
            signal = generate_signal(symbol, history, macro_mode=macro_mode, news_bias=news_bias)
            last_signal = signal
            action = signal.action
            active_decision: DecisionRecord | None = None
            if events is not None:
                last_trade = trades[-1] if trades else None
                active_decision = evaluate_conservative_decision(
                    symbol,
                    history,
                    events,
                    has_position=quantity > 0,
                    last_action_timestamp_ms=last_trade.timestamp_ms if last_trade else None,
                    last_action_side=last_trade.side if last_trade else None,
                )
                action = active_decision.action
            if action == "buy" and cash > 0 and quantity == 0:
                spend = cash * trade_fraction
                fee = spend * fee_rate
                net_spend = spend - fee
                bought = net_spend / candle.close
                quantity += bought
                cash -= spend
                trades.append(Trade(candle.timestamp_ms, symbol, "buy", candle.close, bought, fee, signal.view, signal.reasons))
                if active_decision is not None:
                    decision_records.append(attach_fill(active_decision, quantity=bought, fee=fee))
            elif action == "sell" and quantity > 0:
                gross = quantity * candle.close
                fee = gross * fee_rate
                cash += gross - fee
                trades.append(Trade(candle.timestamp_ms, symbol, "sell", candle.close, quantity, fee, signal.view, signal.reasons))
                if active_decision is not None:
                    decision_records.append(attach_fill(active_decision, quantity=quantity, fee=fee))
                quantity = 0.0
            elif active_decision is not None:
                decision_records.append(active_decision)
        equity_curve.append(cash + quantity * candle.close)

    if last_signal is None:
        last_signal = generate_signal(symbol, candles, macro_mode=macro_mode, news_bias=news_bias)

    final_equity = equity_curve[-1] if equity_curve else initial_cash
    total_return = final_equity / initial_cash - 1.0
    return BacktestResult(
        symbol=symbol,
        initial_cash=initial_cash,
        final_equity=final_equity,
        total_return=total_return,
        max_drawdown=max_drawdown(equity_curve),
        equity_curve=tuple(equity_curve),
        trades=tuple(trades),
        last_signal=last_signal,
        decision_records=tuple(decision_records),
    )
