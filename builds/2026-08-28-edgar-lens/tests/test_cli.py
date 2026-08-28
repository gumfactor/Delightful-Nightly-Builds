import json
import os
import tempfile

import pytest

from src import cli, storage


class FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


TICKERS_PAYLOAD = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
}

COMPANYFACTS_PAYLOAD = {
    "cik": 320193,
    "entityName": "Apple Inc.",
    "facts": {
        "us-gaap": {
            "Revenues": {
                "units": {"USD": [
                    {"start": "2022-01-01", "end": "2022-12-31", "val": 1000, "accn": "a1",
                     "fy": 2022, "fp": "FY", "form": "10-K", "filed": "2023-01-01"},
                ]}
            },
            "NetIncomeLoss": {
                "units": {"USD": [
                    {"start": "2022-01-01", "end": "2022-12-31", "val": 100, "accn": "a1",
                     "fy": 2022, "fp": "FY", "form": "10-K", "filed": "2023-01-01"},
                ]}
            },
        }
    },
}


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


def fake_urlopen_router(routes):
    def fake_urlopen(request, timeout=None):
        for fragment, payload in routes.items():
            if fragment in request.full_url:
                return FakeResponse(payload)
        raise AssertionError(f"Unexpected URL requested: {request.full_url}")

    return fake_urlopen


def test_sync_resolves_ticker_and_stores_financials(db_path, capsys):
    parser = cli.build_parser()
    args = parser.parse_args(["--db", db_path, "sync", "--tickers", "AAPL"])
    urlopen = fake_urlopen_router({
        "company_tickers.json": TICKERS_PAYLOAD,
        "companyfacts": COMPANYFACTS_PAYLOAD,
    })
    result = cli.cmd_sync(args, urlopen_func=urlopen, sleep_func=lambda d: None)
    assert result == 0

    conn = storage.connect(db_path)
    financials = storage.get_financials(conn, "AAPL")
    conn.close()
    assert len(financials) == 1
    assert financials[0]["revenue"] == 1000


def test_sync_is_idempotent_on_rerun(db_path):
    parser = cli.build_parser()
    args = parser.parse_args(["--db", db_path, "sync", "--tickers", "AAPL"])
    urlopen = fake_urlopen_router({
        "company_tickers.json": TICKERS_PAYLOAD,
        "companyfacts": COMPANYFACTS_PAYLOAD,
    })
    cli.cmd_sync(args, urlopen_func=urlopen, sleep_func=lambda d: None)
    cli.cmd_sync(args, urlopen_func=urlopen, sleep_func=lambda d: None)

    conn = storage.connect(db_path)
    financials = storage.get_financials(conn, "AAPL")
    conn.close()
    assert len(financials) == 1


def test_sync_unknown_ticker_does_not_crash(db_path, capsys):
    parser = cli.build_parser()
    args = parser.parse_args(["--db", db_path, "sync", "--tickers", "ZZZZNOTREAL"])
    urlopen = fake_urlopen_router({"company_tickers.json": TICKERS_PAYLOAD})
    result = cli.cmd_sync(args, urlopen_func=urlopen, sleep_func=lambda d: None)
    assert result == 0
    captured = capsys.readouterr()
    assert "not found" in captured.out.lower()


def test_sync_no_tickers_returns_error(db_path):
    parser = cli.build_parser()
    args = parser.parse_args(["--db", db_path, "sync", "--tickers", ""])
    result = cli.cmd_sync(args)
    assert result == 1


def test_list_empty_database(db_path, capsys):
    parser = cli.build_parser()
    args = parser.parse_args(["--db", db_path, "list"])
    result = cli.cmd_list(args)
    assert result == 0
    assert "No tickers tracked" in capsys.readouterr().out


def test_show_missing_ticker_returns_error(db_path):
    parser = cli.build_parser()
    args = parser.parse_args(["--db", db_path, "show", "AAPL"])
    result = cli.cmd_show(args)
    assert result == 1


