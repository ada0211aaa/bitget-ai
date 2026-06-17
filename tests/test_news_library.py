import json
from pathlib import Path

from bitget_ai_backtest.events import NewsEvent
from bitget_ai_backtest.news_library import read_news_library, write_news_library


def _event(event_id: str, symbol: str, published_at: str) -> NewsEvent:
    return NewsEvent(
        event_id=event_id,
        symbol=symbol,
        published_at=published_at,
        title=f"{symbol} raises guidance",
        source_name="Yahoo Finance RSS",
        source_type="public_news_fallback",
        url=f"https://example.com/{event_id}",
        sentiment="bullish",
        confidence=0.7,
        reason="Matched bullish keyword: raises guidance",
        strength="strong",
        topic="earnings_guidance",
        time_horizon="medium_term",
        stock_relevance="direct",
    )


def test_write_news_library_groups_events_by_symbol_and_writes_coverage(tmp_path: Path) -> None:
    write_news_library(
        tmp_path,
        [
            _event("amd-1", "AMDUSDT", "2026-06-01T13:00:00Z"),
            _event("amd-2", "AMDUSDT", "2026-06-03T13:00:00Z"),
            _event("nvda-1", "NVDAUSDT", "2026-06-02T13:00:00Z"),
        ],
        fetched_at="2026-06-17T09:00:00Z",
    )

    amd_raw = json.loads((tmp_path / "AMDUSDT" / "raw" / "events.json").read_text(encoding="utf-8"))
    amd_ai = json.loads((tmp_path / "AMDUSDT" / "ai-events" / "events.json").read_text(encoding="utf-8"))
    coverage = json.loads((tmp_path / "AMDUSDT" / "coverage.json").read_text(encoding="utf-8"))

    assert [row["event_id"] for row in amd_raw["events"]] == ["amd-1", "amd-2"]
    assert amd_raw["events"][0]["fetched_at"] == "2026-06-17T09:00:00Z"
    assert amd_ai["events"][0]["strength"] == "strong"
    assert coverage == {
        "symbol": "AMDUSDT",
        "event_count": 2,
        "start_date": "2026-06-01",
        "end_date": "2026-06-03",
        "coverage": "2026-06-01 -> 2026-06-03",
        "fetched_at": "2026-06-17T09:00:00Z",
    }


def test_read_news_library_returns_events_for_config_symbols(tmp_path: Path) -> None:
    write_news_library(
        tmp_path,
        [
            _event("amd-1", "AMDUSDT", "2026-06-01T13:00:00Z"),
            _event("nvda-1", "NVDAUSDT", "2026-06-02T13:00:00Z"),
        ],
        fetched_at="2026-06-17T09:00:00Z",
    )

    events = read_news_library(tmp_path, ("AMDUSDT",))

    assert [event.event_id for event in events] == ["amd-1"]
