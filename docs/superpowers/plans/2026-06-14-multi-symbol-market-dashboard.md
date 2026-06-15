# Multi-Symbol Market Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing local web demo from a fixed NVDA detail page into a multi-symbol market list with clickable single-symbol detail views.

**Architecture:** Keep the current Python static-file server and vanilla HTML/CSS/JS frontend. `web.py` will emit all-symbol dashboard data and a `symbol_overview` list; `app.js` will use hash routing to render either the market list or a selected symbol detail view.

**Tech Stack:** Python 3.12, stdlib HTTP server, vanilla HTML/CSS/JS, pytest.

---

## Files

- Modify: `src/bitget_ai_backtest/web.py`
  - Stop hard-filtering payload to only `NVDAUSDT`.
  - Add all-symbol `decision_rows`, all relevant events, and `symbol_overview`.
- Modify: `src/bitget_ai_backtest/static/index.html`
  - Change shell title and sections from single-stock detail to market list + detail containers.
- Modify: `src/bitget_ai_backtest/static/app.js`
  - Add hash route parsing.
  - Render market list at `/`.
  - Render selected symbol detail at `/#/symbol/<SYMBOL>`.
  - Filter decisions, trades, events, and price series by selected symbol.
- Modify: `src/bitget_ai_backtest/static/styles.css`
  - Add market table, detail header, row click, back button, and selected symbol styles.
- Modify: `tests/test_web.py`
  - Cover multi-symbol payload and `symbol_overview`.
- Modify: `tests/test_static_dashboard_ui.py`
  - Cover Chinese shell, market list labels, hash routing hooks, and detail labels.

## Task 1: Backend Payload For All Symbols

**Files:**
- Modify: `tests/test_web.py`
- Modify: `src/bitget_ai_backtest/web.py`

- [x] **Step 1: Extend failing web payload test**

Update `tests/test_web.py` so the fixture config contains both `NVDAUSDT` and `AMDUSDT`.

Add AMD rows to:

```python
(report_dir / "backtest-report.md").write_text(
    """
# Bitget AI Local Backtest Report

| Symbol | Final Equity | Total Return | Max Drawdown | Last View | Trades |
| --- | ---: | ---: | ---: | --- | ---: |
| NVDAUSDT | 10020.00 | 0.20% | -0.10% | cautiously_bullish | 1 |
| AMDUSDT | 10080.00 | 0.80% | -0.20% | neutral_observe | 1 |
""".strip(),
    encoding="utf-8",
)
```

Add one AMD candle:

```python
candles.write_text(
    json.dumps(
        {
            "NVDAUSDT": [{"timestamp_ms": 1780916400000, "close": 209.66}],
            "AMDUSDT": [{"timestamp_ms": 1780916400000, "close": 511.06}],
        }
    ),
    encoding="utf-8",
)
```

Add one AMD decision record:

```python
{
    "timestamp_ms": 1780916400000,
    "symbol": "AMDUSDT",
    "action": "buy",
    "price": 511.06,
    "quantity": 1,
    "fee": 0,
    "news_strength": "强利好",
    "news_direction": "看多",
    "technical_confirmation": "已确认",
    "cooldown_state": "可交易",
    "decision_reason": "强利好新闻成立，并且技术面确认，所以回测触发买入。",
    "final_view": "看多",
    "technical_reasons": [],
    "event_id": "amd-event-1",
    "news_title": "AMD gets monster price target",
    "news_source": "Yahoo Finance RSS",
    "news_source_type": "public_news_fallback",
    "news_published_at": "2026-06-08T10:00:00Z",
    "news_url": "https://example.com/amd",
    "news_sentiment": "bullish",
    "news_source_action": "查看原文",
}
```

Add assertions:

