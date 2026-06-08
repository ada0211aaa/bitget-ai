# Bitget Backtest Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a safe, local, backtest-only Python implementation that fetches Bitget public stock USDT perpetual candles, generates cautious AI tech stock signals, and writes reproducible backtest reports.

**Architecture:** The first implementation is a small Python CLI with clear layers: config loading, public market-data client, indicator calculation, strategy signal generation, portfolio backtesting, and report writing. It uses only public Bitget market endpoints, stores no API keys, performs no live trading, and keeps all outputs under `data/` and `reports/`.

**Tech Stack:** Python 3.12 standard library, `pytest`, `argparse`, `urllib`, `json`, `csv`, `dataclasses`, and Markdown/CSV report artifacts.

---

## File Structure

- Create `pyproject.toml`: pytest configuration and package metadata.
- Create `configs/default_universe.json`: first-version Bitget stock USDT perpetual universe and strategy defaults.
- Create `src/bitget_ai_backtest/__init__.py`: package marker.
- Create `src/bitget_ai_backtest/models.py`: shared dataclasses for candles, indicators, signals, trades, and backtest results.
- Create `src/bitget_ai_backtest/config.py`: load and validate JSON config.
- Create `src/bitget_ai_backtest/bitget_client.py`: public Bitget candle API client and response parsing.
- Create `src/bitget_ai_backtest/indicators.py`: moving average, RSI, momentum, drawdown, and return helpers.
- Create `src/bitget_ai_backtest/strategy.py`: cautious signal engine using trend, RSI, momentum, volume, macro mode, and news bias.
- Create `src/bitget_ai_backtest/backtester.py`: single-symbol and multi-symbol long/cash backtest engine.
- Create `src/bitget_ai_backtest/reporting.py`: write CSV and Markdown reports.
- Create `src/bitget_ai_backtest/cli.py`: command-line entry point with `fetch`, `backtest`, and `demo` commands.
- Create `tests/fixtures/bitget_candles_nvda_15m.json`: deterministic Bitget-like candle fixture.
- Create `tests/test_config.py`: config validation tests.
- Create `tests/test_bitget_client.py`: response parsing and URL-building tests.
- Create `tests/test_indicators.py`: indicator math tests.
- Create `tests/test_strategy.py`: strategy signal tests.
- Create `tests/test_backtester.py`: backtest behavior tests.
- Create `tests/test_reporting.py`: report writer tests.
- Create `tests/test_cli.py`: CLI smoke tests with fixture data.
- Modify `README.md`: add local dry-run/backtest commands and safety boundary.
- Modify `docs/requirements/2026-06-07-bitget-playbook-ai-tech-stock-strategy.md`: mark implementation scope as local backtest-only.
- Modify `docs/playbook/backtest-record-template.md`: link local report fields to Playbook evidence fields.
- Modify `CHANGELOG.md` and `MEMORY.md`: record implementation addition and safety boundary.

---

## Task 1: Python Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/bitget_ai_backtest/__init__.py`
- Create: `src/bitget_ai_backtest/models.py`
- Create: `tests/test_models_import.py`

- [ ] **Step 1: Write the failing import test**

Create `tests/test_models_import.py`:

```python
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
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_models_import.py -q
```

Expected: FAIL because `bitget_ai_backtest.models` does not exist.

- [ ] **Step 3: Add minimal package metadata and models**

Create `pyproject.toml`:

```toml
[project]
name = "bitget-ai-backtest"
version = "0.1.0"
description = "Backtest-only Bitget stock USDT perpetual strategy demo"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

Create `src/bitget_ai_backtest/__init__.py`:

```python
"""Backtest-only Bitget AI hackathon package."""
```

Create `src/bitget_ai_backtest/models.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Candle:
    timestamp_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
```

- [ ] **Step 4: Run the test to verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_models_import.py -q
```

Expected: PASS.

---

## Task 2: Config Loading

**Files:**
- Create: `configs/default_universe.json`
- Create: `src/bitget_ai_backtest/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
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
    )


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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_config.py -q
```

