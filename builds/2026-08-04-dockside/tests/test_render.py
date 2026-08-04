from datetime import date

import render


class FakeRow(dict):
    """A dict that also supports the sqlite3.Row-style ['key'] access render.py expects."""


def make_site_row(name="Cottage Dock", place_name="Muskoka, Ontario", marine_available=1):
    return FakeRow(name=name, place_name=place_name, marine_available=marine_available)


def make_task_row(name, category="dock"):
    return FakeRow(name=name, category=category)


def test_render_dashboard_includes_site_name():
    site = make_site_row()
    html_out = render.render_dashboard(site, [], [], [], None, None, "2026-08-04T08:00:00Z")
    assert "Cottage Dock" in html_out
    assert "Muskoka, Ontario" in html_out


def test_render_dashboard_escapes_script_injection_in_task_name():
    site = make_site_row()
    malicious_task = make_task_row('<script>alert(1)</script>')
    task_cards = [{
        "task_row": malicious_task, "status": "ready_now",
        "best_day": date(2026, 8, 16), "constraints_for_best": {"wind": "pass"},
    }]
    html_out = render.render_dashboard(site, task_cards, [], [], None, None, "2026-08-04T08:00:00Z")
    assert "<script>alert(1)</script>" not in html_out
    assert "&lt;script&gt;" in html_out


def test_render_dashboard_escapes_script_injection_in_site_name():
    site = make_site_row(name='<img src=x onerror=alert(1)>')
    html_out = render.render_dashboard(site, [], [], [], None, None, "2026-08-04T08:00:00Z")
    assert "<img src=x onerror=alert(1)>" not in html_out


def test_render_dashboard_shows_empty_state_when_no_tasks():
    site = make_site_row()
    html_out = render.render_dashboard(site, [], [], [], None, None, "2026-08-04T08:00:00Z")
    assert "No active tasks configured" in html_out


def test_render_dashboard_shows_marine_unavailable_note():
    site = make_site_row(marine_available=0)
    html_out = render.render_dashboard(site, [], [], [], None, None, "2026-08-04T08:00:00Z")
    assert "Marine data unavailable" in html_out


def test_render_dashboard_shows_briefing_when_present():
    site = make_site_row()
    html_out = render.render_dashboard(site, [], [], [], "All good this week.", "ai", "2026-08-04T08:00:00Z")
    assert "All good this week." in html_out
    assert "AI-generated" in html_out


def test_render_dashboard_prompts_to_run_brief_when_absent():
    site = make_site_row()
    html_out = render.render_dashboard(site, [], [], [], None, None, "2026-08-04T08:00:00Z")
    assert "dockside brief" in html_out


def test_safe_json_for_script_escapes_closing_script_tag():
    payload = render._safe_json_for_script(["</script><script>alert(1)</script>"])
    assert "</script>" not in payload


def test_render_dashboard_includes_chart_data_for_observations():
    site = make_site_row()
    observations = [{"obs_date": "2026-08-15", "temp_max_c": 25.0, "temp_min_c": 15.0,
                      "precip_mm": 0.0, "wind_speed_max_kmh": 10.0}]
    boating = [{"obs_date": "2026-08-15", "score": 88.5}]
    html_out = render.render_dashboard(site, [], observations, boating, None, None, "2026-08-04T08:00:00Z")
    assert "2026-08-15" in html_out
    assert "88.5" in html_out


def test_task_card_hides_not_applicable_constraints():
    row = make_task_row("Install Dock")
    card = render._task_card_html(row, "ready_now", date(2026, 8, 16), {"wind": "pass", "water_temp": "n/a"})
    assert "Max wind" in card
    assert "Water temp" not in card
