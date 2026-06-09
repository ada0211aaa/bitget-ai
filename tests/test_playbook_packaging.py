import tarfile
from pathlib import Path

from bitget_ai_backtest.playbook_package import create_package_archive


def test_create_package_archive_includes_only_playbook_files(tmp_path: Path) -> None:
    package_dir = tmp_path / "playbook"
    (package_dir / "src").mkdir(parents=True)
    (package_dir / "tests").mkdir()
    (package_dir / "README.md").write_text("readme", encoding="utf-8")
    (package_dir / "manifest.yaml").write_text("name: demo\n", encoding="utf-8")
    (package_dir / "backtest.yaml").write_text("execution: {}\n", encoding="utf-8")
    (package_dir / "src" / "main.py").write_text("def run(): pass\n", encoding="utf-8")
    (package_dir / "tests" / "local_only.py").write_text("secret = 'nope'\n", encoding="utf-8")
    output = tmp_path / "demo.tar.gz"

    create_package_archive(package_dir, output)

    with tarfile.open(output, "r:gz") as archive:
        names = sorted(archive.getnames())

    assert names == [
        "README.md",
        "backtest.yaml",
        "manifest.yaml",
        "src/main.py",
    ]
