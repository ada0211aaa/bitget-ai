from pathlib import Path
from io import BytesIO
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from bitget_ai_backtest.playbook_client import PlaybookClient, PlaybookError


class FakeResponse:
    def __init__(self, payload: bytes, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_list_playbooks_uses_access_key_header() -> None:
    captured: list[Request] = []

    def opener(request: Request, timeout: float) -> FakeResponse:
        captured.append(request)
        assert timeout == 30.0
        return FakeResponse(b'{"code":"200","data":{"items":[]},"msg":""}')

    client = PlaybookClient("secret-key", opener=opener)

    result = client.list_playbooks(status="draft")

    assert result["code"] == "200"
    assert captured[0].full_url == "https://api.bitget.com/api/v1/playbook/list?status=draft"
    assert captured[0].headers["Access-key"] == "secret-key"


def test_run_playbook_posts_version_id_as_json() -> None:
    captured: list[Request] = []

    def opener(request: Request, timeout: float) -> FakeResponse:
        captured.append(request)
        return FakeResponse(b'{"run_id":"run-1","status":"pending"}')

    client = PlaybookClient("secret-key", opener=opener)

    result = client.run_backtest("draft-1")

    assert result["run_id"] == "run-1"
    assert captured[0].full_url == "https://api.bitget.com/api/v1/playbook/run"
    assert captured[0].headers["Content-type"] == "application/json"
    assert captured[0].data == b'{"version_id": "draft-1"}'


def test_upload_playbook_sends_tarball_without_leaking_key(tmp_path: Path) -> None:
    package = tmp_path / "strategy.tar.gz"
    package.write_bytes(b"fake-tarball")
    captured: list[Request] = []

    def opener(request: Request, timeout: float) -> FakeResponse:
        captured.append(request)
        return FakeResponse(b'{"draft_id":"draft-1","strategy_id":"strategy-1"}')

    client = PlaybookClient("secret-key", opener=opener)

    result = client.upload_package(package)

    assert result["draft_id"] == "draft-1"
    assert captured[0].full_url == "https://api.bitget.com/api/v1/playbook/upload"
    assert captured[0].headers["Access-key"] == "secret-key"
    assert b"fake-tarball" in captured[0].data


def test_http_error_redacts_api_key() -> None:
    def opener(_request: Request, _timeout: float) -> FakeResponse:
        raise HTTPError(
            "https://api.bitget.com/api/v1/playbook/run",
            403,
            "Forbidden secret-key",
            hdrs=None,
            fp=None,
        )

    client = PlaybookClient("secret-key", opener=opener)

    with pytest.raises(PlaybookError) as exc:
        client.run_backtest("draft-1")

    assert "secret-key" not in str(exc.value)
    assert "<redacted>" in str(exc.value)


def test_http_error_includes_response_detail(tmp_path: Path) -> None:
    package = tmp_path / "strategy.tar.gz"
    package.write_bytes(b"fake-tarball")

    def opener(_request: Request, _timeout: float) -> FakeResponse:
        raise HTTPError(
            "https://api.bitget.com/api/v1/playbook/upload",
            422,
            "Unprocessable Entity",
            hdrs=None,
            fp=BytesIO(b'{"detail":{"errors":["manifest.yaml: bad value"]}}'),
        )

    client = PlaybookClient("secret-key", opener=opener)

    with pytest.raises(PlaybookError) as exc:
        client.upload_package(package)

    assert "manifest.yaml: bad value" in str(exc.value)
