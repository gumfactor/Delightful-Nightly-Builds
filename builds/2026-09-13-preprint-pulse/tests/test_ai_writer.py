"""Tests for ai_writer.py — template fallback, AI path, and fact-containment."""

from __future__ import annotations

import json
import urllib.error
from datetime import date, datetime, timezone

import pytest

from arxiv_client import Paper
from fact_extractor import Fact
from outline_builder import DigestOutline
from trend_engine import TrendBucket, TrendResult
from ai_writer import build_request_body, draft_sections, template_draft


def _outline() -> DigestOutline:
    trend = TrendResult(
        buckets=[TrendBucket("2026-08", 2), TrendBucket("2026-09", 4)],
        slope=2.0,
        direction="rising",
        first_half_count=2,
        second_half_count=4,
        pct_change=100.0,
    )
    paper = Paper(
        arxiv_id="2609.00001v1",
        title="A Study of Empathy Training",
        authors=["A. Author"],
        abstract="N = 40, p = 0.02.",
        published=date(2026, 9, 1),
        categories=["q-bio.NC"],
        pdf_url="http://arxiv.org/pdf/2609.00001v1",
    )
    fact = Fact(
        arxiv_id="2609.00001v1",
        paper_title="A Study of Empathy Training",
        fact_type="sample_size",
        raw_text="N = 40",
        context="...N = 40 participants...",
    )
    return DigestOutline(
        topic="empathy training",
        window_months=6,
        total_papers=6,
        trend=trend,
        rising_keywords=["empathy", "training"],
        top_papers=[paper],
        notable_facts=[fact],
        hook_stat='Papers on "empathy training" grew +100%.',
        generated_at=datetime(2026, 9, 13, tzinfo=timezone.utc).isoformat(),
    )


class FakeAnthropicResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _valid_sections_payload() -> dict:
    sections = {
        "intro": "AI-written intro.",
        "trend_section": "AI-written trend section.",
        "facts_section": "AI-written facts section.",
        "takeaway": "AI-written takeaway.",
    }
    return {"content": [{"type": "text", "text": json.dumps(sections)}]}


def test_no_api_key_never_calls_network_and_uses_template():
    calls = {"count": 0}

    def raising_urlopen(request, timeout=30):
        calls["count"] += 1
        raise AssertionError("urlopen must not be called without an API key")

    draft = draft_sections(_outline(), api_key=None, urlopen=raising_urlopen)
    assert draft.source == "template"
    assert calls["count"] == 0


def test_template_draft_is_complete_and_non_empty():
    draft = template_draft(_outline())
    assert draft.source == "template"
    for section in (draft.intro, draft.trend_section, draft.facts_section, draft.takeaway):
        assert isinstance(section, str) and section.strip()


def test_template_draft_handles_no_rising_keywords_and_no_facts():
    outline = _outline()
    outline.rising_keywords = []
    outline.notable_facts = []
    outline.top_papers = []
    draft = template_draft(outline)
    assert "no clearly rising keywords" in draft.trend_section.lower() or "none" in draft.trend_section.lower()
    assert draft.takeaway  # still produces something, doesn't crash


def test_ai_draft_used_on_valid_response():
    def fake_urlopen(request, timeout=30):
        return FakeAnthropicResponse(_valid_sections_payload())

    draft = draft_sections(_outline(), api_key="fake-key", urlopen=fake_urlopen)
    assert draft.source == "ai"
    assert draft.intro == "AI-written intro."
    assert draft.takeaway == "AI-written takeaway."


def test_ai_draft_falls_back_on_network_error():
    def failing_urlopen(request, timeout=30):
        raise urllib.error.URLError("connection refused")

    draft = draft_sections(_outline(), api_key="fake-key", urlopen=failing_urlopen)
    assert draft.source == "template"


def test_ai_draft_falls_back_on_unparsable_content():
    def fake_urlopen(request, timeout=30):
        return FakeAnthropicResponse({"content": [{"type": "text", "text": "not json at all"}]})

    draft = draft_sections(_outline(), api_key="fake-key", urlopen=fake_urlopen)
    assert draft.source == "template"


def test_ai_draft_falls_back_on_missing_required_key():
    incomplete = {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"intro": "x", "trend_section": "y", "facts_section": "z"}),
            }
        ]
    }

    def fake_urlopen(request, timeout=30):
        return FakeAnthropicResponse(incomplete)

    draft = draft_sections(_outline(), api_key="fake-key", urlopen=fake_urlopen)
    assert draft.source == "template"


def test_ai_draft_falls_back_on_malformed_envelope():
    def fake_urlopen(request, timeout=30):
        return FakeAnthropicResponse({"unexpected": "shape"})

    draft = draft_sections(_outline(), api_key="fake-key", urlopen=fake_urlopen)
    assert draft.source == "template"


def test_request_body_contains_only_outline_derived_facts():
    outline = _outline()
    body = build_request_body(outline, model="claude-haiku-4-5")
    assert body["model"] == "claude-haiku-4-5"
    assert "ONLY the facts provided" in body["system"]
    user_content = body["messages"][0]["content"]
    payload = json.loads(user_content.split("Facts (JSON):\n", 1)[1])
    assert payload["topic"] == "empathy training"
    assert payload["rising_keywords"] == ["empathy", "training"]
    assert payload["notable_facts"][0]["text"] == "N = 40"
    assert payload["top_papers"][0]["title"] == "A Study of Empathy Training"
    # Nothing outside the outline's own fields is present.
    assert set(payload.keys()) == {
        "topic",
        "window_months",
        "total_papers",
        "hook_stat",
        "trend_direction",
        "first_half_count",
        "second_half_count",
        "pct_change",
        "rising_keywords",
        "top_papers",
        "notable_facts",
    }


def test_draft_sections_respects_anthropic_model_env_override(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=30):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeAnthropicResponse(_valid_sections_payload())

    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-custom")
    draft_sections(_outline(), api_key="fake-key", urlopen=fake_urlopen)
    assert captured["body"]["model"] == "claude-haiku-custom"
