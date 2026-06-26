"""
Tests for renderer.py — verifies the HTML output contains expected structure and data.
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analyzer import compute_stats
from src.renderer import render_dashboard, _CHART_JS_CDN


def _render(stats: dict | None = None, insights: str = "Test insights text.") -> str:
    """Render to a temp file and return the HTML string."""
    if stats is None:
        stats = compute_stats([], username="testuser", months=6)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        path = f.name
    render_dashboard(stats, insights, path)
    html = Path(path).read_text(encoding="utf-8")
    os.unlink(path)
    return html


def test_renderer_contains_username():
    stats = compute_stats([], username="octocat", months=12)
    html = _render(stats)
    assert "octocat" in html


def test_renderer_contains_chart_js():
    html = _render()
    assert _CHART_JS_CDN in html


def test_renderer_contains_all_canvas_ids():
    html = _render()
    assert 'id="chart-hourly"' in html
    assert 'id="chart-dow"' in html
    assert 'id="chart-weekly"' in html
    assert 'id="chart-repos"' in html


def test_renderer_contains_ai_insights():
    insights = "You are a night-owl developer."
    html = _render(insights=insights)
    assert insights in html


def test_renderer_output_is_valid_html_structure():
    html = _render()
    assert html.startswith("<!DOCTYPE html>")
    assert "<html" in html
    assert "<head>" in html
    assert "<body>" in html
    assert "</html>" in html


def test_renderer_total_commits_appears_in_output():
    from tests.test_analyzer import make_commit
    commits = [
        make_commit("2026-01-05T14:00:00Z"),
        make_commit("2026-01-06T14:00:00Z"),
        make_commit("2026-01-07T14:00:00Z"),
    ]
    stats = compute_stats(commits, username="alice", months=12)
    html = _render(stats)
    assert "3" in html  # total commits


def test_renderer_dark_mode_background():
    html = _render()
    assert "--bg: #0d1117" in html


def test_renderer_chart_js_data_embedded():
    from tests.test_analyzer import make_commit
    commits = [make_commit("2026-01-05T14:00:00Z", repo="owner/my-project")] * 5
    stats = compute_stats(commits, username="testuser", months=6)
    html = _render(stats)
    # Verify chart data labels are embedded
    assert '"12am"' in html  # first hourly label
    assert '"Mon"' in html   # day-of-week label
