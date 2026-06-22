"""Tests for report.py — HTML structure, XSS safety, and markdown output."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from report import render_html, render_markdown


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

EMPTY_GITHUB = {"recent_repos": [], "stale_repos": [], "open_prs": []}
EMPTY_PORTFOLIO = {"tickers": [], "total_up": 0, "total_flat": 0, "total_down": 0}
EMPTY_WEATHER = {"hours": [], "best_run": [], "best_golf": [], "best_boat": []}

FULL_PORTFOLIO = {
    "tickers": [
        {
            "ticker": "NVDA",
            "current": 900.0,
            "prev_close": 860.0,
            "change_pct": 4.65,
            "move": "up",
            "currency": "USD",
            "formatted_price": "$900.00",
            "formatted_change": "+4.65%",
        },
        {
            "ticker": "AAPL",
            "current": 180.0,
            "prev_close": 185.0,
            "change_pct": -2.70,
            "move": "down",
            "currency": "USD",
            "formatted_price": "$180.00",
            "formatted_change": "-2.70%",
        },
    ],
    "total_up": 1,
    "total_flat": 0,
    "total_down": 1,
    "top_gainers": [],
    "top_losers": [],
}

FULL_GITHUB = {
    "recent_repos": [
        {"name": "user/repo-a", "pushed_at": "2026-06-22T10:00:00Z", "open_issues": 3, "health": "active"},
    ],
    "stale_repos": [
        {"name": "user/old-repo", "pushed_at": "2026-06-01T08:00:00Z", "open_issues": 1},
    ],
    "open_prs": [
        {"repo": "user/repo-a", "number": 7, "title": "Add tests", "user": "alice", "updated_at": "2026-06-22T09:00:00Z"},
    ],
}

FULL_WEATHER = {
    "hours": [
        {
            "hour": 8,
            "time": "2026-06-22T08:00",
            "temp_c": 18.0,
            "wind_kph": 10.0,
            "precip_prob": 5.0,
            "scores": {"run": 90.0, "golf": 85.0, "boat": 70.0},
        },
        {
            "hour": 10,
            "time": "2026-06-22T10:00",
            "temp_c": 22.0,
            "wind_kph": 12.0,
            "precip_prob": 0.0,
            "scores": {"run": 95.0, "golf": 90.0, "boat": 80.0},
        },
    ],
    "best_run": [],
    "best_golf": [],
    "best_boat": [],
}


# ---------------------------------------------------------------------------
# render_html — structure
# ---------------------------------------------------------------------------

class TestRenderHtmlStructure:
    def test_starts_with_doctype(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert result.startswith("<!DOCTYPE html>")

    def test_includes_chart_js_cdn(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "chart.js@4.4.4" in result

    def test_includes_report_date(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "2026-06-22" in result

    def test_includes_github_section_heading(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "GitHub Activity" in result

    def test_includes_portfolio_section_heading(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "Portfolio Pulse" in result

    def test_includes_weather_section_heading(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "Weather Windows" in result


# ---------------------------------------------------------------------------
# render_html — AI section
# ---------------------------------------------------------------------------

class TestRenderHtmlAiSection:
    def test_ai_section_present_when_summary_provided(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "Focus on NVDA.")
        assert "Today's Priorities" in result
        assert "Focus on NVDA." in result

    def test_ai_section_absent_when_summary_empty(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "Today's Priorities" not in result


# ---------------------------------------------------------------------------
# render_html — XSS safety
# ---------------------------------------------------------------------------

class TestRenderHtmlXSS:
    def test_repo_name_xss_escaped(self):
        github = {
            "recent_repos": [
                {"name": "<script>alert(1)</script>", "pushed_at": "2026-06-22", "open_issues": 0, "health": "active"}
            ],
            "stale_repos": [],
            "open_prs": [],
        }
        result = render_html("2026-06-22", github, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "<script>alert(1)</script>" not in result
        assert "&lt;script&gt;" in result

    def test_pr_title_xss_escaped(self):
        github = {
            "recent_repos": [],
            "stale_repos": [],
            "open_prs": [
                {"repo": "u/r", "number": 1, "title": "<img src=x onerror=alert(1)>", "user": "x", "updated_at": "2026-06-22"},
            ],
        }
        result = render_html("2026-06-22", github, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "<img src=x" not in result

    def test_safe_json_in_chart_data_escapes_angle_brackets(self):
        portfolio = {
            **FULL_PORTFOLIO,
            "tickers": [
                {
                    "ticker": "</script><script>alert(1)",
                    "change_pct": 0.0,
                    "move": "flat",
                    "formatted_price": "$0.00",
                    "formatted_change": "0.00%",
                }
            ],
        }
        result = render_html("2026-06-22", EMPTY_GITHUB, portfolio, EMPTY_WEATHER, "")
        # The raw closing tag must not appear in the script context
        assert "</script><script>" not in result

    def test_ai_summary_xss_escaped(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER,
                             "<script>alert('xss')</script>")
        assert "<script>alert(" not in result


# ---------------------------------------------------------------------------
# render_html — data rendering
# ---------------------------------------------------------------------------

class TestRenderHtmlData:
    def test_shows_ticker_names(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, FULL_PORTFOLIO, EMPTY_WEATHER, "")
        assert "NVDA" in result
        assert "AAPL" in result

    def test_shows_no_portfolio_data_message_when_empty(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "No portfolio data" in result

    def test_shows_no_recent_activity_when_empty_repos(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "No recent repository activity" in result

    def test_shows_repo_name_in_github_section(self):
        result = render_html("2026-06-22", FULL_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "user/repo-a" in result

    def test_shows_open_pr_section_when_prs_exist(self):
        result = render_html("2026-06-22", FULL_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "Open Pull Requests" in result
        assert "Add tests" in result

    def test_weather_scores_appear_in_output(self):
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, FULL_WEATHER, "")
        assert "90.0" in result or "90" in result

    def test_github_error_message_displayed(self):
        github = {"error": "GITHUB_TOKEN not set", "recent_repos": [], "stale_repos": [], "open_prs": []}
        result = render_html("2026-06-22", github, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "GITHUB_TOKEN not set" in result

    def test_weather_error_message_displayed(self):
        weather = {"error": "connection refused", "hours": [], "best_run": [], "best_golf": [], "best_boat": []}
        result = render_html("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, weather, "")
        assert "connection refused" in result


# ---------------------------------------------------------------------------
# render_markdown
# ---------------------------------------------------------------------------

class TestRenderMarkdown:
    def test_includes_all_section_headings(self):
        md = render_markdown("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "## GitHub Activity" in md
        assert "## Portfolio Pulse" in md
        assert "## Weather Windows" in md

    def test_includes_ai_summary_when_provided(self):
        md = render_markdown("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "• Focus here")
        assert "Today's Priorities" in md
        assert "• Focus here" in md

    def test_no_ai_section_when_empty_summary(self):
        md = render_markdown("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "Today's Priorities" not in md

    def test_date_in_title(self):
        md = render_markdown("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "2026-06-22" in md

    def test_shows_portfolio_table_when_tickers_present(self):
        md = render_markdown("2026-06-22", EMPTY_GITHUB, FULL_PORTFOLIO, EMPTY_WEATHER, "")
        assert "NVDA" in md
        assert "|" in md  # table formatting

    def test_shows_no_portfolio_data_when_empty(self):
        md = render_markdown("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "No portfolio data available" in md

    def test_shows_github_error_when_present(self):
        github = {"error": "GITHUB_TOKEN not set", "recent_repos": [], "stale_repos": [], "open_prs": []}
        md = render_markdown("2026-06-22", github, EMPTY_PORTFOLIO, EMPTY_WEATHER, "")
        assert "GITHUB_TOKEN not set" in md

    def test_shows_weather_windows_when_data_present(self):
        weather = {
            **FULL_WEATHER,
            "best_run": [{"time": "2026-06-22T08:00", "temp_c": 18.0, "wind_kph": 10.0, "precip_prob": 5.0, "scores": {"run": 90.0, "golf": 85.0, "boat": 70.0}}],
        }
        md = render_markdown("2026-06-22", EMPTY_GITHUB, EMPTY_PORTFOLIO, weather, "")
        assert "🏃 Running" in md
