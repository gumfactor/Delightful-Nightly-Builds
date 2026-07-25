import urllib.error

import pytest

from src.ai_classify import (
    AIClassificationError,
    ai_coaching_summary,
    build_prompt,
    classify_batch,
    parse_ai_response,
)


def _anthropic_response(items):
    text = "[" + ",".join(
        '{"sha": "%s", "category": "%s", "explanation": "%s"}' % (i["sha"], i["category"], i["explanation"])
        for i in items
    ) + "]"
    return {"content": [{"text": text}]}


def test_build_prompt_includes_all_commits_and_taxonomy():
    items = [{"sha": "abc123", "message": "fix crash", "diff_excerpt": "- bug\n+ fix"}]
    prompt = build_prompt(items)
    assert "abc123" in prompt
    assert "fix crash" in prompt
    assert "null_none_handling" in prompt  # taxonomy member present


def test_parse_ai_response_success():
    response = _anthropic_response(
        [{"sha": "abc", "category": "type_mismatch", "explanation": "compared str to int"}]
    )
    result = parse_ai_response(response)
    assert result["abc"]["category"] == "type_mismatch"


def test_parse_ai_response_rejects_unknown_category():
    response = _anthropic_response([{"sha": "abc", "category": "not_a_real_category", "explanation": "x"}])
    with pytest.raises(AIClassificationError):
        parse_ai_response(response)


def test_parse_ai_response_rejects_malformed_shape():
    with pytest.raises(AIClassificationError):
        parse_ai_response({"content": [{"text": "not json at all"}]})


def test_classify_batch_no_api_key_uses_keyword_fallback():
    items = [{"sha": "abc", "message": "fix TypeError comparing values", "diff_excerpt": "", "changed_files": []}]
    result = classify_batch(api_key=None, items=items)
    assert result["abc"]["source"] == "keyword"
    assert result["abc"]["category"] == "type_mismatch"


def test_classify_batch_empty_items_returns_empty():
    assert classify_batch(api_key="fake-key", items=[]) == {}


def test_classify_batch_success_uses_ai_source():
    items = [{"sha": "abc", "message": "fix it", "diff_excerpt": "", "changed_files": []}]

    def fake_request(api_key, prompt):
        return _anthropic_response([{"sha": "abc", "category": "logic_operator_error", "explanation": "inverted condition"}])

    result = classify_batch(api_key="fake-key", items=items, request_fn=fake_request)
    assert result["abc"]["source"] == "ai"
    assert result["abc"]["category"] == "logic_operator_error"


def test_classify_batch_falls_back_on_network_error():
    items = [{"sha": "abc", "message": "fix TypeError here", "diff_excerpt": "", "changed_files": []}]

    def failing_request(api_key, prompt):
        raise urllib.error.URLError("connection refused")

    result = classify_batch(api_key="fake-key", items=items, request_fn=failing_request)
    assert result["abc"]["source"] == "keyword"
    assert result["abc"]["category"] == "type_mismatch"


def test_classify_batch_falls_back_on_malformed_response():
    items = [{"sha": "abc", "message": "fix TypeError here", "diff_excerpt": "", "changed_files": []}]

    def bad_request(api_key, prompt):
        return {"content": [{"text": "nonsense response with no brackets"}]}

    result = classify_batch(api_key="fake-key", items=items, request_fn=bad_request)
    assert result["abc"]["source"] == "keyword"


def test_classify_batch_partial_ai_response_falls_back_per_item():
    items = [
        {"sha": "abc", "message": "fix TypeError here", "diff_excerpt": "", "changed_files": []},
        {"sha": "def", "message": "fix typo in docs", "diff_excerpt": "", "changed_files": []},
    ]

    def partial_request(api_key, prompt):
        # AI only returns a classification for "abc", not "def"
        return _anthropic_response([{"sha": "abc", "category": "type_mismatch", "explanation": "x"}])

    result = classify_batch(api_key="fake-key", items=items, request_fn=partial_request)
    assert result["abc"]["source"] == "ai"
    assert result["def"]["source"] == "keyword"
    assert result["def"]["category"] == "typo_naming"


def test_ai_coaching_summary_no_key_returns_none():
    assert ai_coaching_summary(None, [{"category": "type_mismatch", "count": 3}]) is None


def test_ai_coaching_summary_no_counts_returns_none():
    assert ai_coaching_summary("fake-key", []) is None


def test_ai_coaching_summary_success():
    def fake_request(api_key, prompt):
        return {"content": [{"text": "You tend to miss type checks. Add mypy to your workflow."}]}

    summary = ai_coaching_summary("fake-key", [{"category": "type_mismatch", "count": 3}], request_fn=fake_request)
    assert "type checks" in summary


def test_ai_coaching_summary_failure_returns_none():
    def failing_request(api_key, prompt):
        raise urllib.error.URLError("no network")

    summary = ai_coaching_summary("fake-key", [{"category": "type_mismatch", "count": 3}], request_fn=failing_request)
    assert summary is None
