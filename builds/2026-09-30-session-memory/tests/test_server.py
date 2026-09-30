import json
import socket

from sessionmemory.server import HOST


def get_json(call, path):
    status, body = call(path)
    return status, json.loads(body)


def test_binds_to_loopback_only():
    assert HOST == "127.0.0.1"


def test_index_page_is_served(live_server):
    status, body = live_server("/")
    assert status == 200 and b"Session Memory" in body


def test_status_and_projects(live_server):
    _, status = get_json(live_server, "/api/status")
    assert status["sessions"] == 5 and set(status["by_source"]) == {"claude-code", "claude-ai", "chatgpt"}
    _, projects = get_json(live_server, "/api/projects")
    assert {p["project"] for p in projects} >= {"canada-list", "stress-book"}


def test_search_endpoint_returns_highlights(live_server):
    code, hits = get_json(live_server, "/api/search?q=postal&project=canada-list")
    assert code == 200 and hits and "\x02" in hits[0]["snippet"]
    assert get_json(live_server, "/api/search?q=")[1] == []


def test_session_endpoint_includes_summary_and_404(live_server):
    _, sessions = get_json(live_server, "/api/sessions?project=canada-list")
    code, detail = get_json(live_server, "/api/session/" + sessions[0]["id"])
    assert code == 200 and detail["summary"]["kind"] == "heuristic" and detail["messages"]
    assert get_json(live_server, "/api/session/does-not-exist")[0] == 404


def test_session_id_path_traversal_is_just_a_missing_id(live_server):
    assert get_json(live_server, "/api/session/..%2F..%2Fetc%2Fpasswd")[0] == 404


def test_brief_endpoint(live_server):
    code, data = get_json(live_server, "/api/brief?project=canada-list")
    assert code == 200 and "resume brief" in data["markdown"]
    assert get_json(live_server, "/api/brief")[0] == 400
    assert get_json(live_server, "/api/brief?project=canada-list&kind=ai")[0] == 404


def test_ai_summarize_uses_injected_post_and_caches(live_server):
    _, sessions = get_json(live_server, "/api/sessions?project=stress-book")
    session_id = sessions[0]["id"]
    code, body = live_server("/api/summarize", {"session_id": session_id})
    assert code == 200 and json.loads(body)["title"] == "AI title"
    _, detail = get_json(live_server, "/api/session/" + session_id)
    assert detail["summary"]["kind"] == "ai"
    assert len(live_server.posts) == 1


def test_ai_summarize_errors_are_reported_without_a_key(live_server, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # the fixture injects a fake post, but the key check happens first
    _, sessions = get_json(live_server, "/api/sessions")
    code, body = live_server("/api/summarize", {"session_id": sessions[0]["id"]})
    assert code == 400 and "ANTHROPIC_API_KEY" in json.loads(body)["error"]


def test_bad_post_bodies(live_server):
    assert live_server("/api/summarize", {"session_id": "nope"})[0] in (400, 404)
    status, _ = live_server("/api/ai_brief", {})
    assert status == 400
    sock = socket.create_connection(("127.0.0.1", live_server.port))
    sock.sendall(b"POST /api/ingest HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 5\r\n\r\n{nope")
    assert b"400" in sock.recv(200).split(b"\r\n")[0]
    sock.close()


def test_foreign_host_header_is_rejected(live_server):
    status, _ = live_server("/api/status", headers={"Host": "evil.example.com"})
    assert status == 403


def test_rescan_is_idempotent(live_server):
    code, body = live_server("/api/ingest", {})
    assert code == 200 and json.loads(body)["unchanged"] == 5
