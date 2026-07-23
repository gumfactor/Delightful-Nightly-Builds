from src.report_html import render_html_report

MINIMAL_REPORT = {
    "summary": {
        "total_rows": 1,
        "error_rows": 0,
        "warning_rows": 0,
        "clean_rows": 1,
        "duplicate_cluster_count": 0,
        "file_level_flags": [],
    },
    "header": ["business_name", "category", "province", "website"],
    "rows": [
        {
            "row_index": 1,
            "fields": {
                "business_name": "Acme Co",
                "category": "Retail",
                "province": "ON",
                "website": "acme.ca",
            },
            "flags": [],
            "recommended_action": "keep",
        }
    ],
    "duplicate_clusters": [],
    "generated_with_ai": False,
}


def _report_with_hostile_business_name(payload: str) -> dict:
    report = {
        **MINIMAL_REPORT,
        "rows": [
            {
                "row_index": 1,
                "fields": {
                    "business_name": payload,
                    "category": "Retail",
                    "province": "ON",
                    "website": "acme.ca",
                },
                "flags": [],
                "recommended_action": "keep",
            }
        ],
    }
    return report


def test_render_html_report_produces_doctype_html():
    html = render_html_report(MINIMAL_REPORT, "sample.csv")
    assert html.strip().startswith("<!doctype html>")
    assert "</html>" in html


def test_render_html_report_pins_chartjs_version():
    html = render_html_report(MINIMAL_REPORT, "sample.csv")
    assert "chart.js@4.4.4" in html


def test_render_html_report_escapes_hostile_filename_in_title():
    html = render_html_report(MINIMAL_REPORT, "<img src=x>.csv")
    assert "<img src=x>.csv" not in html
    assert "&lt;img src=x&gt;.csv" in html


def test_render_html_report_neutralizes_script_close_tag_in_embedded_data():
    hostile = "<script>alert(1)</script> Corp"
    report = _report_with_hostile_business_name(hostile)
    html = render_html_report(report, "sample.csv")
    # The raw, unescaped closing sequence must never appear inside the
    # embedded JSON data block — it would terminate the <script> tag early
    # and let literal HTML/JS after it execute in the browser.
    assert "alert(1)</script>" not in html
    # It should instead be present with the closing tag neutralized.
    assert "alert(1)<\\/script>" in html


def test_render_html_report_never_uses_innerhtml_with_row_data():
    html = render_html_report(MINIMAL_REPORT, "sample.csv")
    # The only innerHTML usage in the whole template must be clearing the
    # table body with a literal empty string, never concatenating field data.
    assert "innerHTML = ''" in html
    assert "innerHTML +=" not in html
    assert ".innerHTML = row" not in html


def test_render_html_report_embeds_valid_json_data_block():
    import json

    html = render_html_report(MINIMAL_REPORT, "sample.csv")
    start = html.index('<script id="qc-data" type="application/json">') + len(
        '<script id="qc-data" type="application/json">'
    )
    end = html.index("</script>", start)
    embedded = html[start:end]
    parsed = json.loads(embedded)
    assert parsed["summary"]["total_rows"] == 1
