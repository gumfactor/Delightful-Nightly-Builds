import json
import threading
import urllib.error
import urllib.request

import pytest

from ctxvault.server import App, make_server

SUMMARY = json.dumps({"title": "T", "goal": "G", "decisions": ["d"], "open_threads": ["o"], "next_steps": ["n"]})


@pytest.fixture
def base(conn, src):
    server = make_server(App(conn, src, complete=lambda prompt: SUMMARY), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def call(url, method="GET", headers=None):
    request = urllib.request.Request(url, method=method, headers=headers or {}, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def get_json(url):
    status, body = call(url)
    return status, json.loads(body)


def test_index_page_served(base):
    status, body = call(base + "/")
    assert status == 200 and b"Context Vault" in body


def test_projects_sessions_and_session_routes(base):
    assert {p["project"] for p in get_json(base + "/api/projects")[1]} == {"canada-list", "kwyeter"}
    sessions = get_json(base + "/api/sessions?project=kwyeter")[1]
    assert len(sessions) == 1
    assert get_json(base + "/api/session/" + sessions[0]["id"])[1]["messages"]


def test_search_route_and_empty_query(base):
    assert get_json(base + "/api/search?q=calibration")[1]
    assert get_json(base + "/api/search?q=")[1] == []


def test_brief_route_and_404s(base):
    assert "Resume brief" in get_json(base + "/api/brief?project=kwyeter")[1]["markdown"]
    assert get_json(base + "/api/brief?project=none")[0] == 404
    assert get_json(base + "/api/session/ghost")[0] == 404
    assert get_json(base + "/api/unknown")[0] == 404


def test_post_without_csrf_header_is_forbidden(base):
    assert call(base + "/api/reindex", "POST")[0] == 403
    assert call(base + "/api/summarize", "POST")[0] == 403


def test_summarize_one_and_all_with_mock(base):
    ok, body = call(base + "/api/summarize/demo-kwyeter-0", "POST", {"X-Ctxvault": "1"})
    assert ok == 200 and json.loads(body)["title"] == "T"
    done = json.loads(call(base + "/api/summarize?project=canada-list", "POST", {"X-Ctxvault": "1"})[1])
    assert done["summarized"] == 2


def test_reindex_route(base):
    assert json.loads(call(base + "/api/reindex", "POST", {"X-Ctxvault": "1"})[1])["indexed"] == 0


def test_foreign_host_header_rejected_against_dns_rebinding(base):
    assert call(base + "/api/projects", headers={"Host": "evil.example.com"})[0] == 403
