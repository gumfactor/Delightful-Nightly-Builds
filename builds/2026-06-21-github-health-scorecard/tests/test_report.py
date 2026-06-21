import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from report import CHART_JS_CDN, render_html


def _make_repo(name: str = "test-repo", score: int = 75, css: str = "good") -> dict:
    return {
        "name": name,
        "full_name": f"user/{name}",
        "language": "Python",
        "description": "A test repository",
        "private": False,
        "archived": False,
        "open_issues": 3,
        "pushed_at": "2026-06-19T10:00:00Z",
        "days_since_push": 2,
        "ci_status": "passing",
        "health_score": score,
        "health_label": "Good",
        "health_css": css,
    }


def test_html_starts_with_doctype():
    html = render_html([], "2026-06-21 12:00 UTC")
    assert html.strip().startswith("<!DOCTYPE html>")


def test_html_includes_chart_js_cdn():
    html = render_html([], "2026-06-21 12:00 UTC")
    assert CHART_JS_CDN in html
    assert "chart.js@4.4.4" in html


def test_html_includes_repo_name():
    repos = [_make_repo("my-awesome-project")]
    html = render_html(repos, "2026-06-21 12:00 UTC")
    assert "my-awesome-project" in html


def test_html_includes_health_score():
    repos = [_make_repo(score=73)]
    html = render_html(repos, "2026-06-21 12:00 UTC")
    assert '"health_score": 73' in html


def test_html_has_dark_mode_css():
    html = render_html([], "2026-06-21 12:00 UTC")
    assert "--bg:" in html
    assert "#0d1117" in html


def test_html_total_count_in_header():
    repos = [_make_repo("r1"), _make_repo("r2"), _make_repo("r3")]
    html = render_html(repos, "2026-06-21 12:00 UTC")
    assert "3 repositories analyzed" in html


def test_html_repo_data_json_embedded():
    repos = [_make_repo("embedded-check")]
    html = render_html(repos, "2026-06-21 12:00 UTC")
    assert '"name": "embedded-check"' in html


def test_html_xss_safe_description():
    """Angle brackets in repo descriptions must be unicode-escaped in embedded JSON."""
    repo = _make_repo("safe-repo")
    repo["description"] = "<script>alert('xss')</script>"
    html = render_html([repo], "2026-06-21 12:00 UTC")
    # Raw angle brackets must not appear verbatim in the HTML output
    assert "<script>alert('xss')</script>" not in html
    # Instead they should appear as unicode escapes in the JSON block
    assert "\\u003cscript" in html


def test_html_ai_panel_present_when_insights_given():
    html = render_html([], "2026-06-21 12:00 UTC", ai_insights="• Repo X needs attention.")
    assert "AI Briefing" in html
    assert "Repo X needs attention." in html


def test_html_ai_panel_absent_when_no_insights():
    html = render_html([], "2026-06-21 12:00 UTC", ai_insights="")
    assert "AI Briefing" not in html


def test_html_ai_panel_escapes_content():
    insights = "• <b>Bold</b> & 'quotes'"
    html = render_html([], "2026-06-21 12:00 UTC", ai_insights=insights)
    assert "<b>Bold</b>" not in html
    assert "&lt;b&gt;" in html


def test_html_stats_count_healthy():
    repos = [
        _make_repo(css="healthy"),
        _make_repo(css="healthy"),
        _make_repo(css="stale"),
    ]
    html = render_html(repos, "2026-06-21 12:00 UTC")
    # Stats grid should have a count of 2 for healthy
    assert ">2<" in html  # count in stat-card


def test_html_sortable_columns_present():
    html = render_html([], "2026-06-21 12:00 UTC")
    assert "sortBy('name')" in html
    assert "sortBy('health_score')" in html
    assert "sortBy('days_since_push')" in html
