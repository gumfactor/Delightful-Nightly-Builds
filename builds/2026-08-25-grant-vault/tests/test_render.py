import json

import pytest

from src import render, store


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = store.init_db(db_path)
    yield connection
    connection.close()


def test_render_produces_valid_html_file(tmp_path, conn):
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    store.insert_chunk(
        conn, doc_id, 0, "Significance", "This is reusable grant text.",
        7, "High", ["stress"], None,
    )
    output_path = str(tmp_path / "dashboard.html")
    render.render_html(conn, output_path)

    with open(output_path, encoding="utf-8") as f:
        html = f.read()

    assert html.startswith("<!DOCTYPE html>")
    assert "This is reusable grant text." in html
    assert "Grant Vault" in html


def test_render_with_no_chunks_still_produces_valid_page(tmp_path, conn):
    output_path = str(tmp_path / "empty_dashboard.html")
    render.render_html(conn, output_path)
    with open(output_path, encoding="utf-8") as f:
        html = f.read()
    assert html.startswith("<!DOCTYPE html>")
    assert "0 document(s)" in html


def test_render_escapes_closing_script_tag_in_chunk_text(tmp_path, conn):
    malicious_text = 'harmless prefix </script><script>alert(1)</script> harmless suffix'
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    store.insert_chunk(conn, doc_id, 0, "Other", malicious_text, 5, "Medium", [], None)

    output_path = str(tmp_path / "dashboard.html")
    render.render_html(conn, output_path)
    with open(output_path, encoding="utf-8") as f:
        html = f.read()

    # The embedded JSON blob must never contain a literal "</script"
    # sequence -- that would prematurely close the embedding <script> tag
    # at the HTML-parser level regardless of what JSON.parse would later
    # do with it.
    data_block_start = html.index('id="chunk-data">') + len('id="chunk-data">')
    data_block_end = html.index("</script>", data_block_start)
    embedded_json = html[data_block_start:data_block_end]
    assert "</script" not in embedded_json.lower()

    # The malicious payload must still be recoverable from the JSON (as
    # inert text, never as a live tag) once unescaped.
    restored = embedded_json.replace("<\\/", "</")
    parsed = json.loads(restored)
    assert parsed[0]["text"] == malicious_text


def test_render_json_blob_contains_all_section_types(tmp_path, conn):
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    store.insert_chunk(conn, doc_id, 0, "Significance", "text one", 5, "Medium", [], None)
    store.insert_chunk(conn, doc_id, 1, "Approach", "text two", 5, "Medium", [], None)

    output_path = str(tmp_path / "dashboard.html")
    render.render_html(conn, output_path)
    with open(output_path, encoding="utf-8") as f:
        html = f.read()

    start = html.index('id="chunk-data">') + len('id="chunk-data">')
    end = html.index("</script>", start)
    parsed = json.loads(html[start:end])
    section_types = {chunk["section_type"] for chunk in parsed}
    assert section_types == {"Significance", "Approach"}


def test_render_does_not_use_innerhtml(tmp_path, conn):
    # Defense-in-depth: the generated page's own script must never use
    # innerHTML to insert chunk-derived content.
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    store.insert_chunk(conn, doc_id, 0, "Other", "text", 5, "Medium", [], None)
    output_path = str(tmp_path / "dashboard.html")
    render.render_html(conn, output_path)
    with open(output_path, encoding="utf-8") as f:
        html = f.read()
    assert "innerHTML" not in html
