from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .backtester import backtest_symbol
from .bitget_client import BitgetPublicClient, parse_candles_response
from .config import load_config
from .env import load_playbook_api_key
from .equity_client import YahooChartDailyClient
from .events import collect_events, deduplicate_events, events_for_symbol, load_events, write_events
from .explanations import explain_trades, write_trade_explanations
from .external_news_collectors import fetch_google_news_search_events, fetch_sec_edgar_events, load_daily_stock_analysis_archive
from .news_library import read_news_coverage, read_news_library, write_news_library
from .playbook_client import PlaybookClient
from .playbook_package import create_package_archive
from .reporting import (
    candles_to_rows,
    write_candles_snapshot,
    write_candidate_markers,
    write_chart_markers,
    write_coverage,
    write_decision_records,
    write_normalized_artifacts,
    write_news_coverage,
    write_report,
    write_technical_candidates,
)
from .technical_candidates import build_technical_candidates
from .web import serve_dashboard


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
    fetch_parser.add_argument("--source", default="bitget_public", choices=["bitget_public", "yahoo_chart_daily"])

    events_parser = subparsers.add_parser("fetch-events", help="Fetch news/events for configured symbols")
    events_parser.add_argument("--config", type=Path, default=Path("configs/default_universe.json"))
    events_parser.add_argument("--output", type=Path, default=Path("data/events/us_stock_events.json"))
    events_parser.add_argument("--skill-export-dir", type=Path, default=Path("data/bitget-skills"))

    news_library_parser = subparsers.add_parser("fetch-news-library", help="Fetch and persist a per-symbol news library")
    news_library_parser.add_argument("--config", type=Path, default=Path("configs/us_stock_daily_external.json"))
    news_library_parser.add_argument("--days", type=int, default=30)
    news_library_parser.add_argument("--output-dir", type=Path, default=Path("data/news"))
    news_library_parser.add_argument("--skill-export-dir", type=Path, default=Path("data/bitget-skills"))
    news_library_parser.add_argument(
        "--external-news-archive",
        type=Path,
        default=Path("/Users/ada/Documents/daily_stock_analysis-main/data/news_archive"),
    )
    news_library_parser.add_argument("--include-sec-edgar", action="store_true")
    news_library_parser.add_argument("--include-web-search", action="store_true")

    backtest_parser = subparsers.add_parser("backtest", help="Backtest from live public candles")
    backtest_parser.add_argument("--config", type=Path, default=Path("configs/default_universe.json"))
    backtest_parser.add_argument("--output-dir", type=Path, default=Path("reports/latest"))
    backtest_parser.add_argument("--events", type=Path, default=None)
    backtest_parser.add_argument("--news-library", type=Path, default=None)

    web_parser = subparsers.add_parser("web", help="Serve local backtest-only web dashboard")
    web_parser.add_argument("--config", type=Path, default=Path("configs/default_universe.json"))
    web_parser.add_argument("--output-dir", type=Path, default=Path("reports/latest"))
    web_parser.add_argument("--events", type=Path, default=Path("data/events/us_stock_events.json"))
    web_parser.add_argument("--news-library", type=Path, default=None, help="Accepted for command consistency; dashboard reads generated report files")
    web_parser.add_argument("--port", type=int, default=8000)

    playbook_list_parser = subparsers.add_parser("playbook-list", help="Call Playbook API to list playbooks")
    playbook_list_parser.add_argument("--env", type=Path, default=Path(".env"))
    playbook_list_parser.add_argument("--status", default="draft", choices=["draft", "published", "deprecated"])
    playbook_list_parser.add_argument("--output", type=Path, default=Path("reports/playbook/playbook-list.json"))

    playbook_backtest_parser = subparsers.add_parser(
        "playbook-backtest",
        help="Package, upload, and run a Playbook API backtest",
    )
    playbook_backtest_parser.add_argument("--env", type=Path, default=Path(".env"))
    playbook_backtest_parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("playbooks/ai-tech-stock-news-signal"),
    )
    playbook_backtest_parser.add_argument("--output-dir", type=Path, default=Path("reports/playbook"))
    playbook_backtest_parser.add_argument("--poll", action="store_true", help="Poll until the run finishes or max polls is reached")
    playbook_backtest_parser.add_argument("--poll-interval", type=float, default=10.0)
    playbook_backtest_parser.add_argument("--max-polls", type=int, default=30)

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
        fetch_symbol = _ticker_for_source(args.symbol, args.source, {})
        candles = _fetch_candles_for_source(
            source=args.source,
            symbol=fetch_symbol,
            granularity=args.granularity,
            limit=args.limit,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(candles_to_rows(candles, source=args.source), indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Fetched {len(candles)} candles for {args.symbol.upper()} from {args.source} into {args.output}")
        return 0

    if args.command == "fetch-events":
        config = load_config(args.config)
        events = collect_events(config, skill_export_dir=args.skill_export_dir)
        write_events(args.output, events)
        print(f"Events written: {args.output}")
        return 0

    if args.command == "fetch-news-library":
        config = load_config(args.config)
        if args.days != 30:
            print(f"Warning: first version is designed for 30 days; requested {args.days} days")
        events = collect_events(config, skill_export_dir=args.skill_export_dir)
        archive_events = load_daily_stock_analysis_archive(args.external_news_archive, config.symbols, config.ticker_map)
        if archive_events:
            print(f"Collected {len(archive_events)} events from daily_stock_analysis archive")
            events.extend(archive_events)
        if args.include_sec_edgar:
            sec_events = fetch_sec_edgar_events(config.symbols, config.ticker_map)
            print(f"Collected {len(sec_events)} events from SEC EDGAR")
            events.extend(sec_events)
        if args.include_web_search:
            web_events = fetch_google_news_search_events(config.symbols, config.ticker_map, days=args.days)
            print(f"Collected {len(web_events)} events from Google News search")
            events.extend(web_events)
        events = _filter_events_by_days(events, args.days)
        events = deduplicate_events(events)
        written = write_news_library(args.output_dir, events)
        print(f"News library written: {args.output_dir}")
        print(f"Symbols written: {', '.join(sorted(written)) if written else 'none'}")
        return 0

    if args.command == "backtest":
        config = load_config(args.config)
        if args.news_library:
            events = read_news_library(args.news_library, config.symbols)
            news_coverage = read_news_coverage(args.news_library, config.symbols)
        else:
            events = load_events(args.events) if args.events else None
            news_coverage = {}
        results = []
        candles_by_symbol = {}
        candidates_by_symbol = {}
        for symbol in config.symbols:
            fetch_symbol = _ticker_for_source(symbol, config.price_source, config.ticker_map)
            candles = _fetch_candles_for_source(
                source=config.price_source,
                symbol=fetch_symbol,
                granularity=config.granularity,
                limit=config.limit,
            )
            candles_by_symbol[symbol] = candles
            candidates_by_symbol[symbol] = build_technical_candidates(symbol, candles)
            result = backtest_symbol(
                symbol,
                candles,
                initial_cash=config.initial_cash,
                trade_fraction=config.trade_fraction,
                fee_rate=config.fee_rate,
                macro_mode=config.macro_mode,
                news_bias=config.news_bias,
                events=events_for_symbol(events, symbol) if events is not None else None,
                decision_mode=config.decision_mode,
            )
            results.append(result)
        paths = write_report(args.output_dir, results, config_name=str(args.config))
        candles_path = write_candles_snapshot(args.output_dir, candles_by_symbol, source=config.price_source)
        coverage_path = write_coverage(args.output_dir, candles_by_symbol, interval=config.granularity, source=config.price_source)
        decisions_path = write_decision_records(args.output_dir, results, interval=config.granularity)
        markers_path = write_chart_markers(args.output_dir, results, interval=config.granularity)
        candidates_path = write_technical_candidates(args.output_dir, candidates_by_symbol)
        candidate_markers_path = write_candidate_markers(args.output_dir, candidates_by_symbol)
        print(f"Candles snapshot written: {candles_path}")
        print(f"Coverage written: {coverage_path}")
        print(f"Decision records written: {decisions_path}")
        print(f"Chart markers written: {markers_path}")
        print(f"Technical candidates written: {candidates_path}")
        print(f"Candidate markers written: {candidate_markers_path}")
        if args.news_library:
            news_coverage_path = write_news_coverage(args.output_dir, news_coverage)
            print(f"News coverage written: {news_coverage_path}")
        if args.events:
            explanations = explain_trades(results, events or [], window_hours=24)
            write_trade_explanations(args.output_dir / "trade-explanations.json", explanations)
            print(f"Trade explanations written: {args.output_dir / 'trade-explanations.json'}")
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
                source=config.price_source,
            )
        print(f"Report written: {paths['markdown']}")
        return 0

    if args.command == "web":
        serve_dashboard(args.config, args.output_dir, port=args.port, events_path=args.events)
        return 0

    if args.command == "playbook-list":
        client = PlaybookClient(load_playbook_api_key(args.env))
        response = client.list_playbooks(status=args.status)
        _write_json(args.output, response)
        print(f"Playbook list written: {args.output}")
        return 0

    if args.command == "playbook-backtest":
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_path = create_package_archive(args.package_dir, output_dir / "playbook.tar.gz")
        client = PlaybookClient(load_playbook_api_key(args.env))

        upload_response = client.upload_package(archive_path)
        _write_json(output_dir / "upload-response.json", upload_response)
        draft_id = _extract_field(upload_response, "draft_id")
        if not draft_id:
            raise ValueError("Playbook upload response did not include draft_id")

        run_response = client.run_backtest(draft_id)
        _write_json(output_dir / "run-dispatch.json", run_response)
        run_id = _extract_field(run_response, "run_id")
        if not run_id:
            raise ValueError("Playbook run response did not include run_id")

        latest_run = run_response
        if args.poll:
            latest_run = _poll_run(
                client,
                run_id,
                poll_interval=args.poll_interval,
                max_polls=args.max_polls,
            )
            _write_json(output_dir / "run-result.json", latest_run)

        _write_playbook_report(
            output_dir / "playbook-report.md",
            upload_response=upload_response,
            run_response=run_response,
            latest_run=latest_run,
        )
        print(f"Playbook upload written: {output_dir / 'upload-response.json'}")
        print(f"Playbook run written: {output_dir / 'run-dispatch.json'}")
        if args.poll:
            print(f"Playbook run result written: {output_dir / 'run-result.json'}")
        print(f"Playbook report written: {output_dir / 'playbook-report.md'}")
        return 0

    parser.error(f"unknown command {args.command}")
    return 2


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _filter_events_by_days(events, days: int):
    cutoff = datetime.now(UTC) - timedelta(days=days)
    filtered = []
    for event in events:
        try:
            published_at = datetime.fromisoformat(event.published_at.replace("Z", "+00:00"))
        except ValueError:
            filtered.append(event)
            continue
        if published_at >= cutoff:
            filtered.append(event)
    return filtered


def _ticker_for_source(symbol: str, source: str, ticker_map: dict[str, str]) -> str:
    normalized = symbol.upper()
    if source == "yahoo_chart_daily":
        return ticker_map.get(normalized, normalized.removesuffix("USDT"))
    return normalized


def _fetch_candles_for_source(*, source: str, symbol: str, granularity: str, limit: int):
    if source == "bitget_public":
        return BitgetPublicClient().fetch_candles(symbol, granularity, limit)
    if source == "yahoo_chart_daily":
        return YahooChartDailyClient().fetch_candles(symbol, granularity, limit)
    raise ValueError(f"unsupported price source: {source}")


def _payload_data(payload: dict) -> dict:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def _extract_field(payload: dict, field: str) -> str:
    data = _payload_data(payload)
    value = data.get(field)
    return str(value) if value else ""


def _poll_run(
    client: PlaybookClient,
    run_id: str,
    *,
    poll_interval: float,
    max_polls: int,
) -> dict:
    latest: dict = {}
    for poll_index in range(max(1, max_polls)):
        if poll_index > 0 and poll_interval > 0:
            time.sleep(poll_interval)
        latest = client.get_run(run_id)
        status = _extract_field(latest, "status")
        if status in {"completed", "failed"}:
            return latest
    return latest


def _write_playbook_report(
    path: Path,
    *,
    upload_response: dict,
    run_response: dict,
    latest_run: dict,
) -> None:
    run_data = _payload_data(latest_run)
    metrics = run_data.get("metrics_output") if isinstance(run_data.get("metrics_output"), dict) else {}
    metric_keys = [
        "total_return_pct",
        "account_total_return_pct",
        "max_drawdown_pct",
        "account_max_drawdown_pct",
        "sharpe_ratio",
        "win_rate",
        "win_rate_pct",
        "total_trades",
        "fill_count",
        "position_count",
        "profit_factor",
        "net_pnl",
        "starting_balance",
        "ending_balance",
        "rows",
        "window_start",
        "window_end",
    ]
    lines = [
        "# Playbook API Backtest Report",
        "",
        "This report is a safe summary generated from Bitget Playbook API responses. It does not publish, enable, or place live orders.",
        "",
        "## IDs",
        "",
        f"- strategy_id: {_extract_field(upload_response, 'strategy_id') or 'n/a'}",
        f"- draft_id: {_extract_field(upload_response, 'draft_id') or 'n/a'}",
        f"- run_id: {_extract_field(run_response, 'run_id') or _extract_field(latest_run, 'run_id') or 'n/a'}",
        f"- status: {_extract_field(latest_run, 'status') or _extract_field(run_response, 'status') or 'n/a'}",
        "",
        "## Metrics",
        "",
    ]
    if metrics:
        for key in metric_keys:
            if key in metrics:
                lines.append(f"- {key}: {metrics[key]}")
    else:
        lines.append("- No completed metrics recorded yet.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
