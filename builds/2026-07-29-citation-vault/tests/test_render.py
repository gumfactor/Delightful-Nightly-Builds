import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import render


def test_render_empty_papers_no_crash():
    html = render.render_dashboard([], {})
    assert "<html" in html
    assert "Citation Vault" in html


def test_render_contains_paper_data_script_tag():
    papers = [{"id": 1, "title": "T", "authors": ["A"], "year": 2020, "journal": "J",
               "abstract": "abs", "doi": None, "status": "to-read", "tags": []}]
    html = render.render_dashboard(papers, {})
    assert '<script id="paper-data" type="application/json">' in html


def test_render_data_roundtrips_correctly():
    papers = [{"id": 1, "title": "Roundtrip Paper", "authors": ["A"], "year": 2020,
               "journal": "J", "abstract": "abs", "doi": None, "status": "read", "tags": ["x"]}]
    html = render.render_dashboard(papers, {1: [{"text": "note", "created_at": "2026-01-01T00:00:00Z"}]})
    match = re.search(
        r'<script id="paper-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    raw = match.group(1).replace("<\\/", "</")
    data = json.loads(raw)
    assert data["papers"][0]["title"] == "Roundtrip Paper"
    assert data["notes"]["1"][0]["text"] == "note"


def test_render_neutralizes_script_breakout_in_title():
    malicious_title = '</script><script>window.__pwned = true;</script>'
    papers = [{"id": 1, "title": malicious_title, "authors": [], "year": None,
               "journal": None, "abstract": None, "doi": None, "status": "to-read", "tags": []}]
    html = render.render_dashboard(papers, {})
    # The raw un-escaped closing sequence must never appear verbatim inside the
    # embedded data script — every "</" in user data is broken up.
    match = re.search(
        r'<script id="paper-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    assert "</script><script>" not in match.group(1)
    # But the data must still round-trip to the original string once decoded.
    raw = match.group(1).replace("<\\/", "</")
    data = json.loads(raw)
    assert data["papers"][0]["title"] == malicious_title


def test_render_neutralizes_script_breakout_in_note():
    papers = [{"id": 1, "title": "T", "authors": [], "year": None, "journal": None,
               "abstract": None, "doi": None, "status": "to-read", "tags": []}]
    notes = {1: [{"text": "</script><img src=x onerror=alert(1)>", "created_at": "2026-01-01T00:00:00Z"}]}
    html = render.render_dashboard(papers, notes)
    match = re.search(
        r'<script id="paper-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert "</script><img" not in match.group(1)


def test_safe_json_helper_escapes_all_closing_tags():
    payload = {"a": "</script>", "b": ["</script>", "safe"]}
    out = render._safe_json_for_script_tag(payload)
    assert "</script>" not in out


def test_render_uses_textcontent_not_innerhtml():
    html = render.render_dashboard([], {})
    assert "innerHTML" not in html


def test_render_includes_dark_mode_media_query():
    # The dashboard defaults to a dark palette and overrides to light via the
    # prefers-color-scheme: light media query, so both modes are considered.
    html = render.render_dashboard([], {})
    assert "prefers-color-scheme: light" in html
    assert "--bg: #0f1115" in html


def test_render_many_papers_no_crash():
    papers = [
        {"id": i, "title": f"Paper {i}", "authors": [f"Author {i}"], "year": 2000 + i,
         "journal": "J", "abstract": None, "doi": None, "status": "to-read", "tags": []}
        for i in range(50)
    ]
    html = render.render_dashboard(papers, {})
    assert html.count('"id": ') >= 50 or html.count('"id":') >= 50
