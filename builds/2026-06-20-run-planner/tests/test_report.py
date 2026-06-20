"""Tests for report.py — HTML report generation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import report


def _sample_runs():
    return [
        {
            "date": "2026-06-15",
            "distance_km": 8.5,
            "duration_seconds": 3030,
            "effort": "moderate",
            "notes": "felt good",
            "pace": "5:55",
        },
        {
            "date": "2026-06-18",
            "distance_km": 5.0,
            "duration_seconds": 1500,
            "effort": "easy",
            "notes": "",
            "pace": "5:00",
        },
    ]


def _sample_windows():
    return [
        {
            "time": "2026-06-20T08:00",
            "apparent_temp_c": 12.0,
            "wind_speed_kmh": 8.0,
            "precip_probability": 5.0,
            "score": 94.0,
            "label": "Excellent",
        }
    ]


def _sample_summary():
    return {
        "run_count": 2,
        "total_km": 13.5,
        "total_seconds": 4530,
        "avg_pace": "5:35",
        "week_runs": _sample_runs(),
    }


def _sample_weekly():
    return [{"year": 2026, "week": 25, "km": 13.5}]


# ---------------------------------------------------------------------------
# HTML report structure
# ---------------------------------------------------------------------------

def test_html_has_doctype():
    html = report.render_html([], [], [], {"run_count": 0, "total_km": 0, "avg_pace": "--:--"})
    assert html.strip().startswith("<!DOCTYPE html>")


def test_html_has_chartjs_script():
    html = report.render_html([], [], [], {"run_count": 0, "total_km": 0, "avg_pace": "--:--"})
    assert "chart.js@4.4.4" in html


def test_html_no_runs_shows_empty_message():
    html = report.render_html([], [], [], {"run_count": 0, "total_km": 0, "avg_pace": "--:--"})
    assert "No runs logged yet" in html


def test_html_with_runs_shows_run_distance():
    html = report.render_html(_sample_runs(), _sample_weekly(), [], _sample_summary())
    assert "8.5" in html


def test_html_with_runs_shows_pace():
    html = report.render_html(_sample_runs(), _sample_weekly(), [], _sample_summary())
    assert "5:55" in html


def test_html_shows_weekly_km_in_stats():
    html = report.render_html(_sample_runs(), _sample_weekly(), [], _sample_summary())
    assert "13.5" in html


def test_html_with_windows_shows_score():
    html = report.render_html([], [], _sample_windows(), {"run_count": 0, "total_km": 0, "avg_pace": "--:--"})
    assert "94.0" in html


def test_html_with_windows_shows_label():
    html = report.render_html([], [], _sample_windows(), {"run_count": 0, "total_km": 0, "avg_pace": "--:--"})
    assert "Excellent" in html


def test_html_escapes_xss_in_notes():
    xss_run = {
        "date": "2026-06-20",
        "distance_km": 5.0,
        "duration_seconds": 1500,
        "effort": "easy",
        "notes": "<script>alert('xss')</script>",
        "pace": "5:00",
    }
    html = report.render_html([xss_run], [], [], {"run_count": 1, "total_km": 5.0, "avg_pace": "5:00"})
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_html_no_forecast_shows_placeholder():
    html = report.render_html([], [], [], {"run_count": 0, "total_km": 0, "avg_pace": "--:--"})
    assert "No forecast data" in html


def test_esc_handles_ampersand():
    assert report._esc("a & b") == "a &amp; b"


def test_esc_handles_angle_brackets():
    result = report._esc("<b>bold</b>")
    assert "<b>" not in result
    assert "&lt;b&gt;" in result
