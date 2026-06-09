from __future__ import annotations

import tarfile
from pathlib import Path


ALLOWED_TOP_LEVEL_FILES = {"README.md", "manifest.yaml", "backtest.yaml"}
ALLOWED_TOP_LEVEL_DIRS = {"src"}


def create_package_archive(package_dir: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output_path, "w:gz") as archive:
        for file_path in sorted(package_dir.rglob("*")):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(package_dir)
            if _is_upload_allowed(relative):
                archive.add(file_path, arcname=str(relative))
    return output_path


def _is_upload_allowed(relative: Path) -> bool:
    parts = relative.parts
    if len(parts) == 1:
        return parts[0] in ALLOWED_TOP_LEVEL_FILES
    return parts[0] in ALLOWED_TOP_LEVEL_DIRS
