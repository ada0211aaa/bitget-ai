from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .config import load_config
from .events import NewsEvent, events_for_symbol, load_events
from .explanations import load_trade_explanations


STATIC_DIR = Path(__file__).with_name("static")
FOCUS_SYMBOL = {"symbol": "NVDAUSDT", "name": "英伟达"}
SYMBOL_NAMES = {
    "NVDAUSDT": "英伟达",
    "MSFTUSDT": "微软",
    "GOOGLUSDT": "谷歌",
    "AMDUSDT": "AMD",
    "METAUSDT": "Meta",
    "AAPLUSDT": "苹果",
    "TSLAUSDT": "特斯拉",
}
SIDE_LABELS = {"buy": "买入", "sell": "卖出"}
SENTIMENT_LABELS = {"bullish": "利好", "bearish": "利空", "neutral": "中性"}
VIEW_LABELS = {
    "bullish": "看多",
    "cautiously_bullish": "谨慎看多",
    "neutral_observe": "中性观察",
    "cautiously_bearish": "谨慎看空",
    "bearish": "看空",
}
REASON_LABELS = {
    "trend_up": "价格趋势走强",
    "trend_down": "价格趋势走弱",
    "news_neutral": "新闻信号中性",
    "macro_neutral": "宏观信号中性",
    "oversold_rebound": "超卖反弹",
    "mean_reversion_buy": "均值回归买点",
    "mean_reversion_sell": "均值回归卖点",
    "stop_loss": "触发止损",
    "take_profit": "触发止盈",
}


def build_dashboard_payload(
    config_path: Path,
    output_dir: Path,
    *,
    playbook_report: Path = Path("reports/playbook/playbook-report.md"),
    events_path: Path | None = Path("data/events/us_stock_events.json"),
) -> dict[str, Any]:
    config = load_config(config_path)
    events = _read_events(events_path)
    filtered_events = _filter_events_for_symbols(events, config.symbols)
    trade_explanations = _read_explanations(output_dir / "trade-explanations.json")
    decision_records = _read_decision_records(output_dir / "decision-records.json")
    summary = _parse_summary(output_dir / "backtest-report.md")
    trades = _read_trades(output_dir / "trades.csv")
    price_series = _read_price_series(output_dir / "candles.json")
    coverage = _read_coverage(output_dir / "coverage.json")
    chart_markers = _read_chart_markers(output_dir / "markers.json")
    candidate_markers = _read_candidate_markers(output_dir / "candidate-markers.json")
    technical_candidates = _read_technical_candidates(output_dir / "technical-candidates.json")
    news_coverage = _read_news_coverage(output_dir / "news-coverage.json")
    decision_rows = _build_decision_rows(decision_records, trade_explanations, filtered_events, config.symbols)
    return {
        "status": {
            "mode": "backtest-only",
            "safe_notice": "本页面只读取回测报告，不下单、不查账户、不展示密钥。",
            "local_report_available": (output_dir / "backtest-report.md").exists(),
            "trade_explanations_available": (output_dir / "trade-explanations.json").exists(),
            "decision_records_available": (output_dir / "decision-records.json").exists(),
        },
        "config": {
            "symbols": list(config.symbols),
            "granularity": config.granularity,
            "limit": config.limit,
            "initial_cash": config.initial_cash,
            "trade_fraction": config.trade_fraction,
            "fee_rate": config.fee_rate,
            "macro_mode": config.macro_mode,
            "news_bias": config.news_bias,
            "price_source": config.price_source,
            "decision_mode": config.decision_mode,
        },
        "focus_symbol": FOCUS_SYMBOL,
        "symbol_overview": _build_symbol_overview(config.symbols, summary, trades, decision_rows, price_series, coverage),
        "summary": summary,
        "trades": trades,
        "trade_explanations": trade_explanations,
        "decision_rows": decision_rows,
        "events": filtered_events,
        "price_series": price_series,
        "chart_markers": chart_markers,
        "candidate_markers": candidate_markers,
        "technical_candidates": technical_candidates,
        "coverage": coverage,
        "news_coverage": news_coverage,
        "playbook": _read_playbook_report(playbook_report),
        "submission_checklist": [
            "GitHub 仓库链接",
            "200 词以内项目说明",
            "回测或模拟交易证据",
            "可选：3 分钟以内演示视频",
            "社区传播帖：#BitgetHackathon 并提及 Bitget AI 官方账号",
        ],
    }