Expected: FAIL because `bitget_ai_backtest.config` does not exist.

- [ ] **Step 3: Implement config loading**

Create `src/bitget_ai_backtest/config.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
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


def load_config(path: Path) -> BacktestConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    symbols = tuple(str(symbol).upper() for symbol in raw.get("symbols", []))
    if not symbols:
        raise ValueError("config must contain at least one symbol")

    config = BacktestConfig(
        symbols=symbols,
        granularity=_required_str(raw, "granularity"),
        limit=_positive_int(raw, "limit"),
        initial_cash=_positive_float(raw, "initial_cash"),
        trade_fraction=_fraction(raw, "trade_fraction"),
        fee_rate=_non_negative_float(raw, "fee_rate"),
        macro_mode=_choice(raw, "macro_mode", {"risk_on", "neutral", "risk_off"}),
        news_bias=_choice(raw, "news_bias", {"bullish", "neutral", "bearish"}),
    )
    return config


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
```

Create `configs/default_universe.json`:

```json
{
  "symbols": ["NVDAUSDT", "MSFTUSDT", "GOOGLUSDT", "AMDUSDT", "METAUSDT"],
  "granularity": "15m",
  "limit": 200,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral"
}
```

- [ ] **Step 4: Run config tests to verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_config.py -q
```

Expected: PASS.

---

## Task 3: Bitget Public Candle Client

**Files:**
- Create: `tests/fixtures/bitget_candles_nvda_15m.json`
- Create: `src/bitget_ai_backtest/bitget_client.py`
- Create: `tests/test_bitget_client.py`

- [ ] **Step 1: Write failing client tests**

Create `tests/fixtures/bitget_candles_nvda_15m.json`:

```json
{
  "code": "00000",
  "msg": "success",
  "requestTime": 1780918202490,
  "data": [
    ["1780914600000", "208.82", "209.49", "208.76", "209.38", "452.46", "94673.102"],
    ["1780915500000", "209.38", "209.45", "208.88", "208.88", "384.02", "80318.3708"],
    ["1780916400000", "208.88", "209.69", "208.58", "209.66", "515.34", "107725.8993"],
    ["1780917300000", "209.66", "210.42", "209.64", "210.04", "933.18", "195945.8038"]
  ]
}
```

Create `tests/test_bitget_client.py`:

```python
import json
from pathlib import Path

import pytest

from bitget_ai_backtest.bitget_client import BitgetPublicClient, parse_candles_response


def test_parse_candles_response_converts_strings_to_candles() -> None:
    raw = json.loads(Path("tests/fixtures/bitget_candles_nvda_15m.json").read_text(encoding="utf-8"))

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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_bitget_client.py -q
```

Expected: FAIL because `bitget_ai_backtest.bitget_client` does not exist.

- [ ] **Step 3: Implement public client and parser**

Create `src/bitget_ai_backtest/bitget_client.py`:

```python
from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen

from .models import Candle


class BitgetPublicClient:
    base_url = "https://api.bitget.com/api/v3/market/candles"

    def build_candles_url(self, symbol: str, interval: str, limit: int) -> str:
        params = urlencode(
            {
                "category": "USDT-FUTURES",
                "symbol": symbol.upper(),
                "interval": interval,
                "kLineType": "MARKET",
                "limit": str(limit),
            }
        )
        return f"{self.base_url}?{params}"

    def fetch_candles(self, symbol: str, interval: str, limit: int) -> list[Candle]:
        url = self.build_candles_url(symbol, interval, limit)
        with urlopen(url, timeout=15) as response:
            raw = json.loads(response.read().decode("utf-8"))
        return parse_candles_response(raw)


def parse_candles_response(raw: dict) -> list[Candle]:
    if raw.get("code") != "00000":
        raise ValueError(f"Bitget API error: {raw.get('code')} {raw.get('msg')}")
    rows = raw.get("data")
    if not isinstance(rows, list):
        raise ValueError("Bitget API response missing candle data")

    candles = [
        Candle(
            timestamp_ms=int(row[0]),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
            quote_volume=float(row[6]),
        )
        for row in rows
    ]
    candles.sort(key=lambda candle: candle.timestamp_ms)
    return candles
