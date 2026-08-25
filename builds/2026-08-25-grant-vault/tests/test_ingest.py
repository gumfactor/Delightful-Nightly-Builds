import pytest

from src import ingest, store
from src.classifier import SECTION_TYPES


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = store.init_db(db_path)
    yield connection
    connection.close()


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_ingest_single_file_creates_chunks(tmp_path, conn):
    path = _write(tmp_path, "grant.txt", "Significance\nThis matters broadly.\n\nApproach\nWe will test it.")
    summary = ingest.ingest_path(path, conn)
    assert summary["documents_processed"] == 1
    assert summary["documents_skipped"] == 0
    assert summary["chunks_inserted"] == 2
    chunks = store.get_all_chunks(conn)
    assert len(chunks) == 2


def test_ingest_folder_processes_all_txt_and_md_files(tmp_path, conn):
    _write(tmp_path, "one.txt", "Significance\nFirst document text here.")
    _write(tmp_path, "two.md", "Approach\nSecond document text here.")
    _write(tmp_path, "ignore.csv", "not,a,grant,file")
    summary = ingest.ingest_path(str(tmp_path), conn)
    assert summary["documents_processed"] == 2
    assert summary["chunks_inserted"] == 2


def test_reingest_unchanged_file_skips(tmp_path, conn):
    path = _write(tmp_path, "grant.txt", "Significance\nStable content that will not change.")
    ingest.ingest_path(path, conn)
    before = len(store.get_all_chunks(conn))
    summary = ingest.ingest_path(path, conn)
    after = len(store.get_all_chunks(conn))
    assert summary["documents_processed"] == 0
    assert summary["documents_skipped"] == 1
    assert before == after


def test_reingest_changed_file_replaces_chunks(tmp_path, conn):
    path = _write(tmp_path, "grant.txt", "Significance\nOriginal content.")
    ingest.ingest_path(path, conn)
    _write(tmp_path, "grant.txt", "Significance\nCompletely different revised content.")
    summary = ingest.ingest_path(path, conn)
    assert summary["documents_processed"] == 1
    chunks = store.get_all_chunks(conn)
    assert len(chunks) == 1
    assert "revised" in chunks[0]["text"]


def test_ingest_missing_path_raises_file_not_found(conn):
    with pytest.raises(FileNotFoundError):
        ingest.ingest_path("/definitely/not/a/real/path.txt", conn)


def test_ingest_empty_file_produces_zero_chunks_without_crashing(tmp_path, conn):
    path = _write(tmp_path, "empty.txt", "")
    summary = ingest.ingest_path(path, conn)
    assert summary["documents_processed"] == 1
    assert summary["chunks_inserted"] == 0


def test_ingested_chunks_have_valid_section_reuse_and_tags(tmp_path, conn):
    path = _write(
        tmp_path,
        "grant.txt",
        "Significance\nThis broadly applicable framework generalizes across many settings and populations for future work.",
    )
    ingest.ingest_path(path, conn)
    chunks = store.get_all_chunks(conn)
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk["section_type"] in SECTION_TYPES
    assert chunk["reuse_tier"] in {"High", "Medium", "Low"}
    assert isinstance(chunk["tags"], list)
    assert len(chunk["tags"]) > 0


def test_ingest_without_ai_makes_no_ai_summary(tmp_path, conn):
    path = _write(tmp_path, "grant.txt", "Significance\nNo AI key is configured for this run.")
    ingest.ingest_path(path, conn, use_ai=False, api_key=None)
    chunk = store.get_all_chunks(conn)[0]
    assert chunk["ai_summary"] is None
