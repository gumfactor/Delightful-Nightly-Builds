import json

from src.ai_enrich import enrich_note


def _raising_transport(url, data, headers):
    raise AssertionError("transport should never be called")


def test_no_api_key_makes_zero_network_calls_and_returns_fallback():
    note = enrich_note(
        prompt_text="fix the bug",
        task_type="bug-fix",
        score=8,
        tools_used=["Bash", "Edit"],
        api_key=None,
        transport=_raising_transport,
    )
    assert "bug-fix" in note
    assert "8/10" in note


def test_fallback_reflects_low_score_language():
    note = enrich_note(
        prompt_text="try something",
        task_type="other",
        score=1,
        tools_used=[],
        api_key=None,
        transport=_raising_transport,
    )
    assert "stalled" in note or "errors" in note


def test_fallback_reflects_mid_score_language():
    note = enrich_note(
        prompt_text="try something",
        task_type="other",
        score=5,
        tools_used=[],
        api_key=None,
        transport=_raising_transport,
    )
    assert "mixed" in note


def test_successful_api_call_returns_model_text():
    def fake_transport(url, data, headers):
        assert "x-api-key" in headers
        return json.dumps({"content": [{"type": "text", "text": "It worked because it was specific."}]}).encode()

    note = enrich_note(
        prompt_text="fix the bug",
        task_type="bug-fix",
        score=8,
        tools_used=["Bash"],
        api_key="fake-key",
        transport=fake_transport,
    )
    assert note == "It worked because it was specific."


def test_api_error_falls_back_deterministically():
    def failing_transport(url, data, headers):
        raise ValueError("boom")

    note = enrich_note(
        prompt_text="fix the bug",
        task_type="bug-fix",
        score=8,
        tools_used=["Bash"],
        api_key="fake-key",
        transport=failing_transport,
    )
    assert "bug-fix" in note


def test_malformed_response_falls_back():
    def bad_transport(url, data, headers):
        return b"not json"

    note = enrich_note(
        prompt_text="fix the bug",
        task_type="bug-fix",
        score=8,
        tools_used=["Bash"],
        api_key="fake-key",
        transport=bad_transport,
    )
    assert "bug-fix" in note