```

- [ ] **Step 4: Run client tests to verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_bitget_client.py -q
```

Expected: PASS.

---

## Task 4: Indicators

**Files:**
- Create: `src/bitget_ai_backtest/indicators.py`
- Create: `tests/test_indicators.py`

- [ ] **Step 1: Write failing indicator tests**

Create `tests/test_indicators.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_indicators.py -q
```

Expected: FAIL because `bitget_ai_backtest.indicators` does not exist.

- [ ] **Step 3: Implement indicators**

Create `src/bitget_ai_backtest/indicators.py`:

```python
from __future__ import annotations


def moving_average(values: list[float], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive")
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
            continue
        chunk = values[index + 1 - window : index + 1]
        result.append(sum(chunk) / window)
    return result


def pct_change(values: list[float], periods: int) -> float:
    if periods <= 0:
        raise ValueError("periods must be positive")
    if len(values) <= periods:
        return 0.0
    start = values[-1 - periods]
    if start == 0:
        return 0.0
    return values[-1] / start - 1.0


def rsi(values: list[float], window: int) -> float:
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) <= window:
        return 50.0
    gains = 0.0
    losses = 0.0
    recent = values[-(window + 1) :]
    for previous, current in zip(recent, recent[1:]):
        change = current - previous
        if change >= 0:
            gains += change
        else:
            losses += abs(change)
    if gains == 0 and losses == 0:
        return 50.0
    if losses == 0:
        return 100.0
    relative_strength = gains / losses
    return 100 - (100 / (1 + relative_strength))


def max_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst
```

- [ ] **Step 4: Run indicator tests to verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_indicators.py -q
```

Expected: PASS.

---

## Task 5: Strategy Signal Engine

**Files:**
- Modify: `src/bitget_ai_backtest/models.py`
- Create: `src/bitget_ai_backtest/strategy.py`
- Create: `tests/test_strategy.py`

- [ ] **Step 1: Write failing strategy tests**

Create `tests/test_strategy.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_strategy.py -q
```

Expected: FAIL because `bitget_ai_backtest.strategy` does not exist.

- [ ] **Step 3: Add signal model and strategy implementation**

Append to `src/bitget_ai_backtest/models.py`:

```python

@dataclass(frozen=True)
class StrategySignal:
    symbol: str
    timestamp_ms: int
    score: int
    view: str
    action: str
    close: float
    reasons: tuple[str, ...]
```

Create `src/bitget_ai_backtest/strategy.py`:

```python
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
    elif score >= 4:
        view = "bullish"
        action = "buy"
    elif score >= 2:
        view = "cautiously_bullish"
        action = "buy"
    elif score <= -3:
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
```

- [ ] **Step 4: Run strategy tests to verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_strategy.py -q
```

Expected: PASS.

---

## Task 6: Backtester

**Files:**
- Modify: `src/bitget_ai_backtest/models.py`
- Create: `src/bitget_ai_backtest/backtester.py`
- Create: `tests/test_backtester.py`

- [ ] **Step 1: Write failing backtester tests**

Create `tests/test_backtester.py`:

```python
from bitget_ai_backtest.backtester import backtest_symbol
from bitget_ai_backtest.models import Candle


def _candles(values: list[float]) -> list[Candle]:
    return [
        Candle(
            timestamp_ms=1000 + index,
            open=value,
            high=value + 1,
            low=value - 1,
            close=value,
            volume=1000,
            quote_volume=1000 * value,
        )
        for index, value in enumerate(values)
    ]


def test_backtest_symbol_generates_equity_curve_and_metrics() -> None:
    result = backtest_symbol(
        "NVDAUSDT",
        _candles([100, 101, 102, 103, 104, 105, 106, 107]),
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_on",
        news_bias="bullish",
    )

    assert result.symbol == "NVDAUSDT"
    assert result.final_equity > 10000
    assert result.total_return > 0
    assert len(result.equity_curve) == 8
    assert result.trades


def test_backtest_symbol_stays_in_cash_when_macro_blocks_bullish_news() -> None:
    result = backtest_symbol(
        "NVDAUSDT",
        _candles([100, 101, 102, 103, 104, 105, 106, 107]),
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_off",
        news_bias="bullish",
    )

    assert result.final_equity == 10000
    assert result.trades == ()
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_backtester.py -q
```

