import json
import urllib.error
from io import BytesIO

from worklog.github_collector import collect_github_activity


class _FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_collect_github_activity_no_token_skips(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    result = collect_github_activity("owner", "repo", token=None)
    assert result.skipped is True
    assert "GITHUB_TOKEN" in result.reason
    assert result.items == []


def test_collect_github_activity_separates_issues_and_prs(monkeypatch):
    issues_payload = [
        {"number": 1, "title": "Real issue", "state": "open", "html_url": "u1", "updated_at": "t1", "body": ""},
        {
            "number": 2,
            "title": "This is actually a PR",
            "state": "open",
            "html_url": "u2",
            "updated_at": "t2",
            "body": "",
            "pull_request": {"url": "..."},
        },
    ]
    prs_payload = [
        {
            "number": 3,
            "title": "A pull request",
            "state": "closed",
            "merged_at": "2026-07-01T00:00:00Z",
            "html_url": "u3",
            "updated_at": "t3",
            "body": "Closes #1",
        }
    ]

    calls = []

    def fake_urlopen(req, timeout=15):
        calls.append(req.full_url)
        if "issues" in req.full_url:
            return _FakeResponse(issues_payload)
        return _FakeResponse(prs_payload)

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    result = collect_github_activity("owner", "repo", token="fake-token")
    assert result.skipped is False
    kinds = {(item.kind, item.number) for item in result.items}
    assert kinds == {("issue", 1), ("pr", 3)}
    pr_item = next(i for i in result.items if i.kind == "pr")
    assert pr_item.merged is True
    assert len(calls) == 2


def test_collect_github_activity_http_error(monkeypatch):
    def fake_urlopen(req, timeout=15):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", hdrs=None, fp=BytesIO(b""))

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = collect_github_activity("owner", "repo", token="fake-token")
    assert result.skipped is True
    assert "404" in result.reason


def test_collect_github_activity_url_error(monkeypatch):
    def fake_urlopen(req, timeout=15):
        raise urllib.error.URLError("network down")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = collect_github_activity("owner", "repo", token="fake-token")
    assert result.skipped is True
    assert "unreachable" in result.reason


def test_collect_github_activity_uses_env_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "env-token")

    def fake_urlopen(req, timeout=15):
        assert req.get_header("Authorization") == "Bearer env-token"
        return _FakeResponse([])

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = collect_github_activity("owner", "repo")
    assert result.skipped is False
