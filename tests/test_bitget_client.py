import json
from pathlib import Path

import pytest

from bitget_ai_backtest.bitget_client import BitgetPublicClient, parse_candles_response


def test_parse_candles_response_converts_strings_to_candles() -> None:
    raw = json.loads(
        Path("tests/fixtures/bitget_candles_nvda_15m.json").read_text(encoding="utf-8")
    )

    candles = parse_candles_response(raw)

    assert len(candles) == 4
    assert candles[0].timestamp_ms == 1780914600000
    assert candles[-1].close == 210.04
    assert candles[-1].quote_volume == 195945.8038


def test_parse_candles_response_rejects_error_code() -> None:
    with pytest.raises(ValueError, match="Bitget API error"):
        parse_candles_response({"code": "40034", "msg": "Parameter does not exist", "data": None})


def test_build_candles_url_uses_v3_market_endpoint() -> None:
    client = BitgetPublicClient()

    url = client.build_candles_url("NVDAUSDT", "15m", 100)

    assert "https://api.bitget.com/api/v3/market/candles" in url
    assert "category=USDT-FUTURES" in url
    assert "symbol=NVDAUSDT" in url
    assert "interval=15m" in url
    assert "limit=100" in url