```python
assert [row["symbol"] for row in payload["symbol_overview"]] == ["NVDAUSDT", "AMDUSDT"]
amd_overview = next(row for row in payload["symbol_overview"] if row["symbol"] == "AMDUSDT")
assert amd_overview["latest_price"] == "511.06"
assert amd_overview["total_return"] == "0.80%"
assert amd_overview["latest_action"] == "买入"
assert amd_overview["latest_news_strength"] == "强利好"
assert amd_overview["latest_technical_confirmation"] == "已确认"
assert {row["symbol"] for row in payload["decision_rows"]} == {"NVDAUSDT", "AMDUSDT"}
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_web.py -q
```

Expected: FAIL because `symbol_overview` does not exist and `decision_rows` is still fixed to `NVDAUSDT`.

- [x] **Step 3: Implement all-symbol payload**

In `src/bitget_ai_backtest/web.py`:

1. Replace fixed `FOCUS_SYMBOL` usage in payload construction with all-symbol processing.
2. Add:

```python
SYMBOL_NAMES = {
    "NVDAUSDT": "英伟达",
    "MSFTUSDT": "微软",
    "GOOGLUSDT": "谷歌",
    "AMDUSDT": "AMD",
    "METAUSDT": "Meta",
}
```

3. Add:

```python
def _symbol_name(symbol: str) -> str:
    return SYMBOL_NAMES.get(symbol, symbol.replace("USDT", ""))
```

4. Change `_decision_record_row` and `_decision_row` to use `_symbol_name(symbol)` instead of `FOCUS_SYMBOL["name"]`.
5. Build decision rows for all symbols:

```python
decision_rows = _build_decision_rows(decision_records, trade_explanations, events, config.symbols)
```

6. Change `_build_decision_rows` signature to accept `symbols: tuple[str, ...]` and filter `row.get("symbol") in set(symbols)`.
7. Add `_build_symbol_overview(config_symbols, summary, trades, decision_rows, price_series)`.

Overview logic:

```python
def _build_symbol_overview(config_symbols, summary, trades, decision_rows, price_series):
    summary_by_symbol = {row["symbol"]: row for row in summary}
    trades_by_symbol = _group_by_symbol(trades)
    decisions_by_symbol = _group_by_symbol(decision_rows)
    overview = []
    for symbol in config_symbols:
        latest_decision = decisions_by_symbol.get(symbol, [])[-1] if decisions_by_symbol.get(symbol) else {}
        latest_price = _latest_close(price_series.get(symbol, []))
        summary_row = summary_by_symbol.get(symbol, {})
        overview.append({
            "symbol": symbol,
            "symbol_name": _symbol_name(symbol),
            "latest_price": _format_number(latest_price, digits=2),
            "total_return": str(summary_row.get("total_return", "")),
            "max_drawdown": str(summary_row.get("max_drawdown", "")),
            "last_view": _translate_view(str(summary_row.get("last_view", ""))),
            "trade_count": str(summary_row.get("trades", len(trades_by_symbol.get(symbol, [])))),
            "latest_action": str(latest_decision.get("action", "观望")),
            "latest_news_strength": str(latest_decision.get("news_strength", "无新闻")),
            "latest_technical_confirmation": str(latest_decision.get("technical_confirmation", "未记录")),
        })
    return overview
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_web.py -q
```

Expected: PASS.

## Task 2: Static Shell For Market List And Detail Views

**Files:**
- Modify: `tests/test_static_dashboard_ui.py`
- Modify: `src/bitget_ai_backtest/static/index.html`

- [x] **Step 1: Update failing static shell test**

Update `tests/test_static_dashboard_ui.py`:

```python
assert "<title>Bitget 多票回测行情台</title>" in html
assert "Bitget 多票回测行情台" in html
assert "回测行情列表" in html
assert 'id="market-view"' in html
assert 'id="detail-view"' in html
assert 'id="market-table"' in html
assert 'id="detail-title"' in html
assert "返回行情列表" in html
```

Remove assertions that require the title `NVDA 单股票回测解释台`.

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: FAIL because the static shell is still single-stock oriented.

