from __future__ import annotations

from .indicators import max_drawdown
from .models import BacktestResult, Candle, Trade
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
) -> BacktestResult:
    cash = initial_cash
    quantity = 0.0
    trades: list[Trade] = []
    equity_curve: list[float] = []
    last_signal = None

    for index, candle in enumerate(candles):
        history = candles[: index + 1]
        if len(history) >= 3:
            signal = generate_signal(symbol, history, macro_mode=macro_mode, news_bias=news_bias)
            last_signal = signal
            if signal.action == "buy" and cash > 0 and quantity == 0:
                spend = cash * trade_fraction
                fee = spend * fee_rate
                net_spend = spend - fee
                bought = net_spend / candle.close
                quantity += bought
                cash -= spend
                trades.append(Trade(candle.timestamp_ms, symbol, "buy", candle.close, bought, fee, signal.view))
            elif signal.action == "sell" and quantity > 0:
                gross = quantity * candle.close
                fee = gross * fee_rate
                cash += gross - fee
                trades.append(Trade(candle.timestamp_ms, symbol, "sell", candle.close, quantity, fee, signal.view))
                quantity = 0.0
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
    )
