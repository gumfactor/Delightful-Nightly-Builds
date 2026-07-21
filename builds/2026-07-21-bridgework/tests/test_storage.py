import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import storage


def make_record(**overrides):
    record = {
        "concept_id": "hpa_axis_response",
        "concept_name": "The HPA Axis Stress Response",
        "subdomain": "stress",
        "domain_id": "kitchen",
        "domain_name": "The Kitchen Stove",
        "audience": "public_talk",
        "hook": "A hook.",
        "analogy": "An analogy paragraph.",
        "caveat": "A caveat.",
        "source": "template",
        "novelty_score": 1.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    record.update(overrides)
    return record


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = storage.connect(db_path)
    yield connection
    connection.close()


def test_connect_creates_schema_on_fresh_db(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = {row["name"] for row in rows}
    assert "analogies" in table_names


def test_insert_and_get_round_trip(conn):
    entry_id = storage.insert_analogy(conn, make_record())
    fetched = storage.get_analogy(conn, entry_id)
    assert fetched is not None
    assert fetched["concept_id"] == "hpa_axis_response"
    assert fetched["hook"] == "A hook."


def test_get_analogy_returns_none_for_missing_id(conn):
    assert storage.get_analogy(conn, 9999) is None


def test_regenerating_same_triple_never_overwrites(conn):
    id1 = storage.insert_analogy(conn, make_record(hook="First version"))
    id2 = storage.insert_analogy(conn, make_record(hook="Second version"))
    assert id1 != id2
    entries = storage.list_analogies(conn, concept_id="hpa_axis_response", domain_id="kitchen", audience="public_talk")
    assert len(entries) == 2
    hooks = {e["hook"] for e in entries}
    assert hooks == {"First version", "Second version"}


def test_list_analogies_filters_by_concept(conn):
    storage.insert_analogy(conn, make_record(concept_id="allostatic_load", concept_name="Allostatic Load"))
    storage.insert_analogy(conn, make_record(concept_id="hpa_axis_response"))
    results = storage.list_analogies(conn, concept_id="allostatic_load")
    assert len(results) == 1
    assert results[0]["concept_id"] == "allostatic_load"


def test_list_analogies_filters_by_domain(conn):
    storage.insert_analogy(conn, make_record(domain_id="garden", domain_name="A Garden Over a Season"))
    storage.insert_analogy(conn, make_record(domain_id="kitchen"))
    results = storage.list_analogies(conn, domain_id="garden")
    assert len(results) == 1
    assert results[0]["domain_id"] == "garden"


def test_list_analogies_filters_by_audience(conn):
    storage.insert_analogy(conn, make_record(audience="book_chapter"))
    storage.insert_analogy(conn, make_record(audience="public_talk"))
    results = storage.list_analogies(conn, audience="book_chapter")
    assert len(results) == 1
    assert results[0]["audience"] == "book_chapter"


def test_list_analogies_search_matches_hook_and_analogy(conn):
    storage.insert_analogy(conn, make_record(hook="A storm is brewing", analogy="unrelated"))
    storage.insert_analogy(conn, make_record(hook="unrelated", analogy="nothing to see"))
    results = storage.list_analogies(conn, search="storm")
    assert len(results) == 1


def test_list_analogies_respects_limit(conn):
    for i in range(5):
        storage.insert_analogy(conn, make_record(hook=f"hook {i}"))
    results = storage.list_analogies(conn, limit=2)
    assert len(results) == 2


def test_count_triple_counts_correctly(conn):
    storage.insert_analogy(conn, make_record())
    storage.insert_analogy(conn, make_record())
    storage.insert_analogy(conn, make_record(domain_id="garden"))
    assert storage.count_triple(conn, "hpa_axis_response", "kitchen", "public_talk") == 2
    assert storage.count_triple(conn, "hpa_axis_response", "garden", "public_talk") == 1
    assert storage.count_triple(conn, "hpa_axis_response", "thermostat", "public_talk") == 0


def test_usage_counts_aggregates_by_triple(conn):
    storage.insert_analogy(conn, make_record())
    storage.insert_analogy(conn, make_record())
    counts = storage.usage_counts(conn)
    assert counts[("hpa_axis_response", "kitchen", "public_talk")] == 2


def test_all_analogy_texts_returns_analogy_field_only(conn):
    storage.insert_analogy(conn, make_record(analogy="text one"))
    storage.insert_analogy(conn, make_record(analogy="text two"))
    texts = storage.all_analogy_texts(conn)
    assert set(texts) == {"text one", "text two"}


def test_stats_reports_totals_and_breakdowns(conn):
    storage.insert_analogy(conn, make_record(subdomain="stress", source="template"))
    storage.insert_analogy(conn, make_record(subdomain="empathy", source="ai", concept_id="empathy_fatigue", domain_id="garden"))
    data = storage.stats(conn)
    assert data["total"] == 2
    assert data["distinct_triples"] == 2
    assert data["by_subdomain"]["stress"] == 1
    assert data["by_subdomain"]["empathy"] == 1
    assert data["by_source"]["template"] == 1
    assert data["by_source"]["ai"] == 1
