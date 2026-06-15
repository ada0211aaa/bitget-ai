# NVDA Decision Table Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-stock `NVDAUSDT / 英伟达` dashboard view with an Excel-like Chinese decision table that explains each backtest buy/sell action.

**Architecture:** Keep the current lightweight Python payload plus static HTML/CSS/JS dashboard. Add a derived `decision_rows` list in `web.py` from existing trade explanations and event records, then render that list in the browser as the main decision table. Do not change live trading behavior, strategy execution, account access, or secrets.

**Tech Stack:** Python 3, pytest, static HTML/CSS/JavaScript, built-in `ThreadingHTTPServer`.

---

### Task 1: Backend Decision Rows

**Files:**
- Modify: `src/bitget_ai_backtest/web.py`
- Modify: `tests/test_web.py`

- [ ] **Step 1: Write the failing test**

Add assertions in `tests/test_web.py` proving `build_dashboard_payload(...)` returns:

```python
assert payload["focus_symbol"] == {"symbol": "NVDAUSDT", "name": "英伟达"}
assert len(payload["decision_rows"]) == 1
row = payload["decision_rows"][0]
assert row["symbol"] == "NVDAUSDT"
assert row["symbol_name"] == "英伟达"
assert row["action"] == "买入"
assert row["price"] == "209.66"
assert row["event_title"] == "Nvidia raises guidance"
assert row["news_sentiment"] == "利好"
assert row["technical_reason"] == "暂无"
assert row["final_view"] == "未知"
assert "因为" in row["decision_reason"]
assert row["backtest_result"] == "待下一笔卖出或回测结算确认"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_web.py -q
```

Expected: fails because `focus_symbol` and `decision_rows` do not exist yet.

- [ ] **Step 3: Implement minimal backend**

In `web.py`, add `focus_symbol` and `decision_rows` to the payload. Create helper functions that:

- Filter trade explanations to `NVDAUSDT`.
- Use each explanation's `matched_event_details` when present.
- Fall back to `matched_events` plus the loaded event list by `event_id`.
- Format timestamp, price, quantity, side, sentiment, view, source, technical reasons, and Chinese decision reason.
- Mark missing news as `未匹配到 24 小时内新闻事件，主要由技术信号触发`.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_web.py -q
```

Expected: pass.

### Task 2: Static Shell For Excel-Like Table

**Files:**
- Modify: `src/bitget_ai_backtest/static/index.html`
- Modify: `tests/test_static_dashboard_ui.py`

- [ ] **Step 1: Write the failing test**

Add assertions that static HTML includes:

```python
assert "NVDA 单股票回测解释台" in html
assert "交易决策明细表" in html
assert 'id="decision-table"' in html
assert "为什么买 / 为什么卖" in html
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: fails because the static shell still uses the old headings.

- [ ] **Step 3: Update the static shell**

Change hero and main table section:

- H1 becomes `NVDA 单股票回测解释台`.
- Subtitle explains the page tracks real events, technical signals, and backtest actions.
- Replace the old summary-first layout with a `交易决策明细表` section containing table headers from the requirement.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: pass.

### Task 3: Frontend Rendering

**Files:**
- Modify: `src/bitget_ai_backtest/static/app.js`
- Modify: `src/bitget_ai_backtest/static/styles.css`
- Modify: `tests/test_static_dashboard_ui.py`

- [ ] **Step 1: Write the failing test**

Add assertions that `app.js` includes:

```python
assert "renderDecisionTable" in script
assert "未匹配到 24 小时内新闻事件" in script
assert "交易决策明细" in script
```

Add assertions that `styles.css` includes:

```python
assert ".decision-table" in css
assert ".reason-cell" in css
assert ".action-pill" in css
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: fails because render and table styles are missing.

- [ ] **Step 3: Implement frontend render**

In `app.js`:

- Display `focus_symbol`.
- Use `decision_rows` to populate `#decision-table tbody`.
- Keep the price chart and optional supporting sections.
- Filter event cards to `NVDAUSDT`.
- Show empty-state text when decision rows are absent.

In `styles.css`:

- Style `.decision-table` as dense dark spreadsheet-like table.
- Use action pills for buy/sell/observe.
- Make `.reason-cell` readable without over-expanding every row.
- Preserve mobile behavior where only the table wrapper scrolls horizontally.

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: pass.

### Task 4: Full Verification

**Files:**
- No new production files unless tests expose a gap.

- [ ] **Step 1: Run all tests**

Run:

```bash
python3 -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Start local foreground server**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web --config configs/default_universe.json --events data/events/us_stock_events.json --output-dir reports/latest --port 18769
```

Expected: foreground server prints local URL and can be stopped with `Ctrl+C`.

- [ ] **Step 3: Browser verification**

Open `http://127.0.0.1:18769` and verify:

- H1 is `NVDA 单股票回测解释台`.
- Page mentions `NVDAUSDT / 英伟达`.
- `#decision-table` exists and has rows.
- Table headers include `交易时间`, `动作`, `匹配新闻 / 事件标题`, `技术原因`, `为什么买 / 为什么卖`.
- No non-NVDA main decision rows appear.
- Mobile viewport has no page-level horizontal overflow; table wrapper may scroll horizontally.

- [ ] **Step 4: Stop local server**

Press `Ctrl+C` in the foreground terminal and confirm `Web demo stopped.`

### Spec Coverage Self-Review

- Single-stock default: covered by Task 1 payload and Task 2/3 UI.
- Excel-like decision table: covered by Task 2 and Task 3.
- Chinese explanations: covered by Task 1 row fields and Task 3 render.
- Missing news explanation: covered by Task 1 and Task 3.
- Safety boundary: preserved by not adding trading/account code and verifying existing safe notice remains.
- Minimal-change constraint: uses existing static page and `web.py`, no new framework or background process.
