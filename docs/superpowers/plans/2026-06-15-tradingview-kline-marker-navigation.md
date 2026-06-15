# TradingView Kline Marker Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the simple canvas price line with a TradingView Lightweight Charts style K-line chart, write buy/sell markers to disk, and let marker clicks scroll to the matching decision row.

**Architecture:** Keep the current stdlib Python web server and vanilla HTML/CSS/JS dashboard. Reuse the existing backtest results and decision records, add stable `decision_id` values plus `markers.json`, copy the local standalone `lightweight-charts` asset from the reference project, and expose chart markers through `dashboard-data.json`.

**Tech Stack:** Python 3.12, pytest, stdlib HTTP server, vanilla HTML/CSS/JS, TradingView Lightweight Charts standalone JS.

---

## Files

- Modify: `src/bitget_ai_backtest/reporting.py`
  - Add stable decision IDs to decision output.
  - Add marker generation and latest/by-date artifact writing helpers.
- Modify: `src/bitget_ai_backtest/cli.py`
  - Backtest writes chart markers and normalized latest/by-date outputs.
- Modify: `src/bitget_ai_backtest/web.py`
  - Read `markers.json` and expose `chart_markers`.
  - Preserve `decision_id` in table rows.
- Modify: `src/bitget_ai_backtest/static/index.html`
  - Replace `canvas#price-chart` with `div#kline-chart`.
  - Load local `lightweight-charts` standalone script before `app.js`.
- Modify: `src/bitget_ai_backtest/static/app.js`
  - Render candlestick chart with markers.
  - Map marker clicks to decision rows.
  - Highlight and scroll to matched row.
- Modify: `src/bitget_ai_backtest/static/styles.css`
  - Add chart container and highlighted decision row styles.
- Add: `src/bitget_ai_backtest/static/vendor/lightweight-charts.standalone.production.js`
  - Local standalone chart library copied from the reference project.
- Add: `src/bitget_ai_backtest/static/vendor/lightweight-charts.LICENSE`
  - License text copied from the reference project package.
- Modify: `tests/test_reporting.py`
  - Cover `markers.json` and latest/by-date artifact output.
- Modify: `tests/test_cli.py`
  - Assert backtest writes marker and normalized artifact files.
- Modify: `tests/test_web.py`
  - Assert payload includes markers and decision IDs.
- Modify: `tests/test_static_dashboard_ui.py`
  - Assert static page loads chart library and marker navigation hooks.

Generated after implementation:

- `reports/amd-daily/markers.json`
- `data/market/AMDUSDT/1d/latest/candles.json`
- `data/market/AMDUSDT/1d/by-date/2026-06-15/candles.json`
- `data/backtests/AMDUSDT/1d/latest/markers.json`
- `data/backtests/AMDUSDT/1d/latest/decisions.json`
- `data/backtests/AMDUSDT/1d/latest/trades.json`
- `data/backtests/AMDUSDT/1d/latest/coverage.json`
- `data/backtests/AMDUSDT/1d/latest/report.md`
- matching `data/backtests/AMDUSDT/1d/by-date/2026-06-15/*`

## Task 1: Reporting Markers And Decision IDs

**Files:**
- Modify: `tests/test_reporting.py`
- Modify: `src/bitget_ai_backtest/reporting.py`

- [x] **Step 1: Add failing marker reporting test**

Add this test to `tests/test_reporting.py`:

```python
def test_write_decision_records_adds_decision_ids_and_markers(tmp_path: Path) -> None:
    candles = [
        Candle(1780876800000, 100, 102, 99, 101, 1000, 101000),
        Candle(1780963200000, 101, 104, 100, 103, 1200, 123600),
    ]
    result = backtest_symbol(
        "AMDUSDT",
        candles,
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_on",
        news_bias="bullish",
    )

    decisions_path = write_decision_records(tmp_path, [result], interval="1d")
    markers_path = write_chart_markers(tmp_path, [result], interval="1d")

    decisions_payload = json.loads(decisions_path.read_text(encoding="utf-8"))
    markers_payload = json.loads(markers_path.read_text(encoding="utf-8"))

    records = decisions_payload["decision_records"]
    assert records
    assert all(record["decision_id"].startswith("AMDUSDT-1d-") for record in records)
    assert all(marker["action"] in {"buy", "sell"} for marker in markers_payload["markers"])
    assert all(marker["decision_id"] for marker in markers_payload["markers"])
    assert {marker["decision_id"] for marker in markers_payload["markers"]} <= {
        record["decision_id"] for record in records
    }
```

