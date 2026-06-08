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
