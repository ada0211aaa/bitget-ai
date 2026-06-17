from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BacktestConfig:
    symbols: tuple[str, ...]
    granularity: str
    limit: int
    initial_cash: float
    trade_fraction: float
    fee_rate: float
    macro_mode: str
    news_bias: str
    price_source: str = "bitget_public"
    ticker_map: dict[str, str] = field(default_factory=dict)
    decision_mode: str = "conservative"


def load_config(path: Path) -> BacktestConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    symbols = tuple(str(symbol).upper() for symbol in raw.get("symbols", []))
    if not symbols:
        raise ValueError("config must contain at least one symbol")

    return BacktestConfig(
        symbols=symbols,
        granularity=_required_str(raw, "granularity"),
        limit=_positive_int(raw, "limit"),
        initial_cash=_positive_float(raw, "initial_cash"),
        trade_fraction=_fraction(raw, "trade_fraction"),
        fee_rate=_non_negative_float(raw, "fee_rate"),
        macro_mode=_choice(raw, "macro_mode", {"risk_on", "neutral", "risk_off"}),
        news_bias=_choice(raw, "news_bias", {"bullish", "neutral", "bearish"}),
        price_source=_choice_with_default(raw, "price_source", "bitget_public", {"bitget_public", "yahoo_chart_daily"}),
        ticker_map=_ticker_map(raw),
        decision_mode=_choice_with_default(raw, "decision_mode", "conservative", {"conservative", "aggressive_news"}),
    )


def _required_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"config field {key} must be a non-empty string")
    return value


def _positive_int(raw: dict[str, Any], key: str) -> int:
    value = int(raw.get(key, 0))
    if value <= 0:
        raise ValueError(f"config field {key} must be positive")
    return value


def _positive_float(raw: dict[str, Any], key: str) -> float:
    value = float(raw.get(key, 0))
    if value <= 0:
        raise ValueError(f"config field {key} must be positive")
    return value


def _non_negative_float(raw: dict[str, Any], key: str) -> float:
    value = float(raw.get(key, -1))
    if value < 0:
        raise ValueError(f"config field {key} must be non-negative")
    return value


def _fraction(raw: dict[str, Any], key: str) -> float:
    value = float(raw.get(key, 0))
    if value <= 0 or value > 1:
        raise ValueError(f"config field {key} must be in (0, 1]")
    return value


def _choice(raw: dict[str, Any], key: str, allowed: set[str]) -> str:
    value = _required_str(raw, key)
    if value not in allowed:
        raise ValueError(f"config field {key} must be one of {sorted(allowed)}")
    return value


def _choice_with_default(raw: dict[str, Any], key: str, default: str, allowed: set[str]) -> str:
    value = str(raw.get(key, default))
    if value not in allowed:
        raise ValueError(f"config field {key} must be one of {sorted(allowed)}")
    return value


def _ticker_map(raw: dict[str, Any]) -> dict[str, str]:
    value = raw.get("ticker_map", {})
    if not isinstance(value, dict):
        raise ValueError("config field ticker_map must be an object")
    return {str(symbol).upper(): str(ticker).upper() for symbol, ticker in value.items()}
