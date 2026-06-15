# AMD Daily Price Curve Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fetch and persist AMDUSDT daily candles, generate a safe backtest-only AMD daily report, and show the AMD daily price curve with clear coverage dates.

**Architecture:** Keep the current Python CLI, public Bitget market client, stdlib static web server, and vanilla JS canvas chart. Add the smallest possible daily-data path by reusing `fetch`, `backtest`, `write_candles_snapshot`, and existing dashboard payload fields; add coverage metadata so the UI can explain what time range the curve covers.

**Tech Stack:** Python 3.12, stdlib HTTP server, Bitget public market candles endpoint, vanilla HTML/CSS/JS, pytest.

---

## Files

- Create: `configs/amd_daily.json`
  - Single-symbol AMDUSDT daily backtest config.
- Modify: `src/bitget_ai_backtest/reporting.py`
  - Include `source` and `date` in candle snapshots.
  - Write `coverage.json` from candle snapshots.
- Modify: `src/bitget_ai_backtest/cli.py`
  - Let `backtest` write coverage after candles are fetched.
  - Keep commands foreground and backtest-only.
- Modify: `src/bitget_ai_backtest/web.py`
  - Add `coverage` to `dashboard-data.json`.
  - Add coverage fields to `symbol_overview`.
- Modify: `src/bitget_ai_backtest/static/index.html`
  - Add coverage labels in the detail page.
- Modify: `src/bitget_ai_backtest/static/app.js`
  - Render AMD daily coverage dates near the curve.
  - Keep the current canvas curve rendering.
- Modify: `tests/test_reporting.py`
  - Cover candle snapshot fields and coverage generation.
- Modify: `tests/test_web.py`
  - Cover payload coverage and symbol overview coverage.
- Modify: `tests/test_static_dashboard_ui.py`
  - Cover Chinese coverage labels and rendering hooks.

Generated after implementation:

- `data/daily/amdusdt-daily-candles.json`
- `reports/amd-daily/backtest-report.md`
- `reports/amd-daily/trades.csv`
- `reports/amd-daily/candles.json`
- `reports/amd-daily/coverage.json`

## Task 1: AMD Daily Config

**Files:**
- Create: `configs/amd_daily.json`

- [x] **Step 1: Create daily config**

Create `configs/amd_daily.json`:

```json
{
  "symbols": ["AMDUSDT"],
  "granularity": "1d",
  "limit": 1000,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral"
}
```

- [x] **Step 2: Validate config loads**

Run:

```bash
python3 -m pytest tests/test_config.py -q
```

Expected: PASS.

## Task 2: Candle Snapshot Dates And Coverage

**Files:**
- Modify: `tests/test_reporting.py`
- Modify: `src/bitget_ai_backtest/reporting.py`

- [x] **Step 1: Add failing reporting test**

Append to `tests/test_reporting.py`:

```python
import json

from bitget_ai_backtest.reporting import write_candles_snapshot, write_coverage


def test_write_candles_snapshot_includes_date_source_and_coverage(tmp_path: Path) -> None:
    candles = [
        Candle(1780876800000, 100, 102, 99, 101, 1000, 101000),
        Candle(1780963200000, 101, 104, 100, 103, 1200, 123600),
    ]

    candles_path = write_candles_snapshot(tmp_path, {"AMDUSDT": candles}, source="bitget_public")
    coverage_path = write_coverage(tmp_path, {"AMDUSDT": candles}, interval="1d", source="bitget_public")

    candles_payload = json.loads(candles_path.read_text(encoding="utf-8"))
    coverage_payload = json.loads(coverage_path.read_text(encoding="utf-8"))

    assert candles_payload["AMDUSDT"][0]["date"] == "2026-06-08"
    assert candles_payload["AMDUSDT"][0]["source"] == "bitget_public"
    assert coverage_payload["symbols"]["AMDUSDT"]["interval"] == "1d"
    assert coverage_payload["symbols"]["AMDUSDT"]["rows"] == 2
    assert coverage_payload["symbols"]["AMDUSDT"]["start_date"] == "2026-06-08"
    assert coverage_payload["symbols"]["AMDUSDT"]["end_date"] == "2026-06-09"
```

