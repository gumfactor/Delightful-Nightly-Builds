import json

from src import render


def make_row(paper_id="p1", title="Title", year=2020, venue="Venue", citation_count=5, external_url=None):
    return {
        "paper_id": paper_id,
        "title": title,
        "year": year,
        "venue": venue,
        "citation_count": citation_count,
        "external_url": external_url,
    }


def test_build_payload_shapes_data_correctly():
    clusters = [
        {
            "label": "stress / cortisol",
            "keywords": ["stress", "cortisol"],
            "narrative": "A narrative.",
            "narrative_source": "deterministic",
            "papers": [make_row()],
        }
    ]
    papers = [make_row()]
    growth = [{"paper_id": "p1", "title": "Title", "first_count": 1, "latest_count": 5, "delta": 4}]

    payload = render.build_payload("Jane Doe", "2026-09-12T00:00:00", clusters, papers, growth)
    assert payload["author"] == "Jane Doe"
    assert payload["clusters"][0]["label"] == "stress / cortisol"
    assert payload["papers"][0]["paper_id"] == "p1"
    assert payload["growth"] == growth


def test_render_dashboard_produces_full_html_document():
    html = render.render_dashboard("Jane Doe", "2026-09-12T00:00:00", [], [make_row()], [])
    assert html.strip().startswith("<!doctype html>")
    assert "<title>Throughline</title>" in html
    assert "</html>" in html.strip()[-20:]


def test_render_dashboard_escapes_closing_script_tag_in_payload():
    hostile_title = "</script><script>window.__xss=true;</script>"
    row = make_row(title=hostile_title)
    html = render.render_dashboard("Jane Doe", "2026-09-12T00:00:00", [], [row], [])

    # The literal, unescaped closing sequence must never appear verbatim --
    # otherwise it would terminate the JSON <script> tag early.
    assert "</script><script>window.__xss" not in html
    # The escaped form (used for safe re-parsing inside the JSON payload) is present.
    assert "<\\/script><script>window.__xss" in html


def test_render_dashboard_payload_is_valid_json_after_unescaping():
    row = make_row(title="A </script> title")
    html = render.render_dashboard("Jane Doe", "2026-09-12T00:00:00", [], [row], [])

    start = html.index('<script type="application/json" id="throughline-data">') + len(
        '<script type="application/json" id="throughline-data">'
    )
    end = html.index("</script>", start)
    raw_payload = html[start:end]
    parsed = json.loads(raw_payload.replace("<\\/script", "</script"))
    assert parsed["papers"][0]["title"] == "A </script> title"


def test_render_dashboard_includes_chart_js_and_fallback_table():
    html = render.render_dashboard("Jane Doe", "2026-09-12T00:00:00", [], [make_row()], [])
    assert render.CHART_JS_URL in html
    assert 'id="growth-fallback"' in html


def test_render_dashboard_never_uses_innerhtml_for_dynamic_text():
    html = render.render_dashboard("Jane Doe", "2026-09-12T00:00:00", [], [make_row()], [])
    # The only innerHTML usages should be clearing containers with a literal
    # empty string, never assigning data-derived content.
    for line in html.splitlines():
        if "innerHTML" in line:
            assert "= ''" in line
