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


def test_build_technical_candidates_marks_sell_observation_days() -> None:
    values = [120.0] * 40 + [95.0] * 20

    rows = build_technical_candidates("AMDUSDT", _daily_candles(values))

    latest = rows[-1]
    assert latest["candidate_type"] == "sell_watch"
    assert "price_below_ma50" in latest["technical_reasons"]
