# 30 Day News Library AI Decision Backtest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 30-day per-symbol news library flow so daily backtests use only pre-existing news, technical candidate days, and AI-structured news judgments.

**Architecture:** Add a small news-library layer that reuses existing `NewsEvent` and `collect_events`, then add a technical-candidate layer that runs before conservative decisions. Keep AI/news as structured evidence only; deterministic backtest logic still decides buy/sell/observe and remains backtest-only.

**Tech Stack:** Python standard library, existing CLI, existing vanilla JS dashboard, pytest.

---

## File Structure

- Create `src/bitget_ai_backtest/news_library.py`: write/read per-symbol raw events, AI event files, and coverage metadata under `data/news/<SYMBOL>/`.
- Create `src/bitget_ai_backtest/technical_candidates.py`: compute daily technical candidate rows from candles and current position state.
- Modify `src/bitget_ai_backtest/cli.py`: add `fetch-news-library`; add `--news-library` to `backtest` and `web`; write candidate and news coverage outputs.
- Modify `src/bitget_ai_backtest/reporting.py`: write `technical-candidates.json`, `news-coverage.json`, and `candidate-markers.json`.
- Modify `src/bitget_ai_backtest/web.py`: include news-library coverage and technical candidates in dashboard payload.
- Modify `src/bitget_ai_backtest/static/index.html`: add sections/headers for news coverage, candidate list, and no-trade reason.
- Modify `src/bitget_ai_backtest/static/app.js`: render coverage, candidates, and separate candidate markers on the chart.
- Modify tests:
  - `tests/test_news_library.py`
  - `tests/test_technical_candidates.py`
  - `tests/test_cli.py`
  - `tests/test_reporting.py`
  - `tests/test_web.py`
  - `tests/test_static_dashboard_ui.py`

## Task 1: News Library Persistence

**Files:**
- Create: `src/bitget_ai_backtest/news_library.py`
- Test: `tests/test_news_library.py`

- [ ] **Step 1: Add failing tests for writing a per-symbol news library**

Create `tests/test_news_library.py` with:

```python
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
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_news_library.py -q
```

Expected: import failure for `bitget_ai_backtest.news_library`.

- [ ] **Step 3: Implement news library persistence**

Create `src/bitget_ai_backtest/news_library.py`:

```python
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

        raw_events = []
        ai_events = []
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
        path = root_dir / symbol.upper() / "coverage.json"
        if path.exists():
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                coverage[symbol.upper()] = raw
        else:
            coverage[symbol.upper()] = {
                "symbol": symbol.upper(),
                "event_count": 0,
                "start_date": "",
                "end_date": "",
                "coverage": "",
                "fetched_at": "",
            }
    return coverage
```

- [ ] **Step 4: Run news library tests**

Run:

```bash
python3 -m pytest tests/test_news_library.py -q
```

Expected: 2 passed.

## Task 2: Fetch 30-Day News Library CLI

