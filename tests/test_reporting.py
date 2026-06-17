import json
from pathlib import Path

from bitget_ai_backtest.backtester import backtest_symbol
from bitget_ai_backtest.models import BacktestResult, Candle, DecisionRecord, StrategySignal, Trade
from bitget_ai_backtest.reporting import (
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


def test_write_report_creates_markdown_and_trade_csv(tmp_path: Path) -> None:
    candles = [
        Candle(1000 + index, value, value + 1, value - 1, value, 1000, value * 1000)
        for index, value in enumerate([100, 101, 102, 103, 104, 105, 106, 107])
    ]
    result = backtest_symbol(
        "NVDAUSDT",
        candles,
        initial_cash=10000,
        trade_fraction=0.5,
        fee_rate=0.0,
        macro_mode="risk_on",
        news_bias="bullish",
    )

    paths = write_report(tmp_path, [result], config_name="test-config")

    markdown = paths["markdown"].read_text(encoding="utf-8")
    csv_text = paths["trades_csv"].read_text(encoding="utf-8")
    assert "Bitget AI Local Backtest Report" in markdown
    assert "NVDAUSDT" in markdown
    assert "Backtest-only" in markdown
    assert "timestamp_ms,symbol,side,price,quantity,fee,reason" in csv_text


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
    assert candles_payload["AMDUSDT"][0]["quote_volume"] == 101000
    assert coverage_payload["symbols"]["AMDUSDT"]["interval"] == "1d"
    assert coverage_payload["symbols"]["AMDUSDT"]["rows"] == 2
    assert coverage_payload["symbols"]["AMDUSDT"]["start_date"] == "2026-06-08"
    assert coverage_payload["symbols"]["AMDUSDT"]["end_date"] == "2026-06-09"
    assert coverage_payload["symbols"]["AMDUSDT"]["kline_coverage"] == "2026-06-08 -> 2026-06-09"


def test_write_decision_records_adds_decision_ids_and_markers(tmp_path: Path) -> None:
    result = BacktestResult(
        symbol="AMDUSDT",
        initial_cash=10000,
        final_equity=10100,
        total_return=0.01,
        max_drawdown=0.0,
        equity_curve=(10000, 10100),
        trades=(
            Trade(1780876800000, "AMDUSDT", "buy", 101, 1, 0, "bullish"),
            Trade(1780963200000, "AMDUSDT", "sell", 103, 1, 0, "bearish"),
        ),
        last_signal=StrategySignal("AMDUSDT", 1780963200000, 0, "neutral_observe", "hold", 103, ()),
        decision_records=(
            DecisionRecord(
                1780876800000,
                "AMDUSDT",
                "buy",
                101,
                "强利好",
                "看多",
                "已确认",
                "可交易",
                "强利好新闻成立，并且技术面确认，所以回测触发买入。",
                "看多",
                quantity=1,
            ),
            DecisionRecord(
                1780963200000,
                "AMDUSDT",
                "sell",
                103,
                "强利空",
                "看空",
                "已确认",
                "可交易",
                "强利空新闻成立，并且技术面确认，所以回测触发卖出。",
                "看空",
                quantity=1,
            ),
        ),
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


def test_write_normalized_artifacts_writes_latest_and_by_date(tmp_path: Path) -> None:
    candles = [Candle(1780876800000, 100, 102, 99, 101, 1000, 101000)]
    result = BacktestResult(
        symbol="AMDUSDT",
        initial_cash=10000,
        final_equity=10000,
        total_return=0,
        max_drawdown=0,
        equity_curve=(10000,),
        trades=(),
        last_signal=StrategySignal("AMDUSDT", 1780876800000, 0, "neutral_observe", "hold", 101, ()),
        decision_records=(),
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
        source="yahoo_chart_daily",
    )

    assert (tmp_path / "market/AMDUSDT/1d/latest/candles.json").exists()
    assert (tmp_path / "market/AMDUSDT/1d/by-date/2026-06-15/candles.json").exists()
    assert (tmp_path / "backtests/AMDUSDT/1d/latest/markers.json").exists()
    assert (tmp_path / "backtests/AMDUSDT/1d/by-date/2026-06-15/report.md").exists()
    assert paths["market_latest"].name == "candles.json"
    latest_candles = json.loads((tmp_path / "market/AMDUSDT/1d/latest/candles.json").read_text(encoding="utf-8"))
    assert latest_candles[0]["source"] == "yahoo_chart_daily"


def test_write_technical_candidates_writes_rows(tmp_path: Path) -> None:
    rows = {
        "AMDUSDT": [
            {
                "symbol": "AMDUSDT",
                "date": "2026-06-15",
                "timestamp_ms": 1781530200000,
                "price": 549.5,
                "candidate_type": "buy_watch",
                "technical_reasons": ["price_above_ma50"],
            }
        ]
    }

    path = write_technical_candidates(tmp_path, rows)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["technical_candidates"][0]["candidate_type"] == "buy_watch"


def test_write_news_coverage_writes_symbol_coverage(tmp_path: Path) -> None:
    path = write_news_coverage(
        tmp_path,
        {
            "AMDUSDT": {
                "symbol": "AMDUSDT",
                "event_count": 3,
                "start_date": "2026-06-01",
                "end_date": "2026-06-15",
                "coverage": "2026-06-01 -> 2026-06-15",
                "fetched_at": "2026-06-17T09:00:00Z",
            }
        },
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["symbols"]["AMDUSDT"]["event_count"] == 3


def test_write_candidate_markers_writes_distinct_observation_markers(tmp_path: Path) -> None:
    path = write_candidate_markers(
        tmp_path,
        {
            "AMDUSDT": [
                {
                    "symbol": "AMDUSDT",
                    "date": "2026-06-15",
                    "timestamp_ms": 1781530200000,
                    "price": 549.5,
                    "candidate_type": "buy_watch",
                    "technical_reasons": ["price_above_ma50"],
                }
            ]
        },
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    marker = payload["candidate_markers"][0]
    assert marker["action"] == "candidate"
    assert marker["label"] == "观察"
    assert marker["color"] == "#38bdf8"