Expected: FAIL because `bitget_ai_backtest.backtester` does not exist.

- [ ] **Step 3: Add result models and backtester**

Append to `src/bitget_ai_backtest/models.py`:

```python

@dataclass(frozen=True)
class Trade:
    timestamp_ms: int
    symbol: str
    side: str
    price: float
    quantity: float
    fee: float
    reason: str


@dataclass(frozen=True)
class BacktestResult:
    symbol: str
    initial_cash: float
    final_equity: float
    total_return: float
    max_drawdown: float
    equity_curve: tuple[float, ...]
    trades: tuple[Trade, ...]
    last_signal: StrategySignal
```

Create `src/bitget_ai_backtest/backtester.py`:

```python
from __future__ import annotations

from .indicators import max_drawdown
from .models import BacktestResult, Candle, Trade
from .strategy import generate_signal


def backtest_symbol(
    symbol: str,
    candles: list[Candle],
    *,
    initial_cash: float,
    trade_fraction: float,
    fee_rate: float,
    macro_mode: str,
    news_bias: str,
) -> BacktestResult:
    cash = initial_cash
    quantity = 0.0
    trades: list[Trade] = []
    equity_curve: list[float] = []
    last_signal = None

    for index, candle in enumerate(candles):
        history = candles[: index + 1]
        if len(history) >= 3:
            signal = generate_signal(symbol, history, macro_mode=macro_mode, news_bias=news_bias)
            last_signal = signal
            if signal.action == "buy" and cash > 0:
                spend = cash * trade_fraction
                fee = spend * fee_rate
                net_spend = spend - fee
                bought = net_spend / candle.close
                quantity += bought
                cash -= spend
                trades.append(Trade(candle.timestamp_ms, symbol, "buy", candle.close, bought, fee, signal.view))
            elif signal.action == "sell" and quantity > 0:
                gross = quantity * candle.close
                fee = gross * fee_rate
                cash += gross - fee
                trades.append(Trade(candle.timestamp_ms, symbol, "sell", candle.close, quantity, fee, signal.view))
                quantity = 0.0
        equity_curve.append(cash + quantity * candle.close)

    if last_signal is None:
        last_signal = generate_signal(symbol, candles, macro_mode=macro_mode, news_bias=news_bias)

    final_equity = equity_curve[-1] if equity_curve else initial_cash
    total_return = final_equity / initial_cash - 1.0
    return BacktestResult(
        symbol=symbol,
        initial_cash=initial_cash,
        final_equity=final_equity,
        total_return=total_return,
        max_drawdown=max_drawdown(equity_curve),
        equity_curve=tuple(equity_curve),
        trades=tuple(trades),
        last_signal=last_signal,
    )
```

- [ ] **Step 4: Run backtester tests to verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_backtester.py -q
```

Expected: PASS.

---

## Task 7: Reporting

**Files:**
- Create: `src/bitget_ai_backtest/reporting.py`
- Create: `tests/test_reporting.py`

- [ ] **Step 1: Write failing report tests**

Create `tests/test_reporting.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_reporting.py -q
```

Expected: FAIL because `bitget_ai_backtest.reporting` does not exist.

- [ ] **Step 3: Implement report writer**

Create `src/bitget_ai_backtest/reporting.py`:

```python
from __future__ import annotations

import csv
from pathlib import Path

from .models import BacktestResult


