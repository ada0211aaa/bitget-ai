from pathlib import Path

from bitget_ai_backtest.events import (
    NewsEvent,
    PUBLIC_SOURCE_TYPE,
    deduplicate_events,
    events_for_symbol,
    load_events,
    score_event_sentiment,
    write_events,
)


def test_score_event_sentiment_uses_explainable_keywords() -> None:
    bullish = score_event_sentiment("Nvidia raises guidance as AI demand accelerates")
    bearish = score_event_sentiment("AMD faces export restriction and analyst downgrade")
    neutral = score_event_sentiment("Microsoft announces annual shareholder meeting")

    assert bullish.sentiment == "bullish"
    assert "raises guidance" in bullish.reason
    assert bearish.sentiment == "bearish"
    assert "export restriction" in bearish.reason
    assert neutral.sentiment == "neutral"
    assert neutral.reason == "No bullish or bearish keyword matched"


def test_write_and_load_events_round_trip_with_deduplication(tmp_path: Path) -> None:
    events = [
        NewsEvent(
            event_id="NVDA-1",
            symbol="NVDAUSDT",
            published_at="2026-06-01T10:00:00Z",
            title="Nvidia raises guidance on AI demand",
            source_name="Bitget news-briefing",
            source_type="bitget_news_briefing",
            url="https://example.com/nvda",
            sentiment="bullish",
            confidence=0.7,
            reason="Matched bullish keyword: raises guidance",
        ),
        NewsEvent(
            event_id="NVDA-2",
            symbol="NVDAUSDT",
            published_at="2026-06-01T12:00:00Z",
            title="Nvidia raises guidance on AI demand",
            source_name="Public news fallback",
            source_type="public_news_fallback",
            url="https://example.com/nvda",
            sentiment="bullish",
            confidence=0.7,
            reason="Duplicate should be removed",
        ),
    ]
    output = tmp_path / "events.json"

    write_events(output, deduplicate_events(events))

    loaded = load_events(output)
    assert len(loaded) == 1
    assert loaded[0].event_id == "NVDA-1"
    assert loaded[0].source_type == "bitget_news_briefing"


def test_load_events_defaults_ai_judgment_fields_for_legacy_files(tmp_path: Path) -> None:
    output = tmp_path / "events.json"
    output.write_text(
        """
{
  "events": [
    {
      "event_id": "legacy",
      "symbol": "NVDAUSDT",
      "published_at": "2026-06-01T10:00:00Z",
      "title": "Nvidia raises guidance on AI demand",
      "source_name": "Bitget news-briefing",
      "source_type": "bitget_news_briefing",
      "url": "https://example.com/nvda",
      "sentiment": "bullish",
      "confidence": 0.8,
      "reason": "Matched bullish keyword: raises guidance"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    loaded = load_events(output)

    assert loaded[0].strength == "strong"
    assert loaded[0].topic == "unknown"
    assert loaded[0].time_horizon == "short_term"
    assert loaded[0].stock_relevance == "direct"


def test_bitget_skill_exports_preserve_ai_judgment_fields(tmp_path: Path) -> None:
    from bitget_ai_backtest.config import BacktestConfig
    from bitget_ai_backtest.events import collect_events

    skill_dir = tmp_path / "bitget-skills"
    skill_dir.mkdir()
    (skill_dir / "news.json").write_text(
        """
{
  "events": [
    {
      "event_id": "ai-news",
      "symbol": "NVDAUSDT",
      "published_at": "2026-06-01T10:00:00Z",
      "title": "Nvidia raises guidance on AI demand",
      "source_name": "Bitget news-briefing",
      "source_type": "bitget_news_briefing",
      "url": "https://example.com/nvda",
      "sentiment": "bullish",
      "confidence": 0.82,
      "reason": "Bitget AI judges the guidance raise as strong and directly relevant.",
      "strength": "strong",
      "topic": "earnings_guidance",
      "time_horizon": "medium_term",
      "stock_relevance": "direct"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    config = BacktestConfig(
        symbols=("NVDAUSDT",),
        granularity="1d",
        limit=100,
        initial_cash=10000,
        trade_fraction=0.25,
        fee_rate=0.0006,
        macro_mode="neutral",
        news_bias="neutral",
    )

    events = collect_events(config, skill_export_dir=skill_dir)

    assert len(events) == 1
    assert events[0].strength == "strong"
    assert events[0].topic == "earnings_guidance"
    assert events[0].time_horizon == "medium_term"
    assert events[0].stock_relevance == "direct"


def test_events_for_symbol_filters_case_insensitively() -> None:
    events = [
        NewsEvent("a", "NVDAUSDT", "2026-06-01T10:00:00Z", "a", "s", "bitget_news_briefing", "", "neutral", 0.5, "r"),
        NewsEvent("b", "MSFTUSDT", "2026-06-01T10:00:00Z", "b", "s", "bitget_news_briefing", "", "neutral", 0.5, "r"),
    ]

    assert [event.event_id for event in events_for_symbol(events, "nvdautdt")] == []
    assert [event.event_id for event in events_for_symbol(events, "nvdAUSDT")] == ["a"]


def test_events_for_symbol_filters_public_feed_noise_but_keeps_bitget_signals() -> None:
    events = [
        NewsEvent(
            "noise",
            "NVDAUSDT",
            "2026-06-01T10:00:00Z",
            "Bitcoin Could Be 50% Undervalued. Should You Buy It Right Now?",
            "Yahoo Finance RSS",
            PUBLIC_SOURCE_TYPE,
            "https://example.com/bitcoin",
            "neutral",
            0.5,
            "No bullish or bearish keyword matched",
        ),
        NewsEvent(
            "nvda",
            "NVDAUSDT",
            "2026-06-01T10:15:00Z",
            "Can Robots Rescue Nvidia Stock?",
            "Yahoo Finance RSS",
            PUBLIC_SOURCE_TYPE,
            "https://example.com/nvidia",
            "neutral",
            0.5,
            "No bullish or bearish keyword matched",
        ),
        NewsEvent(
            "bitget",
            "NVDAUSDT",
            "2026-06-01T10:30:00Z",
            "Structured NVDA signal from Bitget Agent Hub",
            "Bitget news-briefing",
            "bitget_news_briefing",
            "",
            "neutral",
            0.5,
            "Bitget skill export",
        ),
    ]

    assert [event.event_id for event in events_for_symbol(events, "NVDAUSDT")] == ["nvda", "bitget"]


def test_events_for_symbol_recognizes_common_stock_aliases() -> None:
    events = [
        NewsEvent(
            "apple",
            "AAPLUSDT",
            "2026-06-01T10:00:00Z",
            "Apple shares rise after iPhone demand improves",
            "Yahoo Finance RSS",
            PUBLIC_SOURCE_TYPE,
            "https://example.com/apple",
            "bullish",
            0.7,
            "Matched bullish keyword: strong demand",
        ),
        NewsEvent(
            "tesla",
            "TSLAUSDT",
            "2026-06-01T10:00:00Z",
            "Tesla stock slips after delivery downgrade",
            "Yahoo Finance RSS",
            PUBLIC_SOURCE_TYPE,
            "https://example.com/tesla",
            "bearish",
            0.7,
            "Matched bearish keyword: downgrade",
        ),
    ]

    assert [event.event_id for event in events_for_symbol(events, "AAPLUSDT")] == ["apple"]
    assert [event.event_id for event in events_for_symbol(events, "TSLAUSDT")] == ["tesla"]
