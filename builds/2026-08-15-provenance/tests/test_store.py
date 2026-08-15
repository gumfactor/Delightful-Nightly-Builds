import pytest

from src import store


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test_provenance.db")
    connection = store.connect(db_path)
    yield connection
    connection.close()


def test_normalize_key_collapses_whitespace_and_case():
    assert store.normalize_key("  Acme Inc.  ") == store.normalize_key("acme inc.")
    assert store.normalize_key("Acme   Inc.") == store.normalize_key("Acme Inc.")


def test_save_and_get_latest_round_trip(conn):
    store.save_resolution(
        conn,
        business_name="Acme Ltd.",
        website="https://acme.example",
        wikidata_qid="Q1",
        verdict="canadian",
        confidence=0.95,
        evidence="Registered country is Canada.",
        ai_note=None,
        resolved_at="2026-08-15T00:00:00+00:00",
    )
    row = store.get_latest(conn, "Acme Ltd.")
    assert row is not None
    assert row["verdict"] == "canadian"
    assert row["wikidata_qid"] == "Q1"
    assert row["confidence"] == 0.95


def test_get_latest_returns_none_when_never_resolved(conn):
    assert store.get_latest(conn, "Never Seen Before Co") is None


def test_get_latest_matches_regardless_of_name_normalization(conn):
    store.save_resolution(
        conn,
        business_name="Acme Ltd.",
        website=None,
        wikidata_qid="Q1",
        verdict="canadian",
        confidence=0.9,
        evidence="evidence",
        ai_note=None,
        resolved_at="2026-08-15T00:00:00+00:00",
    )
    row = store.get_latest(conn, "  acme LTD.  ")
    assert row is not None
    assert row["business_name"] == "Acme Ltd."


def test_second_save_appends_a_new_version_and_preserves_history(conn):
    store.save_resolution(
        conn,
        business_name="Acme Ltd.",
        website=None,
        wikidata_qid="Q1",
        verdict="uncertain",
        confidence=0.5,
        evidence="first pass",
        ai_note=None,
        resolved_at="2026-08-15T00:00:00+00:00",
    )
    store.save_resolution(
        conn,
        business_name="Acme Ltd.",
        website=None,
        wikidata_qid="Q1",
        verdict="canadian",
        confidence=0.95,
        evidence="second pass, refreshed",
        ai_note=None,
        resolved_at="2026-08-15T01:00:00+00:00",
    )
    history = store.get_history(conn, "Acme Ltd.")
    assert len(history) == 2
    assert history[0]["evidence"] == "first pass"
    assert history[1]["evidence"] == "second pass, refreshed"

    latest = store.get_latest(conn, "Acme Ltd.")
    assert latest["verdict"] == "canadian"
    assert latest["evidence"] == "second pass, refreshed"


def test_get_history_is_empty_list_for_unknown_business(conn):
    assert store.get_history(conn, "Nobody Has Heard Of This Co") == []
