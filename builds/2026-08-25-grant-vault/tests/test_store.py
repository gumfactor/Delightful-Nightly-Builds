import pytest

from src import store


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = store.init_db(db_path)
    yield connection
    connection.close()


def test_init_db_creates_tables(conn):
    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"documents", "chunks"}.issubset(tables)


def test_get_document_hash_returns_none_when_missing(conn):
    assert store.get_document_hash(conn, "/nowhere.txt") is None


def test_upsert_document_inserts_new(conn):
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    assert doc_id is not None
    assert store.get_document_hash(conn, "/a.txt") == "hash1"


def test_upsert_document_updates_existing_hash(conn):
    first_id = store.upsert_document(conn, "/a.txt", "hash1")
    second_id = store.upsert_document(conn, "/a.txt", "hash2")
    assert first_id == second_id
    assert store.get_document_hash(conn, "/a.txt") == "hash2"


def test_insert_and_retrieve_chunk(conn):
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    store.insert_chunk(
        conn, doc_id, 0, "Significance", "Some reusable text.", 7, "High",
        ["tag-one", "tag-two"], None,
    )
    chunks = store.get_all_chunks(conn)
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk["section_type"] == "Significance"
    assert chunk["text"] == "Some reusable text."
    assert chunk["reuse_score"] == 7
    assert chunk["reuse_tier"] == "High"
    assert chunk["tags"] == ["tag-one", "tag-two"]
    assert chunk["ai_summary"] is None
    assert chunk["document_path"] == "/a.txt"


def test_delete_chunks_for_document(conn):
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    store.insert_chunk(conn, doc_id, 0, "Other", "text", 5, "Medium", [], None)
    assert len(store.get_all_chunks(conn)) == 1
    store.delete_chunks_for_document(conn, doc_id)
    assert len(store.get_all_chunks(conn)) == 0


def test_get_all_chunk_texts(conn):
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    store.insert_chunk(conn, doc_id, 0, "Other", "first chunk", 5, "Medium", [], None)
    store.insert_chunk(conn, doc_id, 1, "Other", "second chunk", 5, "Medium", [], None)
    texts = store.get_all_chunk_texts(conn)
    assert sorted(texts) == ["first chunk", "second chunk"]


def test_compute_content_hash_is_deterministic():
    assert store.compute_content_hash("same text") == store.compute_content_hash("same text")
    assert store.compute_content_hash("text a") != store.compute_content_hash("text b")


def test_ai_summary_stored_when_present(conn):
    doc_id = store.upsert_document(conn, "/a.txt", "hash1")
    store.insert_chunk(
        conn, doc_id, 0, "Other", "text", 5, "Medium", [], "an AI summary"
    )
    chunk = store.get_all_chunks(conn)[0]
    assert chunk["ai_summary"] == "an AI summary"
