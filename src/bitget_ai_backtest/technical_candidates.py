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