def serve_dashboard(config_path: Path, output_dir: Path, *, port: int, events_path: Path | None = Path("data/events/us_stock_events.json")) -> None:
    payload = json.dumps(
        build_dashboard_payload(config_path, output_dir, events_path=events_path),
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")
    handler = _handler_for(payload)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Bitget AI Web Demo running at http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWeb demo stopped.")
    finally:
        server.server_close()


def _handler_for(payload: bytes):
    class DashboardHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

        def do_GET(self) -> None:
            if self.path.split("?", 1)[0] == "/dashboard-data.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            super().do_GET()

    return DashboardHandler


def _parse_summary(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| ---") or "Symbol" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 6:
            continue
        rows.append(
            {
                "symbol": cells[0],
                "final_equity": cells[1],
                "total_return": cells[2],
                "max_drawdown": cells[3],
                "last_view": cells[4],
                "trades": cells[5],
            }
        )
    return rows


def _read_trades(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_explanations(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return load_trade_explanations(path)


def _read_decision_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = raw.get("decision_records", []) if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def _read_events(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return [event.__dict__ for event in load_events(path)]


def _filter_events(events: list[dict[str, Any]], symbol: str) -> list[dict[str, Any]]:
    if not events:
        return []
    return [event.__dict__ for event in events_for_symbol(_events_from_rows(events), symbol)]


def _filter_events_for_symbols(events: list[dict[str, Any]], symbols: tuple[str, ...]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for symbol in symbols:
        filtered.extend(_filter_events(events, symbol))
    filtered.sort(key=lambda event: (str(event.get("symbol", "")), str(event.get("published_at", "")), str(event.get("event_id", ""))))
    return filtered


def _events_from_rows(rows: list[dict[str, Any]]) -> list[NewsEvent]:
    return [NewsEvent(**row) for row in rows]


def _read_price_series(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _read_coverage(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"symbols": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {"symbols": {}}


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


def _read_candidate_markers(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    markers = raw.get("candidate_markers", []) if isinstance(raw, dict) else []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for marker in markers:
        if not isinstance(marker, dict):
            continue
        symbol = str(marker.get("symbol", ""))
        if symbol:
            grouped.setdefault(symbol, []).append(marker)
    return grouped


def _read_technical_candidates(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    rows = raw.get("technical_candidates", []) if isinstance(raw, dict) else []
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _read_news_coverage(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"symbols": {}}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {"symbols": {}}


def _read_playbook_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"available": False, "text": ""}
    return {"available": True, "text": path.read_text(encoding="utf-8")}


def _build_decision_rows(
    decision_records: list[dict[str, Any]],
    trade_explanations: list[dict[str, Any]],
    events: list[dict[str, Any]],
    symbols: tuple[str, ...],
) -> list[dict[str, str]]:
    allowed_symbols = set(symbols)
    if decision_records:
        rows = [row for row in decision_records if row.get("symbol") in allowed_symbols]
        rows.sort(key=lambda row: (str(row.get("symbol", "")), int(row.get("timestamp_ms") or 0)))
        return [_decision_record_row(row, index, rows) for index, row in enumerate(rows)]

    events_by_id = {str(event.get("event_id", "")): event for event in events}
    rows = [row for row in trade_explanations if row.get("symbol") in allowed_symbols]
    rows.sort(key=lambda row: (str(row.get("symbol", "")), int(row.get("timestamp_ms") or 0)))
    return [_decision_row(row, index, rows, events_by_id) for index, row in enumerate(rows)]


def _build_symbol_overview(
    config_symbols: tuple[str, ...],
    summary: list[dict[str, Any]],
    trades: list[dict[str, str]],
    decision_rows: list[dict[str, str]],
    price_series: dict[str, list[dict[str, Any]]],
    coverage: dict[str, Any],
) -> list[dict[str, str]]:
    summary_by_symbol = {str(row.get("symbol", "")): row for row in summary}
    trades_by_symbol = _group_by_symbol(trades)
    decisions_by_symbol = _group_by_symbol(decision_rows)
    coverage_by_symbol = coverage.get("symbols", {}) if isinstance(coverage.get("symbols"), dict) else {}
    overview: list[dict[str, str]] = []
    for symbol in config_symbols:
        symbol_decisions = decisions_by_symbol.get(symbol, [])
        latest_decision = symbol_decisions[-1] if symbol_decisions else {}
        summary_row = summary_by_symbol.get(symbol, {})
        latest_price = _latest_close(price_series.get(symbol, []))
        coverage_row = coverage_by_symbol.get(symbol, {}) if isinstance(coverage_by_symbol.get(symbol, {}), dict) else {}
        overview.append(
            {
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
                "kline_coverage": str(coverage_row.get("kline_coverage", "")),
                "news_coverage": str(coverage_row.get("news_coverage", "")),
                "effective_backtest_coverage": str(coverage_row.get("effective_backtest_coverage", "")),
                "data_source": str(coverage_row.get("source", "")),
                "coverage_rows": str(coverage_row.get("rows", "")),
            }
        )
    return overview


def _decision_record_row(row: dict[str, Any], index: int, rows: list[dict[str, Any]]) -> dict[str, str]:
    action = _translate_side(str(row.get("action", "")))
    event_title = str(row.get("news_title", "")) or "未匹配到 24 小时内新闻事件，主要由技术信号触发"
    news_source = str(row.get("news_source", "")) or "无匹配新闻"
    news_url = str(row.get("news_url", ""))
    source_action = str(row.get("news_source_action", "")) or _source_action(news_url, event_title)
    return {
        "decision_id": str(row.get("decision_id", "")),
        "sequence": str(index + 1),
        "trade_time": _format_timestamp(row.get("timestamp_ms")),
        "symbol": str(row.get("symbol", "")),
        "symbol_name": _symbol_name(str(row.get("symbol", ""))),
        "action": action,
        "price": _format_number(row.get("price"), digits=2),
        "quantity": _format_number(row.get("quantity"), digits=4),
        "event_title": event_title,
        "news_source": news_source,
        "news_published_at": _format_event_time(row.get("news_published_at")),
        "news_sentiment": _translate_sentiment(str(row.get("news_sentiment", ""))),
        "news_strength": str(row.get("news_strength", "")) or "未分级",
        "news_direction": str(row.get("news_direction", "")) or "无方向",
        "news_topic": str(row.get("news_topic", "")) or "unknown",
        "news_time_horizon": str(row.get("news_time_horizon", "")) or "short_term",
        "stock_relevance": str(row.get("stock_relevance", "")) or "direct",
        "technical_confirmation": str(row.get("technical_confirmation", "")) or "未记录",
        "cooldown_state": str(row.get("cooldown_state", "")) or "未记录",
        "news_url": news_url,
        "source_action": source_action,
        "technical_reason": _translate_reasons(row.get("technical_reasons") or []),
        "final_view": _translate_view(str(row.get("final_view", ""))),
        "decision_reason": str(row.get("decision_reason", "")),
        "backtest_result": _build_backtest_result(row, index, rows),
    }


def _decision_row(row: dict[str, Any], index: int, rows: list[dict[str, Any]], events_by_id: dict[str, dict[str, Any]]) -> dict[str, str]:
    event = _first_matched_event(row, events_by_id)
    action = _translate_side(str(row.get("side", "")))
    final_view = _translate_view(str(row.get("final_view", "")))
    technical_reason = _translate_reasons(row.get("technical_reasons") or [])
    news_sentiment = _translate_sentiment(str(event.get("sentiment", ""))) if event else "未匹配"
    event_title = str(event.get("title", "")) if event else "未匹配到 24 小时内新闻事件，主要由技术信号触发"
    news_url = str(event.get("url", "")) if event else ""
    return {
        "sequence": str(index + 1),
        "trade_time": _format_timestamp(row.get("timestamp_ms")),
        "symbol": str(row.get("symbol", "")),
        "symbol_name": _symbol_name(str(row.get("symbol", ""))),
        "action": action,
        "price": _format_number(row.get("price"), digits=2),
        "quantity": _format_number(row.get("quantity"), digits=4),
        "event_title": event_title,
        "news_source": str(event.get("source_name", "")) if event else "无匹配新闻",
        "news_published_at": _format_event_time(event.get("published_at")) if event else "无",
        "news_sentiment": news_sentiment,
        "news_strength": news_sentiment if event else "无新闻",
        "news_direction": _legacy_news_direction(news_sentiment),
        "news_topic": str(event.get("topic", "unknown")) if event else "unknown",
        "news_time_horizon": str(event.get("time_horizon", "short_term")) if event else "short_term",
        "stock_relevance": str(event.get("stock_relevance", "direct")) if event else "direct",
        "technical_confirmation": "未记录",
        "cooldown_state": "未记录",
        "news_url": news_url,
        "source_action": _source_action(news_url, event_title),
        "technical_reason": technical_reason,
        "final_view": final_view,
        "decision_reason": _build_decision_reason(action, final_view, technical_reason, event),
        "backtest_result": _build_backtest_result(row, index, rows),
    }


def _first_matched_event(row: dict[str, Any], events_by_id: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    details = row.get("matched_event_details") or []
    if details:
        first_detail = details[0]
        return first_detail if isinstance(first_detail, dict) else None
    for event_id in row.get("matched_events") or []:
        event = events_by_id.get(str(event_id))
        if event:
            return event
    return None


def _build_decision_reason(action: str, final_view: str, technical_reason: str, event: dict[str, Any] | None) -> str:
    if event:
        sentiment = _translate_sentiment(str(event.get("sentiment", "")))
        title = str(event.get("title", ""))
        return f"因为匹配到{sentiment}新闻《{title}》，同时技术原因是{technical_reason}，综合观点为{final_view}，所以回测触发{action}。"
    return f"未匹配到 24 小时内新闻事件，主要由技术信号触发；技术原因是{technical_reason}，综合观点为{final_view}，所以回测触发{action}。"


def _build_backtest_result(row: dict[str, Any], index: int, rows: list[dict[str, Any]]) -> str:
    side = str(row.get("side") or row.get("action", ""))
    if side == "observe":
        return "观望记录，不产生交易盈亏"
    if side != "buy":
        return "卖出动作已记录，结果已体现在回测权益曲线中"
    entry_price = _to_float(row.get("price"))
    symbol = str(row.get("symbol", ""))
    for next_row in rows[index + 1 :]:
        if str(next_row.get("symbol", "")) != symbol:
            continue
        next_side = next_row.get("side") or next_row.get("action")
        if next_side != "sell":
            continue
        exit_price = _to_float(next_row.get("price"))
        if entry_price is None or exit_price is None or entry_price == 0:
            return "已找到后续卖出，但价格数据不足，无法计算单笔收益"
        pct = (exit_price - entry_price) / entry_price * 100
        return f"下一笔卖出价 {_format_number(exit_price, digits=2)}，单笔价格变化 {pct:.2f}%"
    return "待下一笔卖出或回测结算确认"


def _format_timestamp(value: Any) -> str:
    try:
        timestamp_ms = int(value)
    except (TypeError, ValueError):
        return ""
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).strftime("%Y-%m-%d %H:%M")


def _format_event_time(value: Any) -> str:
    if not value:
        return ""
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).astimezone(UTC).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return str(value)


def _format_number(value: Any, *, digits: int) -> str:
    number = _to_float(value)
    if number is None:
        return ""
    return f"{number:.{digits}f}"


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _translate_side(value: str) -> str:
    return SIDE_LABELS.get(value, "观望")


def _translate_sentiment(value: str) -> str:
    return SENTIMENT_LABELS.get(value, value or "未知")


def _translate_view(value: str) -> str:
    return VIEW_LABELS.get(value, SENTIMENT_LABELS.get(value, value or "未知"))


def _translate_reasons(reasons: list[str]) -> str:
    if not reasons:
        return "暂无"
    return "、".join(REASON_LABELS.get(str(reason), str(reason)) for reason in reasons)


def _group_by_symbol(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        symbol = str(row.get("symbol", ""))
        if not symbol:
            continue
        grouped.setdefault(symbol, []).append(row)
    return grouped


def _latest_close(rows: list[dict[str, Any]]) -> Any:
    if not rows:
        return None
    return rows[-1].get("close")


def _symbol_name(symbol: str) -> str:
    return SYMBOL_NAMES.get(symbol, symbol.replace("USDT", ""))


def _legacy_news_direction(news_sentiment: str) -> str:
    if news_sentiment == "利好":
        return "看多"
    if news_sentiment == "利空":
        return "看空"
    return "无方向"


def _source_action(news_url: str, event_title: str) -> str:
    if news_url:
        return "查看原文"
    if event_title and not event_title.startswith("未匹配到"):
        return "查看信号详情"
    return "无新闻来源"
