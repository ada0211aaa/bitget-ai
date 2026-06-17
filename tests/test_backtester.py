from bitget_ai_backtest.backtester import backtest_symbol
from bitget_ai_backtest.events import NewsEvent
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


def _daily_candles(values: list[float]) -> list[Candle]:
    return [
        Candle(
            timestamp_ms=1_800_000_000 + index * 86_400_000,
            open=value,
            high=value,
            low=value,
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


def test_backtest_symbol_sells_on_twelve_percent_drawdown_after_news_buy() -> None:
    values = [100 + index * 0.2 + (1.0 if index % 2 == 0 else -0.5) for index in range(60)]
    values.extend([120, 130, 114])
    events = [
        NewsEvent(
            event_id="strong-buy",
            symbol="NVDAUSDT",
            published_at="1970-03-21T20:00:00Z",
            title="Nvidia raises guidance on AI demand",
            source_name="Bitget news-briefing",
            source_type="bitget_news_briefing",
            url="https://example.com/nvda",
            sentiment="bullish",
            confidence=0.82,
            reason="Bitget AI judges this as strong.",
            strength="strong",
            topic="earnings_guidance",
            time_horizon="medium_term",
            stock_relevance="direct",
        )
    ]

    result = backtest_symbol(
        "NVDAUSDT",
        _daily_candles(values),
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="neutral",
        news_bias="neutral",
        events=events,
    )

    assert [trade.side for trade in result.trades] == ["buy", "sell"]
    assert [record.action for record in result.decision_records if record.action in {"buy", "sell"}] == ["buy", "sell"]
    assert "trailing_drawdown_12pct" in result.decision_records[-1].technical_reasons


def test_backtest_symbol_aggressive_news_mode_creates_news_driven_trade() -> None:
    values = [100 + index * 0.2 + (1.0 if index % 2 == 0 else -0.5) for index in range(60)]
    events = [
        NewsEvent(
            event_id="bullish-buy",
            symbol="NVDAUSDT",
            published_at="1970-03-21T20:00:00Z",
            title="Nvidia shares rise after analyst upgrade",
            source_name="Yahoo Finance RSS",
            source_type="public_news_fallback",
            url="https://example.com/nvda-upgrade",
            sentiment="bullish",
            confidence=0.62,
            reason="Matched bullish keyword: upgrade",
            strength="",
            topic="ai_demand",
            time_horizon="medium_term",
            stock_relevance="direct",
        )
    ]

    result = backtest_symbol(
        "NVDAUSDT",
        _daily_candles(values),
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="neutral",
        news_bias="neutral",
        events=events,
        decision_mode="aggressive_news",
    )

    assert [trade.side for trade in result.trades] == ["buy"]
    buy_records = [record for record in result.decision_records if record.action == "buy"]
    assert buy_records
    assert buy_records[0].event_id == "bullish-buy"
    assert "激进新闻模式" in buy_records[0].decision_reason
