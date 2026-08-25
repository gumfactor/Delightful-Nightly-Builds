import pytest

from src import search, store


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = store.init_db(db_path)
    doc_id = store.upsert_document(connection, "/a.txt", "hash1")
    store.insert_chunk(
        connection, doc_id, 0, "Significance",
        "Stress reactivity shapes empathic accuracy across many settings.",
        8, "High", ["stress", "empathy"], None,
    )
    store.insert_chunk(
        connection, doc_id, 1, "Approach",
        "Participants complete a standard laboratory protocol.",
        5, "Medium", ["protocol"], None,
    )
    store.insert_chunk(
        connection, doc_id, 2, "Budget Justification",
        "Personnel costs total forty thousand dollars this year.",
        2, "Low", ["budget"], None,
    )
    yield connection
    connection.close()


def test_search_ranks_query_match_above_nonmatch(conn):
    results = search.search(conn, query="empathic accuracy")
    assert len(results) == 1
    assert "empathic" in results[0]["text"].lower()


def test_search_filters_by_section(conn):
    results = search.search(conn, query="", section="Approach")
    assert len(results) == 1
    assert results[0]["section_type"] == "Approach"


def test_search_filters_by_tag(conn):
    results = search.search(conn, query="", tag="budget")
    assert len(results) == 1
    assert "budget" in results[0]["tags"]


def test_search_filters_by_tag_case_insensitive(conn):
    results = search.search(conn, query="", tag="BUDGET")
    assert len(results) == 1


def test_search_filters_by_min_reuse(conn):
    results = search.search(conn, query="", min_reuse=5)
    scores = {r["reuse_score"] for r in results}
    assert scores == {8, 5}


def test_search_empty_query_returns_all_sorted_by_reuse_score(conn):
    results = search.search(conn, query="")
    scores = [r["reuse_score"] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert len(results) == 3


def test_search_no_results_for_nonsense_query(conn):
    results = search.search(conn, query="xylophone quicksand nebula")
    assert results == []


def test_search_combines_query_and_filters(conn):
    results = search.search(conn, query="protocol", section="Approach")
    assert len(results) == 1
    assert results[0]["section_type"] == "Approach"

    results = search.search(conn, query="protocol", section="Significance")
    assert results == []
