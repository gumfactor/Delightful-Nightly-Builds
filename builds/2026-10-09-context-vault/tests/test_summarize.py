import json

import pytest

from ctxvault import store, summarize
from ctxvault.summarize import SummarizeError, parse_summary

GOOD = {"title": "Fix dedupe", "goal": "Stop duplicates", "decisions": ["Normalise host"],
        "open_threads": ["Franchise merge"], "next_steps": ["Add location key"]}


def test_parse_plain_and_fenced_json():
    assert parse_summary(json.dumps(GOOD))["title"] == "Fix dedupe"
    fenced = "Here you go:\n```json\n" + json.dumps(GOOD) + "\n```"
    assert parse_summary(fenced)["open_threads"] == ["Franchise merge"]


def test_parse_rejects_garbage():
    with pytest.raises(SummarizeError):
        parse_summary("no json here")
    with pytest.raises(SummarizeError):
        parse_summary("{broken: json}")


def test_parse_coerces_bad_shapes():
    out = parse_summary('{"title": 5, "decisions": "oops", "open_threads": ["a", "", 3]}')
    assert out["title"] == "5" and out["decisions"] == [] and out["open_threads"] == ["a", "3"]


def test_condense_keeps_head_and_tail_when_long():
    msgs = [{"role": "user", "text": "START" + "x" * 1000}] + \
           [{"role": "assistant", "text": "m" * 1000}] * 60 + [{"role": "user", "text": "THE END"}]
    out = summarize.condense(msgs, limit=2000)
    assert "START" in out and "THE END" in out and "omitted" in out and len(out) < 2200


def test_summarize_session_stores_result_using_mock(conn):
    prompts = []

    def fake(prompt):
        prompts.append(prompt)
        return json.dumps(GOOD)

    summarize.summarize_session(conn, "demo-canada-list-0", fake)
    assert "www" in prompts[0]  # transcript content reached the prompt
    assert store.get_session(conn, "demo-canada-list-0")["summary"]["goal"] == "Stop duplicates"


def test_missing_api_key_raises_clear_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SummarizeError, match="ANTHROPIC_API_KEY"):
        summarize.anthropic_complete("hi")


def test_pending_collects_errors_and_continues(conn):
    calls = {"n": 0}

    def flaky(prompt):
        calls["n"] += 1
        if calls["n"] == 1:
            return "not json"
        return json.dumps(GOOD)

    result = summarize.summarize_pending(conn, complete=flaky)
    assert result["summarized"] == 2 and len(result["errors"]) == 1


def test_pending_stops_after_missing_key(conn, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = summarize.summarize_pending(conn)
    assert result["summarized"] == 0 and len(result["errors"]) == 1


def test_unknown_session_raises(conn):
    with pytest.raises(SummarizeError):
        summarize.summarize_session(conn, "ghost", lambda p: "{}")
