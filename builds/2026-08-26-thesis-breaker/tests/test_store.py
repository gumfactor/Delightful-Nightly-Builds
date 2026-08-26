import tempfile
import os

import pytest

from src import store


@pytest.fixture
def conn():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    connection = store.connect(path)
    yield connection
    connection.close()
    os.remove(path)


def _insert(conn, ticker="AAPL", ts="2026-08-26T08:00:00+00:00", score=42):
    return store.insert_check(
        conn, ticker=ticker, thesis_text="Bullish thesis text.", run_timestamp=ts,
        fetched_data={"trailing_pe": 30.0}, triggered=[{"key": "valuation_stretch", "fired": True}],
        persona_scores={"value_skeptic": 60}, overall_score=score, ai_polished=False,
    )


def test_insert_and_get_check_round_trips(conn):
    check_id = _insert(conn)
    row = store.get_check(conn, check_id)
    assert row.ticker == "AAPL"
    assert row.overall_score == 42
    assert row.fetched_data == {"trailing_pe": 30.0}
    assert row.persona_scores == {"value_skeptic": 60}


def test_two_checks_for_same_ticker_produce_two_distinct_rows(conn):
    id1 = _insert(conn, ts="2026-08-26T08:00:00+00:00", score=42)
    id2 = _insert(conn, ts="2026-08-27T08:00:00+00:00", score=55)
    assert id1 != id2
    history = store.history_for_ticker(conn, "AAPL")
    assert len(history) == 2
    assert [row.overall_score for row in history] == [42, 55]


def test_history_is_scoped_to_ticker(conn):
    _insert(conn, ticker="AAPL")
    _insert(conn, ticker="MSFT")
    assert len(store.history_for_ticker(conn, "AAPL")) == 1
    assert len(store.history_for_ticker(conn, "MSFT")) == 1


def test_history_returns_empty_list_for_unknown_ticker(conn):
    assert store.history_for_ticker(conn, "ZZZZ") == []


def test_get_check_returns_none_for_unknown_id(conn):
    assert store.get_check(conn, 9999) is None


def test_list_all_returns_every_row_in_insertion_order(conn):
    _insert(conn, ticker="AAPL", ts="2026-08-26T08:00:00+00:00")
    _insert(conn, ticker="MSFT", ts="2026-08-26T09:00:00+00:00")
    rows = store.list_all(conn)
    assert [row.ticker for row in rows] == ["AAPL", "MSFT"]