- [x] **Step 2: Run reporting test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_reporting.py::test_write_decision_records_adds_decision_ids_and_markers -q
```

Expected: FAIL because `write_chart_markers` does not exist and `write_decision_records` does not accept `interval`.

- [x] **Step 3: Implement decision IDs and markers**

In `src/bitget_ai_backtest/reporting.py`, keep the model imports as:

```python
from .models import BacktestResult, Candle, DecisionRecord
```

Add helpers:

```python
def decision_id(symbol: str, interval: str, timestamp_ms: int, action: str, sequence: int) -> str:
    date = _date_from_timestamp_ms(timestamp_ms).replace("-", "")
    return f"{symbol}-{interval}-{date}-{action}-{sequence:03d}"


def _decision_record_rows(results: list[BacktestResult], *, interval: str) -> list[dict]:
    rows: list[dict] = []
    counters: dict[tuple[str, str, str], int] = {}
    for result in results:
        for record in result.decision_records:
            row = asdict(record)
            action = str(row.get("action", "observe"))
            date = _date_from_timestamp_ms(int(row["timestamp_ms"]))
            key = (result.symbol, date, action)
            counters[key] = counters.get(key, 0) + 1
            row["decision_id"] = decision_id(result.symbol, interval, int(row["timestamp_ms"]), action, counters[key])
            row["date"] = date
            rows.append(row)
    return rows
