from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .config import BacktestConfig


BITGET_SOURCE_TYPES = {
    "bitget_news_briefing",
    "bitget_macro_analyst",
    "bitget_sentiment_analyst",
    "bitget_technical_analysis",
    "bitget_market_intel",
}
PUBLIC_SOURCE_TYPE = "public_news_fallback"
DEFAULT_SKILL_EXPORT_DIR = Path("data/bitget-skills")

SYMBOL_TO_TICKER = {
    "NVDAUSDT": "NVDA",
    "MSFTUSDT": "MSFT",
    "GOOGLUSDT": "GOOGL",
    "AMDUSDT": "AMD",
    "METAUSDT": "META",
    "AAPLUSDT": "AAPL",
    "TSLAUSDT": "TSLA",
}

BULLISH_KEYWORDS = (
    "beats estimates",
    "beat estimates",
    "raises guidance",
    "raised guidance",
    "ai demand",
    "partnership",
    "approval",
    "upgrade",
    "price target",
    "buy rating",
    "record revenue",
    "strong demand",
)
BEARISH_KEYWORDS = (
    "misses estimates",
    "missed estimates",
    "cuts guidance",
    "cut guidance",
    "probe",
    "lawsuit",
    "export restriction",
    "downgrade",
    "layoffs",
    "weak demand",
    "antitrust",
)


@dataclass(frozen=True)
class SentimentScore:
    sentiment: str
    confidence: float
    reason: str


@dataclass(frozen=True)
class NewsEvent:
    event_id: str
    symbol: str
    published_at: str
    title: str
    source_name: str
    source_type: str
    url: str
    sentiment: str
    confidence: float
    reason: str
    strength: str = ""
    topic: str = "unknown"
    time_horizon: str = "short_term"
    stock_relevance: str = "direct"


def score_event_sentiment(title: str, description: str = "") -> SentimentScore:
    text = f"{title} {description}".lower()
    for keyword in BULLISH_KEYWORDS:
        if keyword in text:
            return SentimentScore("bullish", 0.7, f"Matched bullish keyword: {keyword}")
    for keyword in BEARISH_KEYWORDS:
        if keyword in text:
            return SentimentScore("bearish", 0.7, f"Matched bearish keyword: {keyword}")
    return SentimentScore("neutral", 0.5, "No bullish or bearish keyword matched")


def load_events(path: Path) -> list[NewsEvent]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("events", [])
    if not isinstance(rows, list):
        raise ValueError("event file must contain an events list")
    return [_event_from_row(row) for row in rows]


