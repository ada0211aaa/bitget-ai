from bitget_ai_backtest.conservative_policy import evaluate_conservative_decision
from bitget_ai_backtest.events import NewsEvent
from bitget_ai_backtest.models import Candle


BASE_TS = 1_800_000_000


def candle(ts: int, close: float) -> Candle:
    return Candle(ts, close, close, close, close, 100, 100)


def bullish_history(ts: int = BASE_TS) -> list[Candle]:
    return [
        candle(ts - 240_000, 100),
        candle(ts - 180_000, 99),
        candle(ts - 120_000, 101),
        candle(ts - 60_000, 100),
        candle(ts, 102),
    ]


def bearish_history(ts: int = BASE_TS) -> list[Candle]:
    return [
        candle(ts - 240_000, 104),
        candle(ts - 180_000, 103),
        candle(ts - 120_000, 102),
        candle(ts - 60_000, 101),
        candle(ts, 100),
    ]


def event(
    event_id: str,
    *,
    sentiment: str,
    title: str,
    confidence: float = 0.8,
    url: str = "https://example.com/news",
    published_at: str = "1970-01-21T20:00:00Z",
    reason: str = "Matched bullish keyword: raises guidance",
) -> NewsEvent:
    return NewsEvent(
        event_id=event_id,
        symbol="NVDAUSDT",
        published_at=published_at,
        title=title,
        source_name="Bitget news-briefing",
        source_type="bitget_news_briefing",
        url=url,
        sentiment=sentiment,
        confidence=confidence,
        reason=reason,
    )


def test_strong_bullish_news_plus_technical_confirmation_buys() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        bullish_history(),
        [event("strong", sentiment="bullish", title="Nvidia raises guidance on AI demand")],
        has_position=False,
    )

    assert decision.action == "buy"
    assert decision.news_strength == "强利好"
    assert decision.news_direction == "看多"
    assert decision.technical_confirmation == "已确认"
    assert decision.cooldown_state == "可交易"
    assert decision.news_url == "https://example.com/news"
    assert "强利好新闻成立" in decision.decision_reason


def test_bullish_but_not_strong_news_observes() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        bullish_history(),
        [event("weak", sentiment="bullish", title="Nvidia shares edge higher", confidence=0.6, reason="generic bullish")],
        has_position=False,
    )

    assert decision.action == "observe"
    assert decision.news_strength == "利好"
    assert "新闻不错但不够强" in decision.decision_reason


def test_strong_bullish_without_technical_confirmation_observes() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        bearish_history(),
        [event("strong", sentiment="bullish", title="Nvidia raises guidance on AI demand")],
        has_position=False,
    )

    assert decision.action == "observe"
    assert decision.news_strength == "强利好"
    assert decision.technical_confirmation == "未确认"
    assert "技术面未确认" in decision.decision_reason


def test_no_news_with_technical_confirmation_observes() -> None:
    decision = evaluate_conservative_decision("NVDAUSDT", bullish_history(), [], has_position=False)

    assert decision.action == "observe"
    assert decision.news_strength == "无新闻"
    assert decision.news_source_action == "无新闻来源"
    assert "没有足够新闻门票" in decision.decision_reason


def test_same_side_signal_inside_twelve_hour_cooldown_observes() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        bullish_history(),
        [event("strong", sentiment="bullish", title="Nvidia raises guidance on AI demand")],
        has_position=False,
        last_action_timestamp_ms=BASE_TS - 60 * 60 * 1000,
        last_action_side="buy",
    )

    assert decision.action == "observe"
    assert decision.cooldown_state == "冷却中"
    assert "12 小时冷却期" in decision.decision_reason


def test_strong_bearish_news_plus_technical_weakness_sells() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        bearish_history(),
        [
            event(
                "bear",
                sentiment="bearish",
                title="Nvidia cuts guidance after export restriction",
                reason="Matched bearish keyword: export restriction",
            )
        ],
        has_position=True,
    )

    assert decision.action == "sell"
    assert decision.news_strength == "强利空"
    assert decision.news_direction == "看空"
    assert decision.technical_confirmation == "已确认"
    assert "强利空新闻成立" in decision.decision_reason


def test_structured_signal_without_url_uses_detail_fallback() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        bullish_history(),
        [event("strong", sentiment="bullish", title="Nvidia raises guidance on AI demand", url="")],
        has_position=False,
    )

    assert decision.news_url == ""
    assert decision.news_source_action == "查看信号详情"