- [x] **Step 3: Update HTML shell**

In `src/bitget_ai_backtest/static/index.html`:

1. Change title to `Bitget 多票回测行情台`.
2. Change H1 to `Bitget 多票回测行情台`.
3. Add two top-level view containers:

```html
<section id="market-view" class="view-stack">
  ...
</section>
<section id="detail-view" class="view-stack" hidden>
  ...
</section>
```

4. Move existing decision table, chart, explanations, events into `detail-view`.
5. Add market table in `market-view`:

```html
<table id="market-table" class="market-table">
  <thead>
    <tr>
      <th>标的</th>
      <th>最新价</th>
      <th>回测收益</th>
      <th>最大回撤</th>
      <th>最新观点</th>
      <th>交易次数</th>
      <th>最新动作</th>
      <th>新闻强度</th>
      <th>技术确认</th>
      <th>详情</th>
    </tr>
  </thead>
  <tbody></tbody>
</table>
```

6. Add detail heading:

```html
<button id="back-to-market" class="back-button" type="button">返回行情列表</button>
<h2 id="detail-title">单票运行详情</h2>
```

- [x] **Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: PASS.

## Task 3: Frontend Hash Routing And Market Table

**Files:**
- Modify: `tests/test_static_dashboard_ui.py`
- Modify: `src/bitget_ai_backtest/static/app.js`
- Modify: `src/bitget_ai_backtest/static/styles.css`

- [x] **Step 1: Add failing static JS/CSS assertions**

In `tests/test_static_dashboard_ui.py`, assert:

```python
assert "renderMarketTable" in script
assert "renderDetailView" in script
assert "getSelectedSymbolFromHash" in script
assert "window.addEventListener(\"hashchange\"" in script
assert "location.hash = `#/symbol/${row.symbol}`" in script
assert ".market-table" in css
assert ".back-button" in css
assert ".clickable-row" in css
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: FAIL because these functions and styles do not exist.

- [x] **Step 3: Implement hash routing**

In `app.js`:

1. Store payload globally:

```javascript
let dashboardData = null;
```

2. In `loadDashboard`, set `dashboardData = data`, render market table, then route:

```javascript
dashboardData = data;
renderConfig(data.config);
renderMarketTable(data.symbol_overview || []);
routeDashboard();
window.addEventListener("hashchange", routeDashboard);
```

3. Add:

```javascript
function getSelectedSymbolFromHash() {
  const match = location.hash.match(/^#\/symbol\/([^/]+)$/);
  return match ? decodeURIComponent(match[1]).toUpperCase() : "";
}
```

4. Add:

```javascript
function routeDashboard() {
  if (!dashboardData) return;
  const selected = getSelectedSymbolFromHash();
  if (selected) renderDetailView(dashboardData, selected);
  else renderMarketView(dashboardData);
}
```

5. Add `renderMarketView` and `renderDetailView`.

6. `renderDetailView(data, symbol)` must filter:

```javascript
const summaryRows = filterBySymbol(data.summary, symbol);
const decisions = filterBySymbol(data.decision_rows, symbol);
const explanations = filterBySymbol(data.trade_explanations, symbol);
const events = filterBySymbol(data.events, symbol);
```

7. If symbol does not exist:

```javascript
detailTitle.textContent = `${symbol} 未找到`;
decision body shows no rows;
```

- [x] **Step 4: Implement market table**

Add:

