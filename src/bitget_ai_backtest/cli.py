from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backtester import backtest_symbol
from .bitget_client import BitgetPublicClient, parse_candles_response
from .config import load_config
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

    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
