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
