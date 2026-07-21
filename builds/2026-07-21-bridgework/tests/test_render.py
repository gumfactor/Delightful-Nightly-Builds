import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import render


def make_entry(**overrides):
    entry = {
        "id": 1,
        "concept_id": "hpa_axis_response",
        "concept_name": "The HPA Axis Stress Response",
        "subdomain": "stress",
        "domain_id": "kitchen",
        "domain_name": "The Kitchen Stove",
        "audience": "public_talk",
        "hook": "A hook about stress.",
        "analogy": "A full analogy paragraph.",
        "caveat": "Where it breaks down.",
        "source": "template",
        "novelty_score": 1.0,
        "created_at": "2026-07-21T00:00:00+00:00",
    }
    entry.update(overrides)
    return entry


def test_render_html_contains_entry_text():
    html = render.render_html([make_entry()])
    assert "A hook about stress." in html
    assert "A full analogy paragraph." in html


def test_render_html_empty_list_produces_valid_html():
    html = render.render_html([])
    assert "<html" in html
    assert "</html>" in html
    assert "0 analogies" in html


def test_render_html_escapes_script_tag_in_analogy():
    import json
    import re

    malicious = "<script>alert('xss')</script>"
    html = render.render_html([make_entry(analogy=malicious)])
    # If the payload's own "</script>" were left unescaped, it would terminate our
    # <script id="data"> block early and this non-greedy extraction would capture a
    # truncated, invalid JSON fragment instead of the full data payload.
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.DOTALL)
    assert match is not None
    data = json.loads(match.group(1))  # raises if the closing tag broke out early
    assert data[0]["analogy"] == malicious  # original text preserved, just inert as data


def test_render_html_json_embed_survives_closing_script_sequence():
    tricky = "some text </script><script>evil()</script> more text"
    html = render.render_html([make_entry(analogy=tricky)])
    # The literal sequence '</script>' must never appear unescaped inside our data block
    data_start = html.index('id="data"')
    data_section = html[data_start:data_start + 5000]
    assert "</script><script>evil()" not in data_section


def test_render_html_includes_multiple_entries():
    entries = [make_entry(id=1, hook="Hook one"), make_entry(id=2, hook="Hook two")]
    html = render.render_html(entries)
    assert "Hook one" in html
    assert "Hook two" in html
    assert "2 analogies" in html


def test_render_html_is_valid_json_payload():
    import json
    import re

    entries = [make_entry(id=1), make_entry(id=2, concept_id="allostatic_load")]
    html = render.render_html(entries)
    match = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.DOTALL)
    assert match is not None
    data = json.loads(match.group(1))
    assert len(data) == 2
    assert data[0]["id"] == 1
