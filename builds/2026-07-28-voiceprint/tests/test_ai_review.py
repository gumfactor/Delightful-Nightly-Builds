import json

from src import ai_review


def _fake_success_request_fn(expected_count):
    def _request_fn(url, data, headers):
        assert url == ai_review.ANTHROPIC_API_URL
        assert headers["x-api-key"] == "fake-key"
        payload = json.loads(data)
        assert len(payload["messages"]) == 1
        items = [
            {"diagnosis": f"diagnosis {i}", "rewrite": f"rewrite {i}"}
            for i in range(expected_count)
        ]
        body = {"content": [{"type": "text", "text": json.dumps(items)}]}
        return json.dumps(body).encode("utf-8")

    return _request_fn


def _raising_request_fn(url, data, headers):
    raise OSError("network unreachable")


def _malformed_request_fn(url, data, headers):
    return b"not valid json at all"


def test_call_claude_for_review_success_path_parses_items():
    paragraphs = ["First paragraph text.", "Second paragraph text."]
    result = ai_review.call_claude_for_review(
        paragraphs, "fake-key", request_fn=_fake_success_request_fn(2)
    )
    assert result["source"] == "ai"
    assert len(result["items"]) == 2
    assert result["items"][0]["diagnosis"] == "diagnosis 0"
    assert result["items"][0]["rewrite"] == "rewrite 0"


def test_call_claude_for_review_returns_none_on_network_error():
    result = ai_review.call_claude_for_review(
        ["A paragraph."], "fake-key", request_fn=_raising_request_fn
    )
    assert result is None


def test_call_claude_for_review_returns_none_on_malformed_response():
    result = ai_review.call_claude_for_review(
        ["A paragraph."], "fake-key", request_fn=_malformed_request_fn
    )
    assert result is None


def test_call_claude_for_review_returns_none_for_empty_paragraphs():
    result = ai_review.call_claude_for_review([], "fake-key", request_fn=_fake_success_request_fn(0))
    assert result is None


def test_get_review_uses_fallback_when_no_api_key_and_makes_no_network_call():
    calls = []

    def _tracking_request_fn(url, data, headers):
        calls.append(url)
        raise AssertionError("should never be called without an api key")

    result = ai_review.get_review(
        ["We should delve into this topic."],
        breakdown={"ai_tell_phrases": 5.0},
        api_key=None,
        request_fn=_tracking_request_fn,
    )
    assert result["source"] == "fallback"
    assert calls == []
    assert "delve into" in result["items"][0]["diagnosis"]


def test_get_review_falls_back_when_api_call_fails():
    result = ai_review.get_review(
        ["Some paragraph."],
        breakdown={"ai_tell_phrases": 0.0},
        api_key="fake-key",
        request_fn=_raising_request_fn,
    )
    assert result["source"] == "fallback"


def test_get_review_prefers_ai_result_when_available():
    result = ai_review.get_review(
        ["First paragraph text."],
        breakdown={},
        api_key="fake-key",
        request_fn=_fake_success_request_fn(1),
    )
    assert result["source"] == "ai"


def test_deterministic_fallback_names_dominant_issue_when_no_local_phrases():
    items = ai_review.deterministic_fallback(
        ["A perfectly plain paragraph with no issues here."],
        breakdown={"low_burstiness": 8.0, "ai_tell_phrases": 0.0},
    )
    assert "low burstiness" in items[0]["diagnosis"]
    assert items[0]["rewrite"] is None


def test_pick_worst_paragraphs_ranks_by_ai_tell_density():
    paragraphs = [
        "This is a completely clean paragraph about the weather today.",
        "We must delve into and leverage this seamless, robust synergy.",
    ]
    worst = ai_review.pick_worst_paragraphs(paragraphs, limit=1)
    assert worst == [paragraphs[1]]


def test_pick_worst_paragraphs_handles_empty_input():
    assert ai_review.pick_worst_paragraphs([]) == []
