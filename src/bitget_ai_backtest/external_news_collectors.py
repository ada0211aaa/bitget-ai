from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .events import NewsEvent, _event_id, _normalize_datetime, score_event_sentiment


EXTERNAL_ARCHIVE_SOURCE_TYPE = "daily_stock_analysis_archive"
SEC_EDGAR_SOURCE_TYPE = "sec_edgar_filings"
GOOGLE_NEWS_SEARCH_SOURCE_TYPE = "google_news_search"

SYMBOL_NAMES = {
    "NVDAUSDT": "Nvidia",
    "AMDUSDT": "AMD",
    "TSLAUSDT": "Tesla",
    "AAPLUSDT": "Apple",
    "MSFTUSDT": "Microsoft",
}


def load_daily_stock_analysis_archive(root_dir: Path, symbols: tuple[str, ...], ticker_map: dict[str, str]) -> list[NewsEvent]:
    if not root_dir.exists():
        return []
    events: list[NewsEvent] = []
    symbol_by_ticker = _symbol_by_ticker(symbols, ticker_map)
    for path in sorted(root_dir.glob("*/*/news.jsonl")):
        ticker = path.parent.name.upper()
        symbol = symbol_by_ticker.get(ticker)
        if not symbol:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            event = _archive_row_to_event(row, symbol)
            if event is not None:
                events.append(event)
    return events


def fetch_sec_edgar_events(symbols: tuple[str, ...], ticker_map: dict[str, str], *, max_results: int = 20) -> list[NewsEvent]:
    events: list[NewsEvent] = []
    for symbol in symbols:
        ticker = ticker_map.get(symbol.upper(), symbol.upper().replace("USDT", ""))
        events.extend(_fetch_sec_edgar_for_symbol(symbol.upper(), ticker, max_results=max_results))
    return events


def fetch_google_news_search_events(
    symbols: tuple[str, ...],
    ticker_map: dict[str, str],
    *,
    days: int,
    max_results_per_window: int = 10,
) -> list[NewsEvent]:
    events: list[NewsEvent] = []
    end = datetime.now(UTC).date()
    start = end - timedelta(days=max(1, days))
    windows = _monthly_windows(start, end)
    for symbol in symbols:
        normalized = symbol.upper()
        ticker = ticker_map.get(normalized, normalized.replace("USDT", "")).upper()
        name = SYMBOL_NAMES.get(normalized, ticker)
        for window_start, window_end in windows:
            events.extend(
                _fetch_google_news_window(
                    normalized,
                    ticker,
                    name,
                    window_start=window_start,
                    window_end=window_end,
                    max_results=max_results_per_window,
                )
            )
    return events


def _archive_row_to_event(row: dict, symbol: str) -> NewsEvent | None:
    title = str(row.get("title") or "").strip()
    published_at = _normalize_datetime(str(row.get("published_at") or row.get("fetched_at") or ""))
    if not title or not published_at:
        return None
    snippet = str(row.get("snippet") or "")
    scored = score_event_sentiment(title, snippet)
    return NewsEvent(
        event_id=_event_id(symbol, published_at, title),
        symbol=symbol,
        published_at=published_at,
        title=title,
        source_name=str(row.get("source") or row.get("provider") or "daily_stock_analysis"),
        source_type=EXTERNAL_ARCHIVE_SOURCE_TYPE,
        url=str(row.get("url") or ""),
        sentiment=scored.sentiment,
        confidence=scored.confidence,
        reason=scored.reason,
        strength="strong" if scored.confidence >= 0.7 and scored.sentiment in {"bullish", "bearish"} else "weak",
        topic="unknown",
        time_horizon="short_term",
        stock_relevance="direct",
    )


