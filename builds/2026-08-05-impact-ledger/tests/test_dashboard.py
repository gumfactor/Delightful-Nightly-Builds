"""Tests for the dashboard HTML renderer, with emphasis on script-injection safety."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import dashboard  # noqa: E402

AUTHOR = {
    "author_id": "A1",
    "display_name": "Jane Doe",
    "works_count": 2,
    "cited_by_count": 15,
    "h_index": 3,
    "i10_index": 1,
    "last_synced": "2026-08-05",
}


def _extract_embedded_json(html: str) -> dict:
    start_tag = '<script type="application/json" id="impact-ledger-data">'
    start = html.index(start_tag) + len(start_tag)
    end = html.index("</script>", start)
    raw = html[start:end]
    # Reverse the same escaping applied at render time so json.loads sees valid JSON.
    return json.loads(raw.replace("<\\/", "</"))


def test_renders_valid_html_document():
    html = dashboard.render_dashboard(AUTHOR, [], [], [], {})
    assert html.strip().startswith("<!doctype html>")
    assert "</html>" in html
    assert "Jane Doe" in html


def test_embeds_author_stats_correctly():
    html = dashboard.render_dashboard(AUTHOR, [], [], [], {})
    payload = _extract_embedded_json(html)
    assert payload["author"]["display_name"] == "Jane Doe"
    assert payload["author"]["h_index"] == 3


def test_zero_rising_papers_embeds_empty_list():
    html = dashboard.render_dashboard(AUTHOR, [], [], [], {})
    payload = _extract_embedded_json(html)
    assert payload["rising"] == []
    assert "No rising-paper data yet" in html


def test_multi_snapshot_trend_data_present():
    trend = [
        {"sync_date": "2026-08-01", "total_citations": 10},
        {"sync_date": "2026-08-02", "total_citations": 15},
    ]
    html = dashboard.render_dashboard(AUTHOR, trend, [], [], {})
    payload = _extract_embedded_json(html)
    assert payload["trend"] == trend
    assert "new Chart(ctx" in html


def test_malicious_script_payload_in_title_is_neutralized():
    payload_title = '</script><script>alert(1)</script>'
    papers = [
        {
            "work_id": "W1",
            "title": payload_title,
            "publication_year": 2020,
            "host_venue": "Journal A",
            "cited_by_count": 10,
            "concepts": [],
        }
    ]
    html = dashboard.render_dashboard(AUTHOR, [], papers, [], {})

    # The escaped payload must not create a literal closing tag inside our data script —
    # only "</script" (not bare "<script") can break out of a <script> block early, so that's
    # the only sequence that matters here.
    assert "</script><script>alert(1)</script>" not in html
    assert "<\\/script>" in html
    # The data script's JSON must still parse correctly — proving the closing tag inside the
    # payload was neutralized rather than prematurely ending the <script> element.
    parsed = _extract_embedded_json(html)
    assert parsed["papers"][0]["title"] == payload_title


def test_malicious_payload_in_ai_note_is_contained_in_json_only():
    rising = [
        {
            "work_id": "W1",
            "title": "Some Paper",
            "cited_by_count": 10,
            "previous_cited_by_count": 5,
            "velocity": 5,
            "abstract": "",
            "previous_date": "2026-08-01",
            "latest_date": "2026-08-02",
        }
    ]
    ai_notes = {"W1": '<img src=x onerror="alert(1)">'}
    html = dashboard.render_dashboard(AUTHOR, [], [], rising, ai_notes)
    assert html.count("<script") == 3
    parsed = _extract_embedded_json(html)
    assert parsed["aiNotes"]["W1"] == '<img src=x onerror="alert(1)">'


def test_papers_render_with_concepts_and_missing_fields_gracefully():
    papers = [
        {
            "work_id": "W2",
            "title": "No Year Paper",
            "publication_year": None,
            "host_venue": None,
            "cited_by_count": 0,
            "concepts": [],
        }
    ]
    html = dashboard.render_dashboard(AUTHOR, [], papers, [], {})
    parsed = _extract_embedded_json(html)
    assert parsed["papers"][0]["publication_year"] is None


def test_stats_render_with_missing_h_index():
    incomplete_author = {**AUTHOR, "h_index": None, "i10_index": None}
    html = dashboard.render_dashboard(incomplete_author, [], [], [], {})
    parsed = _extract_embedded_json(html)
    assert parsed["author"]["h_index"] is None
