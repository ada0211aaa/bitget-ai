from bitget_ai_backtest.events import NewsEvent
from bitget_ai_backtest.explanations import explain_trades
from bitget_ai_backtest.models import BacktestResult, StrategySignal, Trade


def test_explain_trades_matches_only_prior_events_inside_24_hours() -> None:
    trade = Trade(
        timestamp_ms=1_800_000_000,
        symbol="NVDAUSDT",
        side="buy",
        price=200.0,
        quantity=1.0,
        fee=0.1,
        reason="cautiously_bullish",
    )
    result = BacktestResult(
        symbol="NVDAUSDT",
        initial_cash=10000.0,
        final_equity=10020.0,
        total_return=0.002,
        max_drawdown=-0.001,
        equity_curve=(10000.0, 10020.0),
        trades=(trade,),
        last_signal=StrategySignal(
            symbol="NVDAUSDT",
            timestamp_ms=trade.timestamp_ms,
            score=2,
            view="cautiously_bullish",
            action="buy",
            close=200.0,
            reasons=("trend_up", "news_bullish", "macro_neutral"),
        ),
    )
    events = [
        NewsEvent(
            event_id="matched",
            symbol="NVDAUSDT",
            published_at="1970-01-21T19:30:00Z",
            title="Nvidia raises guidance on AI demand",
            source_name="Bitget news-briefing",
            source_type="bitget_news_briefing",
            url="https://example.com/matched",
            sentiment="bullish",
            confidence=0.7,
            reason="Matched bullish keyword: raises guidance",
        ),
        NewsEvent(
            event_id="future",
            symbol="NVDAUSDT",
            published_at="1970-01-21T21:00:00Z",
            title="Future news should not leak",
            source_name="Bitget news-briefing",
            source_type="bitget_news_briefing",
            url="https://example.com/future",
            sentiment="bullish",
            confidence=0.7,
            reason="future",
        ),
        NewsEvent(
            event_id="old",
            symbol="NVDAUSDT",
            published_at="1970-01-20T18:00:00Z",
            title="Old news should expire",
            source_name="Bitget news-briefing",
            source_type="bitget_news_briefing",
            url="https://example.com/old",
            sentiment="bullish",
            confidence=0.7,
            reason="old",
        ),
    ]

    explanations = explain_trades([result], events, window_hours=24)

    assert len(explanations) == 1
    explanation = explanations[0]
    assert explanation["matched_events"] == ["matched"]
    assert explanation["news_score"] == 1
    assert "Nvidia raises guidance" in explanation["explanation"]
    assert explanation["technical_reasons"] == ["trend_up", "news_bullish", "macro_neutral"]
