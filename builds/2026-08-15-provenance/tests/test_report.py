from src import report

XSS_PAYLOAD = "</script><script>window.__pwned = true;</script><img src=x onerror=alert(1)>"


def test_render_html_produces_a_full_document():
    rows = [{"name": "Acme Ltd.", "verdict": "canadian", "confidence": 0.95, "evidence": "e", "wikidata_qid": "Q1", "ai_note": ""}]
    stats = {"total": 1, "canadian": 1, "foreign": 0, "uncertain": 0, "cache_hits": 0, "cache_misses": 1}
    html = report.render_html(rows, stats)
    assert "<!doctype html>" in html.lower()
    assert "Provenance" in html


def test_xss_payload_in_business_name_never_appears_as_a_literal_script_close_tag():
    rows = [{"name": XSS_PAYLOAD, "verdict": "uncertain", "confidence": 0.0, "evidence": "e", "wikidata_qid": "", "ai_note": ""}]
    stats = {"total": 1, "canadian": 0, "foreign": 0, "uncertain": 1, "cache_hits": 0, "cache_misses": 1}
    html = report.render_html(rows, stats)
    # The payload's literal "</script>" must never appear unescaped inside the page —
    # it would otherwise prematurely close the data <script> tag and let the
    # attacker-controlled markup after it execute as real HTML.
    assert "</script><script>window.__pwned" not in html


def test_data_is_delivered_via_json_script_tag_not_string_concatenation():
    rows = [{"name": "Acme Ltd.", "verdict": "canadian", "confidence": 0.95, "evidence": "e", "wikidata_qid": "Q1", "ai_note": ""}]
    stats = {"total": 1, "canadian": 1, "foreign": 0, "uncertain": 0, "cache_hits": 0, "cache_misses": 1}
    html = report.render_html(rows, stats)
    assert 'type="application/json"' in html
    assert "innerHTML" not in html


def test_dom_construction_uses_createelement_and_textcontent_only():
    rows = []
    stats = {"total": 0, "canadian": 0, "foreign": 0, "uncertain": 0, "cache_hits": 0, "cache_misses": 0}
    html = report.render_html(rows, stats)
    assert "createElement" in html
    assert "textContent" in html
    assert "innerHTML" not in html


def test_json_payload_round_trips_business_data():
    rows = [{"name": "Acme Ltd.", "verdict": "canadian", "confidence": 0.95, "evidence": "clean match", "wikidata_qid": "Q1", "ai_note": ""}]
    stats = {"total": 1, "canadian": 1, "foreign": 0, "uncertain": 0, "cache_hits": 0, "cache_misses": 1}
    html = report.render_html(rows, stats)
    assert "Acme Ltd." in html
    assert "clean match" in html
