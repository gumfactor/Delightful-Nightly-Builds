import json

from src.models import Author, Reference
from src.render_html import render


def test_render_produces_html_document():
    ref = Reference(ref_type="journal-article", authors=[Author("Smith", "Jane")], year="2020", title="A study")
    html = render([ref])
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_embeds_escaped_json_payload_no_raw_script_close():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane")],
        year="2020",
        title='</script><script>window.__xss=true;</script>',
    )
    html = render([ref])
    assert "</script><script>window.__xss" not in html
    assert "<\\/script>" in html


def test_render_never_uses_innerhtml():
    html = render([])
    assert "innerHTML" not in html


def test_render_includes_all_four_styles_per_reference():
    ref = Reference(
        ref_type="journal-article",
        authors=[Author("Smith", "Jane")],
        year="2020",
        title="A study",
        container_title="Journal X",
    )
    html = render([ref])
    payload_start = html.index('id="ref-data">') + len('id="ref-data">')
    payload_end = html.index("</script>", payload_start)
    payload = json.loads(html[payload_start:payload_end].replace("<\\/", "</"))
    assert set(payload[0]["styles"].keys()) == {"apa", "ama", "vancouver", "chicago"}


def test_render_empty_library_still_produces_valid_document():
    html = render([])
    assert "0 reference(s)" in html
    payload_start = html.index('id="ref-data">') + len('id="ref-data">')
    payload_end = html.index("</script>", payload_start)
    payload = json.loads(html[payload_start:payload_end].replace("<\\/", "</"))
    assert payload == []


def test_render_marks_needs_review_entries():
    ref = Reference(
        ref_type="other", authors=[], year="", title="Unparsed line", source="text-unparsed", needs_review=True
    )
    html = render([ref])
    payload_start = html.index('id="ref-data">') + len('id="ref-data">')
    payload_end = html.index("</script>", payload_start)
    payload = json.loads(html[payload_start:payload_end].replace("<\\/", "</"))
    assert payload[0]["needs_review"] is True
