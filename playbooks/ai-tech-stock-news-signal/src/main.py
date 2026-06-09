"""Entry point for the AI Tech Stock News Signal Playbook."""
import math
from typing import Any

from getagent import backtest, data, runtime


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _sanitize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    return {key: _sanitize(value) for key, value in metrics.items()}


def run() -> None:
    cfg = runtime.manifest.get("strategy_config", {}) or {}
    symbols = cfg.get("trading_symbols") or ["NVDAUSDT"]
    symbol = symbols[0]
    margin_budget = cfg.get("margin_budget")

    bars = data.crypto.futures.kline(
        symbol=symbol,
        interval="15m",
        exchange="bitget",
        limit=1000,
    )
    replay_frame = backtest.prepare_frame(bars, datetime_index="date")

    if replay_frame.empty:
        runtime.emit_signal(
            action="watch",
            symbol=symbol,
            confidence=0.0,
            metrics={"rows": 0},
            meta={"reason": "no historical bars returned", "margin_budget": margin_budget},
        )
        return

    instrument_key = f"{symbol}.BITGET"
    result = backtest.run(
        ohlcv_data={instrument_key: replay_frame},
        spec=runtime.backtest_spec,
    )
    chart_path = backtest.generate_chart(result)
    summary = result.summary or {}
    try:
        net_pnl = float(summary.get("net_pnl", 0) or 0)
    except (TypeError, ValueError):
        net_pnl = 0.0

    metrics = _sanitize_metrics(
        {
            "total_return_pct": result.total_return_pct,
            "net_pnl": net_pnl,
            "starting_balance": summary.get("starting_balance"),
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown_pct": result.max_drawdown_pct,
            "win_rate": result.win_rate,
            "total_trades": result.total_trades,
            "profit_factor": result.profit_factor,
            "rows": len(replay_frame),
        }
    )

    runtime.emit_signal(
        action="long" if net_pnl > 0 else "watch",
        symbol=symbol,
        confidence=_sanitize(result.win_rate) or 0.0,
        metrics=metrics,
        meta={
            "chart_path": chart_path,
            "margin_budget": margin_budget,
            "fast_period": cfg.get("fast_period"),
            "slow_period": cfg.get("slow_period"),
        },
    )


if __name__ == "__main__":
    run()
