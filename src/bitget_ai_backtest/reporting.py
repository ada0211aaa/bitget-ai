from __future__ import annotations

import csv
from pathlib import Path

from .models import BacktestResult


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
