import os
import tempfile

import render
import storage


def test_render_knowledge_base_produces_valid_html_file():
    conn = storage.connect(":memory:")
    note_id = storage.upsert_note(conn, "a.md", "Note A", "some body text", "h1")
    storage.replace_note_concepts(conn, note_id, [("term", 1.0)])
    storage.recompute_doc_frequencies(conn)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = render.render_knowledge_base(conn, tmp_dir)
        assert os.path.exists(output_path)
        with open(output_path, encoding="utf-8") as f:
            html_content = f.read()

    assert html_content.startswith("<!DOCTYPE html>")
    assert "Note A" in html_content
    assert "connectome-data" in html_content


def test_render_escapes_hostile_note_body_in_detail_div():
    conn = storage.connect(":memory:")
    hostile_body = '<script>alert(1)</script> and a "quote" and a `backtick`'
    storage.upsert_note(conn, "hostile.md", "Hostile Note", hostile_body, "h1")

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = render.render_knowledge_base(conn, tmp_dir)
        with open(output_path, encoding="utf-8") as f:
            html_content = f.read()

    # The raw, executable script tag must never appear verbatim in the output.
    assert "<script>alert(1)</script>" not in html_content
    # The escaped form should be present instead.
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_content


def test_safe_json_escapes_script_close_tag_without_breaking_json_validity():
    import json
    data = {"title": "</script><img src=x onerror=alert(1)>"}
    embedded = render._safe_json(data)
    assert "</script>" not in embedded
    # Must still round-trip through JSON.parse-equivalent decoding.
    decoded = json.loads(embedded)
    assert decoded == data


def test_render_with_no_notes_does_not_crash():
    conn = storage.connect(":memory:")
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = render.render_knowledge_base(conn, tmp_dir)
        assert os.path.exists(output_path)


def test_build_data_includes_tag_cloud_and_links():
    conn = storage.connect(":memory:")
    id_a = storage.upsert_note(conn, "a.md", "A", "body", "h1")
    id_b = storage.upsert_note(conn, "b.md", "B", "body", "h2")
    storage.replace_note_concepts(conn, id_a, [("shared", 1.0)])
    storage.replace_note_concepts(conn, id_b, [("shared", 1.0)])
    storage.recompute_doc_frequencies(conn)

    import linking
    links = linking.compute_links(
        storage.get_all_note_concepts(conn), storage.get_doc_frequencies(conn), 2
    )
    storage.replace_all_links(conn, links)

    data = render.build_data(conn)
    assert len(data["notes"]) == 2
    assert any(entry["term"] == "shared" for entry in data["tag_cloud"])
    assert len(data["links"]) == 1
