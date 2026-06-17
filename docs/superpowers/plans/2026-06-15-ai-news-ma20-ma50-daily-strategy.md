# AI News MA20 MA50 Daily Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make daily backtests use AI/Bitget skill news strength as the trade gate and MA20/MA50 as technical confirmation, while writing full decisions and chart markers.

**Architecture:** Extend `NewsEvent` and event loading first, then replace conservative daily decision logic with a MA20/MA50-aware evaluator. Keep AI as structured news judgment only; trading remains deterministic and backtest-only.

**Tech Stack:** Python standard library, pytest, existing vanilla JS dashboard.

---

## File Structure

- Modify `src/bitget_ai_backtest/models.py`: extend `DecisionRecord` with `news_topic`, `news_time_horizon`, and `stock_relevance`.
- Modify `src/bitget_ai_backtest/events.py`: extend `NewsEvent` with `strength`, `topic`, `time_horizon`, and `stock_relevance`; preserve backward compatibility.
- Modify `src/bitget_ai_backtest/conservative_policy.py`: implement MA20/MA50 daily rules and sell rule A.
- Modify `src/bitget_ai_backtest/backtester.py`: track entry/high watermark needed for 12% trailing drawdown.
- Modify `src/bitget_ai_backtest/web.py`: expose new decision fields.
- Modify `src/bitget_ai_backtest/static/index.html`: add decision table columns.
- Modify `src/bitget_ai_backtest/static/app.js`: render new columns and labels.
- Modify tests in `tests/test_events.py`, `tests/test_conservative_policy.py`, `tests/test_cli.py`, `tests/test_web.py`, `tests/test_static_dashboard_ui.py`.

## Task 1: Event Schema Extension

**Files:**
- Modify: `src/bitget_ai_backtest/events.py`
- Test: `tests/test_events.py`

- [x] **Step 1: Add failing event schema tests**

Add tests proving Bitget skill exports can include:

```json
{
  "strength": "strong",
  "topic": "earnings_guidance",
  "time_horizon": "medium_term",
  "stock_relevance": "direct"
}
```

Also test older events without these fields still load.

- [x] **Step 2: Run event tests to verify they fail**

Run: `python3 -m pytest tests/test_events.py -q`

- [x] **Step 3: Implement schema fields**

Add optional/default fields to `NewsEvent`, `load_events`, `_load_bitget_skill_exports`, and Yahoo fallback creation.

- [x] **Step 4: Run event tests**

Run: `python3 -m pytest tests/test_events.py -q`

## Task 2: Decision Record Fields

**Files:**
- Modify: `src/bitget_ai_backtest/models.py`
- Modify: `src/bitget_ai_backtest/conservative_policy.py`
- Test: `tests/test_conservative_policy.py`

- [x] **Step 1: Add failing decision field test**

Assert a decision created from a structured event includes `news_topic`, `news_time_horizon`, and `stock_relevance`.

- [x] **Step 2: Run selected test to verify it fails**

Run: `python3 -m pytest tests/test_conservative_policy.py::test_structured_news_fields_are_written_to_decision -q`

- [x] **Step 3: Add decision fields**

Extend `DecisionRecord` and populate fields from the selected event.

- [x] **Step 4: Run conservative policy tests**

Run: `python3 -m pytest tests/test_conservative_policy.py -q`

## Task 3: MA20/MA50 Buy Gate

**Files:**
- Modify: `src/bitget_ai_backtest/conservative_policy.py`
- Test: `tests/test_conservative_policy.py`

- [x] **Step 1: Add failing MA20/MA50 tests**

Add tests:

- strong bullish + MA20 above MA50 + close above MA50 + RSI below 75 buys.
- strong bullish + RSI above/equal 75 observes.
- strong bullish + MA20 below MA50 observes.

- [x] **Step 2: Run selected tests to verify they fail**

Run: `python3 -m pytest tests/test_conservative_policy.py -q`

- [x] **Step 3: Implement MA20/MA50 confirmation**

Replace short `generate_signal` confirmation in `evaluate_conservative_decision` with daily technical confirmation using MA20, MA50, MA50 slope, and RSI.

- [x] **Step 4: Run conservative policy tests**

Run: `python3 -m pytest tests/test_conservative_policy.py -q`

## Task 4: Sell Rule A

**Files:**
- Modify: `src/bitget_ai_backtest/conservative_policy.py`
- Modify: `src/bitget_ai_backtest/backtester.py`
- Test: `tests/test_conservative_policy.py`

- [x] **Step 1: Add failing sell rule tests**

Add tests:

- strong bearish event sells while in position.
- close below MA50 sells while in position.
- high watermark drawdown >= 12% sells while in position.

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_conservative_policy.py -q`

- [x] **Step 3: Implement sell rule A**

Track position high watermark in `backtester.py` and pass it into `evaluate_conservative_decision`.

- [x] **Step 4: Run conservative and backtester tests**

Run: `python3 -m pytest tests/test_conservative_policy.py tests/test_backtester.py -q`

## Task 5: Decisions And Markers For Real Trades

**Files:**
- Modify: `src/bitget_ai_backtest/backtester.py`
- Test: `tests/test_cli.py`

- [x] **Step 1: Add failing CLI marker assertion**

Use a small synthetic event file that should trigger at least one buy and one sell. Assert `decision-records.json` and `markers.json` both contain buy/sell rows.

- [x] **Step 2: Run selected CLI test to verify it fails**

Run: `python3 -m pytest tests/test_cli.py::test_backtest_news_daily_strategy_writes_buy_sell_markers -q`

- [x] **Step 3: Ensure fills attach to decisions**

Make sure every buy/sell generated by conservative policy writes a filled `DecisionRecord`.

- [x] **Step 4: Run selected CLI test**

Run: `python3 -m pytest tests/test_cli.py::test_backtest_news_daily_strategy_writes_buy_sell_markers -q`

## Task 6: Dashboard Fields

**Files:**
- Modify: `src/bitget_ai_backtest/web.py`
- Modify: `src/bitget_ai_backtest/static/index.html`
- Modify: `src/bitget_ai_backtest/static/app.js`
- Test: `tests/test_web.py`
- Test: `tests/test_static_dashboard_ui.py`

- [x] **Step 1: Add failing dashboard tests**

Assert payload and static UI include topic, impact horizon, and stock relevance fields.

- [x] **Step 2: Run dashboard tests to verify they fail**

Run: `python3 -m pytest tests/test_web.py tests/test_static_dashboard_ui.py -q`

- [x] **Step 3: Render new fields**

Expose and render `news_topic`, `news_time_horizon`, and `stock_relevance`.

- [x] **Step 4: Run dashboard tests**

Run: `python3 -m pytest tests/test_web.py tests/test_static_dashboard_ui.py -q`

## Task 7: Full Verification

**Files:**
- No extra code files unless earlier tasks require adjustments.

- [x] **Step 1: Run full test suite**

Run: `python3 -m pytest -q`

- [x] **Step 2: Run external daily events smoke**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/us_stock_daily_external.json \
  --events data/events/us_stock_events.json \
  --output-dir reports/us-stock-daily-external-events
```

- [x] **Step 3: Inspect markers and decisions**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
base = Path("reports/us-stock-daily-external-events")
print(len(json.loads((base / "decision-records.json").read_text())["decision_records"]))
print(len(json.loads((base / "markers.json").read_text())["markers"]))
PY
```

- [x] **Step 4: Do not leave a web server running**

If a web server is started for manual browser checks, start it in the foreground and stop it before final response.

