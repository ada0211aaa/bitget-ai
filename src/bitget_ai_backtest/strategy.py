from __future__ import annotations

from .indicators import moving_average, pct_change, rsi
from .models import Candle, StrategySignal


def generate_signal(
    symbol: str,
    candles: list[Candle],
    *,
    macro_mode: str,
    news_bias: str,
) -> StrategySignal:
    if len(candles) < 3:
        raise ValueError("at least three candles are required")

    closes = [candle.close for candle in candles]
    fast_ma = moving_average(closes, min(3, len(closes)))[-1]
    slow_ma = moving_average(closes, min(5, len(closes)))[-1]
    recent_rsi = rsi(closes, min(5, len(closes) - 1))
    momentum = pct_change(closes, min(3, len(closes) - 1))

    score = 0
    reasons: list[str] = []

    if fast_ma is not None and slow_ma is not None and fast_ma > slow_ma and momentum > 0:
        score += 2
        reasons.append("trend_up")
    elif fast_ma is not None and slow_ma is not None and fast_ma < slow_ma and momentum < 0:
        score -= 2
        reasons.append("trend_down")
    else:
        reasons.append("trend_mixed")

    if news_bias == "bullish":
        score += 1
        reasons.append("news_bullish")
    elif news_bias == "bearish":
        score -= 1
        reasons.append("news_bearish")
    else:
        reasons.append("news_neutral")

    if macro_mode == "risk_on":
        score += 1
        reasons.append("macro_risk_on")
    elif macro_mode == "risk_off":
        score -= 2
        reasons.append("macro_risk_off")
    else:
        reasons.append("macro_neutral")

    if recent_rsi >= 80:
        score -= 1
        reasons.append("overbought_guard")
    elif recent_rsi <= 25:
        score += 1
        reasons.append("oversold_rebound")

    if "macro_risk_off" in reasons and "news_bullish" in reasons:
        view = "neutral_observe"
        action = "hold"
    elif score >= 3:
        view = "bullish"
        action = "buy"
    elif score >= 2:
        view = "cautiously_bullish"
        action = "buy"
    elif score <= -2:
        view = "bearish"
        action = "sell"
    elif score <= -1:
        view = "cautiously_bearish"
        action = "sell"
    else:
        view = "neutral_observe"
        action = "hold"

    latest = candles[-1]
    return StrategySignal(
        symbol=symbol,
        timestamp_ms=latest.timestamp_ms,
        score=score,
        view=view,
        action=action,
        close=latest.close,
        reasons=tuple(reasons),
    )
