from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .models import BacktestResult, Candle


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
        writer = csv.writer(file, lineterminator="\n")
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


def _date_from_timestamp_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).strftime("%Y-%m-%d")


def candles_to_rows(candles: list[Candle], *, source: str = "bitget_public") -> list[dict]:
    return [
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
        for candle in candles
    ]


def write_candles_snapshot(output_dir: Path, candles_by_symbol: dict[str, list[Candle]], *, source: str = "bitget_public") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "candles.json"
    payload = {symbol: candles_to_rows(candles, source=source) for symbol, candles in candles_by_symbol.items()}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_coverage(
    output_dir: Path,
    candles_by_symbol: dict[str, list[Candle]],
    *,
    interval: str,
    source: str = "bitget_public",
) -> Path:
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
        coverage_range = f"{start_date} -> {end_date}" if start_date and end_date else ""
        symbols[symbol] = {
            "symbol": symbol,
            "interval": interval,
            "source": source,
            "rows": len(rows),
            "start_date": start_date,
            "end_date": end_date,
            "kline_coverage": coverage_range,
            "news_coverage": "",
            "effective_backtest_coverage": coverage_range,
        }
    path.write_text(json.dumps({"symbols": symbols}, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


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
            timestamp_ms = int(row["timestamp_ms"])
            date = _date_from_timestamp_ms(timestamp_ms)
            key = (result.symbol, date, action)
            counters[key] = counters.get(key, 0) + 1
            row["decision_id"] = decision_id(result.symbol, interval, timestamp_ms, action, counters[key])
            row["date"] = date
            rows.append(row)
    return rows


def _markers_from_decision_rows(rows: list[dict]) -> list[dict]:
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
    return markers


def _write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_chart_markers(output_dir: Path, results: list[BacktestResult], *, interval: str = "unknown") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "markers.json"
    rows = _decision_record_rows(results, interval=interval)
    path.write_text(json.dumps({"markers": _markers_from_decision_rows(rows)}, indent=2, ensure_ascii=False), encoding="utf-8")
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

    decision_rows = _decision_record_rows(results, interval=interval)
    candles_payload = candles_to_rows(candles)
    decisions_payload = {"decision_records": decision_rows}
    markers_payload = {"markers": _markers_from_decision_rows(decision_rows)}

    paths = {
        "market_latest": _write_json(market_latest / "candles.json", candles_payload),
        "market_by_date": _write_json(market_by_date / "candles.json", candles_payload),
    }
    for output_dir in (backtest_latest, backtest_by_date):
        _write_json(output_dir / "decisions.json", decisions_payload)
        _write_json(output_dir / "markers.json", markers_payload)
        _write_json(output_dir / "coverage.json", coverage)
        _write_text(output_dir / "report.md", report_text)
        _write_text(output_dir / "trades.csv", trades_csv)
    paths["backtest_latest"] = backtest_latest
    paths["backtest_by_date"] = backtest_by_date
    return paths


def write_decision_records(output_dir: Path, results: list[BacktestResult], *, interval: str = "unknown") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "decision-records.json"
    payload = {"decision_records": _decision_record_rows(results, interval=interval)}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