```javascript
function renderMarketTable(rows) {
  const body = document.querySelector("#market-table tbody");
  if (!rows.length) {
    body.innerHTML = `<tr><td colspan="10" class="empty-cell">暂无回测行情列表。请先运行 backtest。</td></tr>`;
    return;
  }
  body.innerHTML = rows.map((row) => `
    <tr class="clickable-row" data-symbol="${escapeHtml(row.symbol)}">
      <td><span class="symbol">${escapeHtml(row.symbol)}<br>${escapeHtml(row.symbol_name)}</span></td>
      <td>${escapeHtml(row.latest_price)}</td>
      <td>${formatSignedCell(row.total_return)}</td>
      <td>${formatSignedCell(row.max_drawdown)}</td>
      <td><span class="view-pill">${escapeHtml(row.last_view)}</span></td>
      <td>${escapeHtml(row.trade_count)}</td>
      <td>${renderActionPill(row.latest_action)}</td>
      <td>${renderStrengthPill(row.latest_news_strength)}</td>
      <td>${renderConfirmationPill(row.latest_technical_confirmation)}</td>
      <td><button class="detail-link" type="button" data-symbol="${escapeHtml(row.symbol)}">查看详情</button></td>
    </tr>
  `).join("");
  body.querySelectorAll("[data-symbol]").forEach((node) => {
    node.addEventListener("click", () => {
      const symbol = node.getAttribute("data-symbol");
      if (symbol) location.hash = `#/symbol/${symbol}`;
    });
  });
}
```

- [x] **Step 5: Add styles**

In `styles.css` add:

```css
.view-stack[hidden] {
  display: none;
}

.market-table {
  min-width: 1080px;
}

.clickable-row {
  cursor: pointer;
}

.detail-link,
.back-button {
  border-radius: 6px;
  border: 1px solid rgba(0, 212, 255, 0.44);
  background: rgba(0, 212, 255, 0.12);
  color: #8deaff;
  cursor: pointer;
  font-weight: 800;
  padding: 8px 10px;
}
```

- [x] **Step 6: Run static tests**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: PASS.

## Task 4: Full Verification And Browser Check

**Files:**
- No required code changes unless verification reveals a bug.

- [x] **Step 1: Run full test suite**

Run:

```bash
python3 -m pytest -q
```

Expected: PASS.

- [x] **Step 2: Verify existing latest reports**

For this implementation pass, reuse the existing five-symbol `reports/latest` outputs and verify that `dashboard-data.json` exposes the new all-symbol overview. If fresh market data is needed later, rerun:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/default_universe.json \
  --events data/events/us_stock_events.json \
  --output-dir reports/latest
```

Expected report files:

```text
reports/latest/backtest-report.md
reports/latest/candles.json
reports/latest/trade-explanations.json
reports/latest/decision-records.json
```

- [x] **Step 3: Start local server in foreground**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web \
  --config configs/default_universe.json \
  --output-dir reports/latest \
  --events data/events/us_stock_events.json \
  --port 8001
```

Expected:

```text
Bitget AI Web Demo running at http://127.0.0.1:8001
Press Ctrl+C to stop.
```

- [x] **Step 4: Browser verify**

Open `http://127.0.0.1:8001` and verify:

1. Root page shows market list table.
2. Table shows at least `NVDAUSDT`, `MSFTUSDT`, `GOOGLUSDT`, `AMDUSDT`, `METAUSDT`.
3. Clicking `AMDUSDT` changes URL to `/#/symbol/AMDUSDT`.
4. AMD detail page shows AMD chart, AMD decisions, AMD events, and original news links.
5. Back button returns to root list.
6. Safety notice remains visible.

- [x] **Step 5: Stop server**

Press `Ctrl+C` in the foreground terminal.

## Self-Review

### Spec Coverage

- Multi-symbol market list: Task 1, Task 2, Task 3.
- Single-symbol detail view: Task 2, Task 3, Task 4.
- Same port and no new framework: Task 2 and Task 3 modify current static frontend only.
- Backtest-only safety: Task 4 browser check includes safety notice.
- Original news link retention: Task 3 reuses existing source-action renderer; Task 4 verifies.

### Placeholder Scan

No TODO, TBD, or undefined placeholder steps remain.

### Type Consistency

The plan consistently uses `symbol_overview`, `decision_rows`, `price_series`, `events`, and existing translated row fields from `web.py`.
