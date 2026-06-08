from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

from .models import Candle


class BitgetPublicClient:
    base_url = "https://api.bitget.com/api/v3/market/candles"

    def build_candles_url(self, symbol: str, interval: str, limit: int) -> str:
        params = urlencode(
            {
                "category": "USDT-FUTURES",
                "symbol": symbol.upper(),
                "interval": interval,
                "kLineType": "MARKET",
                "limit": str(limit),
            }
        )
        return f"{self.base_url}?{params}"

    def fetch_candles(self, symbol: str, interval: str, limit: int) -> list[Candle]:
        url = self.build_candles_url(symbol, interval, limit)
        with urlopen(url, timeout=15) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return parse_candles_response(raw)


def parse_candles_response(raw: dict) -> list[Candle]:
    if raw.get("code") != "00000":
        raise ValueError(f"Bitget API error: {raw.get('code')} {raw.get('msg')}")
    rows = raw.get("data")
    if not isinstance(rows, list):
        raise ValueError("Bitget API response missing candle data")

    candles = [
        Candle(
            timestamp_ms=int(row[0]),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
            quote_volume=float(row[6]),
        )
        for row in rows
    ]
    candles.sort(key=lambda candle: candle.timestamp_ms)
    return candles
