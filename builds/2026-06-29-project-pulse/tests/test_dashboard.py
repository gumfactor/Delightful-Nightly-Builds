import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dashboard import (
    _e,
    _safe_json,
    _staleness_badge,
    compute_staleness_days,
    render_dashboard,
)

PROJECTS = [
    {
        "id": 1,
        "name": "Canada <List>",  # intentionally contains HTML special chars
        "slug": "canada-list",
        "description": "Canadian directory & more",
        "type": "business",
        "github_repos": ["owner/canada-list"],
        "color": "#4a9eff",
        "status": "active",
    },
    {
        "id": 2,
        "name": "Neuroscience Lab",
        "slug": "neuroscience-lab",
        "description": "Research lab",
        "type": "lab",
        "github_repos": [],
        "color": "#3fb950",
        "status": "active",
    },
]

ACTIVITY = [
    {
        "project_id": 1,
        "project_name": "Canada <List>",
        "project_slug": "canada-list",
        "project_color": "#4a9eff",
        "source": "github",
        "event_type": "commit",
        "title": "Fix ingestion bug",
        "occurred_at": "2026-06-28T10:00:00Z",
    }
]


def _render(
    projects=None,
    activity=None,
    proj_acts=None,
    last_act=None,
    generated_at="2026-06-29 11:00 UTC",
):
    projects = projects if projects is not None else PROJECTS
    activity = activity if activity is not None else ACTIVITY
    proj_acts = proj_acts if proj_acts is not None else {
        "canada-list": [ACTIVITY[0]],
        "neuroscience-lab": [],
    }
    last_act = last_act if last_act is not None else {
        1: "2026-06-28T10:00:00Z",
        2: None,
    }
    return render_dashboard(
        projects=projects,
        all_activity=activity,
        project_activities=proj_acts,
        last_activity_map=last_act,
        generated_at=generated_at,
    )


def test_dashboard_has_doctype():
    assert _render().startswith("<!DOCTYPE html>")


def test_dashboard_has_html_lang():
    assert 'lang="en"' in _render()


def test_dashboard_includes_chartjs_cdn():
    assert "chart.js@4.4.4" in _render()


def test_dashboard_includes_project_name():
    assert "Neuroscience Lab" in _render()


def test_dashboard_xss_project_name():
    html = _render()
    # Raw angle brackets from "Canada <List>" must not appear unescaped
    assert "Canada <List>" not in html
    assert "&lt;List&gt;" in html


def test_dashboard_xss_safe_json():
    result = _safe_json({"key": "<script>alert(1)</script>"})
    assert "<script>" not in result
    assert "\\u003c" in result


def test_dashboard_mobile_viewport_meta():
    assert 'name="viewport"' in _render()


def test_dashboard_generated_at_shown():
    html = _render(generated_at="2026-06-29 11:00 UTC")
    assert "2026-06-29 11:00 UTC" in html


def test_dashboard_empty_projects_shows_empty_state():
    html = render_dashboard(
        projects=[],
        all_activity=[],
        project_activities={},
        last_activity_map={},
        generated_at="2026-06-29",
    )
    assert "empty-state" in html or "No active projects" in html


def test_staleness_days_recent():
    days = compute_staleness_days("2026-06-29T10:00:00+00:00")
    assert days is not None
    assert days <= 1


def test_staleness_days_old():
    days = compute_staleness_days("2026-04-01T00:00:00+00:00")
    assert days is not None
    assert days > 14


def test_staleness_days_none_input():
    assert compute_staleness_days(None) is None


def test_staleness_days_bad_input():
    assert compute_staleness_days("not-a-date") is None


def test_staleness_badge_green():
    _, css = _staleness_badge(1)
    assert css == "badge-green"


def test_staleness_badge_yellow():
    _, css = _staleness_badge(5)
    assert css == "badge-yellow"


def test_staleness_badge_orange():
    _, css = _staleness_badge(10)
    assert css == "badge-orange"


def test_staleness_badge_red():
    _, css = _staleness_badge(30)
    assert css == "badge-red"


def test_staleness_badge_grey_when_none():
    label, css = _staleness_badge(None)
    assert css == "badge-grey"
    assert "No activity" in label


def test_html_escape_helper_angle_brackets():
    assert _e("<script>") == "&lt;script&gt;"


def test_html_escape_helper_quotes():
    assert _e('"value"') == "&quot;value&quot;"


def test_dashboard_shows_repo_tags():
    html = _render()
    assert "owner/canada-list" in html


def test_dashboard_filter_buttons_present():
    html = _render()
    assert "filterType" in html
    assert "lab" in html