def write_events(path: Path, events: list[NewsEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"events": [asdict(event) for event in events]}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def deduplicate_events(events: list[NewsEvent]) -> list[NewsEvent]:
    by_key: dict[tuple[str, str], NewsEvent] = {}
    for event in sorted(events, key=lambda item: _parse_iso_datetime(item.published_at)):
        key = (event.symbol.upper(), (event.url or event.title).strip().lower())
        if key not in by_key:
            by_key[key] = event
    return sorted(by_key.values(), key=lambda item: (item.symbol, item.published_at, item.event_id))


def events_for_symbol(events: list[NewsEvent], symbol: str) -> list[NewsEvent]:
    normalized = symbol.upper()
    ticker = SYMBOL_TO_TICKER.get(normalized, normalized.replace("USDT", ""))
    return [
        event
        for event in events
        if event.symbol.upper() == normalized and (event.source_type != PUBLIC_SOURCE_TYPE or _public_event_mentions_ticker(event, ticker))
    ]


def collect_events(config: BacktestConfig, *, skill_export_dir: Path = DEFAULT_SKILL_EXPORT_DIR) -> list[NewsEvent]:
    events = _load_bitget_skill_exports(config, skill_export_dir)
    source = "Bitget skill exports"
    if not events:
        events = _fetch_public_yahoo_events(config)
        source = "public news fallback"
    deduped = deduplicate_events(events)
    print(f"Collected {len(deduped)} events from {source}")
    return deduped


def _load_bitget_skill_exports(config: BacktestConfig, skill_export_dir: Path) -> list[NewsEvent]:
    if not skill_export_dir.exists():
        return []

    events: list[NewsEvent] = []
    allowed_symbols = {symbol.upper() for symbol in config.symbols}
    for path in sorted(skill_export_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw.get("events") if isinstance(raw, dict) else None
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            source_type = str(row.get("source_type", "bitget_news_briefing"))
            if source_type not in BITGET_SOURCE_TYPES:
                source_type = "bitget_news_briefing"
            symbol = str(row.get("symbol", "")).upper()
            if symbol not in allowed_symbols:
                continue
            title = str(row.get("title", "")).strip()
            published_at = _normalize_datetime(str(row.get("published_at", "")))
            if not title or not published_at:
                continue
            scored = score_event_sentiment(title, str(row.get("description", "")))
            sentiment = str(row.get("sentiment", scored.sentiment))
            confidence = float(row.get("confidence", scored.confidence))
            reason = str(row.get("reason", scored.reason))
            events.append(
                NewsEvent(
                    event_id=str(row.get("event_id") or _event_id(symbol, published_at, title)),
                    symbol=symbol,
                    published_at=published_at,
                    title=title,
                    source_name=str(row.get("source_name", "Bitget Agent Hub")),
                    source_type=source_type,
                    url=str(row.get("url", "")),
                    sentiment=sentiment,
                    confidence=confidence,
                    reason=reason,
                    strength=_normalize_strength(str(row.get("strength", "")), sentiment, confidence, title, reason),
                    topic=str(row.get("topic", "unknown") or "unknown"),
                    time_horizon=str(row.get("time_horizon", "short_term") or "short_term"),
                    stock_relevance=str(row.get("stock_relevance", "direct") or "direct"),
                )
            )
    return events


def _fetch_public_yahoo_events(config: BacktestConfig) -> list[NewsEvent]:
    events: list[NewsEvent] = []
    for symbol in config.symbols:
        ticker = SYMBOL_TO_TICKER.get(symbol.upper(), symbol.upper().replace("USDT", ""))
        events.extend(_fetch_yahoo_rss_for_symbol(symbol.upper(), ticker))
    return events


def _fetch_yahoo_rss_for_symbol(symbol: str, ticker: str) -> list[NewsEvent]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=20) as response:
            xml_text = response.read().decode("utf-8", "replace")
    except (TimeoutError, URLError, OSError) as exc:
        print(f"Warning: failed to fetch public news for {symbol}: {exc}")
        return []

    root = ElementTree.fromstring(xml_text)
    events: list[NewsEvent] = []
    for item in root.findall("./channel/item"):
        title = _text(item, "title")
        published_at = _normalize_datetime(_text(item, "pubDate"))
        if not title or not published_at:
            continue
        description = _text(item, "description")
        scored = score_event_sentiment(title, description)
        events.append(
            NewsEvent(
                event_id=_event_id(symbol, published_at, title),
                symbol=symbol,
                published_at=published_at,
                title=title,
                source_name="Yahoo Finance RSS",
                source_type=PUBLIC_SOURCE_TYPE,
                url=_text(item, "link"),
                sentiment=scored.sentiment,
                confidence=scored.confidence,
                reason=scored.reason,
                strength=_normalize_strength("", scored.sentiment, scored.confidence, title, scored.reason),
                topic="unknown",
                time_horizon="short_term",
                stock_relevance="direct",
            )
        )
    return events


def _event_from_row(row: dict[str, Any]) -> NewsEvent:
    sentiment = str(row.get("sentiment", "neutral"))
    confidence = float(row.get("confidence", 0.5))
    title = str(row.get("title", ""))
    reason = str(row.get("reason", ""))
    return NewsEvent(
        event_id=str(row.get("event_id", "")),
        symbol=str(row.get("symbol", "")).upper(),
        published_at=_normalize_datetime(str(row.get("published_at", ""))),
        title=title,
        source_name=str(row.get("source_name", "")),
        source_type=str(row.get("source_type", "")),
        url=str(row.get("url", "")),
        sentiment=sentiment,
        confidence=confidence,
        reason=reason,
        strength=_normalize_strength(str(row.get("strength", "")), sentiment, confidence, title, reason),
        topic=str(row.get("topic", "unknown") or "unknown"),
        time_horizon=str(row.get("time_horizon", "short_term") or "short_term"),
        stock_relevance=str(row.get("stock_relevance", "direct") or "direct"),
    )


def _normalize_strength(value: str, sentiment: str, confidence: float, title: str, reason: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"strong", "medium", "weak"}:
        return normalized
    if sentiment == "bullish" and confidence >= 0.7:
        text = f"{title} {reason}".lower()
        if any(keyword in text for keyword in BULLISH_KEYWORDS):
            return "strong"
        return "medium"
    if sentiment == "bearish" and confidence >= 0.7:
        text = f"{title} {reason}".lower()
        if any(keyword in text for keyword in BEARISH_KEYWORDS):
            return "strong"
        return "medium"
    if sentiment in {"bullish", "bearish"}:
        return "weak"
    return "weak"


def _text(item: ElementTree.Element, tag: str) -> str:
    node = item.find(tag)
    return (node.text or "").strip() if node is not None else ""


def _public_event_mentions_ticker(event: NewsEvent, ticker: str) -> bool:
    if not ticker:
        return True
    aliases = {
        "NVDA": ("nvda", "nvidia"),
        "MSFT": ("msft", "microsoft"),
        "GOOGL": ("googl", "google", "alphabet"),
        "AMD": ("amd", "advanced micro devices"),
        "META": ("meta", "facebook"),
        "AAPL": ("aapl", "apple", "iphone"),
        "TSLA": ("tsla", "tesla"),
    }
    text = f"{event.title} {event.reason}".lower()
    return any(alias in text for alias in aliases.get(ticker.upper(), (ticker.lower(),)))


def _normalize_datetime(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        parsed = _parse_iso_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def event_timestamp_ms(event: NewsEvent) -> int:
    return int(_parse_iso_datetime(event.published_at).timestamp() * 1000)


def _event_id(symbol: str, published_at: str, title: str) -> str:
    digest = hashlib.sha1(f"{symbol}|{published_at}|{title}".encode("utf-8")).hexdigest()[:10]
    return f"{symbol}-{published_at[:10]}-{digest}"
