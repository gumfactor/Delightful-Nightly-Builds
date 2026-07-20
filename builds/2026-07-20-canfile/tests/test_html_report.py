import html_report


def _make_card(company_name="Tim Hortons", assessment_text="A safe assessment.", version=1):
    return {
        "id": 1,
        "company_name": company_name,
        "qid": "Q1524829",
        "wikidata_facts": {"country_labels": ["Canada"], "headquarters_labels": ["Oakville"]},
        "wikipedia_summary": "A summary.",
        "assessment_text": assessment_text,
        "confidence": "high",
        "verdict": "canadian",
        "source_urls": ["https://www.wikidata.org/wiki/Q1524829"],
        "created_at": "2026-07-20T00:00:00+00:00",
        "version": version,
    }


def test_render_html_includes_company_name():
    entries = [{"card": _make_card(), "history": [_make_card()]}]
    output = html_report.render_html(entries)
    assert "Tim Hortons" in output
    assert "<html" in output


def test_render_html_empty_state():
    output = html_report.render_html([])
    assert "No knowledge cards yet" in output


def test_render_html_escapes_script_injection_in_company_name():
    malicious_name = '<script>alert("xss")</script>'
    entries = [{"card": _make_card(company_name=malicious_name), "history": []}]
    output = html_report.render_html(entries)
    assert "<script>alert" not in output
    assert "&lt;script&gt;" in output


def test_render_html_escapes_script_injection_in_assessment_text():
    malicious_text = '<img src=x onerror=alert(1)>'
    entries = [{"card": _make_card(assessment_text=malicious_text), "history": []}]
    output = html_report.render_html(entries)
    assert "<img src=x onerror=alert(1)>" not in output
    assert "&lt;img" in output


def test_render_html_shows_version_history_when_multiple_versions():
    history = [_make_card(version=1), _make_card(version=2)]
    entries = [{"card": _make_card(version=2), "history": history}]
    output = html_report.render_html(entries)
    assert "Version history" in output
    assert "v1" in output and "v2" in output


def test_render_html_hides_version_history_when_single_version():
    entries = [{"card": _make_card(version=1), "history": [_make_card(version=1)]}]
    output = html_report.render_html(entries)
    assert "Version history" not in output


def test_render_html_includes_search_and_filter_controls():
    output = html_report.render_html([{"card": _make_card(), "history": []}])
    assert 'data-testid="search-box"' in output
    assert 'data-testid="verdict-filter"' in output
