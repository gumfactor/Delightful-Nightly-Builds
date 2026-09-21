import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import store  # noqa: E402


def make_repo(id_, full_name, tag="Other", starred_at="2026-09-01T00:00:00Z",
              language="Python", topics=None, description="A repo."):
    return {
        "id": id_,
        "full_name": full_name,
        "description": description,
        "html_url": f"https://github.com/{full_name}",
        "language": language,
        "topics": topics or [],
        "stargazers_count": 10,
        "starred_at": starred_at,
        "tag": tag,
        "note": description or "no note",
        "source": "rule",
        "ingested_at": "2026-09-21T00:00:00Z",
    }


@pytest.fixture
def conn():
    connection = store.connect(":memory:")
    yield connection
    connection.close()


def test_empty_db_has_zero_repos(conn):
    assert store.count_repos(conn) == 0
    assert store.latest_starred_at(conn) is None
    assert store.stats(conn)["total"] == 0


def test_upsert_and_count(conn):
    store.upsert_repo(conn, make_repo(1, "a/b"))
    store.upsert_repo(conn, make_repo(2, "c/d"))
    assert store.count_repos(conn) == 2


def test_upsert_dedups_by_id(conn):
    store.upsert_repo(conn, make_repo(1, "a/b", description="first"))
    store.upsert_repo(conn, make_repo(1, "a/b", description="second"))
    assert store.count_repos(conn) == 1
    results = store.list_repos(conn)
    assert results[0]["description"] == "second"


def test_latest_starred_at_tracks_max(conn):
    store.upsert_repo(conn, make_repo(1, "a/b", starred_at="2026-09-01T00:00:00Z"))
    store.upsert_repo(conn, make_repo(2, "c/d", starred_at="2026-09-10T00:00:00Z"))
    assert store.latest_starred_at(conn) == "2026-09-10T00:00:00Z"


def test_search_by_query_matches_description(conn):
    store.upsert_repo(conn, make_repo(1, "acme/llm-toolkit", description="LLM agent toolkit"))
    store.upsert_repo(conn, make_repo(2, "other/thing", description="unrelated"))
    results = store.search_repos(conn, query="llm")
    assert len(results) == 1
    assert results[0]["full_name"] == "acme/llm-toolkit"


def test_search_by_tag_filter(conn):
    store.upsert_repo(conn, make_repo(1, "a/b", tag="AI/ML"))
    store.upsert_repo(conn, make_repo(2, "c/d", tag="Web & Frontend"))
    results = store.search_repos(conn, tag="AI/ML")
    assert len(results) == 1
    assert results[0]["full_name"] == "a/b"


def test_search_by_language_filter(conn):
    store.upsert_repo(conn, make_repo(1, "a/b", language="Python"))
    store.upsert_repo(conn, make_repo(2, "c/d", language="Go"))
    results = store.search_repos(conn, language="Go")
    assert len(results) == 1
    assert results[0]["full_name"] == "c/d"


def test_search_topics_are_json_decoded(conn):
    store.upsert_repo(conn, make_repo(1, "a/b", topics=["llm", "agent"]))
    results = store.list_repos(conn)
    assert results[0]["topics"] == ["llm", "agent"]


def test_search_query_does_not_allow_sql_injection(conn):
    store.upsert_repo(conn, make_repo(1, "a/b"))
    # A classic injection payload should simply match nothing, not error
    # or drop the table -- proving the query is parameterized.
    results = store.search_repos(conn, query="'; DROP TABLE repos; --")
    assert results == []
    assert store.count_repos(conn) == 1


def test_stats_aggregates_by_tag_and_language(conn):
    store.upsert_repo(conn, make_repo(1, "a/b", tag="AI/ML", language="Python"))
    store.upsert_repo(conn, make_repo(2, "c/d", tag="AI/ML", language="Python"))
    store.upsert_repo(conn, make_repo(3, "e/f", tag="Web & Frontend", language="TypeScript"))
    s = store.stats(conn)
    assert s["total"] == 3
    assert s["by_tag"]["AI/ML"] == 2
    assert s["by_tag"]["Web & Frontend"] == 1
    assert s["by_language"]["Python"] == 2


def test_stats_language_none_bucketed_as_unknown(conn):
    store.upsert_repo(conn, make_repo(1, "a/b", language=None))
    s = store.stats(conn)
    assert s["by_language"]["Unknown"] == 1
