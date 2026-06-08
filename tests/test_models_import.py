from bitget_ai_backtest.models import Candle


def test_candle_import_and_close_property() -> None:
    candle = Candle(
        timestamp_ms=1780917300000,
        open=209.66,
        high=210.42,
        low=209.64,
        close=210.04,
        volume=933.18,
        quote_volume=195945.8038,
    )

    assert candle.close == 210.04
    assert candle.timestamp_ms == 1780917300000