**Files:**
- Modify: `src/bitget_ai_backtest/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Add failing CLI test**

Append to `tests/test_cli.py`:

```python
def test_fetch_news_library_command_writes_per_symbol_news_store(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["AMDUSDT", "NVDAUSDT"],
  "granularity": "1d",
  "limit": 30,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral",
  "price_source": "yahoo_chart_daily",
  "ticker_map": {"AMDUSDT": "AMD", "NVDAUSDT": "NVDA"}
}
""".strip(),
        encoding="utf-8",
    )

    from bitget_ai_backtest.events import NewsEvent

    def fake_collect_events(config, *, skill_export_dir):
        assert config.symbols == ("AMDUSDT", "NVDAUSDT")
        return [
            NewsEvent(
                event_id="amd-news",
                symbol="AMDUSDT",
                published_at="2026-06-12T20:00:00Z",
                title="AMD raises guidance",
                source_name="Yahoo Finance RSS",
                source_type="public_news_fallback",
                url="https://example.com/amd",
                sentiment="bullish",
                confidence=0.7,
                reason="Matched bullish keyword: raises guidance",
                strength="strong",
                topic="earnings_guidance",
                time_horizon="medium_term",
                stock_relevance="direct",
            )
        ]

    monkeypatch.setattr("bitget_ai_backtest.cli.collect_events", fake_collect_events)

    output_dir = tmp_path / "news"
    exit_code = main(
        [
            "fetch-news-library",
            "--config",
            str(config),
            "--days",
            "30",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "AMDUSDT" / "raw" / "events.json").exists()
    assert (output_dir / "AMDUSDT" / "ai-events" / "events.json").exists()
    assert (output_dir / "AMDUSDT" / "coverage.json").exists()
```

- [ ] **Step 2: Run selected CLI test and verify it fails**

Run:

```bash
python3 -m pytest tests/test_cli.py::test_fetch_news_library_command_writes_per_symbol_news_store -q
```

Expected: argparse exits because `fetch-news-library` is unknown.

- [ ] **Step 3: Add CLI parser and command branch**

Modify `src/bitget_ai_backtest/cli.py` imports:

```python
from .news_library import write_news_library
```

Add parser near `fetch-events`:

```python
    news_library_parser = subparsers.add_parser("fetch-news-library", help="Fetch and persist a per-symbol news library")
    news_library_parser.add_argument("--config", type=Path, default=Path("configs/us_stock_daily_external.json"))
    news_library_parser.add_argument("--days", type=int, default=30)
    news_library_parser.add_argument("--output-dir", type=Path, default=Path("data/news"))
    news_library_parser.add_argument("--skill-export-dir", type=Path, default=Path("data/bitget-skills"))
```

Add command branch before `backtest`:

```python
    if args.command == "fetch-news-library":
        config = load_config(args.config)
        if args.days != 30:
            print(f"Warning: first version is designed for 30 days; requested {args.days} days")
        events = collect_events(config, skill_export_dir=args.skill_export_dir)
        written = write_news_library(args.output_dir, events)
        print(f"News library written: {args.output_dir}")
        print(f"Symbols written: {', '.join(sorted(written)) if written else 'none'}")
        return 0
```

- [ ] **Step 4: Run CLI test**

Run:

```bash
python3 -m pytest tests/test_cli.py::test_fetch_news_library_command_writes_per_symbol_news_store -q
```

Expected: 1 passed.

## Task 3: Technical Candidate Generation

**Files:**
- Create: `src/bitget_ai_backtest/technical_candidates.py`
- Test: `tests/test_technical_candidates.py`

- [ ] **Step 1: Add failing tests**

Create `tests/test_technical_candidates.py`:

```python
from bitget_ai_backtest.models import Candle
from bitget_ai_backtest.technical_candidates import build_technical_candidates


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


def test_build_technical_candidates_marks_buy_observation_days() -> None:
    values = [100 + index * 0.2 + (1.0 if index % 2 == 0 else -0.5) for index in range(60)]

    rows = build_technical_candidates("AMDUSDT", _daily_candles(values))

    latest = rows[-1]
    assert latest["symbol"] == "AMDUSDT"
    assert latest["candidate_type"] == "buy_watch"
    assert "price_above_ma50" in latest["technical_reasons"]
    assert "rsi_not_overheated" in latest["technical_reasons"]


def test_build_technical_candidates_marks_non_candidate_days() -> None:
    values = [120.0] * 40 + [95.0] * 20

    rows = build_technical_candidates("AMDUSDT", _daily_candles(values))

    latest = rows[-1]
    assert latest["candidate_type"] == "none"
    assert "price_below_ma50" in latest["technical_reasons"]
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_technical_candidates.py -q
```

Expected: import failure for `technical_candidates`.

- [ ] **Step 3: Implement candidate builder**

Create `src/bitget_ai_backtest/technical_candidates.py`:

```python
from __future__ import annotations

from datetime import UTC, datetime

from .indicators import moving_average, rsi
from .models import Candle


def build_technical_candidates(symbol: str, candles: list[Candle]) -> list[dict]:
    rows: list[dict] = []
    closes: list[float] = []
    for candle in candles:
        closes.append(candle.close)
        reasons: list[str] = []
        candidate_type = "none"
        if len(closes) >= 50:
            ma20 = moving_average(closes, 20)[-1]
            ma50_values = moving_average(closes, 50)
            ma50 = ma50_values[-1]
            ma50_previous = next((value for value in reversed(ma50_values[:-1]) if value is not None), None)
            current_rsi = rsi(closes, 14)

            if ma20 is not None and ma50 is not None and ma20 > ma50:
                reasons.append("ma20_above_ma50")
            else:
                reasons.append("ma20_below_ma50")
            if ma50 is not None and candle.close > ma50:
                reasons.append("price_above_ma50")
            else:
                reasons.append("price_below_ma50")
            if ma50 is not None and ma50_previous is not None and ma50 > ma50_previous:
                reasons.append("ma50_slope_up")
            else:
                reasons.append("ma50_slope_flat_or_down")
            if current_rsi >= 75:
                reasons.append("rsi_overheated")
            else:
                reasons.append("rsi_not_overheated")

            if (
                ma20 is not None
                and ma50 is not None
                and candle.close > ma50
                and (ma20 > ma50 or (ma50_previous is not None and ma50 > ma50_previous))
                and current_rsi < 75
            ):
                candidate_type = "buy_watch"
            elif ma50 is not None and candle.close < ma50:
                candidate_type = "sell_watch"
        rows.append(
            {
                "symbol": symbol,
                "date": datetime.fromtimestamp(candle.timestamp_ms / 1000, tz=UTC).strftime("%Y-%m-%d"),
                "timestamp_ms": candle.timestamp_ms,
                "price": candle.close,
                "candidate_type": candidate_type,
                "technical_reasons": reasons,
            }
        )
    return rows
```

- [ ] **Step 4: Run candidate tests**

Run:

```bash
python3 -m pytest tests/test_technical_candidates.py -q
```

Expected: 2 passed.

## Task 4: Report Candidate, Candidate Marker, And News Coverage Artifacts

**Files:**
- Modify: `src/bitget_ai_backtest/reporting.py`
- Test: `tests/test_reporting.py`

- [ ] **Step 1: Add failing reporting tests**

Append to `tests/test_reporting.py`:

```python
import json

from bitget_ai_backtest.reporting import write_candidate_markers, write_news_coverage, write_technical_candidates


def test_write_technical_candidates_writes_rows(tmp_path):
    rows = {
        "AMDUSDT": [
            {
                "symbol": "AMDUSDT",
                "date": "2026-06-15",
                "timestamp_ms": 1781530200000,
                "price": 549.5,
                "candidate_type": "buy_watch",
                "technical_reasons": ["price_above_ma50"],
            }
        ]
    }

    path = write_technical_candidates(tmp_path, rows)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["technical_candidates"][0]["candidate_type"] == "buy_watch"


def test_write_news_coverage_writes_symbol_coverage(tmp_path):
    path = write_news_coverage(
        tmp_path,
        {
            "AMDUSDT": {
                "symbol": "AMDUSDT",
                "event_count": 3,
                "start_date": "2026-06-01",
                "end_date": "2026-06-15",
                "coverage": "2026-06-01 -> 2026-06-15",
                "fetched_at": "2026-06-17T09:00:00Z",
            }
        },
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["symbols"]["AMDUSDT"]["event_count"] == 3


def test_write_candidate_markers_writes_distinct_observation_markers(tmp_path):
    path = write_candidate_markers(
        tmp_path,
        {
            "AMDUSDT": [
                {
                    "symbol": "AMDUSDT",
                    "date": "2026-06-15",
                    "timestamp_ms": 1781530200000,
                    "price": 549.5,
                    "candidate_type": "buy_watch",
                    "technical_reasons": ["price_above_ma50"],
                }
            ]
        },
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    marker = payload["candidate_markers"][0]
    assert marker["action"] == "candidate"
    assert marker["label"] == "观察"
    assert marker["color"] == "#38bdf8"
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_reporting.py::test_write_technical_candidates_writes_rows tests/test_reporting.py::test_write_news_coverage_writes_symbol_coverage tests/test_reporting.py::test_write_candidate_markers_writes_distinct_observation_markers -q
```

Expected: import failure for new functions.

- [ ] **Step 3: Implement reporting functions**

Add to `src/bitget_ai_backtest/reporting.py`:

```python
def write_technical_candidates(output_dir: Path, candidates_by_symbol: dict[str, list[dict]]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for symbol in sorted(candidates_by_symbol):
        rows.extend(candidates_by_symbol[symbol])
    path = output_dir / "technical-candidates.json"
    path.write_text(json.dumps({"technical_candidates": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_news_coverage(output_dir: Path, coverage_by_symbol: dict[str, dict]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "news-coverage.json"
    path.write_text(json.dumps({"symbols": coverage_by_symbol}, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_candidate_markers(output_dir: Path, candidates_by_symbol: dict[str, list[dict]]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    markers: list[dict] = []
    for symbol in sorted(candidates_by_symbol):
        for row in candidates_by_symbol[symbol]:
            if row.get("candidate_type") == "none":
                continue
            markers.append(
                {
                    "symbol": row["symbol"],
                    "date": row["date"],
                    "timestamp_ms": row["timestamp_ms"],
                    "action": "candidate",
                    "label": "观察",
                    "price": row["price"],
                    "position": "inBar",
                    "shape": "circle",
                    "color": "#38bdf8",
                    "candidate_type": row["candidate_type"],
                }
            )
    path = output_dir / "candidate-markers.json"
    path.write_text(json.dumps({"candidate_markers": markers}, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
```

- [ ] **Step 4: Run reporting tests**

Run:

```bash
python3 -m pytest tests/test_reporting.py -q
```

Expected: all reporting tests pass.

## Task 5: Backtest Uses News Library And Writes Diagnostics

**Files:**
- Modify: `src/bitget_ai_backtest/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Add failing CLI backtest test**

Append to `tests/test_cli.py`:

```python
def test_backtest_with_news_library_writes_candidates_and_news_coverage(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["AMDUSDT"],
  "granularity": "1d",
  "limit": 60,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral",
  "price_source": "yahoo_chart_daily",
  "ticker_map": {"AMDUSDT": "AMD"}
}
""".strip(),
        encoding="utf-8",
    )

    from bitget_ai_backtest.models import Candle
    from bitget_ai_backtest.news_library import write_news_library
    from bitget_ai_backtest.events import NewsEvent

    values = [100 + index * 0.2 + (1.0 if index % 2 == 0 else -0.5) for index in range(60)]

    class FakeYahooClient:
        def fetch_candles(self, ticker: str, granularity: str, limit: int):
            assert ticker == "AMD"
            return [
                Candle(1_800_000_000 + index * 86_400_000, value, value, value, value, 1000, 1000 * value)
                for index, value in enumerate(values)
            ]

    monkeypatch.setattr("bitget_ai_backtest.cli.YahooChartDailyClient", FakeYahooClient)
    news_dir = tmp_path / "news"
    write_news_library(
        news_dir,
        [
            NewsEvent(
                event_id="amd-news",
                symbol="AMDUSDT",
                published_at="1970-03-19T20:00:00Z",
                title="AMD raises guidance on AI demand",
                source_name="Yahoo Finance RSS",
                source_type="public_news_fallback",
                url="https://example.com/amd",
                sentiment="bullish",
                confidence=0.8,
                reason="Matched bullish keyword: raises guidance",
                strength="strong",
                topic="earnings_guidance",
                time_horizon="medium_term",
                stock_relevance="direct",
            )
        ],
        fetched_at="2026-06-17T09:00:00Z",
    )

    output_dir = tmp_path / "reports"
    exit_code = main(
        [
            "backtest",
            "--config",
            str(config),
            "--news-library",
            str(news_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "technical-candidates.json").exists()
    assert (output_dir / "candidate-markers.json").exists()
    assert (output_dir / "news-coverage.json").exists()
    decisions = json.loads((output_dir / "decision-records.json").read_text(encoding="utf-8"))["decision_records"]
    assert any(row["action"] == "buy" for row in decisions)
```

- [ ] **Step 2: Run selected test and verify it fails**

Run:

```bash
python3 -m pytest tests/test_cli.py::test_backtest_with_news_library_writes_candidates_and_news_coverage -q
```

Expected: argparse error because `--news-library` is unknown.

- [ ] **Step 3: Add imports and parser argument**

Modify `src/bitget_ai_backtest/cli.py` imports:

```python
from .news_library import read_news_coverage, read_news_library, write_news_library
from .technical_candidates import build_technical_candidates
```

Modify `backtest_parser`:

```python
    backtest_parser.add_argument("--news-library", type=Path, default=None)
```

Modify reporting imports:

```python
    write_news_coverage,
    write_candidate_markers,
    write_technical_candidates,
```

- [ ] **Step 4: Use news library in backtest branch**

In the `backtest` branch, replace:

```python
        events = load_events(args.events) if args.events else None
```

with:

```python
        if args.news_library:
            events = read_news_library(args.news_library, load_config(args.config).symbols)
            news_coverage = read_news_coverage(args.news_library, load_config(args.config).symbols)
        else:
            events = load_events(args.events) if args.events else None
            news_coverage = {}
```

After `candles_by_symbol = {}`, add:

```python
        candidates_by_symbol = {}
```

Inside the symbol loop after candles are fetched:

```python
            candidates_by_symbol[symbol] = build_technical_candidates(symbol, candles)
```

After `markers_path = write_chart_markers(...)`, add:

```python
        candidates_path = write_technical_candidates(args.output_dir, candidates_by_symbol)
        candidate_markers_path = write_candidate_markers(args.output_dir, candidates_by_symbol)
        print(f"Technical candidates written: {candidates_path}")
        print(f"Candidate markers written: {candidate_markers_path}")
        if args.news_library:
            news_coverage_path = write_news_coverage(args.output_dir, news_coverage)
            print(f"News coverage written: {news_coverage_path}")
```

Keep existing `--events` behavior unchanged for backward compatibility.

- [ ] **Step 5: Run selected CLI test**

Run:

```bash
python3 -m pytest tests/test_cli.py::test_backtest_with_news_library_writes_candidates_and_news_coverage -q
```

Expected: 1 passed.

## Task 6: Dashboard Shows News Coverage And Candidate Rows

**Files:**
- Modify: `src/bitget_ai_backtest/web.py`
- Modify: `src/bitget_ai_backtest/static/index.html`
- Modify: `src/bitget_ai_backtest/static/app.js`
- Test: `tests/test_web.py`
- Test: `tests/test_static_dashboard_ui.py`

- [ ] **Step 1: Add failing web payload test**

In `tests/test_web.py`, add fixture files before building payload:

```python
    (report_dir / "technical-candidates.json").write_text(
        json.dumps(
            {
                "technical_candidates": [
                    {
                        "symbol": "NVDAUSDT",
                        "date": "2026-06-08",
                        "timestamp_ms": 1780916400000,
                        "price": 209.66,
                        "candidate_type": "buy_watch",
                        "technical_reasons": ["price_above_ma50"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (report_dir / "news-coverage.json").write_text(
        json.dumps(
            {
                "symbols": {
                    "NVDAUSDT": {
                        "symbol": "NVDAUSDT",
                        "event_count": 2,
                        "start_date": "2026-06-01",
                        "end_date": "2026-06-08",
                        "coverage": "2026-06-01 -> 2026-06-08",
                        "fetched_at": "2026-06-17T09:00:00Z",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
```

Add assertions:

```python
    assert payload["technical_candidates"][0]["candidate_type"] == "buy_watch"
    assert payload["news_coverage"]["symbols"]["NVDAUSDT"]["event_count"] == 2
```

- [ ] **Step 2: Add failing static UI assertions**

In `tests/test_static_dashboard_ui.py`, add:

```python
    assert "新闻库覆盖" in html
    assert "技术候选观察点" in html
```

And in script assertions:

```python
    assert "renderNewsCoverage" in script
    assert "renderTechnicalCandidates" in script
    assert "mergeChartMarkers" in script
    assert "candidate_markers" in script
    assert "candidate_type" in script
```

- [ ] **Step 3: Run web/static tests and verify they fail**

Run:

```bash
python3 -m pytest tests/test_web.py tests/test_static_dashboard_ui.py -q
```

Expected: payload key and static text assertions fail.

- [ ] **Step 4: Add payload readers to web.py**

In `src/bitget_ai_backtest/web.py`, add:

```python
def _read_technical_candidates(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("technical_candidates", []) if isinstance(raw, dict) else []
    return [row for row in rows if isinstance(row, dict)]


def _read_news_coverage(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"symbols": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {"symbols": {}}


def _read_candidate_markers(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    markers = raw.get("candidate_markers", []) if isinstance(raw, dict) else []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for marker in markers:
        if not isinstance(marker, dict):
            continue
        symbol = str(marker.get("symbol", ""))
        if symbol:
            grouped.setdefault(symbol, []).append(marker)
    return grouped
```

In `build_dashboard_payload`, read and return:

```python
    technical_candidates = _read_technical_candidates(output_dir / "technical-candidates.json")
    news_coverage = _read_news_coverage(output_dir / "news-coverage.json")
    candidate_markers = _read_candidate_markers(output_dir / "candidate-markers.json")
```

Add to returned payload:

```python
        "technical_candidates": technical_candidates,
        "news_coverage": news_coverage,
        "candidate_markers": candidate_markers,
```

- [ ] **Step 5: Add static sections**

In `src/bitget_ai_backtest/static/index.html`, inside detail view before the decision table section, add:

```html
        <section class="band">
          <h2>新闻库覆盖</h2>
          <div id="news-coverage-grid" class="coverage-grid"></div>
        </section>

        <section class="band">
          <h2>技术候选观察点</h2>
          <div id="technical-candidates" class="stack"></div>
        </section>
```

In `src/bitget_ai_backtest/static/app.js`, replace the existing `renderKlineChart(data.price_series, data.chart_markers, symbol);` call inside `renderDetailView` with the merged marker call, then render coverage and candidates:

```javascript
  renderKlineChart(data.price_series, mergeChartMarkers(data.chart_markers, data.candidate_markers), symbol);
  renderNewsCoverage(data.news_coverage, symbol);
  renderTechnicalCandidates(filterBySymbol(data.technical_candidates, symbol));
```

Add functions:

```javascript
function renderNewsCoverage(newsCoverage, symbol) {
  const container = document.getElementById("news-coverage-grid");
  const row = newsCoverage && newsCoverage.symbols ? newsCoverage.symbols[symbol] : null;
  const values = [
    ["新闻条数", row ? row.event_count : 0],
    ["新闻覆盖", row ? row.coverage || "暂无" : "暂无"],
    ["最早新闻", row ? row.start_date || "暂无" : "暂无"],
    ["最新新闻", row ? row.end_date || "暂无" : "暂无"]
  ];
  container.innerHTML = values.map(([label, value]) => `
    <div class="coverage-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `).join("");
}

function renderTechnicalCandidates(rows) {
  const container = document.getElementById("technical-candidates");
  if (!rows.length) {
    container.innerHTML = `<p class="empty-state">暂无技术候选观察点。可能是技术面没有触发，或尚未运行新闻库回测。</p>`;
    return;
  }
  container.innerHTML = rows.slice(-20).reverse().map((row) => `
    <article class="event-card">
      <div class="card-heading">
        <h3>${escapeHtml(row.date)} · ${escapeHtml(translateCandidateType(row.candidate_type))}</h3>
        <span class="source-pill">${escapeHtml(formatFixed(row.price))}</span>
      </div>
      <p class="meta">技术原因：${escapeHtml(translateReasons(row.technical_reasons || []))}</p>
    </article>
  `).join("");
}

function translateCandidateType(value) {
  const labels = {
    buy_watch: "买入观察",
    sell_watch: "卖出观察",
    none: "非候选"
  };
  return labels[value] || value || "未知";
}

function mergeChartMarkers(tradeMarkers, candidateMarkers) {
  const merged = {};
  const symbols = new Set([
    ...Object.keys(tradeMarkers || {}),
    ...Object.keys(candidateMarkers || {})
  ]);
  symbols.forEach((symbol) => {
    merged[symbol] = [
      ...((candidateMarkers && candidateMarkers[symbol]) || []),
      ...((tradeMarkers && tradeMarkers[symbol]) || [])
    ];
  });
  return merged;
}
```

- [ ] **Step 6: Run web/static tests**

Run:

```bash
python3 -m pytest tests/test_web.py tests/test_static_dashboard_ui.py -q
```

Expected: tests pass.

## Task 7: End-to-End Verification

**Files:**
- No code files unless earlier tasks reveal a gap.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m pytest tests/test_news_library.py tests/test_technical_candidates.py tests/test_cli.py tests/test_reporting.py tests/test_web.py tests/test_static_dashboard_ui.py -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```bash
python3 -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Fetch a 30-day news library**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli fetch-news-library \
  --config configs/us_stock_daily_external.json \
  --days 30 \
  --output-dir data/news
```

Expected output includes:

```text
News library written: data/news
```

Then inspect:

```bash
find data/news -maxdepth 3 -type f | sort | head -40
```

Expected: `raw/events.json`, `ai-events/events.json`, and `coverage.json` under at least one configured symbol.

- [ ] **Step 4: Run news-library backtest**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/us_stock_daily_external.json \
  --news-library data/news \
  --output-dir reports/us-stock-daily-news-library
```

Expected output includes:

```text
Technical candidates written: reports/us-stock-daily-news-library/technical-candidates.json
Candidate markers written: reports/us-stock-daily-news-library/candidate-markers.json
News coverage written: reports/us-stock-daily-news-library/news-coverage.json
Decision records written: reports/us-stock-daily-news-library/decision-records.json
```

- [ ] **Step 5: Inspect diagnostics**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
base = Path("reports/us-stock-daily-news-library")
print("decisions", len(json.loads((base / "decision-records.json").read_text())["decision_records"]))
print("markers", len(json.loads((base / "markers.json").read_text())["markers"]))
print("candidate markers", len(json.loads((base / "candidate-markers.json").read_text())["candidate_markers"]))
print("candidates", len(json.loads((base / "technical-candidates.json").read_text())["technical_candidates"]))
print("coverage symbols", sorted(json.loads((base / "news-coverage.json").read_text())["symbols"]))
PY
```

Expected: decisions and candidates are non-zero; candidate markers are non-zero when candidates exist; trade markers may be zero if no strong news passes, but the page must explain why.

- [ ] **Step 6: Optional foreground web check**

Run in foreground only:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web \
  --config configs/us_stock_daily_external.json \
  --output-dir reports/us-stock-daily-news-library \
  --events data/events/us_stock_events.json \
  --port 8014
```

Expected: page opens at `http://127.0.0.1:8014`; detail pages show news coverage and technical candidates. Stop with `Ctrl+C`.

## Spec Coverage Self-Review

- 30-day news library: Task 1 and Task 2.
- Per-symbol storage: Task 1.
- Existing Yahoo RSS / Bitget skill source only: Task 2 reuses `collect_events`.
- Technical candidate dates: Task 3 and Task 4.
- News library backtest: Task 5.
- No future news: existing conservative-policy event window plus Task 5 fixture uses pre-candidate news; add stricter future-news test during implementation if regression appears.
- Page diagnostics: Task 6.
- Candidate markers: Task 4 and Task 6 include distinct candidate marker output and chart rendering with a different color/label from real buy/sell markers.
- Backtest-only safety: maintained by CLI/reporting; no live account or order code is added.
