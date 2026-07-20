import os

import pytest

import storage


@pytest.fixture
def conn(tmp_path):
    db_path = os.path.join(tmp_path, "test_canfile.db")
    connection = storage.get_connection(db_path)
    yield connection
    connection.close()


def _insert(conn, name, verdict="canadian", confidence="high"):
    return storage.insert_card(
        conn,
        company_name=name,
        qid="Q1524829",
        wikidata_facts={"country_labels": ["Canada"]},
        wikipedia_summary="A test summary.",
        assessment_text=f"{name} is likely Canadian-owned.",
        confidence=confidence,
        verdict=verdict,
        source_urls=["https://www.wikidata.org/wiki/Q1524829"],
    )


def test_insert_card_starts_at_version_one(conn):
    card = _insert(conn, "Tim Hortons")
    assert card["version"] == 1
    assert card["company_name"] == "Tim Hortons"


def test_repeat_insert_creates_new_version(conn):
    _insert(conn, "Tim Hortons")
    second = _insert(conn, "Tim Hortons", verdict="uncertain", confidence="medium")
    assert second["version"] == 2
    assert second["verdict"] == "uncertain"


def test_get_history_returns_all_versions_in_order(conn):
    _insert(conn, "Tim Hortons")
    _insert(conn, "Tim Hortons")
    _insert(conn, "Tim Hortons")
    history = storage.get_history(conn, "Tim Hortons")
    assert [card["version"] for card in history] == [1, 2, 3]


def test_list_latest_returns_only_newest_version_per_company(conn):
    _insert(conn, "Tim Hortons")
    _insert(conn, "Tim Hortons")
    _insert(conn, "Loblaws")
    latest = storage.list_latest(conn)
    by_name = {card["company_name"]: card for card in latest}
    assert len(latest) == 2
    assert by_name["Tim Hortons"]["version"] == 2
    assert by_name["Loblaws"]["version"] == 1


def test_search_matches_company_name(conn):
    _insert(conn, "Tim Hortons")
    _insert(conn, "Loblaws")
    results = storage.search(conn, "hortons")
    assert len(results) == 1
    assert results[0]["company_name"] == "Tim Hortons"


def test_search_matches_assessment_text(conn):
    _insert(conn, "Tim Hortons")
    results = storage.search(conn, "Canadian-owned")
    assert len(results) == 1


def test_search_no_match_returns_empty_list(conn):
    _insert(conn, "Tim Hortons")
    results = storage.search(conn, "nonexistent term xyz")
    assert results == []


def test_wikidata_facts_round_trip_through_json(conn):
    facts = {"country_labels": ["Canada"], "headquarters_labels": ["Oakville"]}
    card = storage.insert_card(
        conn,
        company_name="Tim Hortons",
        qid="Q1524829",
        wikidata_facts=facts,
        wikipedia_summary=None,
        assessment_text="text",
        confidence="high",
        verdict="canadian",
        source_urls=[],
    )
    assert card["wikidata_facts"] == facts
    assert card["wikipedia_summary"] is None
