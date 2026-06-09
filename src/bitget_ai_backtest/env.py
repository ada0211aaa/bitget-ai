from __future__ import annotations

from pathlib import Path


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_playbook_api_key(path: Path = Path(".env")) -> str:
    key = load_dotenv(path).get("PLAYBOOK_API_KEY", "").strip()
    if not key or key == "<YOUR_PLAYBOOK_API_KEY>":
        raise ValueError(f"PLAYBOOK_API_KEY is missing in {path}")
    return key
