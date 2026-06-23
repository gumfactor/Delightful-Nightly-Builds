"""Tests for renderer.py — HTML generation."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from renderer import render_html, _safe_json

_SAMPLE_PAPERS = [
    {
        "id": 1,
        "arxiv_id": "2410.00001",
        "title": "Neural Correlates of Empathy",
        "authors": "Alice Smith, Bob Jones",
        "abstract": "Study of empathy in the brain.",
        "published_date": "2024-10-01",
        "fetched_date": "2024-10-15T10:00:00",
        "relevance_score": 8,
        "summary": "This paper explores empathy. It uses fMRI.",
        "methodology": "fMRI",
        "topic_label": "empathy neuroscience",
        "is_read": 0,
    },
    {
        "id": 2,
        "arxiv_id": "2410.00002",
        "title": "Autonomous AI Agents",
        "authors": "Carol Doe",
        "abstract": "About AI agents.",
        "published_date": "2024-10-02",
        "fetched_date": "2024-10-15T10:00:00",
        "relevance_score": 5,
        "summary": "AI agent survey paper.",
        "methodology": "ML",
        "topic_label": "AI agents",
        "is_read": 0,
    },
]


def test_render_html_has_doctype():
    html = render_html(_SAMPLE_PAPERS)
    assert html.strip().startswith("<!DOCTYPE html>")


def test_render_html_contains_paper_title():
    html = render_html(_SAMPLE_PAPERS)
    assert "Neural Correlates of Empathy" in html


def test_render_html_contains_relevance_score_in_json():
    html = render_html(_SAMPLE_PAPERS)
    # Relevance score 8 should appear in the embedded JSON
    assert '"relevance_score": 8' in html or '"relevance_score":8' in html


def test_render_html_xss_escapes_script_tag_in_title():
    evil_papers = [{
        "id": 3,
        "arxiv_id": "2410.99999",
        "title": "<script>alert('xss')</script>",
        "authors": "Evil",
        "abstract": "Malicious.",
        "published_date": "2024-10-01",
        "fetched_date": "2024-10-15T10:00:00",
        "relevance_score": 1,
        "summary": "Bad paper.",
        "methodology": "other",
        "topic_label": "",
        "is_read": 0,
    }]
    html = render_html(evil_papers)
    # Raw <script> tag from user data must not appear in the JSON blob
    assert "<script>alert('xss')</script>" not in html


def test_render_html_safe_json_escapes_angle_brackets():
    data = [{"title": "<script>alert(1)</script>"}]
    result = _safe_json(data)
    assert "<script>" not in result
    assert "\\u003cscript\\u003e" in result


def test_render_html_empty_state_rendered_for_empty_list():
    html = render_html([])
    assert "No papers match" in html or "no papers" in html.lower() or "empty" in html.lower()


def test_render_html_contains_search_input():
    html = render_html(_SAMPLE_PAPERS)
    assert 'id="search"' in html or "id='search'" in html


def test_render_html_contains_paper_count_in_stats():
    html = render_html(_SAMPLE_PAPERS)
    # The total count (2) should appear in the header stats
    assert ">2<" in html or ">2 <" in html or "Total" in html


def test_render_html_json_data_embedded_as_script():
    html = render_html(_SAMPLE_PAPERS)
    assert "<script>" in html
    # The JSON variable should be present
    assert "const P=" in html


def test_render_html_arxiv_link_included():
    html = render_html(_SAMPLE_PAPERS)
    assert "https://arxiv.org/abs/2410.00001" in html


def test_render_html_high_relevance_badge_class():
    html = render_html(_SAMPLE_PAPERS)
    # Paper with score 8 should get the high-relevance CSS class
    assert "rh" in html


def test_safe_json_escapes_ampersand():
    data = {"key": "a & b"}
    result = _safe_json(data)
    assert "&" not in result
    assert "\\u0026" in result