```

Change `write_decision_records` signature:

```python
def write_decision_records(output_dir: Path, results: list[BacktestResult], *, interval: str = "unknown") -> Path:
```

Use `_decision_record_rows(results, interval=interval)` in the JSON payload.

Add:

```python
def write_chart_markers(output_dir: Path, results: list[BacktestResult], *, interval: str = "unknown") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "markers.json"
    rows = _decision_record_rows(results, interval=interval)
    markers = []
    for row in rows:
        action = str(row.get("action", ""))
        if action not in {"buy", "sell"}:
            continue
        is_buy = action == "buy"
        markers.append(
            {
                "decision_id": row["decision_id"],
                "symbol": row["symbol"],
                "date": row["date"],
                "timestamp_ms": row["timestamp_ms"],
                "action": action,
                "label": "买入" if is_buy else "卖出",
                "price": row["price"],
                "position": "belowBar" if is_buy else "aboveBar",
                "shape": "arrowUp" if is_buy else "arrowDown",
                "color": "#22c55e" if is_buy else "#ef4444",
            }
        )
    path.write_text(json.dumps({"markers": markers}, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
```

- [x] **Step 4: Run reporting tests**

Run:

```bash
python3 -m pytest tests/test_reporting.py -q
```

Expected: PASS.

## Task 2: Latest And By-Date Data Artifacts

**Files:**
- Modify: `tests/test_reporting.py`
- Modify: `src/bitget_ai_backtest/reporting.py`

- [x] **Step 1: Add failing artifact writer test**

Add this test to `tests/test_reporting.py`:

```python
def test_write_normalized_artifacts_writes_latest_and_by_date(tmp_path: Path) -> None:
    candles = [Candle(1780876800000, 100, 102, 99, 101, 1000, 101000)]
    result = backtest_symbol(
        "AMDUSDT",
        candles,
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_on",
        news_bias="bullish",
    )

    paths = write_normalized_artifacts(
        root_dir=tmp_path,
        symbol="AMDUSDT",
        interval="1d",
        run_date="2026-06-15",
        candles=candles,
        results=[result],
        coverage={"symbols": {"AMDUSDT": {"rows": 1}}},
        report_text="# report\n",
        trades_csv="timestamp_ms,symbol,side,price,quantity,fee,reason\n",
    )

    assert (tmp_path / "market/AMDUSDT/1d/latest/candles.json").exists()
    assert (tmp_path / "market/AMDUSDT/1d/by-date/2026-06-15/candles.json").exists()
    assert (tmp_path / "backtests/AMDUSDT/1d/latest/markers.json").exists()
    assert (tmp_path / "backtests/AMDUSDT/1d/by-date/2026-06-15/report.md").exists()
    assert paths["market_latest"].name == "candles.json"
```

- [x] **Step 2: Run artifact test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_reporting.py::test_write_normalized_artifacts_writes_latest_and_by_date -q
```

Expected: FAIL because `write_normalized_artifacts` does not exist.

- [x] **Step 3: Implement normalized artifact writer**

In `src/bitget_ai_backtest/reporting.py`, add:

```python
def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_normalized_artifacts(
    *,
    root_dir: Path,
    symbol: str,
    interval: str,
    run_date: str,
    candles: list[Candle],
    results: list[BacktestResult],
    coverage: dict,
    report_text: str,
    trades_csv: str,
) -> dict[str, Path]:
    market_latest = root_dir / "market" / symbol / interval / "latest"
    market_by_date = root_dir / "market" / symbol / interval / "by-date" / run_date
    backtest_latest = root_dir / "backtests" / symbol / interval / "latest"
    backtest_by_date = root_dir / "backtests" / symbol / interval / "by-date" / run_date

    candles_payload = candles_to_rows(candles)
    decisions_payload = {"decision_records": _decision_record_rows(results, interval=interval)}
    markers_payload = json.loads(json.dumps({"markers": []}))
    marker_rows = []
    for row in decisions_payload["decision_records"]:
        action = str(row.get("action", ""))
        if action not in {"buy", "sell"}:
            continue
        is_buy = action == "buy"
        marker_rows.append(
            {
                "decision_id": row["decision_id"],
                "symbol": row["symbol"],
                "date": row["date"],
                "timestamp_ms": row["timestamp_ms"],
                "action": action,
                "label": "买入" if is_buy else "卖出",
                "price": row["price"],
                "position": "belowBar" if is_buy else "aboveBar",
                "shape": "arrowUp" if is_buy else "arrowDown",
                "color": "#22c55e" if is_buy else "#ef4444",
            }
        )
    markers_payload["markers"] = marker_rows

    paths = {
        "market_latest": _write_json(market_latest / "candles.json", candles_payload),
        "market_by_date": _write_json(market_by_date / "candles.json", candles_payload),
    }
    for root in [backtest_latest, backtest_by_date]:
        _write_json(root / "decisions.json", decisions_payload)
        _write_json(root / "markers.json", markers_payload)
        _write_json(root / "coverage.json", coverage)
        _write_text(root / "report.md", report_text)
        _write_text(root / "trades.csv", trades_csv)
    paths["backtest_latest"] = backtest_latest
    paths["backtest_by_date"] = backtest_by_date
    return paths
```

- [x] **Step 4: Run reporting tests**

Run:

```bash
python3 -m pytest tests/test_reporting.py -q
```

Expected: PASS.

## Task 3: CLI Writes Markers And Normalized Artifacts

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/bitget_ai_backtest/cli.py`

- [x] **Step 1: Add failing CLI assertions**

In `tests/test_cli.py::test_backtest_command_with_events_writes_trade_explanations`, after existing file assertions add:

```python
assert (output_dir / "markers.json").exists()
assert (Path("data/backtests/NVDAUSDT/15m/latest/markers.json")).exists()
assert (Path("data/backtests/NVDAUSDT/15m/latest/decisions.json")).exists()
assert (Path("data/market/NVDAUSDT/15m/latest/candles.json")).exists()
```

Use `monkeypatch.chdir(tmp_path)` at the start of this test so `data/market` and `data/backtests` artifacts are written under the test temp directory instead of the repository root.

- [x] **Step 2: Run CLI test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_cli.py::test_backtest_command_with_events_writes_trade_explanations -q
```

Expected: FAIL because marker and normalized artifact writing is not connected to CLI.

- [x] **Step 3: Implement CLI artifact writes**

In `src/bitget_ai_backtest/cli.py`, import:

```python
from datetime import UTC, datetime
from .reporting import candles_to_rows, write_candles_snapshot, write_chart_markers, write_coverage, write_decision_records, write_normalized_artifacts, write_report
```

In the `backtest` branch:

1. Call `write_chart_markers` after `write_decision_records`.
2. Pass `interval=config.granularity` to `write_decision_records`.
3. Read report, trades, and coverage payload from the files that were just written.
4. For each symbol, call `write_normalized_artifacts` with `root_dir=Path("data")` and `run_date=datetime.now(UTC).strftime("%Y-%m-%d")`.

Use this exact shape:

```python
decisions_path = write_decision_records(args.output_dir, results, interval=config.granularity)
markers_path = write_chart_markers(args.output_dir, results, interval=config.granularity)
print(f"Decision records written: {decisions_path}")
print(f"Chart markers written: {markers_path}")

coverage_payload = json.loads(coverage_path.read_text(encoding="utf-8"))
report_text = paths["markdown"].read_text(encoding="utf-8")
trades_csv = paths["trades_csv"].read_text(encoding="utf-8")
run_date = datetime.now(UTC).strftime("%Y-%m-%d")
for result in results:
    write_normalized_artifacts(
        root_dir=Path("data"),
        symbol=result.symbol,
        interval=config.granularity,
        run_date=run_date,
        candles=candles_by_symbol[result.symbol],
        results=[result],
        coverage={"symbols": {result.symbol: coverage_payload.get("symbols", {}).get(result.symbol, {})}},
        report_text=report_text,
        trades_csv=trades_csv,
    )
```

- [x] **Step 4: Run CLI test**

Run:

```bash
python3 -m pytest tests/test_cli.py::test_backtest_command_with_events_writes_trade_explanations -q
```

Expected: PASS.

## Task 4: Web Payload Exposes Markers And Decision IDs

**Files:**
- Modify: `tests/test_web.py`
- Modify: `src/bitget_ai_backtest/web.py`

- [x] **Step 1: Add failing web payload assertions**

In `tests/test_web.py`, add a `markers.json` fixture in `report_dir`:

```python
(report_dir / "markers.json").write_text(
    json.dumps(
        {
            "markers": [
                {
                    "decision_id": "NVDAUSDT-15m-20260608-buy-001",
                    "symbol": "NVDAUSDT",
                    "date": "2026-06-08",
                    "timestamp_ms": 1780916400000,
                    "action": "buy",
                    "label": "买入",
                    "price": 209.66,
                    "position": "belowBar",
                    "shape": "arrowUp",
                    "color": "#22c55e",
                }
            ]
        }
    ),
    encoding="utf-8",
)
```

Add assertions:

```python
assert payload["chart_markers"]["NVDAUSDT"][0]["decision_id"] == "NVDAUSDT-15m-20260608-buy-001"
assert decision["decision_id"] == "NVDAUSDT-15m-20260608-buy-001"
```

- [x] **Step 2: Run web test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_web.py -q
```

Expected: FAIL because `chart_markers` and decision row `decision_id` are not exposed.

- [x] **Step 3: Implement web marker payload**

In `src/bitget_ai_backtest/web.py`:

1. Add `_read_chart_markers(path: Path) -> dict[str, list[dict[str, Any]]]`.
2. Read `markers.json` in `build_dashboard_payload`.
3. Add `"chart_markers": chart_markers` to the payload.
4. Add `"decision_id": str(row.get("decision_id", ""))` to `_decision_record_row`.

Use:

```python
def _read_chart_markers(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    markers = raw.get("markers", []) if isinstance(raw, dict) else []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for marker in markers:
        if not isinstance(marker, dict):
            continue
        symbol = str(marker.get("symbol", ""))
        if symbol:
            grouped.setdefault(symbol, []).append(marker)
    return grouped
```

- [x] **Step 4: Run web tests**

Run:

```bash
python3 -m pytest tests/test_web.py -q
```

Expected: PASS.

## Task 5: Static Dashboard Uses Lightweight Charts

**Files:**
- Add: `src/bitget_ai_backtest/static/vendor/lightweight-charts.standalone.production.js`
- Add: `src/bitget_ai_backtest/static/vendor/lightweight-charts.LICENSE`
- Modify: `tests/test_static_dashboard_ui.py`
- Modify: `src/bitget_ai_backtest/static/index.html`
- Modify: `src/bitget_ai_backtest/static/app.js`
- Modify: `src/bitget_ai_backtest/static/styles.css`

- [x] **Step 1: Copy local chart library**

Copy files from the reference project:

```bash
mkdir -p src/bitget_ai_backtest/static/vendor
cp /Users/ada/Documents/daily_stock_analysis-main/apps/dsa-web/node_modules/lightweight-charts/dist/lightweight-charts.standalone.production.js src/bitget_ai_backtest/static/vendor/lightweight-charts.standalone.production.js
cp /Users/ada/Documents/daily_stock_analysis-main/apps/dsa-web/node_modules/lightweight-charts/LICENSE src/bitget_ai_backtest/static/vendor/lightweight-charts.LICENSE
```

Implementation note: if editing manually, use `cp` for vendored third-party assets; do not retype this file.

- [x] **Step 2: Add failing static assertions**

In `tests/test_static_dashboard_ui.py`, add assertions:

```python
assert "./vendor/lightweight-charts.standalone.production.js" in html
assert 'id="kline-chart"' in html
assert 'id="price-chart"' not in html
assert "renderKlineChart" in script
assert "scrollToDecisionRow" in script
assert "highlighted-row" in css
```

- [x] **Step 3: Run static test to verify it fails**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: FAIL because the static UI still uses canvas.

- [x] **Step 4: Update HTML**

In `src/bitget_ai_backtest/static/index.html`:

1. Replace:

```html
<canvas id="price-chart" width="1080" height="280"></canvas>
```

with:

```html
<div id="kline-chart" class="kline-chart"></div>
<div id="kline-hover" class="kline-hover"></div>
```

2. Add before `app.js`:

```html
<script src="./vendor/lightweight-charts.standalone.production.js"></script>
```

- [x] **Step 5: Update JS chart rendering**

In `src/bitget_ai_backtest/static/app.js`:

1. Replace calls to `renderPriceChart(data.price_series, symbol)` with:

```javascript
renderKlineChart(data.price_series, data.chart_markers, symbol);
```

2. Add a module-level chart state:

```javascript
let chartState = {
  chart: null,
  candleSeries: null,
  markerByTime: new Map()
};
```

3. Replace `renderPriceChart` with `renderKlineChart`:

```javascript
function renderKlineChart(priceSeries, chartMarkers, symbol) {
  const container = document.getElementById("kline-chart");
  const hover = document.getElementById("kline-hover");
  const rows = (priceSeries && priceSeries[symbol]) || [];
  const markers = (chartMarkers && chartMarkers[symbol]) || [];
  destroyKlineChart();
  container.innerHTML = "";
  hover.textContent = "";
  if (!rows.length) {
    container.innerHTML = `<p class="empty-state">暂无价格快照。请先运行 backtest 生成 candles.json。</p>`;
    return;
  }
  if (!window.LightweightCharts) {
    container.innerHTML = `<p class="empty-state">图表库未加载，请检查本地静态资源。</p>`;
    return;
  }
  const chart = LightweightCharts.createChart(container, {
    height: 420,
    layout: { background: { type: "solid", color: "transparent" }, textColor: "#dbe7f3" },
    grid: {
      vertLines: { color: "rgba(159, 176, 196, 0.16)" },
      horzLines: { color: "rgba(159, 176, 196, 0.16)" }
    },
    rightPriceScale: { borderColor: "rgba(159, 176, 196, 0.22)" },
    timeScale: { borderColor: "rgba(159, 176, 196, 0.22)", timeVisible: true, secondsVisible: false },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal }
  });
  const candleSeries = chart.addCandlestickSeries({
    upColor: "#22c55e",
    downColor: "#ef4444",
    borderUpColor: "#22c55e",
    borderDownColor: "#ef4444",
    wickUpColor: "#22c55e",
    wickDownColor: "#ef4444"
  });
  const candleData = rows.map((row) => ({
    time: row.date || dateFromTimestamp(row.timestamp_ms),
    open: Number(row.open),
    high: Number(row.high),
    low: Number(row.low),
    close: Number(row.close)
  })).filter((row) => Number.isFinite(row.open) && Number.isFinite(row.high) && Number.isFinite(row.low) && Number.isFinite(row.close));
  candleSeries.setData(candleData);
  const markerData = markers.map((marker) => ({
    time: marker.date || dateFromTimestamp(marker.timestamp_ms),
    position: marker.position,
    color: marker.color,
    shape: marker.shape,
    text: marker.label,
    decision_id: marker.decision_id
  }));
  candleSeries.setMarkers(markerData);
  chartState = {
    chart,
    candleSeries,
    markerByTime: new Map(markerData.map((marker) => [String(marker.time), marker]))
  };
  chart.subscribeClick((param) => {
    const marker = chartState.markerByTime.get(String(param.time || ""));
    if (marker && marker.decision_id) {
      scrollToDecisionRow(marker.decision_id);
    }
  });
  chart.subscribeCrosshairMove((param) => {
    const series = param.seriesData.get(candleSeries);
    if (!series) return;
    hover.textContent = `${symbol} ${series.time} 开 ${formatFixed(series.open)} 高 ${formatFixed(series.high)} 低 ${formatFixed(series.low)} 收 ${formatFixed(series.close)}`;
  });
  chart.timeScale().fitContent();
}
```

4. Add:

```javascript
function destroyKlineChart() {
  if (chartState.chart) {
    chartState.chart.remove();
  }
  chartState = { chart: null, candleSeries: null, markerByTime: new Map() };
}

function dateFromTimestamp(timestampMs) {
  const date = new Date(Number(timestampMs));
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().slice(0, 10);
}

function formatFixed(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "--";
}

function scrollToDecisionRow(decisionId) {
  const row = document.querySelector(`[data-decision-id="${CSS.escape(decisionId)}"]`);
  if (!row) return;
  row.scrollIntoView({ behavior: "smooth", block: "center" });
  row.classList.add("highlighted-row");
  window.setTimeout(() => row.classList.remove("highlighted-row"), 2200);
}
```

5. In `renderDecisionTable`, add `data-decision-id` to each row:

```javascript
<tr data-decision-id="${escapeHtml(row.decision_id || "")}">
```

- [x] **Step 6: Update CSS**

In `src/bitget_ai_backtest/static/styles.css`, replace `#price-chart` styles with:

```css
.kline-chart {
  background: #0b1018;
  border: 1px solid var(--border);
  border-radius: 8px;
  min-height: 420px;
  overflow: hidden;
  width: 100%;
}

.kline-hover {
  color: var(--muted);
  font-size: 13px;
  margin: 10px 0 14px;
  min-height: 20px;
}

.highlighted-row {
  animation: row-highlight 2.2s ease;
}

@keyframes row-highlight {
  0% { background: rgba(0, 212, 255, 0.22); }
  100% { background: transparent; }
}
```

- [x] **Step 7: Run static tests**

Run:

```bash
python3 -m pytest tests/test_static_dashboard_ui.py -q
```

Expected: PASS.

## Task 6: Generate AMD Artifacts And Browser Verify

**Files:**
- Generated: `reports/amd-daily/markers.json`
- Generated: `data/market/AMDUSDT/1d/latest/candles.json`
- Generated: `data/backtests/AMDUSDT/1d/latest/markers.json`
- Generated: `data/backtests/AMDUSDT/1d/latest/decisions.json`

- [x] **Step 1: Run full tests**

Run:

```bash
python3 -m pytest -q
```

Expected: PASS.

- [x] **Step 2: Regenerate AMD daily report**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli backtest \
  --config configs/amd_daily.json \
  --events data/events/us_stock_events.json \
  --output-dir reports/amd-daily
```

Expected output includes:

```text
Chart markers written: reports/amd-daily/markers.json
Report written: reports/amd-daily/backtest-report.md
```

- [x] **Step 3: Inspect generated marker files**

Run:

```bash
python3 -m json.tool reports/amd-daily/markers.json
python3 -m json.tool data/backtests/AMDUSDT/1d/latest/markers.json
```

Expected: JSON is valid. If the current conservative AMD backtest has no trades, `markers` may be an empty list; this is acceptable as long as generated files exist.

- [x] **Step 4: Start web server in foreground**

Run:

```bash
PYTHONPATH=src python3 -m bitget_ai_backtest.cli web \
  --config configs/amd_daily.json \
  --output-dir reports/amd-daily \
  --events data/events/us_stock_events.json \
  --port 8002
```

Expected:

```text
Bitget AI Web Demo running at http://127.0.0.1:8002
Press Ctrl+C to stop.
```

- [x] **Step 5: Browser verify**

Open `http://127.0.0.1:8002` and verify:

1. Market list has `AMDUSDT`.
2. Click AMDUSDT.
3. Detail page shows TradingView Lightweight Charts K-line chart.
4. Coverage cards remain visible.
5. Decision table rows render.
6. If marker data exists, clicking a marker scrolls to the matching row and highlights it.
7. Safety notice still says the page is backtest-only and does not place orders.

- [x] **Step 6: Stop server**

Press `Ctrl+C` in the foreground terminal.

## Self-Review

### Spec Coverage

- TradingView style K-line: Task 5.
- Buy/sell markers: Tasks 1, 3, 4, 5.
- Marker click to decision row: Tasks 4, 5, 6.
- `decision_id` binding: Tasks 1, 4, 5.
- latest/by-date landing: Tasks 2, 3, 6.
- Safety boundary: Tasks 5 and 6.

### Placeholder Scan

No unresolved implementation placeholders remain. The plan intentionally allows empty markers when a conservative backtest has no real buy/sell trades.

### Type Consistency

- Marker payload uses `decision_id`, `symbol`, `date`, `timestamp_ms`, `action`, `label`, `price`, `position`, `shape`, `color`.
- Decision rows use `decision_id`.
- Frontend payload key is `chart_markers`.
- Chart container id is `kline-chart`.
