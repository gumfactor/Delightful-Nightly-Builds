import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import ai_polish  # noqa: E402
from parser import Lecture, Section  # noqa: E402


def make_lecture() -> Lecture:
    section = Section(heading="Intro", level=2, bullets=["  messy   bullet text  ", "another point"])
    return Lecture(
        path="fake.md", title="Fake", objectives=["obj"], sections=[section], heading_skip_warning=False
    )


class _CountingUrlopen:
    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        raise AssertionError("urlopen should never be called without an API key")


def test_no_api_key_uses_deterministic_fallback_and_makes_zero_calls(monkeypatch):
    counter = _CountingUrlopen()
    monkeypatch.setattr(ai_polish, "urlopen", counter)

    result = ai_polish.polish_lecture(make_lecture(), api_key=None)

    assert counter.calls == 0
    assert result.used_ai is False
    assert result.discussion_questions == []
    assert result.sections["Intro"] == ["Messy bullet text", "Another point"]


def test_deterministic_fallback_cleans_whitespace_and_capitalizes():
    lecture = make_lecture()
    result = ai_polish._deterministic_fallback(lecture)
    assert result.sections["Intro"][0] == "Messy bullet text"


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_mocked_ai_response_used_when_valid(monkeypatch):
    fake_reply = {
        "content": [
            {
                "text": json.dumps(
                    {
                        "sections": {"Intro": ["Polished bullet one", "Polished bullet two"]},
                        "discussion_questions": ["Why does this matter?"],
                    }
                )
            }
        ]
    }
    calls = []

    def fake_urlopen(request, timeout=30):
        calls.append(request)
        return _FakeResponse(json.dumps(fake_reply).encode("utf-8"))

    monkeypatch.setattr(ai_polish, "urlopen", fake_urlopen)

    result = ai_polish.polish_lecture(make_lecture(), api_key="fake-key")

    assert len(calls) == 1
    assert result.used_ai is True
    assert result.sections["Intro"] == ["Polished bullet one", "Polished bullet two"]
    assert result.discussion_questions == ["Why does this matter?"]


def test_ai_call_raising_falls_back_gracefully(monkeypatch):
    def raising_urlopen(request, timeout=30):
        raise ConnectionError("network unreachable")

    monkeypatch.setattr(ai_polish, "urlopen", raising_urlopen)

    result = ai_polish.polish_lecture(make_lecture(), api_key="fake-key")

    assert result.used_ai is False
    assert result.sections["Intro"] == ["Messy bullet text", "Another point"]


def test_malformed_ai_response_falls_back_gracefully(monkeypatch):
    def bad_urlopen(request, timeout=30):
        return _FakeResponse(b"not json at all")

    monkeypatch.setattr(ai_polish, "urlopen", bad_urlopen)

    result = ai_polish.polish_lecture(make_lecture(), api_key="fake-key")

    assert result.used_ai is False


def test_ai_response_with_empty_sections_falls_back(monkeypatch):
    fake_reply = {"content": [{"text": json.dumps({"sections": {}, "discussion_questions": []})}]}

    def empty_urlopen(request, timeout=30):
        return _FakeResponse(json.dumps(fake_reply).encode("utf-8"))

    monkeypatch.setattr(ai_polish, "urlopen", empty_urlopen)

    result = ai_polish.polish_lecture(make_lecture(), api_key="fake-key")

    assert result.used_ai is False
    assert result.sections["Intro"] == ["Messy bullet text", "Another point"]


def test_prompt_never_includes_prose_only_structure():
    lecture = make_lecture()
    prompt = ai_polish._build_prompt(lecture)
    assert "Intro" in prompt
    assert "messy" in prompt.lower()
