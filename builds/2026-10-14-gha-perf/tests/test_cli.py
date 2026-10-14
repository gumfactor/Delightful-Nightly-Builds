import json

import pytest

from conftest import FakeTransport, json_response
from gha_perf import ai
from gha_perf.cli import run

RUN = {"id": 11, "name": "CI", "event": "push", "head_sha": "abc", "conclusion": "success",
       "run_started_at": "2026-10-13T10:00:00Z", "updated_at": "2026-10-13T10:03:00Z"}
JOB = {"name": "t", "labels": ["ubuntu-latest"], "started_at": "2026-10-13T10:00:00Z", "completed_at": "2026-10-13T10:02:00Z",
       "steps": []}


def routes():
    return FakeTransport([
        ("/user/repos", json_response([{"full_name": "me/app"}])),
        ("/jobs", json_response({"jobs": [JOB]})),
        ("/actions/runs", json_response({"workflow_runs": [RUN]})),
    ])


def test_end_to_end_writes_html_and_json(tmp_path, capsys):
    html_path, json_path = tmp_path / "r.html", tmp_path / "r.json"
    code = run(["-o", str(html_path), "--json", str(json_path)], env={"GITHUB_TOKEN": "t"}, transport=routes())
    assert code == 0 and "me/app" in html_path.read_text()
    assert json.loads(json_path.read_text())["summary"]["runs"] == 1
    assert "1 runs across 1 repos" in capsys.readouterr().out


def test_missing_token_exits_2(tmp_path, capsys):
    assert run(["-o", str(tmp_path / "r.html")], env={}, transport=routes()) == 2
    assert "GITHUB_TOKEN" in capsys.readouterr().err


def test_invalid_days_exits_2(tmp_path):
    assert run(["--days", "0", "-o", str(tmp_path / "r.html")], env={"GITHUB_TOKEN": "t"}, transport=routes()) == 2


def test_explicit_repos_skip_repo_listing(tmp_path):
    transport = routes()
    run(["--repos", "me/app", "-o", str(tmp_path / "r.html")], env={"GITHUB_TOKEN": "t"}, transport=transport)
    assert not any("/user/repos" in url for url in transport.calls)


def test_repo_listing_failure_returns_1(tmp_path, capsys):
    transport = FakeTransport([("/user/repos", (401, {}, b"{}"))])
    assert run(["-o", str(tmp_path / "r.html")], env={"GITHUB_TOKEN": "bad"}, transport=transport) == 1


def test_ai_flag_without_key_still_produces_report(tmp_path, capsys):
    out = tmp_path / "r.html"
    assert run(["--ai", "-o", str(out)], env={"GITHUB_TOKEN": "t"}, transport=routes()) == 0
    assert out.exists() and "AI briefing" not in out.read_text()
    assert "AI briefing unavailable" in capsys.readouterr().err


def test_ai_summary_is_included_when_api_responds(tmp_path):
    out = tmp_path / "r.html"
    sent = {}

    def fake_post(url, headers, body):
        sent["headers"], sent["body"] = headers, json.loads(body)
        return json.dumps({"content": [{"type": "text", "text": "Cache npm in me/app CI."}]}).encode()

    run(["--ai", "-o", str(out)], env={"GITHUB_TOKEN": "t", "ANTHROPIC_API_KEY": "k"}, transport=routes(), ai_post=fake_post)
    assert "Cache npm in me/app CI." in out.read_text()
    assert sent["headers"]["x-api-key"] == "k" and "me/app" in sent["body"]["messages"][0]["content"]


def test_ai_failure_returns_none_instead_of_raising():
    def failing_post(url, headers, body):
        raise OSError("down")

    report = {"summary": {}, "workflows": [], "steps": [], "findings": []}
    assert ai.summarize(report, "k", failing_post) is None


@pytest.mark.parametrize("body", [b"not json", b'{"content": []}'])
def test_ai_malformed_response_returns_none(body):
    report = {"summary": {}, "workflows": [], "steps": [], "findings": []}
    assert ai.summarize(report, "k", lambda *_: body) is None
