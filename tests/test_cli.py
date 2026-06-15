import json
from pathlib import Path

from bitget_ai_backtest.cli import main


def test_demo_command_writes_report_from_fixture(tmp_path: Path) -> None:
    exit_code = main(["demo", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "backtest-report.md").exists()
    assert (tmp_path / "trades.csv").exists()


def test_help_command_returns_zero() -> None:
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0


def test_playbook_list_command_writes_response(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text('PLAYBOOK_API_KEY="x"\n', encoding="utf-8")
    output = tmp_path / "list.json"

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            assert api_key == "x"

        def list_playbooks(self, *, status: str):
            assert status == "draft"
            return {"code": "200", "data": {"items": []}, "msg": ""}

    monkeypatch.setattr("bitget_ai_backtest.cli.PlaybookClient", FakeClient)

    exit_code = main(
        [
            "playbook-list",
            "--env",
            str(env_path),
            "--status",
            "draft",
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert '"items": []' in output.read_text(encoding="utf-8")


def test_playbook_backtest_command_uploads_runs_and_writes_results(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text('PLAYBOOK_API_KEY="x"\n', encoding="utf-8")
    package_dir = tmp_path / "playbook"
    (package_dir / "src").mkdir(parents=True)
    (package_dir / "README.md").write_text("策略 开仓 平仓 风险", encoding="utf-8")
    (package_dir / "manifest.yaml").write_text("name: demo\n", encoding="utf-8")
    (package_dir / "backtest.yaml").write_text("execution: {}\n", encoding="utf-8")
    (package_dir / "src" / "main.py").write_text("def run(): pass\n", encoding="utf-8")
    output_dir = tmp_path / "reports"
    calls: list[str] = []

    class FakeClient:
        def __init__(self, api_key: str) -> None:
            assert api_key == "x"

        def upload_package(self, package_path: Path):
            calls.append(f"upload:{package_path.name}")
            return {"data": {"draft_id": "draft-1", "strategy_id": "strategy-1"}}

        def run_backtest(self, version_id: str):
            calls.append(f"run:{version_id}")
            return {"data": {"run_id": "run-1", "status": "pending"}}

        def get_run(self, run_id: str):
            calls.append(f"poll:{run_id}")
            return {
                "data": {
                    "run_id": run_id,
                    "status": "completed",
                    "metrics_output": {
                        "total_return_pct": 1.2,
                        "max_drawdown_pct": 0.4,
                        "win_rate": 0.55,
                        "total_trades": 3,
                        "reports": {"orders": [{"account_id": "BITGET-001"}]},
                        "config": {"account_id": "BITGET-001"},
                    },
                }
            }

    monkeypatch.setattr("bitget_ai_backtest.cli.PlaybookClient", FakeClient)

    exit_code = main(
        [
            "playbook-backtest",
            "--env",
            str(env_path),
            "--package-dir",
            str(package_dir),
            "--output-dir",
            str(output_dir),
            "--poll",
            "--poll-interval",
            "0",
            "--max-polls",
            "1",
        ]
    )

    assert exit_code == 0
    assert calls == ["upload:playbook.tar.gz", "run:draft-1", "poll:run-1"]
    assert (output_dir / "playbook.tar.gz").exists()
    assert (output_dir / "upload-response.json").exists()
    assert (output_dir / "run-dispatch.json").exists()
    assert (output_dir / "run-result.json").exists()
    report = (output_dir / "playbook-report.md").read_text(encoding="utf-8")
    assert "total_return_pct" in report
    assert "BITGET-001" not in report
    assert "reports:" not in report
    assert "config:" not in report


def test_fetch_events_command_writes_event_file(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["NVDAUSDT"],
  "granularity": "15m",
  "limit": 10,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral"
}
""".strip(),
        encoding="utf-8",
    )
    output = tmp_path / "events.json"
    skill_dir = tmp_path / "bitget-skills"
    skill_dir.mkdir()
    (skill_dir / "news.json").write_text(
        """
{
  "events": [
    {
      "event_id": "bitget-nvda",
      "symbol": "NVDAUSDT",
      "published_at": "2026-06-08T10:00:00Z",
      "title": "Nvidia raises guidance on AI demand",
      "source_name": "Bitget news-briefing",
      "source_type": "bitget_news_briefing",
      "url": "https://example.com/bitget",
      "sentiment": "bullish",
      "confidence": 0.8,
      "reason": "Bitget skill export"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "fetch-events",
            "--config",
            str(config),
            "--output",
            str(output),
            "--skill-export-dir",
            str(skill_dir),
        ]
    )

    assert exit_code == 0
    payload = output.read_text(encoding="utf-8")
    assert '"events"' in payload
    assert "NVDAUSDT" in payload
    assert "bitget_news_briefing" in payload


def test_fetch_command_writes_enriched_candle_rows(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "amdusdt-daily-candles.json"

    class FakeClient:
        def fetch_candles(self, symbol: str, granularity: str, limit: int):
            from bitget_ai_backtest.models import Candle

            assert symbol == "AMDUSDT"
            assert granularity == "1d"
            assert limit == 2
            return [
                Candle(1780876800000, 100, 102, 99, 101, 1000, 101000),
                Candle(1780963200000, 101, 104, 100, 103, 1200, 123600),
            ]

    monkeypatch.setattr("bitget_ai_backtest.cli.BitgetPublicClient", FakeClient)

    exit_code = main(
        [
            "fetch",
            "--symbol",
            "AMDUSDT",
            "--granularity",
            "1d",
            "--limit",
            "2",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload[0]["date"] == "2026-06-08"
    assert payload[0]["source"] == "bitget_public"
    assert payload[0]["quote_volume"] == 101000


def test_backtest_command_with_events_writes_trade_explanations(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["NVDAUSDT"],
  "granularity": "15m",
  "limit": 200,
  "initial_cash": 10000,
  "trade_fraction": 0.5,
  "fee_rate": 0.0,
  "macro_mode": "risk_on",
  "news_bias": "bullish"
}
""".strip(),
        encoding="utf-8",
    )
    events = tmp_path / "events.json"
    events.write_text(
        """
{
  "events": [
    {
      "event_id": "NVDA-test",
      "symbol": "NVDAUSDT",
      "published_at": "2026-06-08T10:00:00Z",
      "title": "Nvidia raises guidance on AI demand",
      "source_name": "Bitget news-briefing",
      "source_type": "bitget_news_briefing",
      "url": "https://example.com/nvda",
      "sentiment": "bullish",
      "confidence": 0.7,
      "reason": "Matched bullish keyword: raises guidance"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    output_dir = tmp_path / "reports"

    fixture = Path(__file__).resolve().parent / "fixtures/bitget_candles_nvda_15m.json"

    class FakeClient:
        def fetch_candles(self, symbol: str, granularity: str, limit: int):
            from bitget_ai_backtest.bitget_client import parse_candles_response
            import json

            return parse_candles_response(json.loads(fixture.read_text(encoding="utf-8")))

    monkeypatch.setattr("bitget_ai_backtest.cli.BitgetPublicClient", FakeClient)

    exit_code = main(
        [
            "backtest",
            "--config",
            str(config),
            "--events",
            str(events),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr().out
    assert (output_dir / "backtest-report.md").exists()
    coverage = output_dir / "coverage.json"
    assert coverage.exists()
    assert "Coverage written:" in captured
    assert (output_dir / "markers.json").exists()
    assert (Path("data/backtests/NVDAUSDT/15m/latest/markers.json")).exists()
    assert (Path("data/backtests/NVDAUSDT/15m/latest/decisions.json")).exists()
    assert (Path("data/market/NVDAUSDT/15m/latest/candles.json")).exists()
    explanations = output_dir / "trade-explanations.json"
    assert explanations.exists()
    assert "NVDA-test" in explanations.read_text(encoding="utf-8")
    decisions = output_dir / "decision-records.json"
    assert decisions.exists()
    decision_payload = json.loads(decisions.read_text(encoding="utf-8"))
    records = decision_payload["decision_records"]
    assert records
    assert len(records) > len(json.loads(explanations.read_text(encoding="utf-8"))["trade_explanations"])
    first = records[0]
    assert {"news_strength", "news_direction", "technical_confirmation", "cooldown_state", "decision_reason", "news_url"} <= set(first)
    assert any(record["action"] == "observe" for record in records)
    assert any(record["news_source_action"] == "查看原文" and record["news_url"] == "https://example.com/nvda" for record in records)
