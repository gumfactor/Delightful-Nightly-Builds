"""Tests for Investment Thesis Journal — all tests run without network calls."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import main as app
from main import ThesisStore, fetch_quote, format_date, format_market_cap


# ---------------------------------------------------------------------------
# ThesisStore — CRUD operations
# ---------------------------------------------------------------------------


@pytest.fixture
def store(tmp_path: Path) -> ThesisStore:
    """Isolated store backed by a temp file so tests don't touch real data."""
    return ThesisStore(path=tmp_path / "theses.json")


def test_add_creates_entry_with_correct_fields(store: ThesisStore) -> None:
    entry = store.add("NVDA", "Strong GPU moat in AI training")
    assert entry["id"] == 1
    assert entry["note"] == "Strong GPU moat in AI training"
    assert entry["price_at_note"] is None
    assert "date" in entry


def test_add_normalizes_ticker_to_uppercase(store: ThesisStore) -> None:
    store.add("nvda", "lowercase ticker")
    assert store.get("NVDA") != []


def test_add_with_price_records_price(store: ThesisStore) -> None:
    entry = store.add("MSFT", "Cloud dominance", price=420.50)
    assert entry["price_at_note"] == 420.50


def test_add_multiple_entries_same_ticker_increments_ids(store: ThesisStore) -> None:
    e1 = store.add("AAPL", "First note")
    e2 = store.add("AAPL", "Second note")
    assert e1["id"] == 1
    assert e2["id"] == 2
    assert len(store.get("AAPL")) == 2


def test_get_returns_empty_for_unknown_ticker(store: ThesisStore) -> None:
    assert store.get("ZZZZ") == []


def test_get_returns_all_notes_for_ticker(store: ThesisStore) -> None:
    store.add("GOOG", "AI cloud exposure")
    store.add("GOOG", "Follow-up note after earnings")
    entries = store.get("GOOG")
    assert len(entries) == 2
    assert entries[0]["note"] == "AI cloud exposure"
    assert entries[1]["note"] == "Follow-up note after earnings"


def test_list_tickers_returns_alphabetically_sorted(store: ThesisStore) -> None:
    store.add("TSLA", "EV bet")
    store.add("AAPL", "Consumer moat")
    store.add("NVDA", "GPU dominance")
    tickers = store.list_tickers()
    assert [t[0] for t in tickers] == ["AAPL", "NVDA", "TSLA"]


def test_list_tickers_includes_correct_note_counts(store: ThesisStore) -> None:
    store.add("AAPL", "Note one")
    store.add("AAPL", "Note two")
    store.add("MSFT", "Only note")
    tickers = store.list_tickers()
    counts = {t[0]: t[1] for t in tickers}
    assert counts["AAPL"] == 2
    assert counts["MSFT"] == 1


def test_list_tickers_empty_store(store: ThesisStore) -> None:
    assert store.list_tickers() == []


def test_search_finds_keyword_in_note(store: ThesisStore) -> None:
    store.add("NVDA", "GPU dominance in AI market")
    store.add("AAPL", "Consumer brand moat")
    results = store.search("AI")
    assert len(results) == 1
    assert results[0][0] == "NVDA"


def test_search_is_case_insensitive(store: ThesisStore) -> None:
    store.add("NVDA", "GPU Dominance")
    results = store.search("gpu dominance")
    assert len(results) == 1


def test_search_returns_empty_when_no_match(store: ThesisStore) -> None:
    store.add("AAPL", "Consumer brand moat")
    assert store.search("blockchain") == []


def test_search_matches_across_multiple_tickers(store: ThesisStore) -> None:
    store.add("NVDA", "Dominant moat in AI chips")
    store.add("AAPL", "Ecosystem moat in consumer hardware")
    store.add("TSLA", "EV growth story")
    results = store.search("moat")
    tickers_found = {r[0] for r in results}
    assert tickers_found == {"NVDA", "AAPL"}


def test_delete_removes_correct_entry_by_id(store: ThesisStore) -> None:
    store.add("META", "Social media moat")
    store.add("META", "AI pivot upside")
    assert store.delete("META", 1) is True
    remaining = store.get("META")
    assert len(remaining) == 1
    assert remaining[0]["id"] == 2


def test_delete_removes_ticker_when_last_entry_deleted(store: ThesisStore) -> None:
    store.add("SNOW", "Only note")
    store.delete("SNOW", 1)
    assert not any(t[0] == "SNOW" for t in store.list_tickers())


def test_delete_nonexistent_id_returns_false(store: ThesisStore) -> None:
    store.add("AMD", "CPU resurgence")
    assert store.delete("AMD", 99) is False


def test_delete_unknown_ticker_returns_false(store: ThesisStore) -> None:
    assert store.delete("ZZZZ", 1) is False


def test_data_persists_across_store_instances(tmp_path: Path) -> None:
    path = tmp_path / "theses.json"
    store1 = ThesisStore(path=path)
    store1.add("INTC", "Value turnaround play")

    store2 = ThesisStore(path=path)
    entries = store2.get("INTC")
    assert len(entries) == 1
    assert entries[0]["note"] == "Value turnaround play"


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def test_format_market_cap_trillions() -> None:
    assert format_market_cap(3_000_000_000_000) == "$3.0T"


def test_format_market_cap_billions() -> None:
    assert format_market_cap(500_000_000_000) == "$500.0B"


def test_format_market_cap_millions() -> None:
    assert format_market_cap(750_000_000) == "$750.0M"


def test_format_market_cap_none() -> None:
    assert format_market_cap(None) == "N/A"


def test_format_date_parses_iso_string() -> None:
    result = format_date("2026-06-14T02:30:00+00:00")
    assert result == "2026-06-14 02:30 UTC"


def test_format_date_returns_original_on_invalid_input() -> None:
    bad = "not-a-date"
    assert format_date(bad) == bad


# ---------------------------------------------------------------------------
# fetch_quote — graceful degradation
# ---------------------------------------------------------------------------


def test_fetch_quote_returns_none_when_yfinance_unavailable() -> None:
    # Simulate yfinance not installed
    with patch.object(app, "_YFINANCE_AVAILABLE", False):
        result = fetch_quote("NVDA")
    assert result is None


def test_fetch_quote_returns_none_on_exception() -> None:
    mock_yf = MagicMock()
    mock_yf.Ticker.side_effect = RuntimeError("network error")
    with patch.object(app, "_YFINANCE_AVAILABLE", True), patch.object(app, "yf", mock_yf):
        result = fetch_quote("NVDA")
    assert result is None


def test_fetch_quote_returns_price_data_on_success() -> None:
    mock_info = {
        "currentPrice": 1102.50,
        "regularMarketChangePercent": 2.35,
        "marketCap": 2_700_000_000_000,
        "currency": "USD",
    }
    mock_ticker = MagicMock()
    mock_ticker.info = mock_info
    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = mock_ticker

    with patch.object(app, "_YFINANCE_AVAILABLE", True), patch.object(app, "yf", mock_yf):
        result = fetch_quote("NVDA")

    assert result is not None
    assert result["price"] == 1102.50
    assert result["change_pct"] == 2.35
    assert result["market_cap"] == 2_700_000_000_000
    assert result["currency"] == "USD"


def test_fetch_quote_returns_none_when_price_missing() -> None:
    mock_info = {"marketCap": 1_000_000_000}  # no price fields
    mock_ticker = MagicMock()
    mock_ticker.info = mock_info
    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = mock_ticker

    with patch.object(app, "_YFINANCE_AVAILABLE", True), patch.object(app, "yf", mock_yf):
        result = fetch_quote("FAKE")

    assert result is None
