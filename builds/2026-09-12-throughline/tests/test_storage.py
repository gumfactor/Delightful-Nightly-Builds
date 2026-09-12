import pytest

from src import storage
from src.semantic_scholar import Paper


@pytest.fixture
def conn():
    connection = storage.connect(":memory:")
    yield connection
    connection.close()


def make_paper(paper_id="p1", title="Title", abstract="Abstract text", year=2020,
               venue="Venue", citation_count=10, external_url=None):
    return Paper(paper_id, title, abstract, year, venue, citation_count, external_url)


def test_set_and_get_author(conn):
    assert storage.get_author(conn) is None
    storage.set_author(conn, "auth1", "Jane Doe")
    row = storage.get_author(conn)
    assert row["author_id"] == "auth1"
    assert row["name"] == "Jane Doe"


def test_set_author_overwrites_single_row(conn):
    storage.set_author(conn, "auth1", "Jane Doe")
    storage.set_author(conn, "auth2", "Jane D. Doe")
    row = storage.get_author(conn)
    assert row["author_id"] == "auth2"
    count = conn.execute("SELECT COUNT(*) AS n FROM author").fetchone()["n"]
    assert count == 1


def test_upsert_papers_inserts_new_paper(conn):
    written = storage.upsert_papers(conn, [make_paper()])
    assert written == 1
    papers = storage.list_papers(conn)
    assert len(papers) == 1
    assert papers[0]["title"] == "Title"


def test_upsert_papers_updates_existing_without_duplicating(conn):
    storage.upsert_papers(conn, [make_paper(citation_count=10)])
    storage.upsert_papers(conn, [make_paper(citation_count=15)])
    papers = storage.list_papers(conn)
    assert len(papers) == 1
    assert papers[0]["citation_count"] == 15


def test_upsert_papers_appends_citation_snapshot_each_call(conn):
    storage.upsert_papers(conn, [make_paper(citation_count=10)])
    storage.upsert_papers(conn, [make_paper(citation_count=15)])
    snapshots = conn.execute(
        "SELECT citation_count FROM citation_snapshots ORDER BY id"
    ).fetchall()
    assert [row["citation_count"] for row in snapshots] == [10, 15]


def test_citation_growth_computes_delta(conn):
    storage.upsert_papers(conn, [make_paper(paper_id="p1", citation_count=10)])
    storage.upsert_papers(conn, [make_paper(paper_id="p1", citation_count=17)])
    growth = storage.citation_growth(conn)
    assert len(growth) == 1
    assert growth[0]["delta"] == 7
    assert growth[0]["first_count"] == 10
    assert growth[0]["latest_count"] == 17


def test_citation_growth_empty_when_no_snapshots(conn):
    assert storage.citation_growth(conn) == []


def test_citation_growth_sorted_by_delta_descending(conn):
    storage.upsert_papers(conn, [make_paper(paper_id="p1", citation_count=10)])
    storage.upsert_papers(conn, [make_paper(paper_id="p2", citation_count=5)])
    storage.upsert_papers(conn, [make_paper(paper_id="p1", citation_count=30)])
    storage.upsert_papers(conn, [make_paper(paper_id="p2", citation_count=6)])
    growth = storage.citation_growth(conn)
    assert growth[0]["paper_id"] == "p1"
    assert growth[0]["delta"] == 20
    assert growth[1]["paper_id"] == "p2"
    assert growth[1]["delta"] == 1


def test_replace_clusters_and_list_clusters(conn):
    storage.upsert_papers(conn, [make_paper(paper_id="p1"), make_paper(paper_id="p2", title="Other")])
    clusters = [{"label": "stress / cortisol", "keywords": ["stress", "cortisol"], "paper_ids": ["p1"]}]
    storage.replace_clusters(conn, clusters)
    result = storage.list_clusters(conn)
    assert len(result) == 1
    assert result[0]["label"] == "stress / cortisol"
    assert len(result[0]["papers"]) == 1
    assert result[0]["papers"][0]["paper_id"] == "p1"
    assert result[0]["narrative"] is None


def test_replace_clusters_drops_stale_clusters_and_narratives(conn):
    storage.upsert_papers(conn, [make_paper(paper_id="p1")])
    storage.replace_clusters(conn, [{"label": "old", "keywords": [], "paper_ids": ["p1"]}])
    old_cluster_id = storage.list_clusters(conn)[0]["id"]
    storage.set_narrative(conn, old_cluster_id, "Old narrative", "deterministic")

    storage.replace_clusters(conn, [{"label": "new", "keywords": [], "paper_ids": ["p1"]}])
    clusters = storage.list_clusters(conn)
    assert len(clusters) == 1
    assert clusters[0]["label"] == "new"
    assert clusters[0]["narrative"] is None


def test_set_narrative_stores_and_updates(conn):
    storage.upsert_papers(conn, [make_paper(paper_id="p1")])
    storage.replace_clusters(conn, [{"label": "a", "keywords": [], "paper_ids": ["p1"]}])
    cluster_id = storage.list_clusters(conn)[0]["id"]

    storage.set_narrative(conn, cluster_id, "First draft", "deterministic")
    storage.set_narrative(conn, cluster_id, "AI draft", "ai")

    clusters = storage.list_clusters(conn)
    assert clusters[0]["narrative"] == "AI draft"
    assert clusters[0]["narrative_source"] == "ai"
