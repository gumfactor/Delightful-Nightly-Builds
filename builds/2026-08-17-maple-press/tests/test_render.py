import json

import render


def _piece(headline="Test Headline", business_name="Acme Co", description="A pitch."):
    return {
        "id": 1,
        "created_at": "2026-08-17 00:00:00",
        "piece_type": "spotlight",
        "tone": "consumer",
        "occasion": "general",
        "headline": headline,
        "body_markdown": "Some body text.",
        "businesses": [{"name": business_name, "category": "Bakery", "description": description}],
        "novelty_score": 0.0,
        "ai_polished": False,
    }


def test_render_html_produces_valid_structure():
    html = render.render_html([_piece()])
    assert html.startswith("<!doctype html>")
    assert "<title>Maple Press" in html
    assert 'id="pieces-data"' in html
    assert 'id="search"' in html


def test_render_html_empty_pieces_list_still_renders():
    html = render.render_html([])
    assert "<!doctype html>" in html
    payload_start = html.index('id="pieces-data">') + len('id="pieces-data">')
    payload_end = html.index("</script>", payload_start)
    payload = html[payload_start:payload_end]
    assert json.loads(payload) == []


def test_render_html_embeds_pieces_as_valid_json():
    piece = _piece()
    html = render.render_html([piece])
    payload_start = html.index('id="pieces-data">') + len('id="pieces-data">')
    payload_end = html.index("</script>", payload_start)
    payload = html[payload_start:payload_end]
    decoded = json.loads(payload)
    assert decoded[0]["headline"] == "Test Headline"


def test_render_html_escapes_script_close_sequences_in_business_name():
    xss_name = "Acme</script><script>alert(1)</script>"
    piece = _piece(business_name=xss_name)
    html = render.render_html([piece])

    # The raw closing-tag sequence must never appear verbatim in the output —
    # every '</' inside embedded JSON is escaped to '<\/', which breaks this
    # exact contiguous substring even though the surrounding text survives.
    assert "</script><script>alert(1)</script>" not in html

    # The data itself is preserved exactly — JSON.parse in the browser will
    # reconstruct the original string faithfully; it's just never live markup.
    payload_start = html.index('id="pieces-data">') + len('id="pieces-data">')
    payload_end = html.index("</script>", payload_start)
    decoded = json.loads(html[payload_start:payload_end])
    assert decoded[0]["businesses"][0]["name"] == xss_name


def test_render_html_escapes_img_onerror_payload_in_description():
    xss_description = '<img src=x onerror=alert(1)>'
    piece = _piece(description=xss_description)
    html = render.render_html([piece])
    payload_start = html.index('id="pieces-data">') + len('id="pieces-data">')
    payload_end = html.index("</script>", payload_start)
    payload = html[payload_start:payload_end]
    decoded = json.loads(payload)
    assert decoded[0]["businesses"][0]["description"] == xss_description

    # The <img> text exists only inside the inert JSON payload (a <script
    # type="application/json"> tag is never parsed for markup by a browser),
    # never as live markup anywhere else in the document.
    html_outside_payload = html[:payload_start] + html[payload_end:]
    assert "<img" not in html_outside_payload


def test_render_html_multiple_pieces_all_present():
    pieces = [_piece(headline="First"), _piece(headline="Second"), _piece(headline="Third")]
    html = render.render_html(pieces)
    payload_start = html.index('id="pieces-data">') + len('id="pieces-data">')
    payload_end = html.index("</script>", payload_start)
    decoded = json.loads(html[payload_start:payload_end])
    assert [p["headline"] for p in decoded] == ["First", "Second", "Third"]
