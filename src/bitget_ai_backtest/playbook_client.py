from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_PLAYBOOK_BASE_URL = "https://api.bitget.com"


class PlaybookError(RuntimeError):
    pass


Opener = Callable[[Request, float], Any]


def _default_opener(request: Request, timeout: float) -> Any:
    return urlopen(request, timeout=timeout)


class PlaybookClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_PLAYBOOK_BASE_URL,
        opener: Opener | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._credential = api_key
        self.base_url = base_url.rstrip("/")
        self.opener = opener or _default_opener
        self.timeout = timeout

    def list_playbooks(self, *, status: str = "published") -> dict[str, Any]:
        query = urlencode({"status": status})
        request = self._request("GET", f"/api/v1/playbook/list?{query}")
        return self._send_json(request)

    def upload_package(self, package_path: Path) -> dict[str, Any]:
        boundary = f"----bitget-playbook-{uuid.uuid4().hex}"
        body = self._multipart_file_body("package", package_path, boundary)
        request = self._request(
            "POST",
            "/api/v1/playbook/upload",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        return self._send_json(request)

    def run_backtest(self, version_id: str) -> dict[str, Any]:
        body = json.dumps({"version_id": version_id}).encode("utf-8")
        request = self._request(
            "POST",
            "/api/v1/playbook/run",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        return self._send_json(request)

    def get_run(self, run_id: str) -> dict[str, Any]:
        query = urlencode({"run_id": run_id})
        request = self._request("GET", f"/api/v1/playbook/run?{query}")
        return self._send_json(request)

    def _request(
        self,
        method: str,
        path: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> Request:
        request_headers = {"ACCESS-KEY": self._credential}
        if headers:
            request_headers.update(headers)
        return Request(
            f"{self.base_url}{path}",
            data=data,
            headers=request_headers,
            method=method,
        )

    def _send_json(self, request: Request) -> dict[str, Any]:
        try:
            with self.opener(request, self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = self._format_error_body(exc.read())
            message = f"Playbook API HTTP {exc.code}: {exc.reason}"
            if detail:
                message = f"{message}; {detail}"
            raise PlaybookError(self._redact(message)) from exc
        except URLError as exc:
            raise PlaybookError(self._redact(f"Playbook API connection failed: {exc.reason}")) from exc

        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise PlaybookError("Playbook API returned non-JSON response") from exc
        if not isinstance(payload, dict):
            raise PlaybookError("Playbook API returned an unexpected response shape")
        return payload

    def _multipart_file_body(self, field_name: str, path: Path, boundary: str) -> bytes:
        filename = path.name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        parts = [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
        return b"".join(parts)

    def _redact(self, message: str) -> str:
        return message.replace(self._credential, "<redacted>")

    @staticmethod
    def _format_error_body(raw: bytes) -> str:
        if not raw:
            return ""
        text = raw.decode("utf-8", errors="replace")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text[:500]
        detail = payload.get("detail") if isinstance(payload, dict) else None
        if isinstance(detail, str):
            return detail
        if isinstance(detail, dict):
            errors = detail.get("errors")
            if isinstance(errors, list):
                return "; ".join(str(error) for error in errors)
        return json.dumps(payload, ensure_ascii=False)[:500]
