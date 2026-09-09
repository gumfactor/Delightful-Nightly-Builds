import json

from src.dashboard import render_dashboard


def _base_context(**overrides):
    context = {
        "as_of": "2026-09-09",
        "tfsa": {
            "available_room": 100000.0,
            "is_overcontributed": False,
            "overcontribution_amount": 0.0,
            "estimated_monthly_penalty": 0.0,
            "year_snapshots": [{"year": 2025, "ending_balance": 93000.0}],
        },
        "rrsp": {
            "available_room": 89660.0,
            "is_overcontributed": False,
            "overcontribution_amount": 0.0,
            "estimated_monthly_penalty": 0.0,
            "year_snapshots": [{"year": 2025, "ending_balance": 70760.0}],
        },
        "deadlines": [
            {"label": "RRSP contribution deadline (tax year 2026)", "date": "2027-03-01", "days_until": 173},
            {"label": "Next TFSA room opens", "date": "2027-01-01", "days_until": 114},
        ],
        "briefing": "TFSA has $100,000.00 of room available.",
        "history": [{"account": "TFSA contribution", "date": "2020-06-01", "amount": 6000.0}],
    }
    context.update(overrides)
    return context


def test_render_produces_full_html_document():
    html = render_dashboard(_base_context())
    assert html.startswith("<!doctype html>")
    assert "</html>" in html
    assert "Headroom" in html


def test_render_embeds_data_as_parseable_json():
    context = _base_context()
    html = render_dashboard(context)
    start = html.index('<script id="headroom-data" type="application/json">') + len(
        '<script id="headroom-data" type="application/json">'
    )
    end = html.index("</script>", start)
    embedded = json.loads(html[start:end])
    assert embedded["tfsa"]["available_room"] == 100000.0
    assert embedded["briefing"] == "TFSA has $100,000.00 of room available."


def test_render_pins_chart_js_version():
    html = render_dashboard(_base_context())
    assert "Chart.js/4.4.4/chart.umd.min.js" in html


def test_render_escapes_script_close_tag_in_user_data():
    malicious = _base_context(briefing="</script><script>window.__xss=true;</script>")
    html = render_dashboard(malicious)
    # The literal sequence "</script><script>" must not appear verbatim
    # inside the data block — it must be escaped so it can't terminate the
    # surrounding <script> element early.
    data_block_start = html.index('<script id="headroom-data"')
    data_block_end = html.index("</script>", data_block_start + 40)
    assert "</script><script>" not in html[data_block_start:data_block_end]
    # But the JSON, once parsed back out, still carries the original text.
    start = data_block_start + html[data_block_start:].index(">") + 1
    embedded = json.loads(html[start:data_block_end])
    assert embedded["briefing"] == "</script><script>window.__xss=true;</script>"


def test_render_includes_overcontribution_warning_data():
    context = _base_context()
    context["tfsa"]["is_overcontributed"] = True
    context["tfsa"]["overcontribution_amount"] = 500.0
    context["tfsa"]["estimated_monthly_penalty"] = 5.0
    html = render_dashboard(context)
    assert '"is_overcontributed": true' in html or "is_overcontributed\": true" in html
