import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.enrich import (
    default_description,
    detect_language,
    enrich_snippet,
    expand_query,
    extract_tags,
)


def test_detect_language_known_extension():
    assert detect_language("script.py") == "python"
    assert detect_language("app.jsx") == "javascript"


def test_detect_language_unknown_extension_returns_text():
    assert detect_language("notes.xyz") == "text"


def test_detect_language_no_filename_returns_text():
    assert detect_language(None) == "text"


def test_extract_tags_filters_stopwords_and_ranks_by_frequency():
    code = "def dedup(items):\n    seen = set()\n    return [i for i in items if i not in seen]"
    tags = extract_tags(code, "python")
    assert "python" in tags
    assert "the" not in tags
    assert "return" not in tags
    assert "items" in tags


def test_default_description_prefers_comment():
    code = "# dedupe a list preserving order\ndef dedup(items):\n    pass"
    assert default_description(code, "python") == "dedupe a list preserving order"


def test_default_description_falls_back_to_first_line():
    code = "def dedup(items):\n    pass"
    assert default_description(code, "python") == "def dedup(items):"


def test_default_description_empty_code_returns_empty_string():
    assert default_description("   \n  ", "python") == ""


def test_enrich_snippet_no_api_key_makes_zero_network_calls(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    calls = []
    monkeypatch.setattr("src.enrich.urllib.request.urlopen", lambda *a, **k: calls.append(1))

    description, tags = enrich_snippet("def f(): pass", "python", "My func")

    assert calls == []
    assert description  # deterministic fallback still produces something
    assert "python" in tags


def test_enrich_snippet_success_path_uses_ai_result(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(
                {"content": [{"text": json.dumps({"description": "AI description", "tags": ["ai", "tag"]})}]}
            ).encode("utf-8")

    monkeypatch.setattr("src.enrich.urllib.request.urlopen", lambda *a, **k: FakeResponse())

    description, tags = enrich_snippet("def f(): pass", "python", "My func")

    assert description == "AI description"
    assert tags == ["ai", "tag"]


def test_enrich_snippet_falls_back_on_network_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    def raise_error(*a, **k):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("src.enrich.urllib.request.urlopen", raise_error)

    description, tags = enrich_snippet("def f(): pass", "python", "My func")

    assert description == default_description("def f(): pass", "python")
    assert tags == extract_tags("def f(): pass", "python")


def test_enrich_snippet_falls_back_on_malformed_json(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"content": [{"text": "not valid json {{"}]}).encode("utf-8")

    monkeypatch.setattr("src.enrich.urllib.request.urlopen", lambda *a, **k: FakeResponse())

    description, tags = enrich_snippet("def f(): pass", "python", "My func")

    assert description == default_description("def f(): pass", "python")


def test_expand_query_no_api_key_splits_on_whitespace(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    calls = []
    monkeypatch.setattr("src.enrich.urllib.request.urlopen", lambda *a, **k: calls.append(1))

    keywords = expand_query("dedupe a list")

    assert calls == []
    assert keywords == ["dedupe", "a", "list"]


def test_expand_query_success_path_uses_ai_keywords(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"content": [{"text": json.dumps(["dedup", "unique", "list"])}]}).encode("utf-8")

    monkeypatch.setattr("src.enrich.urllib.request.urlopen", lambda *a, **k: FakeResponse())

    keywords = expand_query("remove duplicates but keep order")

    assert keywords == ["dedup", "unique", "list"]


def test_expand_query_falls_back_on_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(
        "src.enrich.urllib.request.urlopen",
        lambda *a, **k: (_ for _ in ()).throw(urllib.error.URLError("timeout")),
    )

    keywords = expand_query("remove duplicates")

    assert keywords == ["remove", "duplicates"]
