from bitget_ai_backtest.indicators import max_drawdown, moving_average, pct_change, rsi


def test_moving_average_returns_none_until_window_is_available() -> None:
    assert moving_average([1, 2, 3, 4], 3) == [None, None, 2.0, 3.0]


def test_pct_change_calculates_period_change() -> None:
    assert pct_change([100, 105, 110], 2) == 0.10


def test_rsi_returns_high_value_for_consistent_gains() -> None:
    values = [100, 101, 102, 103, 104, 105]

    assert rsi(values, 5) == 100.0


def test_max_drawdown_uses_equity_peak_to_trough() -> None:
    assert round(max_drawdown([100, 120, 90, 110]), 4) == -0.25
