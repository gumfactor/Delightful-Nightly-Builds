import json
import os
import tempfile

from src import render

SAMPLE_COMPANIES = [
    {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "rows": [
            {"fiscal_year": 2022, "revenue": 1000, "net_income": 100, "operating_income": 120,
             "assets": 500, "liabilities": 200, "equity": 300, "cash": 50,
             "net_margin": 0.1, "operating_margin": 0.12, "debt_to_equity": 0.667,
             "revenue_yoy": None, "net_margin_delta": None, "debt_to_equity_delta": None},
            {"fiscal_year": 2023, "revenue": 850, "net_income": 60, "operating_income": 70,
             "assets": 480, "liabilities": 210, "equity": 270, "cash": 40,
             "net_margin": 0.0706, "operating_margin": 0.0824, "debt_to_equity": 0.778,
             "revenue_yoy": -0.15, "net_margin_delta": -0.0294, "debt_to_equity_delta": 0.111},
        ],
        "anomalies": [
            {"fiscal_year": 2023, "type": "revenue_decline", "detail": "Revenue fell 15.0% year-over-year",
             "narrative": "AAPL FY2023: Revenue decline -- Revenue fell 15.0% year-over-year."},
        ],
    }
]


def test_build_dashboard_html_contains_expected_data():
    html = render.build_dashboard_html(SAMPLE_COMPANIES)
    assert "EDGAR Lens" in html
    assert "AAPL" in html
    assert "Apple Inc." in html


def test_build_dashboard_html_embeds_valid_json_payload():
    html = render.build_dashboard_html(SAMPLE_COMPANIES)
    start = html.index('<script type="application/json" id="edgar-lens-data">') + len(
        '<script type="application/json" id="edgar-lens-data">'
    )
    end = html.index("</script>", start)
    payload = json.loads(html[start:end])
    assert payload["companies"][0]["ticker"] == "AAPL"
    assert len(payload["companies"][0]["rows"]) == 2


def test_script_injection_in_ticker_is_neutralized():
    malicious = [
        {
            "ticker": "</script><script>window.__xss=true;</script>",
            "company_name": "<img src=x onerror=window.__xss2=true>",
            "rows": [],
            "anomalies": [],
        }
    ]
    html = render.build_dashboard_html(malicious)
    # The payload must not contain a literal "</script>" sequence that
    # could prematurely close the data script tag -- it must be escaped.
    start = html.index('<script type="application/json" id="edgar-lens-data">')
    end = html.index("</script>", start + 10)
    embedded_segment = html[start:end]
    assert "</script>" not in embedded_segment


def test_only_expected_script_tags_present_for_malicious_data():
    malicious = [
        {
            "ticker": "</script><script>alert(1)</script>",
            "company_name": "Evil Corp",
            "rows": [],
            "anomalies": [],
        }
    ]
    html = render.build_dashboard_html(malicious)
    # Count real (unescaped) closing script tags: the page itself should
    # define exactly 3 (Chart.js CDN, the JSON data tag, the app logic tag).
    assert html.count("</script>") == 3


def test_render_dashboard_writes_file():
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        html = render.render_dashboard(SAMPLE_COMPANIES, path)
        with open(path, encoding="utf-8") as f:
            written = f.read()
        assert written == html
        assert "AAPL" in written
    finally:
        os.remove(path)


def test_build_dashboard_html_handles_empty_companies_list():
    html = render.build_dashboard_html([])
    assert "EDGAR Lens" in html
    start = html.index('<script type="application/json" id="edgar-lens-data">') + len(
        '<script type="application/json" id="edgar-lens-data">'
    )
    end = html.index("</script>", start)
    payload = json.loads(html[start:end])
    assert payload["companies"] == []


def test_escape_for_script_tag_neutralizes_closing_tag():
    assert "</script>" not in render._escape_for_script_tag('{"x": "</script>"}')
