"""fetch.py is exercised only against fake, in-memory objects shaped like
yfinance's real return types -- no network call is made in any test.
"""
from src.fetch import fetch_ticker_data


class FakeSeries:
    """Mimics the slice of pandas.Series behavior fetch.py relies on."""
    def __init__(self, values):
        self._values = values

    def tolist(self):
        return self._values


class FakeStatement:
    """Mimics the slice of a pandas DataFrame (quarterly financials) that
    fetch.py reads: `.index` and `.loc[row_name]`.
    """
    def __init__(self, rows: dict):
        self._rows = rows

    @property
    def index(self):
        return list(self._rows.keys())

    @property
    def loc(self):
        return self

    def __getitem__(self, key):
        return FakeSeries(self._rows[key])


class FakeInsiderTable:
    def __init__(self, records):
        self._records = records

    def to_dict(self, orient):
        assert orient == "records"
        return self._records


class FakeTicker:
    def __init__(self, info=None, quarterly_income_stmt=None, insider_transactions=None):
        self.info = info or {}
        self.quarterly_income_stmt = quarterly_income_stmt
        self.insider_transactions = insider_transactions


def factory_for(fake_ticker: FakeTicker):
    return lambda ticker: fake_ticker


def test_fetch_reads_valuation_fields_from_info():
    fake = FakeTicker(info={
        "sector": "Technology", "trailingPE": 30.5, "forwardPE": 25.0,
        "priceToSalesTrailing12Months": 6.0, "debtToEquity": 80.0,
    })
    data = fetch_ticker_data("aapl", factory_for(fake))
    assert data["ticker"] == "AAPL"
    assert data["sector"] == "Technology"
    assert data["trailing_pe"] == 30.5
    assert data["debt_to_equity"] == 80.0


def test_fetch_returns_none_for_missing_info_fields():
    fake = FakeTicker(info={"sector": "Energy"})
    data = fetch_ticker_data("XOM", factory_for(fake))
    assert data["trailing_pe"] is None
    assert data["debt_to_equity"] is None


def test_fetch_computes_yoy_growth_from_five_quarters_of_revenue():
    # most-recent-first: Q4 100, Q3 95, Q2 90, Q1 85, Q4-1yr 80
    stmt = FakeStatement({"Total Revenue": [100.0, 95.0, 90.0, 85.0, 80.0]})
    fake = FakeTicker(info={}, quarterly_income_stmt=stmt)
    data = fetch_ticker_data("AAPL", factory_for(fake))
    assert data["quarterly_revenue_yoy_growth"] == [0.25]


def test_fetch_yoy_growth_none_with_fewer_than_five_quarters():
    stmt = FakeStatement({"Total Revenue": [100.0, 95.0]})
    fake = FakeTicker(info={}, quarterly_income_stmt=stmt)
    data = fetch_ticker_data("AAPL", factory_for(fake))
    assert data["quarterly_revenue_yoy_growth"] is None


def test_fetch_computes_operating_margin_from_revenue_and_operating_income():
    stmt = FakeStatement({
        "Total Revenue": [100.0, 95.0, 90.0, 85.0, 80.0],
        "Operating Income": [30.0, 28.0, 27.0, 26.0, 24.0],
    })
    fake = FakeTicker(info={}, quarterly_income_stmt=stmt)
    data = fetch_ticker_data("AAPL", factory_for(fake))
    assert data["quarterly_operating_margin"][0] == 0.3


def test_fetch_parses_insider_transactions():
    table = FakeInsiderTable([
        {"Insider": "Doe, Jane", "Transaction": "Sale", "Shares": 5000, "Value": 850000},
    ])
    fake = FakeTicker(info={}, insider_transactions=table)
    data = fetch_ticker_data("AAPL", factory_for(fake))
    assert data["insider_transactions"] == [
        {"insider": "Doe, Jane", "transaction": "Sale", "shares": 5000.0, "value": 850000.0}
    ]


def test_fetch_insider_transactions_none_when_absent():
    fake = FakeTicker(info={})
    data = fetch_ticker_data("AAPL", factory_for(fake))
    assert data["insider_transactions"] is None
