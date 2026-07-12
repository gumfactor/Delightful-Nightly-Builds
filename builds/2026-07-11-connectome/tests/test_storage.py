import linking
import storage
import pytest

NOTES = storage.DEFAULT_CATEGORY


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
    note_id = storage.upsert_note(conn, "a.md", NOTES, "Title A", "body text", "hash1")
    row = storage.get_note_by_path(conn, "a.md", NOTES)
    assert row["id"] == note_id
    assert row["title"] == "Title A"
    assert row["content_hash"] == "hash1"
    assert row["category"] == NOTES
    assert row["subcategory"] is None


def test_upsert_note_updates_existing_note_same_id(conn):
    first_id = storage.upsert_note(conn, "a.md", NOTES, "Title A", "body v1", "hash1")
    second_id = storage.upsert_note(conn, "a.md", NOTES, "Title A v2", "body v2", "hash2")
    assert first_id == second_id
    row = storage.get_note_by_path(conn, "a.md", NOTES)
    assert row["title"] == "Title A v2"
    assert row["content_hash"] == "hash2"


def test_reindexing_same_content_does_not_duplicate_rows(conn):
    storage.upsert_note(conn, "a.md", NOTES, "Title A", "body text", "hash1")
    storage.upsert_note(conn, "a.md", NOTES, "Title A", "body text", "hash1")
    count = conn.execute("SELECT COUNT(*) as c FROM notes").fetchone()["c"]
    assert count == 1


def test_delete_note_removes_links_and_concepts(conn):
    id_a = storage.upsert_note(conn, "a.md", NOTES, "A", "body", "h1")
    id_b = storage.upsert_note(conn, "b.md", NOTES, "B", "body", "h2")
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
    note_id = storage.upsert_note(conn, "a.md", NOTES, "A", "body", "h1")
    storage.replace_note_concepts(conn, note_id, [("term", 1.0)])
    storage.recompute_doc_frequencies(conn)
    assert storage.get_doc_frequencies(conn)["term"] == 1

    # Removing the only note referencing "term" should drop it from concepts.
    storage.replace_note_concepts(conn, note_id, [])
    storage.recompute_doc_frequencies(conn)
    assert "term" not in storage.get_doc_frequencies(conn)


def test_search_notes_is_case_insensitive_across_title_body_and_concept(conn):
    note_id = storage.upsert_note(conn, "a.md", NOTES, "Semiconductor Thesis", "capex discussion", "h1")
    storage.replace_note_concepts(conn, note_id, [("workflow", 1.0)])

    assert len(storage.search_notes(conn, "SEMICONDUCTOR")) == 1
    assert len(storage.search_notes(conn, "capex")) == 1
    assert len(storage.search_notes(conn, "WORKFLOW")) == 1
    assert len(storage.search_notes(conn, "nonexistent")) == 0


def test_get_all_note_concepts_returns_empty_dict_for_note_with_no_concepts(conn):
    note_id = storage.upsert_note(conn, "a.md", NOTES, "A", "body", "h1")
    all_concepts = storage.get_all_note_concepts(conn)
    assert all_concepts[note_id] == {}


def test_same_path_allowed_across_different_categories(conn):
    # "overview.md" can exist independently in Notes and in Academic Papers —
    # uniqueness is scoped to (category, path), not path alone.
    note_id = storage.upsert_note(conn, "overview.md", "Notes", "Notes Overview", "note body", "h1")
    paper_id = storage.upsert_note(conn, "overview.md", "Academic Papers", "Paper Overview", "paper body", "h2")
    assert note_id != paper_id
    assert storage.get_note_by_path(conn, "overview.md", "Notes")["title"] == "Notes Overview"
    assert storage.get_note_by_path(conn, "overview.md", "Academic Papers")["title"] == "Paper Overview"


def test_get_note_by_path_scoped_to_category_returns_none_for_wrong_category(conn):
    storage.upsert_note(conn, "a.md", "Notes", "A", "body", "h1")
    assert storage.get_note_by_path(conn, "a.md", "Academic Papers") is None


def test_find_note_by_path_any_category_ignores_category(conn):
    storage.upsert_note(conn, "a.md", "Academic Papers", "A Paper", "body", "h1")
    found = storage.find_note_by_path_any_category(conn, "a.md")
    assert found["title"] == "A Paper"


def test_all_notes_filters_by_category_case_insensitively(conn):
    storage.upsert_note(conn, "a.md", "Notes", "A", "body", "h1")
    storage.upsert_note(conn, "b.md", "Academic Papers", "B", "body", "h2")
    notes_only = storage.all_notes(conn, category="notes")
    assert len(notes_only) == 1
    assert notes_only[0]["title"] == "A"


def test_all_notes_without_category_returns_everything(conn):
    storage.upsert_note(conn, "a.md", "Notes", "A", "body", "h1")
    storage.upsert_note(conn, "b.md", "Academic Papers", "B", "body", "h2")
    assert len(storage.all_notes(conn)) == 2


def test_get_categories_returns_distinct_sorted_categories(conn):
    storage.upsert_note(conn, "a.md", "Notes", "A", "body", "h1")
    storage.upsert_note(conn, "b.md", "Academic Papers", "B", "body", "h2")
    storage.upsert_note(conn, "c.md", "Notes", "C", "body", "h3")
    assert storage.get_categories(conn) == ["Academic Papers", "Notes"]


def test_set_subcategory_persists_and_defaults_to_none(conn):
    note_id = storage.upsert_note(conn, "a.md", NOTES, "A", "body", "h1")
    assert storage.get_note_by_path(conn, "a.md", NOTES)["subcategory"] is None
    storage.set_subcategory(conn, note_id, "AI Agents")
    assert storage.get_note_by_path(conn, "a.md", NOTES)["subcategory"] == "AI Agents"


def test_search_notes_respects_category_filter(conn):
    note_id = storage.upsert_note(conn, "a.md", "Notes", "Shared Topic", "workflow content", "h1")
    storage.replace_note_concepts(conn, note_id, [("workflow", 1.0)])
    paper_id = storage.upsert_note(conn, "b.md", "Academic Papers", "Shared Topic Paper", "workflow content", "h2")
    storage.replace_note_concepts(conn, paper_id, [("workflow", 1.0)])

    assert len(storage.search_notes(conn, "workflow")) == 2
    assert len(storage.search_notes(conn, "workflow", category="Notes")) == 1
    assert len(storage.search_notes(conn, "workflow", category="notes")) == 1


def test_migrate_schema_adds_missing_columns_to_pre_existing_table(tmp_path):
    db_path = str(tmp_path / "legacy.db")
    import sqlite3
    legacy_conn = sqlite3.connect(db_path)
    legacy_conn.execute("""
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            indexed_at TEXT NOT NULL
        )
    """)
    legacy_conn.execute(
        "INSERT INTO notes (path, title, body, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?)",
        ("old.md", "Old Note", "body", "h1", "2026-01-01"),
    )
    legacy_conn.commit()
    legacy_conn.close()

    migrated = storage.connect(db_path)
    row = storage.get_note_by_path(migrated, "old.md", storage.DEFAULT_CATEGORY)
    assert row is not None
    assert row["category"] == storage.DEFAULT_CATEGORY
    assert row["subcategory"] is None
