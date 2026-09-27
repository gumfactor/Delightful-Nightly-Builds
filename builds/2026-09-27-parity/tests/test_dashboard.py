import json

from dashboard import build_payload, render_dashboard
from store import SyncRun


def make_run(run_id=1, run_at="2026-09-27T08:00:00+00:00", matched=1, conflict=0, tw_only=0, coda_only=0):
    return SyncRun(run_id, run_at, matched, conflict, tw_only, coda_only)


def test_build_payload_uses_latest_run_for_hero_stats():
    runs = [
        make_run(1, matched=2, conflict=1, tw_only=0, coda_only=0),
        make_run(2, matched=5, conflict=2, tw_only=1, coda_only=3),
    ]
    payload = build_payload(runs, items=[])
    assert payload["hero"] == {
        "matched_ok": 5,
        "status_conflict": 2,
        "teamwork_only": 1,
        "coda_only": 3,
    }


def test_build_payload_with_no_runs_has_zeroed_hero():
    payload = build_payload([], items=[])
    assert payload["hero"] == {
        "matched_ok": 0,
        "status_conflict": 0,
        "teamwork_only": 0,
        "coda_only": 0,
    }
    assert payload["trend"] == []


def test_build_payload_trend_includes_every_run_gap_size():
    runs = [make_run(1, conflict=1, tw_only=1), make_run(2, conflict=0, tw_only=0, coda_only=2)]
    payload = build_payload(runs, items=[])
    assert [t["gap_size"] for t in payload["trend"]] == [2, 2]


def test_render_dashboard_produces_valid_html_shell():
    html = render_dashboard([make_run()], items=[])
    assert html.startswith("<!doctype html>")
    assert "</html>" in html
    assert "parity-data" in html


def test_render_dashboard_escapes_script_injection_payload():
    malicious_title = "</script><script>alert(1)</script>"
    items = [
        {
            "bucket": "teamwork_only",
            "teamwork_title": malicious_title,
            "teamwork_url": "https://example.com",
            "coda_title": None,
            "coda_url": None,
            "detail": None,
        }
    ]
    html = render_dashboard([make_run()], items)

    # The raw payload must never contain a literal, parseable "</script>" sequence
    # that would let the payload text prematurely close the surrounding <script> tag.
    assert "</script><script>alert(1)</script>" not in html

    # The JSON payload is still valid JSON (the browser's JSON.parse decodes the
    # standard "\/" escape back to "/" automatically) and round-trips the exact
    # malicious string as inert data, never executable markup.
    payload_block = html.split('id="parity-data">', 1)[1].split("</script>", 1)[0]
    parsed = json.loads(payload_block)
    assert parsed["items"][0]["teamwork_title"] == malicious_title


def test_render_dashboard_only_innerhtml_usage_is_a_static_clear():
    html = render_dashboard([make_run()], items=[{
        "bucket": "coda_only", "teamwork_title": None, "teamwork_url": None,
        "coda_title": "x", "coda_url": "https://example.com", "detail": None,
    }])
    # The only innerHTML usage anywhere in the page must be a hardcoded empty-string
    # clear, never an assignment built from item/payload data (which would be an XSS vector).
    occurrences = [line.strip() for line in html.splitlines() if "innerHTML" in line]
    assert occurrences == ['container.innerHTML = "";']
