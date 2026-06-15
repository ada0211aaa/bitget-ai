# News-First Conservative Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved `NVDA 新闻优先 + 技术确认保守型低频策略` requirement with conservative backtest decisions, observation rows, and `查看原文` source buttons.

**Architecture:** Keep the existing Python backtest and static dashboard. Add a small conservative policy module that evaluates news strength first and uses technical signals only as confirmation; wire it only into event-driven backtests so existing no-event demos remain stable. Persist decision records for trades and observations, then render those records in the existing dashboard table.

**Tech Stack:** Python 3, pytest, existing static HTML/CSS/JavaScript, built-in local HTTP server.

---

### Task 1: Conservative Policy Unit

**Files:**
- Create: `src/bitget_ai_backtest/conservative_policy.py`
- Modify: `tests/test_conservative_policy.py`

- [ ] **Step 1: Write failing tests**

Create tests proving:

- strong bullish news plus technical confirmation returns `buy`;
- bullish but not strong news returns `observe`;
- strong bullish without technical confirmation returns `observe`;
- no news with technical confirmation returns `observe`;
- repeat same-side action inside 12 hours returns `observe` with `冷却中`;
- strong bearish plus weak technical state returns `sell`;
- a decision with URL exposes the URL for `查看原文`.

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
python3 -m pytest tests/test_conservative_policy.py -q
```

Expected: fails because module does not exist.

- [ ] **Step 3: Implement the policy**

Implement `evaluate_conservative_decision(...)` with:

- event window: prior 24 hours;
- cooldown: 12 hours;
- strong bullish / bearish classification from event sentiment, confidence, and existing keyword reasons;
- technical confirmation from existing `generate_signal(...)` with neutral news bias;
- buy only for strong bullish + technical confirmation + cooldown clear;
- sell for strong bearish + technical weakness or position risk break;
- otherwise observe.

- [ ] **Step 4: Run the unit test and verify it passes**

Run:

```bash
python3 -m pytest tests/test_conservative_policy.py -q
```

Expected: pass.

### Task 2: Backtest Decision Records

**Files:**
- Modify: `src/bitget_ai_backtest/models.py`
- Modify: `src/bitget_ai_backtest/backtester.py`
- Modify: `src/bitget_ai_backtest/reporting.py`
- Modify: `src/bitget_ai_backtest/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing tests**

Update CLI tests to prove event-driven backtests:

- write `decision-records.json`;
- include observation rows;
- include news strength, technical confirmation, cooldown state, action, decision reason, and URL;
- produce fewer trades than decision records;
- do not buy when no strong news gate exists.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m pytest tests/test_cli.py -q
```

Expected: fails because `decision-records.json` does not exist.

- [ ] **Step 3: Wire the policy into backtest**

When `--events` is supplied:

- load events before fetching candles;
- pass matching symbol events into `backtest_symbol(...)`;
- use conservative policy instead of raw technical actions;
- store all decisions in `BacktestResult.decision_records`;
- write `reports/.../decision-records.json`.

No-event `demo` and legacy backtests keep existing behavior.

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
python3 -m pytest tests/test_cli.py -q
```

Expected: pass.

### Task 3: Dashboard Decision Rows And Source Buttons

**Files:**
- Modify: `src/bitget_ai_backtest/web.py`
- Modify: `src/bitget_ai_backtest/static/index.html`
- Modify: `src/bitget_ai_backtest/static/app.js`
- Modify: `src/bitget_ai_backtest/static/styles.css`
- Modify: `tests/test_web.py`
- Modify: `tests/test_static_dashboard_ui.py`

- [ ] **Step 1: Write failing tests**

Update tests to prove:

- dashboard payload prefers `decision-records.json`;
- decision rows contain `news_strength`, `news_direction`, `technical_confirmation`, `cooldown_state`, `news_url`, `source_action`;
- static table has headers for these fields and `查看原文`;
- JS renders a `target="_blank"` source link when `news_url` exists and a details fallback when no URL exists.

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
python3 -m pytest tests/test_web.py tests/test_static_dashboard_ui.py -q
```

Expected: fails because fields and render paths are missing.

- [ ] **Step 3: Implement dashboard rendering**

Update backend and frontend:

- read `decision-records.json` if present;
- fall back to old trade explanations if missing;
- add new columns to the decision table;
- render `查看原文` as `<a target="_blank" rel="noopener noreferrer">`;
- render no-URL structured signals as expandable details;
- render no-news rows as `无新闻来源`;
- keep the page read-only.

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
python3 -m pytest tests/test_web.py tests/test_static_dashboard_ui.py -q
```

Expected: pass.

### Task 4: Full Verification

**Files:**
- No extra production files unless tests expose a gap.

- [ ] **Step 1: Run full tests**

Run:

```bash
python3 -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Regenerate event-driven backtest artifacts**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest --config configs/default_universe.json --events data/events/us_stock_events.json --output-dir reports/latest
```

Expected: writes report, trades, explanations, candles, and decision records.

- [ ] **Step 3: Serve dashboard in foreground**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web --config configs/default_universe.json --events data/events/us_stock_events.json --output-dir reports/latest --port 18770
```

Expected: foreground local URL, stoppable with `Ctrl+C`.

- [ ] **Step 4: Browser verification**

Verify:

- table contains news strength, news direction, technical confirmation, cooldown state;
- strong-news rows expose `查看原文` buttons;
- URL buttons open new tab;
- no-news rows say `无新闻来源`;
- observation rows are visible;
- safe notice remains.

- [ ] **Step 5: Stop the server**

Use `Ctrl+C` and confirm `Web demo stopped.`

### Spec Coverage Self-Review

- News-first gate: Task 1 and Task 2.
- Technical confirmation: Task 1 and Task 2.
- Conservative low-frequency cooldown: Task 1 and Task 2.
- Observation rows: Task 2 and Task 3.
- `查看原文` source traceability: Task 3 and Task 4.
- Safety boundary: no account/order/live trading code; verified in Task 4.
