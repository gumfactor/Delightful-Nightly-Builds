"""Tests for renderer.py — HTML dashboard output."""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from renderer import render_html, _safe_json


GENERATED_AT = datetime(2024, 6, 28, 12, 0, 0, tzinfo=timezone.utc)


def _sample_global_stats():
    return {
        "total_runs": 42,
        "total_failures": 7,
        "repos_with_ci": 5,
        "total_ci_minutes": 320.5,
        "overall_failure_rate": 0.167,
        "slowest_workflow": "myrepo/CI",
        "most_failed_workflow": "myrepo/Deploy",
    }


def _sample_workflow_stats():
    return [
        {
            "repo": "user/repo-a",
            "workflow_name": "CI",
            "total_runs": 20,
            "success_count": 18,
            "failure_count": 2,
            "failure_rate": 0.1,
            "avg_duration_s": 180.0,
            "p95_duration_s": 240.0,
            "durations": [180.0] * 20,
        },
        {
            "repo": "user/repo-b",
            "workflow_name": "Deploy",
            "total_runs": 22,
            "success_count": 17,
            "failure_count": 5,
            "failure_rate": 0.227,
            "avg_duration_s": 90.0,
            "p95_duration_s": 120.0,
            "durations": [90.0] * 22,
        },
    ]


def _sample_trend():
    return [
        {"week": "2024-W25", "run_count": 10, "avg_duration_s": 150.0, "failure_count": 1, "failure_rate": 0.1},
        {"week": "2024-W26", "run_count": 15, "avg_duration_s": 200.0, "failure_count": 3, "failure_rate": 0.2},
    ]


def test_html_starts_with_doctype():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert html.strip().startswith("<!DOCTYPE html>")


def test_chart_js_cdn_present():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert "chart.js@4.4.4" in html


def test_stat_cards_present():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert "42" in html  # total_runs
    assert "320" in html  # ci minutes


def test_workflow_names_appear_in_table():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert "repo-a" in html
    assert "repo-b" in html


def test_xss_escaping_in_workflow_name():
    stats = _sample_workflow_stats()
    stats[0]["workflow_name"] = "<script>alert(1)</script>"
    stats[0]["repo"] = "user/safe-repo"
    html = render_html(_sample_global_stats(), stats, _sample_trend(), "", GENERATED_AT)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_ai_insights_rendered_when_provided():
    html = render_html(
        _sample_global_stats(), _sample_workflow_stats(), _sample_trend(),
        "• Workflow X is slow\n• Workflow Y fails often", GENERATED_AT
    )
    assert "AI Insights" in html
    assert "Workflow X is slow" in html


def test_ai_insights_fallback_when_empty():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert "ANTHROPIC_API_KEY" in html


def test_empty_state_message_when_no_workflows():
    html = render_html(_sample_global_stats(), [], [], "", GENERATED_AT)
    assert "No completed workflow runs" in html


def test_trend_labels_in_chart_data():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert "2024-W25" in html
    assert "2024-W26" in html


def test_safe_json_escapes_angle_brackets():
    result = _safe_json(["<script>", "normal"])
    assert "<script>" not in result
    assert "\\u003c" in result or r"<" in result or "<" not in result


def test_mobile_responsive_viewport_meta():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert 'name="viewport"' in html


def test_sortable_table_script_present():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert "sortTable" in html


def test_generated_date_in_output():
    html = render_html(_sample_global_stats(), _sample_workflow_stats(), _sample_trend(), "", GENERATED_AT)
    assert "2024-06-28" in html


def test_failure_rate_badge_colors():
    stats = _sample_workflow_stats()
    stats[0]["failure_rate"] = 0.3   # > 20% → red
    stats[1]["failure_rate"] = 0.0   # 0% → green
    html = render_html(_sample_global_stats(), stats, _sample_trend(), "", GENERATED_AT)
    assert "badge-red" in html
    assert "badge-green" in html
