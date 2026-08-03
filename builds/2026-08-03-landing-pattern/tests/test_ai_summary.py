"""Tests for the optional AI note generator. Every test mocks the HTTP call —
none of these ever reach the real Anthropic API.
"""

from __future__ import annotations

import io
import json
import urllib.error

from landing_pattern import ai_summary


def make_pr(label="ci_failing"):
    return {"number": 1, "title": "Fix the thing", "label": label, "age_days": 3, "files": ["a.py"]}


def test_deterministic_fallback_when_no_api_key():
    note = ai_summary.summarize_blocked_pr(make_pr(), api_key=None)
    assert note == ai_summary.deterministic_note("ci_failing")


def test_deterministic_fallback_makes_no_network_call(monkeypatch):
    called = {"count": 0}

    def should_not_be_called(*args, **kwargs):
        called["count"] += 1
        raise AssertionError("should never be called without an API key")

    ai_summary.summarize_blocked_pr(make_pr(), api_key=None, http_post=should_not_be_called)
    assert called["count"] == 0


def test_deterministic_note_unknown_label_falls_back():
    note = ai_summary.deterministic_note("some_label_that_does_not_exist")
    assert note == ai_summary._DETERMINISTIC_TEMPLATES["unknown"]


def test_every_readiness_label_has_a_distinct_template():
    templates = ai_summary._DETERMINISTIC_TEMPLATES
    assert len(set(templates.values())) == len(templates)


def test_mocked_successful_api_call_returns_claude_text():
    response_body = json.dumps(
        {"content": [{"type": "text", "text": "Rebase onto main and re-run CI."}]}
    ).encode("utf-8")

    class FakeResponse:
        def read(self):
            return response_body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    note = ai_summary.summarize_blocked_pr(
        make_pr(), api_key="fake-key", http_post=lambda request: FakeResponse()
    )
    assert note == "Rebase onto main and re-run CI."


def test_mocked_api_failure_falls_back_to_template():
    def failing_post(request):
        raise urllib.error.URLError("connection refused")

    note = ai_summary.summarize_blocked_pr(
        make_pr(label="conflict"), api_key="fake-key", http_post=failing_post
    )
    assert note == ai_summary.deterministic_note("conflict")


def test_mocked_malformed_response_falls_back_to_template():
    class FakeResponse:
        def read(self):
            return b"not valid json"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    note = ai_summary.summarize_blocked_pr(
        make_pr(label="awaiting_review"), api_key="fake-key", http_post=lambda request: FakeResponse()
    )
    assert note == ai_summary.deterministic_note("awaiting_review")
