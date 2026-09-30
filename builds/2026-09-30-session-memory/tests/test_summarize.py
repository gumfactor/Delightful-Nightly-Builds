import json

import pytest

from conftest import EXAMPLES
from sessionmemory import parsers, summarize
from sessionmemory.models import Message, Session


def session_from_example(name):
    return parsers.parse_claude_code(EXAMPLES / name)


def fake_reply(text):
    return lambda url, headers, body, timeout=90: {"content": [{"type": "text", "text": text}]}


def test_heuristic_finds_decisions_and_open_items():
    summary = summarize.heuristic_summary(session_from_example("claude_code_canada_list_encoding.jsonl"))
    assert any("normalise province names" in d for d in summary["decisions"])
    assert "Add a regression test for Québec and Nunavut" in summary["open_items"]
    assert summary["files"] == ["pipeline/load.py"]


def test_heuristic_open_questions_section():
    summary = summarize.heuristic_summary(session_from_example("claude_code_canada_list_dedupe.jsonl"))
    assert len(summary["open_items"]) == 2 and summary["left_off"].startswith("Postal code bucketing")


def test_heuristic_handles_user_only_session():
    session = Session("x:1", "chatgpt", "p", "t", messages=[Message("user", "hello")])
    summary = summarize.heuristic_summary(session)
    assert summary["left_off"] == "" and summary["decisions"] == []


def test_compact_transcript_keeps_start_and_end_of_long_sessions():
    messages = [Message("user" if i % 2 == 0 else "assistant", f"message-{i} " + "x" * 800) for i in range(200)]
    text = summarize.compact_transcript(Session("x:1", "chatgpt", "p", "t", messages=messages), budget=6000)
    assert "message-0 " in text and "message-199 " in text and "omitted" in text
    assert len(text) < 7000


def test_parse_ai_json_handles_fences_and_prose():
    assert summarize.parse_ai_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert summarize.parse_ai_json('Here you go: {"a": 2} thanks') == {"a": 2}


@pytest.mark.parametrize("bad", ["no json here", "{broken", "[1, 2]"])
def test_parse_ai_json_rejects_garbage(bad):
    with pytest.raises(summarize.SummaryError):
        summarize.parse_ai_json(bad)


def test_ai_summary_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(summarize.SummaryError, match="ANTHROPIC_API_KEY"):
        summarize.ai_summary(session_from_example("claude_code_stress_book_ch4.jsonl"))


def test_ai_summary_merges_model_output_with_exact_fields():
    reply = json.dumps({"title": "Encoding fix", "summary": "Fixed cp1252 bug.", "decisions": ["Use NFC"], "open_items": ["Test Québec", ""]})
    result = summarize.ai_summary(session_from_example("claude_code_canada_list_encoding.jsonl"),
                                  api_key="test-key", post=fake_reply(reply))
    assert result["title"] == "Encoding fix" and result["decisions"] == ["Use NFC"]
    assert result["open_items"] == ["Test Québec"]
    assert result["files"] == ["pipeline/load.py"]  # comes from the transcript, not the model


def test_call_claude_sends_key_model_and_prompt():
    seen = {}

    def post(url, headers, body, timeout=90):
        seen.update(url=url, headers=headers, body=body)
        return {"content": [{"type": "text", "text": "ok"}]}

    assert summarize.call_claude("sys", "usr", api_key="k123", post=post) == "ok"
    assert seen["headers"]["x-api-key"] == "k123" and seen["url"].startswith("https://api.anthropic.com/")
    assert seen["body"]["messages"][0]["content"] == "usr"


def test_empty_api_reply_is_an_error():
    with pytest.raises(summarize.SummaryError, match="empty"):
        summarize.call_claude("s", "u", api_key="k", post=lambda *a, **k: {"content": []})
