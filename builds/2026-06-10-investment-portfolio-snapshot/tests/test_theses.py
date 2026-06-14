"""Unit tests for src/theses.py — ThesisStore CRUD and persistence."""

import sys
import tempfile
import json
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.theses import ThesisStore


@pytest.fixture
def store(tmp_path: Path) -> ThesisStore:
    return ThesisStore(tmp_path / "theses.json")


def test_add_creates_entry(store: ThesisStore) -> None:
    entry = store.add("AAPL", "Strong moat.")
    assert entry["id"] == 1
    assert entry["note"] == "Strong moat."
    assert entry["price_at_note"] is None
    assert "date" in entry


def test_add_records_price(store: ThesisStore) -> None:
    entry = store.add("NVDA", "AI play.", price=850.0)
    assert entry["price_at_note"] == 850.0


def test_add_multiple_increments_ids(store: ThesisStore) -> None:
    e1 = store.add("AAPL", "First note.")
    e2 = store.add("AAPL", "Second note.")
    assert e1["id"] == 1
    assert e2["id"] == 2


def test_add_different_tickers_independent_ids(store: ThesisStore) -> None:
    e1 = store.add("AAPL", "Apple note.")
    e2 = store.add("MSFT", "Microsoft note.")
    assert e1["id"] == 1
    assert e2["id"] == 1


def test_get_returns_entries_in_order(store: ThesisStore) -> None:
    store.add("AAPL", "First.")
    store.add("AAPL", "Second.")
    entries = store.get("AAPL")
    assert len(entries) == 2
    assert entries[0]["note"] == "First."
    assert entries[1]["note"] == "Second."


def test_get_unknown_ticker_returns_empty(store: ThesisStore) -> None:
    assert store.get("UNKNOWN") == []


def test_get_latest_returns_most_recent(store: ThesisStore) -> None:
    store.add("AAPL", "Older note.")
    store.add("AAPL", "Newer note.")
    latest = store.get_latest("AAPL")
    assert latest is not None
    assert latest["note"] == "Newer note."


def test_get_latest_no_entries_returns_none(store: ThesisStore) -> None:
    assert store.get_latest("NOPE") is None


def test_list_tickers_sorted_alphabetically(store: ThesisStore) -> None:
    store.add("MSFT", "Microsoft.")
    store.add("AAPL", "Apple.")
    store.add("NVDA", "Nvidia.")
    tickers = store.list_tickers()
    symbols = [t[0] for t in tickers]
    assert symbols == ["AAPL", "MSFT", "NVDA"]


def test_list_tickers_returns_correct_counts(store: ThesisStore) -> None:
    store.add("AAPL", "Note one.")
    store.add("AAPL", "Note two.")
    store.add("MSFT", "Just one.")
    tickers = {t[0]: t[1] for t in store.list_tickers()}
    assert tickers["AAPL"] == 2
    assert tickers["MSFT"] == 1


def test_search_finds_matching_note(store: ThesisStore) -> None:
    store.add("NVDA", "Strong GPU moat in AI training.")
    results = store.search("GPU moat")
    assert len(results) == 1
    assert results[0][0] == "NVDA"


def test_search_is_case_insensitive(store: ThesisStore) -> None:
    store.add("AAPL", "Great ecosystem play.")
    assert len(store.search("ECOSYSTEM")) == 1
    assert len(store.search("ecosystem")) == 1


def test_search_no_match_returns_empty(store: ThesisStore) -> None:
    store.add("AAPL", "Strong moat.")
    assert store.search("quantum computing") == []


def test_delete_removes_entry(store: ThesisStore) -> None:
    entry = store.add("AAPL", "To be deleted.")
    removed = store.delete("AAPL", entry["id"])
    assert removed is True
    assert store.get("AAPL") == []


def test_delete_nonexistent_id_returns_false(store: ThesisStore) -> None:
    store.add("AAPL", "Existing note.")
    assert store.delete("AAPL", 999) is False


def test_delete_removes_ticker_when_last_note_gone(store: ThesisStore) -> None:
    store.add("AAPL", "Only note.")
    store.delete("AAPL", 1)
    assert store.list_tickers() == []


def test_persistence_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "theses.json"
    s1 = ThesisStore(path)
    s1.add("TSLA", "Long-term bet.")

    s2 = ThesisStore(path)
    entries = s2.get("TSLA")
    assert len(entries) == 1
    assert entries[0]["note"] == "Long-term bet."


def test_all_data_returns_copy(store: ThesisStore) -> None:
    store.add("AAPL", "Some note.")
    data = store.all_data()
    data["AAPL"] = []  # mutate the copy
    assert len(store.get("AAPL")) == 1  # original unchanged
