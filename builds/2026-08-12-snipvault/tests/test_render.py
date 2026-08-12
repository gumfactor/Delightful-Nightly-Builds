import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import Snippet
from src.render import render_html


def _snippet(**overrides):
    defaults = dict(
        id=1,
        title="Test snippet",
        language="python",
        code="print('hi')",
        description="Prints hi",
        tags=["util"],
        source=None,
        created_at="2026-08-12T00:00:00+00:00",
        updated_at="2026-08-12T00:00:00+00:00",
        usage_count=0,
    )
    defaults.update(overrides)
    return Snippet(**defaults)


def test_render_html_is_self_contained_document():
    html = render_html([_snippet()])
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert "Test snippet" not in html.split('id="snippet-data"')[0]  # not in the visible markup shell


def test_render_html_empty_vault_does_not_crash():
    html = render_html([])
    assert "<!DOCTYPE html>" in html
    assert 'id="snippet-data">[]</script>' in html


def test_render_html_script_injection_payload_is_inert_text():
    payload = "</script><script>alert(1)</script>"
    html = render_html([_snippet(title=payload)])
    # The raw payload must never appear as an executable sibling <script> tag —
    # it must only exist inside the escaped JSON data blob.
    assert "<script>alert(1)</script>" not in html
    assert "\\u003c/script>\\u003cscript>alert(1)\\u003c/script>" in html


def test_render_html_escapes_every_angle_bracket_in_payload():
    # A payload containing an HTML comment immediately followed by a script
    # tag can otherwise drive the HTML tokenizer into a state where the
    # template's real closing </script> tag fails to end the data element.
    # No raw "<" may survive inside the embedded JSON segment for this to be
    # impossible, regardless of what precedes it.
    payload = "<!--<script>alert(1)</script>-->"
    html = render_html([_snippet(code=payload)])
    start = html.index('id="snippet-data">') + len('id="snippet-data">')
    end = html.index("</script>", start)
    data_segment = html[start:end]
    assert "<" not in data_segment
    assert "\\u003c" in data_segment


def test_render_html_embeds_data_as_json_payload():
    html = render_html([_snippet(title="Alpha"), _snippet(id=2, title="Beta")])
    assert html.count('id="snippet-data"') == 1
    assert "Alpha" in html
    assert "Beta" in html


def test_render_html_includes_all_snippet_fields_in_payload():
    html = render_html([_snippet(tags=["regex", "sql"], usage_count=3)])
    assert "regex" in html
    assert "sql" in html