def _fetch_sec_edgar_for_symbol(symbol: str, ticker: str, *, max_results: int) -> list[NewsEvent]:
    url = (
        "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
        f"&CIK={quote(ticker, safe='')}&type=&owner=exclude&count={max_results}&output=atom"
    )
    request = Request(
        url,
        headers={
            "User-Agent": "bitget-ai-backtest research@example.com",
            "Accept": "application/atom+xml,application/xml,text/xml,*/*",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            xml_text = response.read().decode("utf-8-sig", "replace")
    except (TimeoutError, URLError, OSError) as exc:
        print(f"Warning: failed to fetch SEC EDGAR for {symbol}: {exc}")
        return []
    return _parse_sec_edgar_atom(xml_text, symbol=symbol, ticker=ticker)


def _parse_sec_edgar_atom(xml_text: str, *, symbol: str, ticker: str) -> list[NewsEvent]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return []
    events: list[NewsEvent] = []
    for entry in list(root.findall("{http://www.w3.org/2005/Atom}entry")) + list(root.findall("entry")):
        title = _clean_text(_find_text(entry, "title"))
        published_at = _normalize_datetime(_find_text(entry, "updated") or _find_text(entry, "published"))
        if not title or not published_at:
            continue
        url = _entry_link(entry)
        full_title = f"{ticker.upper()} SEC filing: {title}"
        scored = score_event_sentiment(full_title)
        events.append(
            NewsEvent(
                event_id=_event_id(symbol, published_at, full_title),
                symbol=symbol,
                published_at=published_at,
                title=full_title,
                source_name="SEC EDGAR",
                source_type=SEC_EDGAR_SOURCE_TYPE,
                url=url,
                sentiment=scored.sentiment,
                confidence=scored.confidence,
                reason=scored.reason,
                strength="weak",
                topic="sec_filing",
                time_horizon="medium_term",
                stock_relevance="direct",
            )
        )
    return events


def _fetch_google_news_window(
    symbol: str,
    ticker: str,
    name: str,
    *,
    window_start: date,
    window_end: date,
    max_results: int,
) -> list[NewsEvent]:
    query = f'"{name}" OR {ticker} stock news after:{window_start.isoformat()} before:{window_end.isoformat()}'
    url = "https://news.google.com/rss/search?" + urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=20) as response:
            xml_text = response.read().decode("utf-8-sig", "replace")
    except (TimeoutError, URLError, OSError) as exc:
        print(f"Warning: failed to fetch Google News search for {symbol} {window_start}: {exc}")
        return []
    return _parse_google_news_rss(xml_text, symbol=symbol, max_results=max_results)


def _parse_google_news_rss(xml_text: str, *, symbol: str, max_results: int) -> list[NewsEvent]:
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError:
        return []
    events: list[NewsEvent] = []
    for item in root.findall(".//item")[:max_results]:
        title = _clean_text(item.findtext("title"))
        published_at = _normalize_datetime(_clean_text(item.findtext("pubDate")))
        if not title or not published_at:
            continue
        description = _clean_text(item.findtext("description"))
        scored = score_event_sentiment(title, description)
        events.append(
            NewsEvent(
                event_id=_event_id(symbol, published_at, title),
                symbol=symbol,
                published_at=published_at,
                title=title,
                source_name=_clean_text(item.findtext("source")) or "Google News",
                source_type=GOOGLE_NEWS_SEARCH_SOURCE_TYPE,
                url=_clean_text(item.findtext("link")),
                sentiment=scored.sentiment,
                confidence=scored.confidence,
                reason=scored.reason,
                strength="strong" if scored.confidence >= 0.7 and scored.sentiment in {"bullish", "bearish"} else "weak",
                topic="unknown",
                time_horizon="short_term",
                stock_relevance="direct",
            )
        )
    return events


def _monthly_windows(start: date, end: date) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    cursor = start.replace(day=1)
    while cursor <= end:
        if cursor.month == 12:
            next_month = date(cursor.year + 1, 1, 1)
        else:
            next_month = date(cursor.year, cursor.month + 1, 1)
        window_start = max(start, cursor)
        window_end = min(end + timedelta(days=1), next_month)
        if window_start < window_end:
            windows.append((window_start, window_end))
        cursor = next_month
    return windows


def _symbol_by_ticker(symbols: tuple[str, ...], ticker_map: dict[str, str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for symbol in symbols:
        normalized = symbol.upper()
        ticker = ticker_map.get(normalized, normalized.replace("USDT", "")).upper()
        mapping[ticker] = normalized
        mapping[normalized] = normalized
    return mapping


def _find_text(element: ElementTree.Element, tag: str) -> str:
    return _clean_text(element.findtext(tag) or element.findtext(f"{{http://www.w3.org/2005/Atom}}{tag}"))


def _entry_link(entry: ElementTree.Element) -> str:
    links = list(entry.findall("{http://www.w3.org/2005/Atom}link")) + list(entry.findall("link"))
    for link in links:
        href = _clean_text(link.attrib.get("href"))
        if href and link.attrib.get("rel", "alternate") in {"alternate", ""}:
            return href
    return _clean_text(links[0].attrib.get("href")) if links else ""


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").split())
