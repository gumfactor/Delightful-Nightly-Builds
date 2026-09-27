import json
import urllib.error
from unittest.mock import patch

import pytest

from coda_client import CodaAPIError, CodaClient, HttpResponse, _default_http_get


def make_page(items, next_page_token=None):
    body = {"items": items}
    if next_page_token:
        body["nextPageToken"] = next_page_token
    return HttpResponse(200, json.dumps(body).encode("utf-8"))


def row(row_id, values, browser_link=None):
    r = {"id": row_id, "values": values}
    if browser_link:
        r["browserLink"] = browser_link
    return r


def test_requires_api_key():
    with pytest.raises(ValueError):
        CodaClient(api_key="")


def test_fetch_rows_extracts_configured_columns():
    def fake_get(url, headers):
        return make_page([row("r1", {"Name": "Finish report", "Status": "Done"}, "https://coda.io/x")])

    client = CodaClient(api_key="tok", http_get=fake_get)
    rows = client.fetch_rows("doc1", "table1", "Name", "Status", ["Done", "Complete"])

    assert rows == [
        {
            "id": "r1",
            "title": "Finish report",
            "status_text": "Done",
            "is_done": True,
            "url": "https://coda.io/x",
        }
    ]


def test_fetch_rows_requests_named_columns_not_column_ids():
    # Without useColumnNames=true, Coda keys `values` by internal column ID, not
    # the display names ("Name", "Status") this client looks up — every title and
    # status would come back blank on a live sync without this request parameter.
    captured = {}

    def fake_get(url, headers):
        captured["url"] = url
        return make_page([])

    client = CodaClient(api_key="tok", http_get=fake_get)
    client.fetch_rows("doc1", "table1", "Name", "Status", ["Done"])
    assert "useColumnNames=true" in captured["url"]


def test_fetch_rows_sends_bearer_auth_header():
    captured = {}

    def fake_get(url, headers):
        captured["headers"] = headers
        return make_page([])

    client = CodaClient(api_key="secret-tok", http_get=fake_get)
    client.fetch_rows("doc1", "table1", "Name", "Status", ["Done"])
    assert captured["headers"]["Authorization"] == "Bearer secret-tok"


def test_done_value_matching_is_case_insensitive():
    def fake_get(url, headers):
        return make_page([row("r1", {"Name": "Task", "Status": "done"})])

    client = CodaClient(api_key="tok", http_get=fake_get)
    rows = client.fetch_rows("doc1", "table1", "Name", "Status", ["Done"])
    assert rows[0]["is_done"] is True


def test_missing_status_value_treated_as_not_done():
    def fake_get(url, headers):
        return make_page([row("r1", {"Name": "Task with no status"})])

    client = CodaClient(api_key="tok", http_get=fake_get)
    rows = client.fetch_rows("doc1", "table1", "Name", "Status", ["Done"])
    assert rows[0]["is_done"] is False
    assert rows[0]["status_text"] == ""


def test_blank_status_value_treated_as_not_done():
    def fake_get(url, headers):
        return make_page([row("r1", {"Name": "Task", "Status": "   "})])

    client = CodaClient(api_key="tok", http_get=fake_get)
    rows = client.fetch_rows("doc1", "table1", "Name", "Status", ["Done"])
    assert rows[0]["is_done"] is False


def test_fetch_rows_follows_next_page_token_until_exhausted():
    pages = [
        make_page([row("r1", {"Name": "First"})], next_page_token="page2"),
        make_page([row("r2", {"Name": "Second"})]),
    ]
    calls = []

    def fake_get(url, headers):
        calls.append(url)
        return pages.pop(0)

    client = CodaClient(api_key="tok", http_get=fake_get)
    rows = client.fetch_rows("doc1", "table1", "Name", "Status", ["Done"])

    assert len(calls) == 2
    assert "pageToken=page2" in calls[1]
    assert [r["title"] for r in rows] == ["First", "Second"]


def test_default_http_get_converts_connection_failure_to_coda_api_error():
    # A DNS/timeout/connection failure raises urllib.error.URLError (HTTPError's
    # superclass) before any HTTP response exists — this must surface as a typed
    # CodaAPIError, not an uncaught traceback out of the CLI.
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Name or service not known")):
        with pytest.raises(CodaAPIError, match="Coda API request failed"):
            _default_http_get("https://coda.io/apis/v1/docs/doc1/tables/table1/rows", {})


def test_non_200_status_raises_coda_api_error():
    def fake_get(url, headers):
        return HttpResponse(403, b'{"error": "forbidden"}')

    client = CodaClient(api_key="badtok", http_get=fake_get)
    with pytest.raises(CodaAPIError):
        client.fetch_rows("doc1", "table1", "Name", "Status", ["Done"])


def test_malformed_json_raises_coda_api_error():
    def fake_get(url, headers):
        return HttpResponse(200, b"not json")

    client = CodaClient(api_key="tok", http_get=fake_get)
    with pytest.raises(CodaAPIError):
        client.fetch_rows("doc1", "table1", "Name", "Status", ["Done"])
