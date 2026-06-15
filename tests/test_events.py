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
