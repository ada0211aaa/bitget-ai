from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .backtester import backtest_symbol
from .bitget_client import BitgetPublicClient, parse_candles_response
from .config import load_config
from .env import load_playbook_api_key
from .playbook_client import PlaybookClient
from .playbook_package import create_package_archive
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
