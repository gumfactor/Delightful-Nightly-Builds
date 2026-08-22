import json
import re

from src.render import render_dashboard

MALICIOUS_TITLE = "</script><script>alert(1)</script>"


def make_items(title=MALICIOUS_TITLE):
    return [
        {
            "id": "manual-1",
            "source": "Manual",
            "title": title,
            "project_label": "Kwyeter",
            "category": "license",
            "expiration": "2026-09-01",
            "days_remaining": 10,
            "urgency": "Due This Month",
            "detail": "annual",
        },
        {
            "id": "domain-rdap-1",
            "source": "Domain",
            "title": "thecanadalist.ca",
            "project_label": "The Canada List",
            "category": "registration",
            "expiration": None,
            "days_remaining": None,
            "urgency": "Unknown",
            "detail": "not yet synced",
        },
    ]


def test_render_produces_full_html_document():
    html = render_dashboard(make_items(title="Business License"), "All clear.", False, {}, "2026-08-22 08:00 UTC")
    assert html.startswith("<!doctype html>")
    assert "</html>" in html
    assert "Renewal Radar" in html


def test_script_injection_payload_never_appears_as_raw_closing_tag():
    html = render_dashboard(make_items(), "All clear.", False, {}, "2026-08-22 08:00 UTC")
    # The literal "</script><script>" sequence must never appear verbatim —
    # it must always be escaped ("<\/script>") inside the JSON payload.
    assert "</script><script>alert(1)</script>" not in html
    assert "<\\/script><script>alert(1)<\\/script>" in html


def test_payload_is_valid_json_round_trip():
    html = render_dashboard(make_items(), "All clear.", False, {}, "2026-08-22 08:00 UTC")
    match = re.search(
        r'<script type="application/json" id="data-payload">(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    raw_json = match.group(1)
    # The escaped "<\/" sequences must parse back to the exact original title
    # once read via textContent/JSON.parse, exactly like the browser does.
    parsed = json.loads(raw_json)
    assert parsed["items"][0]["title"] == MALICIOUS_TITLE


def test_dom_construction_uses_textcontent_not_innerhtml():
    html = render_dashboard(make_items(title="Business License"), "All clear.", False, {}, "2026-08-22 08:00 UTC")
    assert "innerHTML" not in html


def test_briefing_text_included_verbatim_in_payload():
    html = render_dashboard(
        make_items(title="Business License"), "3 items need attention this week.", True, {}, "2026-08-22 08:00 UTC"
    )
    assert "3 items need attention this week." in html
    assert '"usedAi": true' in html


def test_domain_history_included_for_chart():
    history = {"example.com": [{"date": "2026-08-01", "ssl_days_remaining": 120}]}
    html = render_dashboard([], "Nothing to report.", False, history, "2026-08-22 08:00 UTC")
    assert "example.com" in html
    assert "120" in html
