"""Read-only client for the Coda API v1 (docs/{docId}/tables/{tableId}/rows).

HTTP transport is injected (`http_get`) so tests can substitute a mock
instead of touching the network or monkeypatching urllib internals.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Optional

PAGE_LIMIT = 200


class CodaAPIError(RuntimeError):
    """Raised when the Coda API returns a non-2xx response or malformed body."""


HttpGet = Callable[[str, dict[str, str]], "HttpResponse"]


class HttpResponse:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self.body = body


def _default_http_get(url: str, headers: dict[str, str]) -> HttpResponse:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return HttpResponse(response.status, response.read())
    except urllib.error.HTTPError as exc:
        return HttpResponse(exc.code, exc.read())


class CodaClient:
    def __init__(
        self,
        api_key: str,
        http_get: Optional[HttpGet] = None,
    ):
        if not api_key:
            raise ValueError("Coda api_key is required")
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._http_get = http_get or _default_http_get

    def fetch_rows(
        self,
        doc_id: str,
        table_id: str,
        title_column: str,
        status_column: str,
        done_values: list[str],
    ) -> list[dict]:
        """Fetch every row of one table, following `nextPageToken` pagination."""
        done_values_lower = {v.casefold() for v in done_values}
        rows: list[dict] = []
        page_token: Optional[str] = None

        while True:
            # useColumnNames=true is required so `values` is keyed by the column's
            # display name (e.g. "Name", "Status") instead of its internal column ID —
            # without it, every _normalize_row lookup below would silently return "".
            params = {"valueFormat": "simple", "useColumnNames": "true", "limit": str(PAGE_LIMIT)}
            if page_token:
                params["pageToken"] = page_token
            url = (
                f"https://coda.io/apis/v1/docs/{doc_id}/tables/{table_id}/rows"
                f"?{urllib.parse.urlencode(params)}"
            )
            response = self._http_get(url, self._headers)
            if response.status != 200:
                raise CodaAPIError(
                    f"Coda API returned status {response.status} for table {table_id}"
                )
            try:
                payload = json.loads(response.body)
            except json.JSONDecodeError as exc:
                raise CodaAPIError("Coda API returned malformed JSON") from exc

            for raw in payload.get("items", []):
                rows.append(
                    _normalize_row(raw, title_column, status_column, done_values_lower, doc_id)
                )

            page_token = payload.get("nextPageToken")
            if not page_token:
                break

        return rows


def _normalize_row(
    raw: dict,
    title_column: str,
    status_column: str,
    done_values_lower: set[str],
    doc_id: str,
) -> dict:
    values = raw.get("values", {})
    title = str(values.get(title_column, "") or "")
    status_text = str(values.get(status_column, "") or "")
    is_done = status_text.strip().casefold() in done_values_lower
    row_id = raw.get("id", "")
    browser_link = raw.get("browserLink") or f"https://coda.io/d/{doc_id}#_{row_id}"
    return {
        "id": row_id,
        "title": title,
        "status_text": status_text,
        "is_done": is_done,
        "url": browser_link,
    }
