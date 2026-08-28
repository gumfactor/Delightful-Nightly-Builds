import os
import tempfile

import pytest

from src import storage


@pytest.fixture
def conn():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    connection = storage.connect(path)
    yield connection
    connection.close()
    os.remove(path)


def test_upsert_ticker_then_get(conn):
    storage.upsert_ticker(conn, "aapl", "0000320193", "Apple Inc.")
    row = storage.get_ticker(conn, "AAPL")
    assert row is not None
    assert row["cik"] == "0000320193"
    assert row["company_name"] == "Apple Inc."


def test_get_ticker_case_insensitive(conn):
    storage.upsert_ticker(conn, "MSFT", "0000789019", "Microsoft Corp.")
    assert storage.get_ticker(conn, "msft") is not None


def test_get_ticker_missing_returns_none(conn):
    assert storage.get_ticker(conn, "NOPE") is None


def test_upsert_ticker_updates_existing_row(conn):
    storage.upsert_ticker(conn, "AAPL", "0000320193", "Apple Inc.")
    storage.upsert_ticker(conn, "AAPL", "0000320193", "Apple Inc. (renamed)")
    rows = storage.list_tickers(conn)
    assert len(rows) == 1
    assert rows[0]["company_name"] == "Apple Inc. (renamed)"


def test_upsert_financials_inserts_rows(conn):
    rows = [
        {"fiscal_year": 2022, "revenue": 100, "net_income": 10, "operating_income": 12,
         "assets": 500, "liabilities": 200, "equity": 300, "cash": 50,
         "filed_date": "2023-01-01", "accn": "acc-1"},
        {"fiscal_year": 2023, "revenue": 110, "net_income": 12, "operating_income": 14,
         "assets": 520, "liabilities": 210, "equity": 310, "cash": 55,
         "filed_date": "2024-01-01", "accn": "acc-2"},
    ]
    count = storage.upsert_financials(conn, "0000320193", "AAPL", "Apple Inc.", rows)
    assert count == 2
    stored = storage.get_financials(conn, "AAPL")
    assert len(stored) == 2
    assert stored[0]["fiscal_year"] == 2022
    assert stored[1]["fiscal_year"] == 2023


def test_upsert_financials_is_idempotent_for_same_fiscal_year(conn):
    row_v1 = [{"fiscal_year": 2022, "revenue": 100, "net_income": 10, "operating_income": 12,
               "assets": 500, "liabilities": 200, "equity": 300, "cash": 50,
               "filed_date": "2023-01-01", "accn": "acc-1"}]
    row_v2 = [{"fiscal_year": 2022, "revenue": 150, "net_income": 15, "operating_income": 18,
               "assets": 550, "liabilities": 220, "equity": 330, "cash": 60,
               "filed_date": "2023-06-01", "accn": "acc-1-restated"}]
    storage.upsert_financials(conn, "0000320193", "AAPL", "Apple Inc.", row_v1)
    storage.upsert_financials(conn, "0000320193", "AAPL", "Apple Inc.", row_v2)
    stored = storage.get_financials(conn, "AAPL")
    assert len(stored) == 1
    assert stored[0]["revenue"] == 150
    assert stored[0]["accn"] == "acc-1-restated"


def test_get_financials_ordered_by_fiscal_year(conn):
    rows = [
        {"fiscal_year": 2023, "revenue": 1, "net_income": 1, "operating_income": 1,
         "assets": 1, "liabilities": 1, "equity": 1, "cash": 1, "filed_date": "d", "accn": "a"},
        {"fiscal_year": 2021, "revenue": 1, "net_income": 1, "operating_income": 1,
         "assets": 1, "liabilities": 1, "equity": 1, "cash": 1, "filed_date": "d", "accn": "a"},
        {"fiscal_year": 2022, "revenue": 1, "net_income": 1, "operating_income": 1,
         "assets": 1, "liabilities": 1, "equity": 1, "cash": 1, "filed_date": "d", "accn": "a"},
    ]
    storage.upsert_financials(conn, "CIK1", "ZZZ", "Zzz Corp", rows)
    stored = storage.get_financials(conn, "ZZZ")
    assert [r["fiscal_year"] for r in stored] == [2021, 2022, 2023]


def test_get_financials_missing_ticker_returns_empty_list(conn):
    assert storage.get_financials(conn, "NOPE") == []


def test_get_tracked_tickers(conn):
    rows = [{"fiscal_year": 2022, "revenue": 1, "net_income": 1, "operating_income": 1,
             "assets": 1, "liabilities": 1, "equity": 1, "cash": 1, "filed_date": "d", "accn": "a"}]
    storage.upsert_financials(conn, "CIK1", "AAA", "AAA Corp", rows)
    storage.upsert_financials(conn, "CIK2", "BBB", "BBB Corp", rows)
    assert storage.get_tracked_tickers(conn) == ["AAA", "BBB"]


def test_get_all_financials_spans_multiple_companies(conn):
    row = [{"fiscal_year": 2022, "revenue": 1, "net_income": 1, "operating_income": 1,
            "assets": 1, "liabilities": 1, "equity": 1, "cash": 1, "filed_date": "d", "accn": "a"}]
    storage.upsert_financials(conn, "CIK1", "AAA", "AAA Corp", row)
    storage.upsert_financials(conn, "CIK2", "BBB", "BBB Corp", row)
    all_rows = storage.get_all_financials(conn)
    assert {r["ticker"] for r in all_rows} == {"AAA", "BBB"}
