import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import dashboard  # noqa: E402


def _sample_trip(trip_id=1, name="Cottage Weekend"):
    return {
        "id": trip_id,
        "name": name,
        "resolved_name": "Muskoka, Ontario, Canada",
        "start_date": "2026-08-10",
        "end_date": "2026-08-12",
        "activity_tags": ["cottage", "boating"],
        "mode": "forecast",
        "briefing": "Pack for warm, calm conditions.",
        "daily": [
            {"day_date": "2026-08-10", "temp_max_c": 24.0, "temp_min_c": 15.0, "precip_mm": 0.0, "wind_max_kmh": 10.0, "weathercode": 1}
        ],
        "packing_list": {"Clothing": ["Swimsuit"], "Gear": ["Life jacket"], "Documents & Admin": [], "Health & Comfort": []},
    }


def test_dashboard_escapes_script_injection_in_trip_name():
    malicious_trip = _sample_trip(name="<script>alert('xss')</script>")
    html_output = dashboard.generate_dashboard_html([malicious_trip])

    assert "<script>alert('xss')</script>" not in html_output
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_output


def test_dashboard_renders_one_card_per_trip_with_mode_badge():
    trips = [_sample_trip(trip_id=1, name="Cottage Weekend"), _sample_trip(trip_id=2, name="Golf Trip")]
    trips[1]["mode"] = "climate_normal"

    html_output = dashboard.generate_dashboard_html(trips)

    assert html_output.count('data-testid="trip-card"') == 2
    assert "Cottage Weekend" in html_output
    assert "Golf Trip" in html_output
    assert "Live forecast" in html_output
    assert "Historical average (not a live forecast)" in html_output


def test_dashboard_shows_empty_state_with_no_trips():
    html_output = dashboard.generate_dashboard_html([])
    assert 'data-testid="empty-state"' in html_output
    assert "No trips yet" in html_output


def test_dashboard_includes_pinned_chartjs_cdn_version():
    html_output = dashboard.generate_dashboard_html([_sample_trip()])
    assert "chart.js@4.4.4" in html_output


def test_dashboard_packing_items_are_escaped():
    trip = _sample_trip()
    trip["packing_list"]["Gear"] = ["<img src=x onerror=alert(1)>"]
    html_output = dashboard.generate_dashboard_html([trip])
    assert "<img src=x onerror=alert(1)>" not in html_output
