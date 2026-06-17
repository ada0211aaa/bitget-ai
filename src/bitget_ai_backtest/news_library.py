from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from .events import NewsEvent, load_events


def write_news_library(root_dir: Path, events: Iterable[NewsEvent], *, fetched_at: str | None = None) -> dict[str, Path]:
    fetched_at = fetched_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    grouped: dict[str, list[NewsEvent]] = {}
    for event in events:
        grouped.setdefault(event.symbol.upper(), []).append(event)

    written: dict[str, Path] = {}
    for symbol, rows in grouped.items():
        rows.sort(key=lambda event: (event.published_at, event.event_id))
        symbol_dir = root_dir / symbol
        raw_path = symbol_dir / "raw" / "events.json"
        ai_path = symbol_dir / "ai-events" / "events.json"
        coverage_path = symbol_dir / "coverage.json"

        raw_events: list[dict] = []
        ai_events: list[dict] = []
        for event in rows:
            payload = asdict(event)
            payload["fetched_at"] = fetched_at
            raw_events.append(payload)
            ai_events.append(payload)

        raw_path.parent.mkdir(parents=True, exist_ok=True)
        ai_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(json.dumps({"events": raw_events}, indent=2, ensure_ascii=False), encoding="utf-8")
        ai_path.write_text(json.dumps({"events": ai_events}, indent=2, ensure_ascii=False), encoding="utf-8")

        start_date = rows[0].published_at[:10] if rows else ""
        end_date = rows[-1].published_at[:10] if rows else ""
        coverage = {
            "symbol": symbol,
            "event_count": len(rows),
            "start_date": start_date,
            "end_date": end_date,
            "coverage": f"{start_date} -> {end_date}" if start_date and end_date else "",
            "fetched_at": fetched_at,
        }
        coverage_path.write_text(json.dumps(coverage, indent=2, ensure_ascii=False), encoding="utf-8")
        written[symbol] = symbol_dir
    return written


def read_news_library(root_dir: Path, symbols: tuple[str, ...]) -> list[NewsEvent]:
    events: list[NewsEvent] = []
    for symbol in symbols:
        path = root_dir / symbol.upper() / "ai-events" / "events.json"
        if path.exists():
            events.extend(load_events(path))
    events.sort(key=lambda event: (event.symbol, event.published_at, event.event_id))
    return events


def read_news_coverage(root_dir: Path, symbols: tuple[str, ...]) -> dict[str, dict]:
    coverage: dict[str, dict] = {}
    for symbol in symbols:
        normalized = symbol.upper()
        path = root_dir / normalized / "coverage.json"
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                coverage[normalized] = raw
                continue
        coverage[normalized] = {
            "symbol": normalized,
            "event_count": 0,
            "start_date": "",
            "end_date": "",
            "coverage": "",
            "fetched_at": "",
        }
    return coverage