def test_show_prints_yearly_table(db_path, capsys):
    conn = storage.connect(db_path)
    storage.upsert_ticker(conn, "AAPL", "0000320193", "Apple Inc.")
    storage.upsert_financials(conn, "0000320193", "AAPL", "Apple Inc.", [
        {"fiscal_year": 2022, "revenue": 1000, "net_income": 100, "operating_income": 120,
         "assets": 500, "liabilities": 200, "equity": 300, "cash": 50,
         "filed_date": "2023-01-01", "accn": "a1"},
    ])
    conn.close()

    parser = cli.build_parser()
    args = parser.parse_args(["--db", db_path, "show", "AAPL"])
    result = cli.cmd_show(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "AAPL" in out
    assert "2022" in out


def test_flags_reports_anomalies_across_tickers(db_path, capsys):
    conn = storage.connect(db_path)
    storage.upsert_ticker(conn, "AAPL", "0000320193", "Apple Inc.")
    storage.upsert_financials(conn, "0000320193", "AAPL", "Apple Inc.", [
        {"fiscal_year": 2021, "revenue": 1000, "net_income": 100, "operating_income": 120,
         "assets": 500, "liabilities": 200, "equity": 300, "cash": 50,
         "filed_date": "2022-01-01", "accn": "a1"},
        {"fiscal_year": 2022, "revenue": 800, "net_income": 50, "operating_income": 60,
         "assets": 480, "liabilities": 220, "equity": 290, "cash": 40,
         "filed_date": "2023-01-01", "accn": "a2"},
    ])
    conn.close()

    parser = cli.build_parser()
    args = parser.parse_args(["--db", db_path, "flags"])
    result = cli.cmd_flags(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "revenue_decline" in out


def test_render_produces_dashboard_file_without_ai(db_path):
    conn = storage.connect(db_path)
    storage.upsert_ticker(conn, "AAPL", "0000320193", "Apple Inc.")
    storage.upsert_financials(conn, "0000320193", "AAPL", "Apple Inc.", [
        {"fiscal_year": 2021, "revenue": 1000, "net_income": 100, "operating_income": 120,
         "assets": 500, "liabilities": 200, "equity": 300, "cash": 50,
         "filed_date": "2022-01-01", "accn": "a1"},
        {"fiscal_year": 2022, "revenue": 800, "net_income": 50, "operating_income": 60,
         "assets": 480, "liabilities": 220, "equity": 290, "cash": 40,
         "filed_date": "2023-01-01", "accn": "a2"},
    ])
    conn.close()

    fd, out_path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        parser = cli.build_parser()
        args = parser.parse_args(["--db", db_path, "render", "--out", out_path])

        def failing_urlopen(request, timeout=None):
            raise AssertionError("render without --ai must never call the network")

        result = cli.cmd_render(args, urlopen_func=failing_urlopen)
        assert result == 0
        with open(out_path, encoding="utf-8") as f:
            html = f.read()
        assert "AAPL" in html
        assert "revenue_decline" in html
    finally:
        os.remove(out_path)


def test_build_companies_payload_without_ai_uses_deterministic_narrative(db_path):
    conn = storage.connect(db_path)
    storage.upsert_ticker(conn, "AAPL", "0000320193", "Apple Inc.")
    storage.upsert_financials(conn, "0000320193", "AAPL", "Apple Inc.", [
        {"fiscal_year": 2021, "revenue": 1000, "net_income": 100, "operating_income": 120,
         "assets": 500, "liabilities": 200, "equity": 300, "cash": 50,
         "filed_date": "2022-01-01", "accn": "a1"},
        {"fiscal_year": 2022, "revenue": 800, "net_income": 50, "operating_income": 60,
         "assets": 480, "liabilities": 220, "equity": 290, "cash": 40,
         "filed_date": "2023-01-01", "accn": "a2"},
    ])
    companies = cli.build_companies_payload(conn, use_ai=False)
    conn.close()
    assert companies[0]["anomalies"][0]["narrative"].startswith("AAPL FY2022")
