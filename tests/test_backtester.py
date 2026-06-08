from bitget_ai_backtest.backtester import backtest_symbol
from bitget_ai_backtest.models import Candle


def _candles(values: list[float]) -> list[Candle]:
    return [
        Candle(
            timestamp_ms=1000 + index,
            open=value,
            high=value + 1,
            low=value - 1,
            close=value,
            volume=1000,
            quote_volume=1000 * value,
        )
        for index, value in enumerate(values)
    ]


def test_backtest_symbol_generates_equity_curve_and_metrics() -> None:
    result = backtest_symbol(
        "NVDAUSDT",
        _candles([100, 101, 102, 103, 104, 105, 106, 107]),
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_on",
        news_bias="bullish",
    )

    assert result.symbol == "NVDAUSDT"
    assert result.final_equity > 10000
    assert result.total_return > 0
    assert len(result.equity_curve) == 8
    assert result.trades


def test_backtest_symbol_does_not_repeat_buy_when_already_long() -> None:
    result = backtest_symbol(
        "NVDAUSDT",
        _candles([100, 101, 102, 103, 104, 105, 106, 107]),
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_on",
        news_bias="bullish",
    )

    assert [trade.side for trade in result.trades] == ["buy"]


def test_backtest_symbol_stays_in_cash_when_macro_blocks_bullish_news() -> None:
    result = backtest_symbol(
        "NVDAUSDT",
        _candles([100, 101, 102, 103, 104, 105, 106, 107]),
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_off",
        news_bias="bullish",
    )

    assert result.final_equity == 10000
    assert result.trades == ()
