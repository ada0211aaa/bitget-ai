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


def daily_trend_history(ts: int = BASE_TS, *, latest_close: float = 165.0) -> list[Candle]:
    values = [100 + index * 0.2 + (1.0 if index % 2 == 0 else -0.5) for index in range(60)]
    return [candle(ts + index * 86_400_000, value) for index, value in enumerate(values)]


def daily_flat_then_spike_history(ts: int = BASE_TS) -> list[Candle]:
    values = [100.0] * 55 + [115.0, 130.0, 145.0, 160.0, 180.0]
    return [candle(ts + index * 86_400_000, value) for index, value in enumerate(values)]


def daily_weak_trend_history(ts: int = BASE_TS) -> list[Candle]:
    values = [120.0] * 40 + [95.0] * 20
    return [candle(ts + index * 86_400_000, value) for index, value in enumerate(values)]


def daily_drop_below_ma50_history(ts: int = BASE_TS) -> list[Candle]:
    values = [120.0] * 55 + [100.0, 96.0, 92.0, 88.0, 84.0]
    return [candle(ts + index * 86_400_000, value) for index, value in enumerate(values)]


def event(
    event_id: str,
    *,
    sentiment: str,
    title: str,
    confidence: float = 0.8,
    url: str = "https://example.com/news",
    published_at: str = "1970-01-21T20:00:00Z",
    reason: str = "Matched bullish keyword: raises guidance",
    strength: str = "",
    topic: str = "unknown",
    time_horizon: str = "short_term",
    stock_relevance: str = "direct",
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
        strength=strength,
        topic=topic,
        time_horizon=time_horizon,
        stock_relevance=stock_relevance,
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


def test_structured_news_fields_are_written_to_decision() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        bullish_history(),
        [
            event(
                "strong",
                sentiment="bullish",
                title="Nvidia raises guidance on AI demand",
                strength="strong",
                topic="earnings_guidance",
                time_horizon="medium_term",
                stock_relevance="direct",
            )
        ],
        has_position=False,
    )

    assert decision.news_topic == "earnings_guidance"
    assert decision.news_time_horizon == "medium_term"
    assert decision.stock_relevance == "direct"


def test_daily_ma20_ma50_confirmation_buys_on_strong_direct_bullish_news() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_trend_history(),
        [
            event(
                "strong",
                sentiment="bullish",
                title="Nvidia raises guidance on AI demand",
                strength="strong",
                published_at="1970-03-21T23:00:00Z",
            )
        ],
        has_position=False,
    )

    assert decision.action == "buy"
    assert decision.technical_confirmation == "已确认"
    assert "ma20_above_ma50" in decision.technical_reasons
    assert "price_above_ma50" in decision.technical_reasons


def test_daily_news_window_carries_weekend_events_into_next_session() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_trend_history(),
        [
            event(
                "friday-after-close",
                sentiment="bullish",
                title="Nvidia raises guidance on AI demand",
                strength="strong",
                published_at="1970-03-19T20:00:00Z",
            )
        ],
        has_position=False,
    )

    assert decision.action == "buy"
    assert decision.event_id == "friday-after-close"


def test_daily_news_window_allows_same_day_news_after_daily_bar_timestamp() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_trend_history(),
        [
            event(
                "same-day-news",
                sentiment="bullish",
                title="Nvidia raises guidance on AI demand",
                strength="strong",
                published_at="1970-03-21T23:00:00Z",
            )
        ],
        has_position=False,
    )

    assert decision.action == "buy"
    assert decision.event_id == "same-day-news"


def test_daily_strategy_does_not_chase_when_rsi_is_overheated() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_flat_then_spike_history(),
        [
            event(
                "strong",
                sentiment="bullish",
                title="Nvidia raises guidance on AI demand",
                strength="strong",
                published_at="1970-03-21T20:00:00Z",
            )
        ],
        has_position=False,
    )

    assert decision.action == "observe"
    assert decision.technical_confirmation == "未确认"
    assert "rsi_overheated" in decision.technical_reasons
    assert "避免追高" in decision.decision_reason


def test_daily_strategy_observes_when_ma20_is_below_ma50() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_weak_trend_history(),
        [
            event(
                "strong",
                sentiment="bullish",
                title="Nvidia raises guidance on AI demand",
                strength="strong",
                published_at="1970-03-21T20:00:00Z",
            )
        ],
        has_position=False,
    )

    assert decision.action == "observe"
    assert decision.technical_confirmation == "未确认"
    assert "ma20_below_ma50" in decision.technical_reasons


def test_daily_strategy_sells_when_price_breaks_below_ma50() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_drop_below_ma50_history(),
        [],
        has_position=True,
    )

    assert decision.action == "sell"
    assert "price_below_ma50" in decision.technical_reasons
    assert "跌破 MA50" in decision.decision_reason


def test_daily_strategy_sells_when_drawdown_from_position_high_reaches_twelve_percent() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_trend_history(latest_close=110),
        [],
        has_position=True,
        position_high_price=130,
    )

    assert decision.action == "sell"
    assert "trailing_drawdown_12pct" in decision.technical_reasons
    assert "回撤达到 12%" in decision.decision_reason


def test_aggressive_news_mode_buys_on_bullish_news_with_acceptable_daily_trend() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_trend_history(),
        [
            event(
                "bullish",
                sentiment="bullish",
                title="Nvidia shares rise after analyst upgrade",
                confidence=0.62,
                reason="Matched bullish keyword: upgrade",
                published_at="1970-03-21T20:00:00Z",
            )
        ],
        has_position=False,
        decision_mode="aggressive_news",
    )

    assert decision.action == "buy"
    assert decision.news_strength == "利好"
    assert decision.news_direction == "看多"
    assert "激进新闻模式" in decision.decision_reason


def test_aggressive_news_mode_still_does_not_buy_without_news() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_trend_history(),
        [],
        has_position=False,
        decision_mode="aggressive_news",
    )

    assert decision.action == "observe"
    assert decision.news_strength == "无新闻"
    assert "没有足够新闻门票" in decision.decision_reason


def test_aggressive_news_mode_sells_on_bearish_news_even_before_ma50_break() -> None:
    decision = evaluate_conservative_decision(
        "NVDAUSDT",
        daily_trend_history(),
        [
            event(
                "bearish",
                sentiment="bearish",
                title="Nvidia slips after analyst downgrade",
                confidence=0.62,
                reason="Matched bearish keyword: downgrade",
                published_at="1970-03-21T20:00:00Z",
            )
        ],
        has_position=True,
        decision_mode="aggressive_news",
    )

    assert decision.action == "sell"
    assert decision.news_strength == "利空"
    assert decision.news_direction == "看空"
    assert "激进新闻模式" in decision.decision_reason
