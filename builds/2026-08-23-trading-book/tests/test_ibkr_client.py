"""Tests for src/ibkr_client.py.

`ib_insync` is never actually installed in this build environment (or
required to be) — every test injects a fake module into `sys.modules`
before calling `fetch_snapshot`, so no real network call is ever made.
"""

import sys
import types

import pytest

from src.ibkr_client import IBKRConnectionError, fetch_snapshot


class FakeSummaryItem:
    def __init__(self, account, tag, value):
        self.account = account
        self.tag = tag
        self.value = value


class FakeContract:
    def __init__(self, symbol, secType, currency, exchange=""):
        self.symbol = symbol
        self.secType = secType
        self.currency = currency
        self.exchange = exchange


class FakePortfolioItem:
    def __init__(self, contract, position, averageCost, marketPrice, marketValue, unrealizedPNL):
        self.contract = contract
        self.position = position
        self.averageCost = averageCost
        self.marketPrice = marketPrice
        self.marketValue = marketValue
        self.unrealizedPNL = unrealizedPNL


def make_fake_ib_insync(connect_error=None, summary=None, portfolio=None, read_error=None):
    calls = {"connect": [], "disconnect": 0}

    class FakeIB:
        def connect(self, host, port, clientId=None, timeout=None):
            calls["connect"].append({"host": host, "port": port, "clientId": clientId, "timeout": timeout})
            if connect_error:
                raise connect_error

        def accountSummary(self):
            if read_error:
                raise read_error
            return summary or []

        def portfolio(self):
            if read_error:
                raise read_error
            return portfolio or []

        def disconnect(self):
            calls["disconnect"] += 1

    module = types.ModuleType("ib_insync")
    module.IB = FakeIB
    module._calls = calls
    return module


@pytest.fixture(autouse=True)
def clean_sys_modules():
    yield
    sys.modules.pop("ib_insync", None)


def test_fetch_snapshot_success():
    contract = FakeContract("AAPL", "STK", "USD", "NASDAQ")
    portfolio_item = FakePortfolioItem(contract, 10, 150.0, 200.0, 2000.0, 500.0)
    summary = [
        FakeSummaryItem("U123", "NetLiquidation", "10000.0"),
        FakeSummaryItem("U123", "TotalCashValue", "5000.0"),
        FakeSummaryItem("U123", "UnrealizedPnL", "500.0"),
    ]
    fake_module = make_fake_ib_insync(summary=summary, portfolio=[portfolio_item])
    sys.modules["ib_insync"] = fake_module

    snapshot = fetch_snapshot(host="127.0.0.1", port=7497, client_id=7, timeout=5.0)

    assert snapshot["account_id"] == "U123"
    assert snapshot["net_liquidation"] == 10000.0
    assert snapshot["total_cash"] == 5000.0
    assert snapshot["unrealized_pnl"] == 500.0
    assert len(snapshot["positions"]) == 1
    assert snapshot["positions"][0]["symbol"] == "AAPL"
    assert snapshot["positions"][0]["market_value"] == 2000.0
    assert fake_module._calls["disconnect"] == 1
    assert fake_module._calls["connect"][0] == {
        "host": "127.0.0.1", "port": 7497, "clientId": 7, "timeout": 5.0
    }


def test_fetch_snapshot_connection_failure_raises_and_still_disconnects():
    fake_module = make_fake_ib_insync(connect_error=ConnectionRefusedError("refused"))
    sys.modules["ib_insync"] = fake_module

    with pytest.raises(IBKRConnectionError):
        fetch_snapshot()

    assert fake_module._calls["disconnect"] == 1


def test_fetch_snapshot_empty_positions_returns_empty_list():
    summary = [FakeSummaryItem("U123", "NetLiquidation", "0.0")]
    fake_module = make_fake_ib_insync(summary=summary, portfolio=[])
    sys.modules["ib_insync"] = fake_module

    snapshot = fetch_snapshot()
    assert snapshot["positions"] == []


def test_fetch_snapshot_read_error_raises_and_still_disconnects():
    fake_module = make_fake_ib_insync(read_error=RuntimeError("boom"))
    sys.modules["ib_insync"] = fake_module

    with pytest.raises(IBKRConnectionError):
        fetch_snapshot()

    assert fake_module._calls["disconnect"] == 1


def test_fetch_snapshot_missing_ib_insync_raises_friendly_error():
    # sys.modules[name] = None makes Python's import machinery raise
    # ImportError, simulating "package not installed" without depending on
    # whether the real package happens to be present in this environment.
    sys.modules["ib_insync"] = None
    with pytest.raises(IBKRConnectionError, match="ib_insync is not installed"):
        fetch_snapshot()
