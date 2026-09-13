"""Tests for report.py — Markdown/HTML rendering, escaping, and slugify safety."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone

from ai_writer import DigestDraft
from arxiv_client import Paper
from outline_builder import DigestOutline
from report import render_html, render_markdown, safe_json_for_script, slugify
from trend_engine import TrendBucket, TrendResult


def _outline(topic: str = "empathy training", paper_title: str = "A Study of Empathy Training") -> DigestOutline:
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
        title=paper_title,
        authors=["A. Author"],
        abstract="N = 40",
        published=date(2026, 9, 1),
        categories=["q-bio.NC"],
        pdf_url="http://arxiv.org/pdf/2609.00001v1",
    )
    return DigestOutline(
        topic=topic,
        window_months=6,
        total_papers=6,
        trend=trend,
        rising_keywords=["empathy", "training"],
        top_papers=[paper],
        notable_facts=[],
        hook_stat="Papers grew.",
        generated_at=datetime(2026, 9, 13, tzinfo=timezone.utc).isoformat(),
    )


def _draft() -> DigestDraft:
    return DigestDraft(
        intro="Intro text.",
        trend_section="Trend text.",
        facts_section="Facts text.",
        takeaway="Takeaway text.",
        source="template",
    )


def test_slugify_basic_lowercases_and_hyphenates():
    assert slugify("Empathy Training & AI") == "empathy-training-ai"


def test_slugify_rejects_path_traversal_characters():
    slug = slugify("../../etc/passwd")
    assert "/" not in slug
    assert ".." not in slug
    assert re.fullmatch(r"[a-z0-9-]+", slug)


def test_slugify_symbols_only_falls_back_to_topic():
    assert slugify("!!!???") == "topic"


def test_slugify_truncates_to_max_length():
    long_text = "x" * 200
    slug = slugify(long_text, max_length=20)
    assert len(slug) <= 20


def test_safe_json_for_script_neutralizes_script_close_tag():
    payload = {"evil": "</script><script>alert(1)</script>"}
    encoded = safe_json_for_script(payload)
    assert "</script>" not in encoded
    assert json.loads(encoded.replace("<\\/", "</")) == payload  # round-trips back


def test_render_html_escapes_hostile_topic_and_title():
    hostile = '<script>window.__xss=true;</script>'
    outline = _outline(topic=hostile, paper_title=hostile)
    html_out = render_html(outline, _draft())
    # The raw, executable tag must never appear ...
    assert "<script>window.__xss=true;</script>" not in html_out
    # ... it must appear only in its harmless, escaped form.
    assert "&lt;script&gt;window.__xss=true;&lt;/script&gt;" in html_out


def test_render_html_embeds_valid_chart_data_matching_buckets():
    outline = _outline()
    html_out = render_html(outline, _draft())
    match = re.search(
        r'<script type="application/json" id="chart-data">(.*?)</script>', html_out, re.S
    )
    assert match is not None
    data = json.loads(match.group(1))
    assert data["labels"] == ["2026-08", "2026-09"]
    assert data["counts"] == [2, 4]


def test_render_html_pins_chart_js_version():
    html_out = render_html(_outline(), _draft())
    assert "Chart.js/4.4.4/chart.umd.min.js" in html_out


def test_render_markdown_contains_expected_sections():
    md = render_markdown(_outline(), _draft())
    assert "## Trend" in md
    assert "## Notable figures" in md
    assert "## Takeaway" in md
    assert "## Sources" in md
    assert "A Study of Empathy Training" in md
    assert "Intro text." in md


def test_render_markdown_includes_source_link():
    md = render_markdown(_outline(), _draft())
    assert "http://arxiv.org/pdf/2609.00001v1" in md
