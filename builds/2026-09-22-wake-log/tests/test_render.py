import json
import re

from src.openmeteo import WindowAggregate
from src.render import render_html
from src.store import Entry


def make_entry(**overrides) -> Entry:
    defaults = dict(
        id=1,
        created_at="2026-10-04T12:00:00+00:00",
        location_name="Stony Lake",
        latitude=44.5,
        longitude=-78.2,
        target_date="2026-10-05",
        window_label="afternoon",
        score=78.5,
        beaufort=3,
        beaufort_name="Gentle Breeze",
        wind_knots=9.5,
        gust_knots=12.0,
        temp_c=21.0,
        precip_probability=10.0,
        cloud_cover=30.0,
        narrative="A fine afternoon on the water.",
        ai_polished=False,
    )
    defaults.update(overrides)
    return Entry(**defaults)


def make_window(**overrides) -> WindowAggregate:
    defaults = dict(
        date="2026-10-06",
        window="morning",
        wind_knots=8.0,
        gust_knots=10.0,
        temp_c=19.0,
        precip_probability=15.0,
        cloud_cover=40.0,
        daylight_hours=6.0,
        beaufort_number=3,
        beaufort_name="Gentle Breeze",
        score=72.0,
    )
    defaults.update(overrides)
    return WindowAggregate(**defaults)


def test_render_produces_valid_looking_html_document():
    html = render_html([make_entry()], [make_window()], "Stony Lake")
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "<title>Wake Log</title>" in html
    assert html.strip().endswith("</html>")


def test_render_handles_empty_entries_and_windows():
    html = render_html([], [], "Stony Lake")
    assert "<!DOCTYPE html>" in html
    data_match = re.search(r'<script type="application/json" id="wake-log-data">(.*?)</script>', html, re.S)
    assert data_match is not None
    payload = json.loads(data_match.group(1).replace("<\\/", "</"))
    assert payload["entries"] == []
    assert payload["upcoming"] == []


def test_render_embeds_entry_data_as_escaped_json_not_live_html():
    payload = "</script><script>alert(1)</script>"
    html = render_html([make_entry(location_name=payload, narrative=payload)], [], "Stony Lake")

    # The raw, unescaped payload must never appear as a live tag in the document.
    assert "<script>alert(1)</script>" not in html

    # It must still be present, but only inside the neutralized JSON block.
    assert "<\\/script><script>alert(1)<\\/script>" in html


def test_render_never_uses_innerHTML():
    html = render_html([make_entry()], [make_window()], "Stony Lake")
    assert "innerHTML" not in html


def test_render_uses_createElement_and_textContent_for_dynamic_content():
    html = render_html([make_entry()], [make_window()], "Stony Lake")
    assert "createElement" in html
    assert "textContent" in html


def test_render_includes_pinned_chartjs_version():
    html = render_html([make_entry()], [make_window()], "Stony Lake")
    assert "chart.js@4.4.4" in html


def test_render_json_payload_round_trips_all_entry_fields():
    entry = make_entry(narrative="round trip check")
    html = render_html([entry], [], "Stony Lake")
    data_match = re.search(r'<script type="application/json" id="wake-log-data">(.*?)</script>', html, re.S)
    payload = json.loads(data_match.group(1).replace("<\\/", "</"))
    assert payload["entries"][0]["narrative"] == "round trip check"
    assert payload["entries"][0]["id"] == 1


def test_render_to_file_writes_readable_html(tmp_path):
    from src.render import render_to_file

    output_path = tmp_path / "journal.html"
    render_to_file([make_entry()], [make_window()], "Stony Lake", str(output_path))
    content = output_path.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
