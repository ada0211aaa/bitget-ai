from bitget_ai_backtest.models import Candle
from bitget_ai_backtest.strategy import generate_signal


def _candles(values: list[float]) -> list[Candle]:
    return [
        Candle(
            timestamp_ms=1000 + index,
            open=value,
            high=value + 1,
            low=value - 1,
            close=value,
            volume=1000 + index,
            quote_volume=(1000 + index) * value,
        )
        for index, value in enumerate(values)
    ]


def test_generate_signal_is_bullish_when_trend_news_and_macro_align() -> None:
    signal = generate_signal(
        "NVDAUSDT",
        _candles([100, 101, 102, 103, 104, 105, 106]),
        macro_mode="risk_on",
        news_bias="bullish",
    )

    assert signal.view == "bullish"
    assert signal.action == "buy"
    assert signal.score > 0


def test_generate_signal_is_neutral_when_signals_conflict() -> None:
    signal = generate_signal(
        "NVDAUSDT",
        _candles([100, 101, 102, 103, 104, 105, 106]),
        macro_mode="risk_off",
        news_bias="bullish",
    )

    assert signal.view == "neutral_observe"
    assert signal.action == "hold"


def test_generate_signal_is_bearish_on_downtrend_and_bad_news() -> None:
    signal = generate_signal(
        "NVDAUSDT",
        _candles([106, 105, 104, 103, 102, 101, 100]),
        macro_mode="neutral",
        news_bias="bearish",
    )

    assert signal.view == "bearish"
    assert signal.action == "sell"
