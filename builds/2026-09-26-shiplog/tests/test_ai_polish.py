from classify import Commit
from ai_polish import polish_sections


def _commit(subject="add widget", scope=None):
    return Commit(
        sha="abc1234", subject=subject, body="", author_date="2026-09-01",
        type="feat", scope=scope, breaking=False, pr_number=None, source="keyword",
    )


def test_no_api_key_makes_zero_calls_and_uses_deterministic_fallback():
    calls = []

    def spy_call_fn(api_key, prompt):
        calls.append((api_key, prompt))
        return "should not be reached"

    sections = {"Features": [_commit("add widget")]}
    result = polish_sections(sections, api_key=None, call_fn=spy_call_fn)

    assert calls == []
    assert "add widget" in result["Features"]


def test_deterministic_fallback_includes_scope():
    sections = {"Features": [_commit("add widget", scope="ui")]}
    result = polish_sections(sections, api_key=None)
    assert "**ui**" in result["Features"]


def test_successful_ai_call_used_verbatim():
    def fake_call_fn(api_key, prompt):
        assert api_key == "sk-test"
        return "The UI gained a new widget this release."

    sections = {"Features": [_commit("add widget")]}
    result = polish_sections(sections, api_key="sk-test", call_fn=fake_call_fn)

    assert result["Features"] == "The UI gained a new widget this release."


def test_ai_call_failure_falls_back_to_deterministic_bullets():
    def failing_call_fn(api_key, prompt):
        raise TimeoutError("simulated network timeout")

    sections = {"Features": [_commit("add widget")]}
    result = polish_sections(sections, api_key="sk-test", call_fn=failing_call_fn)

    assert "add widget" in result["Features"]


def test_prompt_never_contains_diff_or_file_content_markers():
    captured = {}

    def capturing_call_fn(api_key, prompt):
        captured["prompt"] = prompt
        return "ok"

    sections = {"Features": [_commit("add widget")]}
    polish_sections(sections, api_key="sk-test", call_fn=capturing_call_fn)

    assert "diff --git" not in captured["prompt"]
    assert "@@" not in captured["prompt"]
