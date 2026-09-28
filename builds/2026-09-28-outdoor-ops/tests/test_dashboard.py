from src import dashboard

SAMPLE_DAY = {
    "forecast_date": "2026-09-28", "temp_max": 17.0, "temp_min": 10.0,
    "precip_prob_max": 10.0, "wind_max": 10.0, "aqi_max": 40.0,
    "weathercode": 1, "running_score": 85.0, "golf_score": 78.0,
}

SAMPLE_SUMMARY = {
    "best_running_day": "2026-09-28", "best_running_score": 85.0,
    "best_golf_day": "2026-09-28", "best_golf_score": 78.0,
}


def test_render_dashboard_escapes_hostile_location_name():
    hostile = "</script><script>alert(1)</script>"
    html_out = dashboard.render_dashboard(
        location_name=hostile, days=[SAMPLE_DAY], summary=SAMPLE_SUMMARY,
        coach_note="Looks good.", sync_count=1, last_sync_time="2026-09-28T08:00:00",
    )
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_out


def test_render_dashboard_includes_pinned_chartjs_version():
    html_out = dashboard.render_dashboard(
        location_name="Toronto, ON", days=[SAMPLE_DAY], summary=SAMPLE_SUMMARY,
        coach_note="Looks good.", sync_count=1, last_sync_time="2026-09-28T08:00:00",
    )
    assert "chart.js@4.4.4" in html_out


def test_render_dashboard_handles_empty_days_without_crashing():
    html_out = dashboard.render_dashboard(
        location_name="Toronto, ON", days=[], summary={},
        coach_note="No data yet.", sync_count=0, last_sync_time=None,
    )
    assert "Toronto, ON" in html_out
    assert "No data yet." in html_out
    assert "never" in html_out


def test_render_dashboard_includes_score_table_row_for_each_day():
    days = [SAMPLE_DAY, {**SAMPLE_DAY, "forecast_date": "2026-09-29"}]
    html_out = dashboard.render_dashboard(
        location_name="Toronto, ON", days=days, summary=SAMPLE_SUMMARY,
        coach_note="Looks good.", sync_count=1, last_sync_time="2026-09-28T08:00:00",
    )
    assert html_out.count('data-testid="score-table"') == 1
    assert html_out.count("2026-09-28") >= 1
    assert html_out.count("2026-09-29") >= 1


def test_render_dashboard_escapes_hostile_forecast_date_in_chart_json():
    hostile_day = {**SAMPLE_DAY, "forecast_date": "2026-09-28</script><script>window.__xss=1</script>"}
    html_out = dashboard.render_dashboard(
        location_name="Toronto, ON", days=[hostile_day], summary=SAMPLE_SUMMARY,
        coach_note="Looks good.", sync_count=1, last_sync_time="2026-09-28T08:00:00",
    )
    assert "</script><script>window.__xss" not in html_out
    assert "<\\/script><script>window.__xss" in html_out


def test_render_dashboard_includes_chartjs_fallback_guard():
    html_out = dashboard.render_dashboard(
        location_name="Toronto, ON", days=[SAMPLE_DAY], summary=SAMPLE_SUMMARY,
        coach_note="Looks good.", sync_count=1, last_sync_time="2026-09-28T08:00:00",
    )
    assert "typeof Chart === 'undefined'" in html_out
    assert "chart-fallback" in html_out


def test_render_dashboard_escapes_hostile_coach_note():
    hostile_note = "<img src=x onerror=alert(2)>"
    html_out = dashboard.render_dashboard(
        location_name="Toronto, ON", days=[SAMPLE_DAY], summary=SAMPLE_SUMMARY,
        coach_note=hostile_note, sync_count=1, last_sync_time="2026-09-28T08:00:00",
    )
    assert "<img src=x onerror=alert(2)>" not in html_out
