import json

from src.ai import build_briefing


def _drift_entries():
    return [
        {"ecosystem": "python", "dependency": "requests", "severity": "major",
         "repo_versions": {"a": "1.0.0", "b": "2.0.0"}, "min_version": "1.0.0", "max_version": "2.0.0"},
        {"ecosystem": "npm", "dependency": "react", "severity": "minor",
         "repo_versions": {"a": "18.0.0", "b": "18.2.0"}, "min_version": "18.0.0", "max_version": "18.2.0"},
    ]


def _repo_summary():
    return {"user/a": {"total": 5, "behind_count": 2, "major_count": 1}}


def test_no_api_key_returns_deterministic_fallback_and_makes_no_network_call():
    calls = []

    def transport(url, headers, method="GET", data=None):
        calls.append(url)
        return 200, b"{}"

    result = build_briefing(_drift_entries(), _repo_summary(), api_key=None, transport=transport)
    assert calls == []
    assert "requests" in result
    assert "2 dependencies" in result or "requests (major)" in result


def test_deterministic_fallback_handles_no_drift():
    result = build_briefing([], {}, api_key=None)
    assert "No cross-repo dependency drift" in result


def test_prompt_sent_contains_only_aggregate_names_never_raw_content():
    captured = {}

    def transport(url, headers, method="GET", data=None):
        captured["body"] = json.loads(data.decode("utf-8"))
        response = {"content": [{"text": "Fix requests first."}]}
        return 200, json.dumps(response).encode("utf-8")

    result = build_briefing(_drift_entries(), _repo_summary(), api_key="fake-key", transport=transport)
    assert result == "Fix requests first."
    prompt_text = captured["body"]["messages"][0]["content"]
    assert "requests" in prompt_text
    assert "1.0.0" not in prompt_text  # exact per-repo pinned versions never sent, only names/severity


def test_exactly_one_call_made_when_key_present():
    call_count = {"n": 0}

    def transport(url, headers, method="GET", data=None):
        call_count["n"] += 1
        return 200, json.dumps({"content": [{"text": "ok"}]}).encode("utf-8")

    build_briefing(_drift_entries(), _repo_summary(), api_key="fake-key", transport=transport)
    assert call_count["n"] == 1


def test_falls_back_on_non_200_response():
    def transport(url, headers, method="GET", data=None):
        return 500, b"Internal Server Error"

    result = build_briefing(_drift_entries(), _repo_summary(), api_key="fake-key", transport=transport)
    assert "requests" in result


def test_falls_back_on_malformed_response_body():
    def transport(url, headers, method="GET", data=None):
        return 200, b"not json"

    result = build_briefing(_drift_entries(), _repo_summary(), api_key="fake-key", transport=transport)
    assert "requests" in result


def test_falls_back_on_transport_exception():
    def transport(url, headers, method="GET", data=None):
        raise ConnectionError("boom")

    result = build_briefing(_drift_entries(), _repo_summary(), api_key="fake-key", transport=transport)
    assert "requests" in result


def test_falls_back_when_response_missing_content_key():
    def transport(url, headers, method="GET", data=None):
        return 200, json.dumps({"unexpected": "shape"}).encode("utf-8")

    result = build_briefing(_drift_entries(), _repo_summary(), api_key="fake-key", transport=transport)
    assert "requests" in result
