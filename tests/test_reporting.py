from pathlib import Path

from bitget_ai_backtest.backtester import backtest_symbol
from bitget_ai_backtest.models import Candle
from bitget_ai_backtest.reporting import write_report


def test_write_report_creates_markdown_and_trade_csv(tmp_path: Path) -> None:
    candles = [
        Candle(1000 + index, value, value + 1, value - 1, value, 1000, value * 1000)
        for index, value in enumerate([100, 101, 102, 103, 104, 105, 106, 107])
    ]
    result = backtest_symbol(
        "NVDAUSDT",
        candles,
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_on",
        news_bias="bullish",
    )

    paths = write_report(tmp_path, [result], config_name="test-config")

    markdown = paths["markdown"].read_text(encoding="utf-8")
    csv_text = paths["trades_csv"].read_text(encoding="utf-8")
    assert "Bitget AI Local Backtest Report" in markdown
    assert "NVDAUSDT" in markdown
    assert "Backtest-only" in markdown
    assert "timestamp_ms,symbol,side,price,quantity,fee,reason" in csv_text
