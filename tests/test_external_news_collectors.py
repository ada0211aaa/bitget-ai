import json
from pathlib import Path

from bitget_ai_backtest.external_news_collectors import (
    EXTERNAL_ARCHIVE_SOURCE_TYPE,
    GOOGLE_NEWS_SEARCH_SOURCE_TYPE,
    SEC_EDGAR_SOURCE_TYPE,
    _monthly_windows,
    _parse_google_news_rss,
    _parse_sec_edgar_atom,
    load_daily_stock_analysis_archive,
)
from datetime import date


def test_load_daily_stock_analysis_archive_reads_jsonl_for_mapped_ticker(tmp_path: Path) -> None:
    archive = tmp_path / "2026-03-01" / "AMD" / "news.jsonl"
    archive.parent.mkdir(parents=True)
    archive.write_text(
        json.dumps(
            {
                "symbol": "AMD",
                "provider": "YahooFinanceRSS",
                "source_type": "rss",
                "title": "AMD receives analyst upgrade on AI demand",
                "url": "https://example.com/amd-upgrade",
                "source": "Yahoo Finance",
                "published_at": "2026-03-01T13:30:00Z",
                "snippet": "Analyst cites AI demand.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    events = load_daily_stock_analysis_archive(tmp_path, ("AMDUSDT",), {"AMDUSDT": "AMD"})

    assert len(events) == 1
    assert events[0].symbol == "AMDUSDT"
    assert events[0].source_type == EXTERNAL_ARCHIVE_SOURCE_TYPE
    assert events[0].sentiment == "bullish"
    assert events[0].published_at == "2026-03-01T13:30:00Z"


def test_parse_sec_edgar_atom_returns_official_filing_events() -> None:
    xml = """
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>10-K annual report</title>
    <updated>2026-02-20T18:45:00Z</updated>
    <link href="https://www.sec.gov/example" rel="alternate" />
  </entry>
</feed>
""".strip()

    events = _parse_sec_edgar_atom(xml, symbol="NVDAUSDT", ticker="NVDA")

    assert len(events) == 1
    assert events[0].symbol == "NVDAUSDT"
    assert events[0].source_type == SEC_EDGAR_SOURCE_TYPE
    assert events[0].source_name == "SEC EDGAR"
    assert events[0].published_at == "2026-02-20T18:45:00Z"
    assert "NVDA SEC filing" in events[0].title


def test_parse_google_news_rss_returns_search_events() -> None:
    xml = """
<rss>
  <channel>
    <item>
      <title>AMD receives analyst upgrade on AI demand</title>
      <link>https://news.google.com/example</link>
      <pubDate>Mon, 02 Mar 2026 14:30:00 GMT</pubDate>
      <source>Example News</source>
      <description>Analyst cites AI demand.</description>
    </item>
  </channel>
</rss>
""".strip()

    events = _parse_google_news_rss(xml, symbol="AMDUSDT", max_results=10)

    assert len(events) == 1
    assert events[0].source_type == GOOGLE_NEWS_SEARCH_SOURCE_TYPE
    assert events[0].published_at == "2026-03-02T14:30:00Z"
    assert events[0].sentiment == "bullish"


def test_monthly_windows_split_date_range() -> None:
    windows = _monthly_windows(date(2026, 1, 15), date(2026, 3, 3))

    assert windows == [
        (date(2026, 1, 15), date(2026, 2, 1)),
        (date(2026, 2, 1), date(2026, 3, 1)),
        (date(2026, 3, 1), date(2026, 3, 4)),
    ]
