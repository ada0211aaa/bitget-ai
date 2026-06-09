from pathlib import Path

import pytest

from bitget_ai_backtest.env import load_playbook_api_key


def test_load_playbook_api_key_reads_dotenv_without_printing_value(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        'PLAYBOOK_API_KEY="x"\nOTHER_VALUE=ignored\n',
        encoding="utf-8",
    )

    assert load_playbook_api_key(env_path) == "x"


def test_load_playbook_api_key_rejects_missing_key(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OTHER_VALUE=ignored\n", encoding="utf-8")

    with pytest.raises(ValueError, match="PLAYBOOK_API_KEY"):
        load_playbook_api_key(env_path)
