import pytest

from conftest import write_jsonl, user, assistant
from atlas.pricing import DEFAULT_PRICES
from atlas.store import Store
from atlas.summarize import SummarizeError, build_payload, summarize_missing, summarize_session


def sess(**over):
    base = {"source": "x", "project": "p", "first_prompt": "a", "last_prompt": "b", "last_assistant": "c",
            "files": {"f.py": 2}, "summary": ""}
    base.update(over)
    return base


def fake(text="Worked on parser. Stopped at tests."):
    calls = []

    def transport(payload, key):
        calls.append((payload, key))
        return {"content": [{"type": "text", "text": text}]}
    transport.calls = calls
    return transport


def test_payload_contains_session_material_and_cheap_model():
    payload = build_payload(sess())
    assert "f.py" in payload["messages"][0]["content"] and "haiku" in payload["model"]


def test_summarize_session_returns_text_and_sends_key():
    t = fake()
    assert summarize_session(sess(), "k", t).startswith("Worked")
    assert t.calls[0][1] == "k"


@pytest.mark.parametrize("bad", [{}, {"content": []}, {"content": "str"}, {"content": [{"type": "text", "text": " "}]}])
def test_malformed_responses_raise(bad):
    with pytest.raises(SummarizeError):
        summarize_session(sess(), "k", lambda p, k: bad)


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SummarizeError):
        summarize_missing(None, [sess()], transport=fake())


def test_summaries_cached_and_not_repeated(tmp_path):
    write_jsonl(tmp_path / "l" / "a.jsonl", [user("2026-09-01T10:00:00Z", "go"),
                                             assistant("2026-09-01T10:00:05Z", [{"type": "text", "text": "ok"}])])
    store = Store(tmp_path / "t.db")
    store.index_directory(tmp_path / "l", DEFAULT_PRICES)
    t = fake()
    assert summarize_missing(store, store.sessions(), transport=t, api_key="k") == {"summarized": 1, "failed": 0}
    assert summarize_missing(store, store.sessions(), transport=t, api_key="k") == {"summarized": 0, "failed": 0}
    assert len(t.calls) == 1 and store.sessions()[0]["summary"].startswith("Worked")
    store.close()


def test_failures_are_counted_not_fatal_and_limit_respected():
    def boom(payload, key):
        raise SummarizeError("down")
    sessions = [sess(source=str(i)) for i in range(5)]
    assert summarize_missing(None, sessions, limit=3, transport=boom, api_key="k") == {"summarized": 0, "failed": 3}
