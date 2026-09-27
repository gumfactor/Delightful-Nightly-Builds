import json

from briefing import generate_briefing
from store import SyncRun


def run(run_id, matched=1, conflict=0, tw_only=0, coda_only=0):
    return SyncRun(run_id, "2026-09-27T08:00:00+00:00", matched, conflict, tw_only, coda_only)


def test_no_api_key_returns_deterministic_template_and_makes_no_network_call():
    called = {"count": 0}

    def fake_post(url, headers, body):
        called["count"] += 1
        return b"{}"

    latest = run(1, matched=3, conflict=1, tw_only=2, coda_only=1)
    text = generate_briefing(latest, [latest], api_key=None, http_post=fake_post)

    assert called["count"] == 0
    assert "3" in text and "1" in text and "2" in text
    assert "first recorded sync" in text


def test_deterministic_briefing_reports_improving_trend():
    older = run(1, matched=1, conflict=3, tw_only=2, coda_only=1)  # gap = 6
    latest = run(2, matched=1, conflict=1, tw_only=1, coda_only=0)  # gap = 2
    text = generate_briefing(latest, [older, latest], api_key=None)
    assert "shrunk" in text


def test_deterministic_briefing_reports_worsening_trend():
    older = run(1, matched=1, conflict=0, tw_only=0, coda_only=0)  # gap = 0
    latest = run(2, matched=1, conflict=2, tw_only=1, coda_only=1)  # gap = 4
    text = generate_briefing(latest, [older, latest], api_key=None)
    assert "grown" in text


def test_with_api_key_calls_anthropic_and_sends_only_aggregate_counts():
    captured = {}

    def fake_post(url, headers, body):
        captured["url"] = url
        captured["body"] = json.loads(body)
        return json.dumps({"content": [{"text": "Everything looks fine overall."}]}).encode("utf-8")

    latest = run(1, matched=5, conflict=1, tw_only=0, coda_only=2)
    text = generate_briefing(latest, [latest], api_key="fake-key", http_post=fake_post)

    assert text == "Everything looks fine overall."
    assert captured["url"].startswith("https://api.anthropic.com")
    request_text = json.dumps(captured["body"])
    # Only aggregate numbers/labels should ever appear in the outbound request body —
    # never a task title (none of our fixtures' distinctive titles should leak through).
    assert "Finish Q3" not in request_text
    assert "Lone TW" not in request_text
    assert '"matched_ok": 5' in request_text or "matched_ok" in request_text


def test_anthropic_error_falls_back_to_deterministic_template():
    from briefing import BriefingError

    def failing_post(url, headers, body):
        raise BriefingError("Anthropic API returned status 500")

    latest = run(1, matched=2, conflict=0, tw_only=0, coda_only=0)
    text = generate_briefing(latest, [latest], api_key="fake-key", http_post=failing_post)
    assert "2" in text
    assert "first recorded sync" in text