- [x] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_reporting.py -q
```

Expected: FAIL because `write_coverage` does not exist and candle snapshot does not include `date` / `source`.

- [x] **Step 3: Implement snapshot metadata and coverage**

In `src/bitget_ai_backtest/reporting.py`:

1. Import `UTC` and `datetime`:

```python
from datetime import UTC, datetime
```

2. Add:

```python
def _date_from_timestamp_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).strftime("%Y-%m-%d")
```

3. Change `write_candles_snapshot` signature:

```python
def write_candles_snapshot(output_dir: Path, candles_by_symbol: dict, *, source: str = "bitget_public") -> Path:
```

4. Add `date`, `source`, and `quote_volume` fields to each candle payload:

```python
{
    "date": _date_from_timestamp_ms(candle.timestamp_ms),
    "timestamp_ms": candle.timestamp_ms,
    "open": candle.open,
    "high": candle.high,
    "low": candle.low,
    "close": candle.close,
    "volume": candle.volume,
    "quote_volume": candle.quote_volume,
    "source": source,
}
```

5. Add:

```python
def write_coverage(output_dir: Path, candles_by_symbol: dict, *, interval: str, source: str = "bitget_public") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "coverage.json"
    symbols = {}
    for symbol, candles in candles_by_symbol.items():
        rows = list(candles)
        if rows:
            start_date = _date_from_timestamp_ms(rows[0].timestamp_ms)
            end_date = _date_from_timestamp_ms(rows[-1].timestamp_ms)
        else:
            start_date = ""
            end_date = ""
        symbols[symbol] = {
            "symbol": symbol,
            "interval": interval,
            "source": source,
            "rows": len(rows),
            "start_date": start_date,
            "end_date": end_date,
            "kline_coverage": f"{start_date} -> {end_date}" if start_date and end_date else "",
            "news_coverage": "",
            "effective_backtest_coverage": f"{start_date} -> {end_date}" if start_date and end_date else "",
        }
    path.write_text(json.dumps({"symbols": symbols}, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
```

- [x] **Step 4: Run reporting tests**

Run:

```bash
python3 -m pytest tests/test_reporting.py -q
```

Expected: PASS.

## Task 3: CLI Writes Coverage

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/bitget_ai_backtest/cli.py`

- [x] **Step 1: Add failing CLI assertion**

In `tests/test_cli.py`, in `test_backtest_command_with_events_writes_trade_explanations`, add:

```python
assert (output_dir / "coverage.json").exists()
```

Also assert the command output contains:

```python
assert "Coverage written:" in captured
```

If the test does not yet capture stdout, add `capsys` to the test signature and after `main([...])` add:

```python
captured = capsys.readouterr().out
```

- [x] **Step 2: Run CLI test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_cli.py::test_backtest_command_with_events_writes_trade_explanations -q
```

Expected: FAIL because coverage is not written.

- [x] **Step 3: Implement coverage writing**

In `src/bitget_ai_backtest/cli.py`:

1. Change import:

```python
from .reporting import write_candles_snapshot, write_coverage, write_decision_records, write_report
```

2. In the `backtest` command after `write_candles_snapshot`:

```python
coverage_path = write_coverage(args.output_dir, candles_by_symbol, interval=config.granularity)
print(f"Coverage written: {coverage_path}")
```

- [x] **Step 4: Run CLI test**

Run:

```bash
python3 -m pytest tests/test_cli.py::test_backtest_command_with_events_writes_trade_explanations -q
```

Expected: PASS.

## Task 4: Web Payload Coverage

**Files:**
- Modify: `tests/test_web.py`
- Modify: `src/bitget_ai_backtest/web.py`

- [x] **Step 1: Add failing web payload assertions**

In `tests/test_web.py`, create `coverage.json` in the report fixture:

```python
(report_dir / "coverage.json").write_text(
    json.dumps(
        {
            "symbols": {
                "NVDAUSDT": {
                    "symbol": "NVDAUSDT",
                    "interval": "1d",
                    "source": "bitget_public",
                    "rows": 2,
                    "start_date": "2026-06-08",
                    "end_date": "2026-06-09",
                    "kline_coverage": "2026-06-08 -> 2026-06-09",
                    "news_coverage": "",
                    "effective_backtest_coverage": "2026-06-08 -> 2026-06-09",
                }
            }
        }
    ),
    encoding="utf-8",
)
```

Add assertions:

```python
assert payload["coverage"]["symbols"]["NVDAUSDT"]["interval"] == "1d"
nvda_overview = next(row for row in payload["symbol_overview"] if row["symbol"] == "NVDAUSDT")
assert nvda_overview["kline_coverage"] == "2026-06-08 -> 2026-06-09"
```

- [x] **Step 2: Run web test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_web.py -q
```

Expected: FAIL because web payload does not expose coverage.

- [x] **Step 3: Implement coverage in web payload**

In `src/bitget_ai_backtest/web.py`:

1. In `build_dashboard_payload`, read coverage:

```python
coverage = _read_coverage(output_dir / "coverage.json")
```

2. Pass coverage into overview:

```python
"symbol_overview": _build_symbol_overview(config.symbols, summary, trades, decision_rows, price_series, coverage),
"coverage": coverage,
```

3. Add:

```python
def _read_coverage(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"symbols": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {"symbols": {}}
```

4. Change `_build_symbol_overview` signature to include `coverage`.

5. Inside `_build_symbol_overview`, add:

```python
coverage_row = (coverage.get("symbols", {}) or {}).get(symbol, {})
```

Then add fields:

```python
"kline_coverage": str(coverage_row.get("kline_coverage", "")),
"news_coverage": str(coverage_row.get("news_coverage", "")),
"effective_backtest_coverage": str(coverage_row.get("effective_backtest_coverage", "")),
```

- [x] **Step 4: Run web test**

Run:

```bash
python3 -m pytest tests/test_web.py -q
```

Expected: PASS.

## Task 5: UI Coverage Labels

**Files:**
- Modify: `tests/test_static_dashboard_ui.py`
- Modify: `src/bitget_ai_backtest/static/index.html`
- Modify: `src/bitget_ai_backtest/static/app.js`
- Modify: `src/bitget_ai_backtest/static/styles.css`

- [x] **Step 1: Add failing static UI assertions**

In `tests/test_static_dashboard_ui.py`, add shell assertions:

```python
assert "K线覆盖区间" in html
assert "新闻覆盖区间" in html
assert "有效回测区间" in html
```

Add script assertions:

```python
assert "renderCoverage" in script
assert "kline_coverage" in script
assert "effective_backtest_coverage" in script
```

Add CSS assertion:

```python
assert ".coverage-grid" in css
```

- [x] **Step 2: Run static test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: FAIL because coverage UI is missing.

- [x] **Step 3: Add coverage HTML**

In `src/bitget_ai_backtest/static/index.html`, inside the first detail `band`, below the detail heading, add:

```html
<div id="coverage" class="coverage-grid">
  <div><span>K线覆盖区间</span><strong id="kline-coverage">-</strong></div>
  <div><span>新闻覆盖区间</span><strong id="news-coverage">-</strong></div>
  <div><span>有效回测区间</span><strong id="effective-coverage">-</strong></div>
</div>
```

- [x] **Step 4: Add coverage rendering**

In `src/bitget_ai_backtest/static/app.js`, add:

```javascript
function renderCoverage(overview) {
  document.getElementById("kline-coverage").textContent = overview.kline_coverage || "未记录";
  document.getElementById("news-coverage").textContent = overview.news_coverage || "未记录";
  document.getElementById("effective-coverage").textContent = overview.effective_backtest_coverage || "未记录";
}
```

Call it in `renderDetailView` after the title:

```javascript
renderCoverage(overview);
```

In the missing-symbol branch, call:

```javascript
renderCoverage({});
```

- [x] **Step 5: Add coverage styles**

In `src/bitget_ai_backtest/static/styles.css`, add:

```css
.coverage-grid {
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 14px;
}

.coverage-grid div {
  background: var(--bg-panel-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  min-width: 0;
  padding: 12px;
}

.coverage-grid span {
  color: var(--muted);
  display: block;
  font-size: 12px;
  margin-bottom: 7px;
}

.coverage-grid strong {
  color: var(--text);
  display: block;
  font-size: 14px;
  line-height: 1.35;
}
```

Inside the mobile media query, add:

```css
.coverage-grid {
  grid-template-columns: 1fr;
}
```

- [x] **Step 6: Run static tests**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: PASS.

## Task 6: Fetch AMD Daily Data And Generate Curve Payload

**Files:**
- Generated: `data/daily/amdusdt-daily-candles.json`
- Generated: `reports/amd-daily/backtest-report.md`
- Generated: `reports/amd-daily/trades.csv`
- Generated: `reports/amd-daily/candles.json`
- Generated: `reports/amd-daily/coverage.json`

- [x] **Step 1: Run full test suite before network fetch**

Run:

```bash
python3 -m pytest -q
```

Expected: PASS.

- [x] **Step 2: Fetch AMDUSDT daily candles to data folder**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli fetch \
  --symbol AMDUSDT \
  --granularity 1d \
  --limit 1000 \
  --output data/daily/amdusdt-daily-candles.json
```

Expected: command exits 0 and writes `data/daily/amdusdt-daily-candles.json`.

- [x] **Step 3: Run AMD daily backtest report**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/amd_daily.json \
  --events data/events/us_stock_events.json \
  --output-dir reports/amd-daily
```

Expected output includes:

```text
Candles snapshot written: reports/amd-daily/candles.json
Coverage written: reports/amd-daily/coverage.json
Report written: reports/amd-daily/backtest-report.md
```

- [x] **Step 4: Inspect generated coverage**

Run:

```bash
python3 -m json.tool reports/amd-daily/coverage.json
```

Expected: output includes `AMDUSDT`, `interval` equal to `1d`, non-empty `start_date`, non-empty `end_date`, and row count greater than 0.

## Task 7: Browser Verify Price Curve

**Files:**
- No code changes unless verification reveals a bug.

- [x] **Step 1: Start server in foreground**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web \
  --config configs/amd_daily.json \
  --output-dir reports/amd-daily \
  --events data/events/us_stock_events.json \
  --port 8001
```

Expected:

```text
Bitget AI Web Demo running at http://127.0.0.1:8001
Press Ctrl+C to stop.
```

- [x] **Step 2: Browser verify**

Open `http://127.0.0.1:8001` and verify:

1. Market list has `AMDUSDT`.
2. Click `AMDUSDT`.
3. Detail page shows `AMDUSDT / AMD 运行详情`.
4. Coverage labels show K-line coverage and effective backtest coverage.
5. Price chart is nonblank and displays the AMD daily curve.
6. Safety notice remains visible.

- [x] **Step 3: Stop server**

Press `Ctrl+C` in the foreground terminal.

## Self-Review

### Spec Coverage

- AMDUSDT single daily backtest: Tasks 1, 6, 7.
- Data landing: Tasks 2, 3, 6.
- Price curve: Tasks 4, 5, 7.
- Coverage dates: Tasks 2, 4, 5, 6, 7.
- Safety boundary: Tasks 3, 7.

### Placeholder Scan

No unresolved placeholder steps remain.

### Type Consistency

- Coverage payload is consistently under `coverage["symbols"][symbol]`.
- UI overview fields are `kline_coverage`, `news_coverage`, `effective_backtest_coverage`.
- Existing `price_series` shape is reused for the canvas curve.
