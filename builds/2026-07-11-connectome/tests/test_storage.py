import linking
import storage
import pytest


@pytest.fixture
def conn():
    connection = storage.connect(":memory:")
    yield connection
    connection.close()


def test_connect_creates_schema_idempotently():
    c = storage.connect(":memory:")
    # Re-running the schema script against the same connection must not raise.
    c.executescript(storage.SCHEMA)
    c.close()


def test_upsert_note_inserts_new_note(conn):
    note_id = storage.upsert_note(conn, "a.md", "Title A", "body text", "hash1")
    row = storage.get_note_by_path(conn, "a.md")
    assert row["id"] == note_id
    assert row["title"] == "Title A"
    assert row["content_hash"] == "hash1"


def test_upsert_note_updates_existing_note_same_id(conn):
    first_id = storage.upsert_note(conn, "a.md", "Title A", "body v1", "hash1")
    second_id = storage.upsert_note(conn, "a.md", "Title A v2", "body v2", "hash2")
    assert first_id == second_id
    row = storage.get_note_by_path(conn, "a.md")
    assert row["title"] == "Title A v2"
    assert row["content_hash"] == "hash2"


def test_reindexing_same_content_does_not_duplicate_rows(conn):
    storage.upsert_note(conn, "a.md", "Title A", "body text", "hash1")
    storage.upsert_note(conn, "a.md", "Title A", "body text", "hash1")
    count = conn.execute("SELECT COUNT(*) as c FROM notes").fetchone()["c"]
    assert count == 1


def test_delete_note_removes_links_and_concepts(conn):
    id_a = storage.upsert_note(conn, "a.md", "A", "body", "h1")
    id_b = storage.upsert_note(conn, "b.md", "B", "body", "h2")
    storage.replace_note_concepts(conn, id_a, [("shared", 1.0)])
    storage.replace_note_concepts(conn, id_b, [("shared", 1.0)])
    storage.recompute_doc_frequencies(conn)
    links = linking.compute_links(
        storage.get_all_note_concepts(conn), storage.get_doc_frequencies(conn), 2
    )
    storage.replace_all_links(conn, links)
    assert len(storage.get_all_links(conn)) == 1

    storage.delete_note(conn, id_a)

    # Regression test: deleting a note must cascade-remove its links,
    # otherwise `related` on the surviving note crashes on a dangling note_id.
    remaining_links = storage.get_all_links(conn)
    assert all(link.note_a != id_a and link.note_b != id_a for link in remaining_links)
    remaining_concepts = conn.execute(
        "SELECT * FROM note_concepts WHERE note_id = ?", (id_a,)
    ).fetchall()
    assert remaining_concepts == []


def test_recompute_doc_frequencies_removes_orphaned_concepts(conn):
    note_id = storage.upsert_note(conn, "a.md", "A", "body", "h1")
    storage.replace_note_concepts(conn, note_id, [("term", 1.0)])
    storage.recompute_doc_frequencies(conn)
    assert storage.get_doc_frequencies(conn)["term"] == 1

    # Removing the only note referencing "term" should drop it from concepts.
    storage.replace_note_concepts(conn, note_id, [])
    storage.recompute_doc_frequencies(conn)
    assert "term" not in storage.get_doc_frequencies(conn)


def test_search_notes_is_case_insensitive_across_title_body_and_concept(conn):
    note_id = storage.upsert_note(conn, "a.md", "Semiconductor Thesis", "capex discussion", "h1")
    storage.replace_note_concepts(conn, note_id, [("workflow", 1.0)])

    assert len(storage.search_notes(conn, "SEMICONDUCTOR")) == 1
    assert len(storage.search_notes(conn, "capex")) == 1
    assert len(storage.search_notes(conn, "WORKFLOW")) == 1
    assert len(storage.search_notes(conn, "nonexistent")) == 0


def test_get_all_note_concepts_returns_empty_dict_for_note_with_no_concepts(conn):
    note_id = storage.upsert_note(conn, "a.md", "A", "body", "h1")
    all_concepts = storage.get_all_note_concepts(conn)
    assert all_concepts[note_id] == {}
