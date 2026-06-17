from __future__ import annotations

import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Candle


class YahooChartDailyClient:
    base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    def build_chart_url(self, ticker: str, *, limit: int, now_timestamp: int | None = None) -> str:
        period2 = int(now_timestamp if now_timestamp is not None else time.time())
        period1 = period2 - int(limit) * 24 * 60 * 60
        params = urlencode(
            {
                "period1": str(period1),
                "period2": str(period2),
                "interval": "1d",
                "events": "history",
                "includeAdjustedClose": "true",
            }
        )
        return f"{self.base_url}/{ticker.upper()}?{params}"

    def fetch_candles(self, ticker: str, interval: str, limit: int) -> list[Candle]:
        if interval.lower() != "1d":
            raise ValueError("yahoo_chart_daily only supports 1d granularity")
        url = self.build_chart_url(ticker, limit=limit)
        request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=20) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return parse_yahoo_chart_response(raw)


def parse_yahoo_chart_response(raw: dict) -> list[Candle]:
    chart = raw.get("chart") if isinstance(raw, dict) else None
    if not isinstance(chart, dict):
        raise ValueError("Yahoo Chart response missing chart data")
    error = chart.get("error")
    if error:
        raise ValueError(f"Yahoo Chart API error: {error}")
    results = chart.get("result")
    if not isinstance(results, list) or not results:
        raise ValueError("Yahoo Chart response missing result data")

    result = results[0]
    timestamps = result.get("timestamp")
    indicators = result.get("indicators")
    if not isinstance(timestamps, list) or not isinstance(indicators, dict):
        raise ValueError("Yahoo Chart response missing timestamp or indicators")
    quotes = indicators.get("quote")
    if not isinstance(quotes, list) or not quotes:
        raise ValueError("Yahoo Chart response missing quote data")

    quote = quotes[0]
    candles: list[Candle] = []
    for index, timestamp in enumerate(timestamps):
        row = {
            "open": _item_at(quote.get("open"), index),
            "high": _item_at(quote.get("high"), index),
            "low": _item_at(quote.get("low"), index),
            "close": _item_at(quote.get("close"), index),
            "volume": _item_at(quote.get("volume"), index),
        }
        if any(value is None for value in row.values()):
            continue
        close = float(row["close"])
        volume = float(row["volume"])
        candles.append(
            Candle(
                timestamp_ms=int(timestamp) * 1000,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=close,
                volume=volume,
                quote_volume=close * volume,
            )
        )
    candles.sort(key=lambda candle: candle.timestamp_ms)
    return candles


def _item_at(values: object, index: int) -> object:
    if not isinstance(values, list) or index >= len(values):
        return None
    return values[index]