def write_report(output_dir: Path, results: list[BacktestResult], *, config_name: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "backtest-report.md"
    trades_path = output_dir / "trades.csv"

    markdown_lines = [
        "# Bitget AI Local Backtest Report",
        "",
        "Backtest-only report. This does not use API keys, does not place orders, and does not represent live trading.",
        "",
        f"- Config: `{config_name}`",
        "",
        "| Symbol | Final Equity | Total Return | Max Drawdown | Last View | Trades |",
        "| --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for result in results:
        markdown_lines.append(
            "| {symbol} | {final:.2f} | {ret:.2%} | {drawdown:.2%} | {view} | {trades} |".format(
                symbol=result.symbol,
                final=result.final_equity,
                ret=result.total_return,
                drawdown=result.max_drawdown,
                view=result.last_signal.view,
                trades=len(result.trades),
            )
        )
    markdown_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    with trades_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp_ms", "symbol", "side", "price", "quantity", "fee", "reason"])
        for result in results:
            for trade in result.trades:
                writer.writerow(
                    [
                        trade.timestamp_ms,
                        trade.symbol,
                        trade.side,
                        f"{trade.price:.8f}",
                        f"{trade.quantity:.12f}",
                        f"{trade.fee:.8f}",
                        trade.reason,
                    ]
                )

    return {"markdown": markdown_path, "trades_csv": trades_path}
```

- [ ] **Step 4: Run reporting tests to verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_reporting.py -q
```

Expected: PASS.

---

## Task 8: CLI

**Files:**
- Create: `src/bitget_ai_backtest/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli.py`:

```python
from pathlib import Path

from bitget_ai_backtest.cli import main


def test_demo_command_writes_report_from_fixture(tmp_path: Path) -> None:
    exit_code = main(["demo", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "backtest-report.md").exists()
    assert (tmp_path / "trades.csv").exists()


def test_help_command_returns_zero() -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_cli.py -q
```

Expected: FAIL because `bitget_ai_backtest.cli` does not exist.

- [ ] **Step 3: Implement CLI with safe commands**

Create `src/bitget_ai_backtest/cli.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backtester import backtest_symbol
from .bitget_client import BitgetPublicClient, parse_candles_response
from .config import load_config
from .reporting import write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bitget stock futures backtest-only CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="Run deterministic fixture backtest")
    demo_parser.add_argument("--output-dir", type=Path, default=Path("reports/local-demo"))

    fetch_parser = subparsers.add_parser("fetch", help="Fetch public Bitget candles")
    fetch_parser.add_argument("--symbol", required=True)
    fetch_parser.add_argument("--granularity", default="15m")
    fetch_parser.add_argument("--limit", type=int, default=200)
    fetch_parser.add_argument("--output", type=Path, required=True)

    backtest_parser = subparsers.add_parser("backtest", help="Backtest from live public candles")
    backtest_parser.add_argument("--config", type=Path, default=Path("configs/default_universe.json"))
    backtest_parser.add_argument("--output-dir", type=Path, default=Path("reports/latest"))

    args = parser.parse_args(argv)

    if args.command == "demo":
        fixture = Path("tests/fixtures/bitget_candles_nvda_15m.json")
        candles = parse_candles_response(json.loads(fixture.read_text(encoding="utf-8")))
        result = backtest_symbol(
            "NVDAUSDT",
            candles,
            initial_cash=10000,
            trade_fraction=0.5,
            fee_rate=0.0,
            macro_mode="risk_on",
            news_bias="bullish",
        )
        paths = write_report(args.output_dir, [result], config_name="fixture-demo")
        print(f"Report written: {paths['markdown']}")
        return 0

    if args.command == "fetch":
        candles = BitgetPublicClient().fetch_candles(args.symbol, args.granularity, args.limit)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps([candle.__dict__ for candle in candles], indent=2), encoding="utf-8")
        print(f"Fetched {len(candles)} candles for {args.symbol.upper()} into {args.output}")
        return 0

    if args.command == "backtest":
        config = load_config(args.config)
        client = BitgetPublicClient()
        results = []
        for symbol in config.symbols:
            candles = client.fetch_candles(symbol, config.granularity, config.limit)
            result = backtest_symbol(
                symbol,
                candles,
                initial_cash=config.initial_cash,
                trade_fraction=config.trade_fraction,
                fee_rate=config.fee_rate,
                macro_mode=config.macro_mode,
                news_bias=config.news_bias,
            )
            results.append(result)
        paths = write_report(args.output_dir, results, config_name=str(args.config))
        print(f"Report written: {paths['markdown']}")
        return 0

    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests to verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_cli.py -q
```

Expected: PASS.

---

## Task 9: Documentation and Safe Local Run

**Files:**
- Modify: `README.md`
- Modify: `docs/playbook/backtest-record-template.md`
- Modify: `docs/requirements/2026-06-07-bitget-playbook-ai-tech-stock-strategy.md`
- Modify: `CHANGELOG.md`
- Modify: `MEMORY.md`

- [ ] **Step 1: Run full test suite before docs**

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
```

Expected: all tests PASS.

- [ ] **Step 2: Run deterministic demo**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli demo --output-dir reports/local-demo
```

Expected: command exits 0 and writes `reports/local-demo/backtest-report.md` plus `reports/local-demo/trades.csv`.

- [ ] **Step 3: Run public-data smoke backtest**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest --config configs/default_universe.json --output-dir reports/latest
```

Expected: command exits 0 and writes `reports/latest/backtest-report.md` plus `reports/latest/trades.csv`. If the public API is temporarily unavailable, capture the exact error and keep the deterministic demo as the verified fallback.

- [ ] **Step 4: Update docs with run commands and evidence**

Add to `README.md`:

```markdown
## Local Backtest Demo

This implementation is backtest-only. It uses Bitget public market data or deterministic fixtures. It does not use API keys and cannot place orders.

Run deterministic fixture demo:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli demo --output-dir reports/local-demo
```

Run public-data backtest:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest --config configs/default_universe.json --output-dir reports/latest
```

Outputs:

- `reports/local-demo/backtest-report.md`
- `reports/local-demo/trades.csv`
- `reports/latest/backtest-report.md`
- `reports/latest/trades.csv`
```

Add to `docs/playbook/backtest-record-template.md`:

```markdown
## Local Backtest Evidence

- Local report path:
- Local trades CSV path:
- Data source: Bitget public stock USDT perpetual candle endpoint or deterministic fixture.
- Safety boundary: backtest-only, no API key, no live orders.
```

Update the requirements document to say the first implementation now includes a local backtest CLI while Playbook remains the preferred official submission backtest once API access is available.

Update `CHANGELOG.md` with the local backtest implementation.

Update `MEMORY.md` with the verified run command and safety boundary.

- [ ] **Step 5: Final verification**

Run:

```bash
PYTHONPATH=src python3 -m pytest -q
git diff --check
rg -n -i "(API_KEY|API_SECRET|SECRET_KEY|PRIVATE_KEY|PASSPHRASE|PLAYBOOK_API_KEY|BITGET_API_KEY|BITGET_SECRET_KEY)\s*=\s*['\"]?[^<\s'\"]{6,}" .
git status --short
```

Expected:
- pytest PASS.
- `git diff --check` exits 0.
- secret assignment scan returns no matches.
- `git status --short` shows only intended docs, config, source, tests, and report artifacts.

---

## Self-Review

- Spec coverage: The plan implements local backtesting from public Bitget stock USDT perpetual candles, keeps Playbook as official future path, avoids API keys and live trading, writes evidence reports, and updates docs.
- Placeholder scan: The implementation steps contain concrete file paths, commands, expected outcomes, and code. There are no `TODO` or `TBD` placeholders.
- Type consistency: `Candle`, `StrategySignal`, `Trade`, and `BacktestResult` are introduced before use. CLI calls shared config, client, backtester, and reporting modules consistently.
