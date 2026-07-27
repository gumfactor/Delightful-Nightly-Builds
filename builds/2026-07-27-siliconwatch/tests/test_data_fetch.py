import pandas as pd
import pytest
from data_fetch import empty_snapshot_metrics, fetch_price_history, fetch_snapshot


class FakeTicker:
    def __init__(self, info=None, history_df=None, raise_on_info=False, raise_on_history=False):
        self._info = info or {}
        self._history_df = history_df
        self._raise_on_info = raise_on_info
        self._raise_on_history = raise_on_history

    @property
    def info(self):
        if self._raise_on_info:
            raise RuntimeError("simulated network failure")
        return self._info

    def history(self, period="1y"):
        if self._raise_on_history:
            raise RuntimeError("simulated network failure")
        return self._history_df


def make_factory(fake_ticker):
    return lambda ticker: fake_ticker


def test_fetch_snapshot_maps_all_fields_correctly():
    info = {
        "currentPrice": 120.5,
        "marketCap": 3_000_000_000_000,
        "trailingPE": 45.2,
        "forwardPE": 38.1,
        "pegRatio": 1.8,
        "profitMargins": 0.55,
        "revenueGrowth": 0.62,
        "targetMeanPrice": 150.0,
        "fiftyTwoWeekLow": 80.0,
        "fiftyTwoWeekHigh": 140.0,
    }
    metrics = fetch_snapshot("NVDA", ticker_factory=make_factory(FakeTicker(info=info)))
    assert metrics["price"] == 120.5
    assert metrics["market_cap"] == 3_000_000_000_000
    assert metrics["pe_trailing"] == 45.2
    assert metrics["peg_ratio"] == 1.8
    assert metrics["profit_margin"] == 0.55
    assert metrics["week52_low"] == 80.0
    assert metrics["week52_high"] == 140.0


def test_fetch_snapshot_falls_back_to_regular_market_price():
    info = {"regularMarketPrice": 99.9}
    metrics = fetch_snapshot("AMD", ticker_factory=make_factory(FakeTicker(info=info)))
    assert metrics["price"] == 99.9


def test_fetch_snapshot_missing_optional_fields_are_none():
    metrics = fetch_snapshot("MRVL", ticker_factory=make_factory(FakeTicker(info={"currentPrice": 50.0})))
    assert metrics["price"] == 50.0
    assert metrics["peg_ratio"] is None
    assert metrics["revenue_growth"] is None


def test_fetch_snapshot_never_raises_on_info_exception():
    metrics = fetch_snapshot("TSM", ticker_factory=make_factory(FakeTicker(raise_on_info=True)))
    assert metrics == empty_snapshot_metrics()


def test_fetch_snapshot_never_raises_on_factory_exception():
    def bad_factory(ticker):
        raise ConnectionError("no network")

    metrics = fetch_snapshot("ASML", ticker_factory=bad_factory)
    assert metrics == empty_snapshot_metrics()


def test_fetch_snapshot_ignores_non_numeric_field_values():
    info = {"currentPrice": 10.0, "trailingPE": "not-a-number"}
    metrics = fetch_snapshot("MU", ticker_factory=make_factory(FakeTicker(info=info)))
    assert metrics["pe_trailing"] is None


def test_fetch_price_history_converts_dataframe_to_tuples():
    df = pd.DataFrame(
        {"Close": [100.0, 101.5, 99.25]},
        index=pd.to_datetime(["2026-07-24", "2026-07-25", "2026-07-26"]),
    )
    history = fetch_price_history("NVDA", ticker_factory=make_factory(FakeTicker(history_df=df)))
    assert history == [
        ("2026-07-24", 100.0),
        ("2026-07-25", 101.5),
        ("2026-07-26", 99.25),
    ]


def test_fetch_price_history_empty_dataframe_returns_empty_list():
    df = pd.DataFrame({"Close": []}, index=pd.to_datetime([]))
    history = fetch_price_history("AMD", ticker_factory=make_factory(FakeTicker(history_df=df)))
    assert history == []


def test_fetch_price_history_none_returns_empty_list():
    history = fetch_price_history("INTC", ticker_factory=make_factory(FakeTicker(history_df=None)))
    assert history == []


def test_fetch_price_history_never_raises_on_exception():
    history = fetch_price_history("LRCX", ticker_factory=make_factory(FakeTicker(raise_on_history=True)))
    assert history == []
