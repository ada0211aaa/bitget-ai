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


def test_fetch_command_writes_yahoo_daily_rows(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "nvda-daily-candles.json"

    class FakeYahooClient:
        def fetch_candles(self, ticker: str, granularity: str, limit: int):
            from bitget_ai_backtest.models import Candle

            assert ticker == "NVDA"
            assert granularity == "1d"
            assert limit == 2
            return [
                Candle(1780876800000, 100, 102, 99, 101, 1000, 101000),
                Candle(1780963200000, 101, 104, 100, 103, 1200, 123600),
            ]

    monkeypatch.setattr("bitget_ai_backtest.cli.YahooChartDailyClient", FakeYahooClient)

    exit_code = main(
        [
            "fetch",
            "--source",
            "yahoo_chart_daily",
            "--symbol",
            "NVDAUSDT",
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
    assert payload[0]["source"] == "yahoo_chart_daily"
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


def test_backtest_command_uses_external_equity_source(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["NVDAUSDT"],
  "granularity": "1d",
  "limit": 6,
  "initial_cash": 10000,
  "trade_fraction": 0.5,
  "fee_rate": 0.0,
  "macro_mode": "risk_on",
  "news_bias": "bullish",
  "price_source": "yahoo_chart_daily",
  "ticker_map": {"NVDAUSDT": "NVDA"}
}
""".strip(),
        encoding="utf-8",
    )
    output_dir = tmp_path / "reports"

    class FakeYahooClient:
        def fetch_candles(self, ticker: str, granularity: str, limit: int):
            from bitget_ai_backtest.models import Candle

            assert ticker == "NVDA"
            assert granularity == "1d"
            assert limit == 6
            return [
                Candle(1780876800000, 100, 102, 99, 101, 1000, 101000),
                Candle(1780963200000, 101, 104, 100, 103, 1200, 123600),
                Candle(1781049600000, 103, 107, 102, 106, 1300, 137800),
                Candle(1781136000000, 106, 110, 105, 109, 1400, 152600),
                Candle(1781222400000, 109, 112, 108, 111, 1500, 166500),
                Candle(1781308800000, 111, 116, 110, 115, 1600, 184000),
            ]

    monkeypatch.setattr("bitget_ai_backtest.cli.YahooChartDailyClient", FakeYahooClient)

    exit_code = main(["backtest", "--config", str(config), "--output-dir", str(output_dir)])

    assert exit_code == 0
    candles = json.loads((output_dir / "candles.json").read_text(encoding="utf-8"))
    coverage = json.loads((output_dir / "coverage.json").read_text(encoding="utf-8"))
    normalized = json.loads(Path("data/market/NVDAUSDT/1d/latest/candles.json").read_text(encoding="utf-8"))
    assert candles["NVDAUSDT"][0]["source"] == "yahoo_chart_daily"
    assert coverage["symbols"]["NVDAUSDT"]["source"] == "yahoo_chart_daily"
    assert normalized[0]["source"] == "yahoo_chart_daily"


def test_backtest_news_daily_strategy_writes_buy_sell_markers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["NVDAUSDT"],
  "granularity": "1d",
  "limit": 63,
  "initial_cash": 10000,
  "trade_fraction": 0.5,
  "fee_rate": 0.0,
  "macro_mode": "neutral",
  "news_bias": "neutral",
  "price_source": "yahoo_chart_daily",
  "ticker_map": {"NVDAUSDT": "NVDA"}
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
      "event_id": "strong-buy",
      "symbol": "NVDAUSDT",
      "published_at": "1970-03-21T20:00:00Z",
      "title": "Nvidia raises guidance on AI demand",
      "source_name": "Bitget news-briefing",
      "source_type": "bitget_news_briefing",
      "url": "https://example.com/nvda",
      "sentiment": "bullish",
      "confidence": 0.82,
      "reason": "Bitget AI judges this as strong.",
      "strength": "strong",
      "topic": "earnings_guidance",
      "time_horizon": "medium_term",
      "stock_relevance": "direct"
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    output_dir = tmp_path / "reports"

    class FakeYahooClient:
        def fetch_candles(self, ticker: str, granularity: str, limit: int):
            from bitget_ai_backtest.models import Candle

            values = [100 + index * 0.2 + (1.0 if index % 2 == 0 else -0.5) for index in range(60)]
            values.extend([120, 130, 114])
            return [
                Candle(1_800_000_000 + index * 86_400_000, value, value, value, value, 1000, value * 1000)
                for index, value in enumerate(values)
            ]

    monkeypatch.setattr("bitget_ai_backtest.cli.YahooChartDailyClient", FakeYahooClient)

    exit_code = main(["backtest", "--config", str(config), "--events", str(events), "--output-dir", str(output_dir)])

    assert exit_code == 0
    decisions = json.loads((output_dir / "decision-records.json").read_text(encoding="utf-8"))["decision_records"]
    markers = json.loads((output_dir / "markers.json").read_text(encoding="utf-8"))["markers"]
    assert [row["action"] for row in decisions if row["action"] in {"buy", "sell"}] == ["buy", "sell"]
    assert [marker["action"] for marker in markers] == ["buy", "sell"]
    assert all(marker["decision_id"] for marker in markers)


def test_fetch_news_library_command_writes_per_symbol_news_store(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["AMDUSDT", "NVDAUSDT"],
  "granularity": "1d",
  "limit": 30,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral",
  "price_source": "yahoo_chart_daily",
  "ticker_map": {"AMDUSDT": "AMD", "NVDAUSDT": "NVDA"}
}
""".strip(),
        encoding="utf-8",
    )

    from bitget_ai_backtest.events import NewsEvent

    def fake_collect_events(config, *, skill_export_dir):
        assert config.symbols == ("AMDUSDT", "NVDAUSDT")
        return [
            NewsEvent(
                event_id="amd-news",
                symbol="AMDUSDT",
                published_at="2026-06-12T20:00:00Z",
                title="AMD raises guidance",
                source_name="Yahoo Finance RSS",
                source_type="public_news_fallback",
                url="https://example.com/amd",
                sentiment="bullish",
                confidence=0.7,
                reason="Matched bullish keyword: raises guidance",
                strength="strong",
                topic="earnings_guidance",
                time_horizon="medium_term",
                stock_relevance="direct",
            )
        ]

    monkeypatch.setattr("bitget_ai_backtest.cli.collect_events", fake_collect_events)

    output_dir = tmp_path / "news"
    empty_archive = tmp_path / "empty-archive"
    exit_code = main(
        [
            "fetch-news-library",
            "--config",
            str(config),
            "--days",
            "30",
            "--output-dir",
            str(output_dir),
            "--external-news-archive",
            str(empty_archive),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "AMDUSDT" / "raw" / "events.json").exists()
    assert (output_dir / "AMDUSDT" / "ai-events" / "events.json").exists()
    assert (output_dir / "AMDUSDT" / "coverage.json").exists()


def test_fetch_news_library_merges_daily_stock_analysis_archive(tmp_path: Path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["AMDUSDT"],
  "granularity": "1d",
  "limit": 180,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral",
  "price_source": "yahoo_chart_daily",
  "ticker_map": {"AMDUSDT": "AMD"}
}
""".strip(),
        encoding="utf-8",
    )
    archive = tmp_path / "archive" / "2026-03-01" / "AMD" / "news.jsonl"
    archive.parent.mkdir(parents=True)
    archive.write_text(
        json.dumps(
            {
                "symbol": "AMD",
                "provider": "YahooFinanceRSS",
                "source_type": "rss",
                "title": "AMD receives analyst upgrade on AI demand",
                "url": "https://example.com/amd-upgrade",
                "source": "Yahoo Finance",
                "published_at": "2026-03-01T13:30:00Z",
                "snippet": "Analyst cites AI demand.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr("bitget_ai_backtest.cli.collect_events", lambda config, *, skill_export_dir: [])

    output_dir = tmp_path / "news"
    exit_code = main(
        [
            "fetch-news-library",
            "--config",
            str(config),
            "--days",
            "180",
            "--output-dir",
            str(output_dir),
            "--external-news-archive",
            str(tmp_path / "archive"),
        ]
    )

    events = json.loads((output_dir / "AMDUSDT" / "ai-events" / "events.json").read_text(encoding="utf-8"))["events"]
    assert exit_code == 0
    assert len(events) == 1
    assert events[0]["source_type"] == "daily_stock_analysis_archive"


def test_backtest_with_news_library_writes_candidates_and_news_coverage(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.json"
    config.write_text(
        """
{
  "symbols": ["AMDUSDT"],
  "granularity": "1d",
  "limit": 60,
  "initial_cash": 10000,
  "trade_fraction": 0.25,
  "fee_rate": 0.0006,
  "macro_mode": "neutral",
  "news_bias": "neutral",
  "price_source": "yahoo_chart_daily",
  "ticker_map": {"AMDUSDT": "AMD"}
}
""".strip(),
        encoding="utf-8",
    )

    from bitget_ai_backtest.events import NewsEvent
    from bitget_ai_backtest.models import Candle
    from bitget_ai_backtest.news_library import write_news_library

    values = [100 + index * 0.2 + (1.0 if index % 2 == 0 else -0.5) for index in range(60)]

    class FakeYahooClient:
        def fetch_candles(self, ticker: str, granularity: str, limit: int):
            assert ticker == "AMD"
            return [
                Candle(1_800_000_000 + index * 86_400_000, value, value, value, value, 1000, 1000 * value)
                for index, value in enumerate(values)
            ]

    monkeypatch.setattr("bitget_ai_backtest.cli.YahooChartDailyClient", FakeYahooClient)
    news_dir = tmp_path / "news"
    write_news_library(
        news_dir,
        [
            NewsEvent(
                event_id="amd-news",
                symbol="AMDUSDT",
                published_at="1970-03-19T20:00:00Z",
                title="AMD raises guidance on AI demand",
                source_name="Yahoo Finance RSS",
                source_type="public_news_fallback",
                url="https://example.com/amd",
                sentiment="bullish",
                confidence=0.8,
                reason="Matched bullish keyword: raises guidance",
                strength="strong",
                topic="earnings_guidance",
                time_horizon="medium_term",
                stock_relevance="direct",
            )
        ],
        fetched_at="2026-06-17T09:00:00Z",
    )

    output_dir = tmp_path / "reports"
    exit_code = main(
        [
            "backtest",
            "--config",
            str(config),
            "--news-library",
            str(news_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    assert (output_dir / "technical-candidates.json").exists()
    assert (output_dir / "candidate-markers.json").exists()
    assert (output_dir / "news-coverage.json").exists()
    decisions = json.loads((output_dir / "decision-records.json").read_text(encoding="utf-8"))["decision_records"]
    candidate_markers = json.loads((output_dir / "candidate-markers.json").read_text(encoding="utf-8"))["candidate_markers"]
    assert any(row["action"] == "buy" for row in decisions)
    assert candidate_markers
