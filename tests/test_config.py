import json
from pathlib import Path

import pytest

from bitget_ai_backtest.config import BacktestConfig, load_config


def test_load_config_reads_symbols_and_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "symbols": ["NVDAUSDT", "MSFTUSDT"],
                "granularity": "15m",
                "limit": 200,
                "initial_cash": 10000,
                "trade_fraction": 0.25,
                "fee_rate": 0.0006,
                "macro_mode": "neutral",
                "news_bias": "neutral",
                "price_source": "yahoo_chart_daily",
                "ticker_map": {"NVDAUSDT": "NVDA", "MSFTUSDT": "MSFT"},
            }
        ),
        encoding="utf-8",
    )

    config = load_config(path)

    assert config == BacktestConfig(
        symbols=("NVDAUSDT", "MSFTUSDT"),
        granularity="15m",
        limit=200,
        initial_cash=10000.0,
        trade_fraction=0.25,
        fee_rate=0.0006,
        macro_mode="neutral",
        news_bias="neutral",
        price_source="yahoo_chart_daily",
        ticker_map={"NVDAUSDT": "NVDA", "MSFTUSDT": "MSFT"},
        decision_mode="conservative",
    )


def test_load_config_defaults_to_bitget_public_source(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "symbols": ["AMDUSDT"],
                "granularity": "1d",
                "limit": 100,
                "initial_cash": 10000,
                "trade_fraction": 0.25,
                "fee_rate": 0.0006,
                "macro_mode": "neutral",
                "news_bias": "neutral",
            }
        ),
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.price_source == "bitget_public"
    assert config.ticker_map == {}
    assert config.decision_mode == "conservative"


def test_load_config_reads_aggressive_news_decision_mode(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "symbols": ["AMDUSDT"],
                "granularity": "1d",
                "limit": 100,
                "initial_cash": 10000,
                "trade_fraction": 0.25,
                "fee_rate": 0.0006,
                "macro_mode": "neutral",
                "news_bias": "neutral",
                "decision_mode": "aggressive_news",
            }
        ),
        encoding="utf-8",
    )

    config = load_config(path)

    assert config.decision_mode == "aggressive_news"


def test_load_config_rejects_missing_symbols(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "symbols": [],
                "granularity": "15m",
                "limit": 200,
                "initial_cash": 10000,
                "trade_fraction": 0.25,
                "fee_rate": 0.0006,
                "macro_mode": "neutral",
                "news_bias": "neutral",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="at least one symbol"):
        load_config(path)
