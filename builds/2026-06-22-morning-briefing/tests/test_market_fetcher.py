"""Tests for market_fetcher.py — price change math, classification, yfinance integration."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from market_fetcher import (
    calculate_change_pct,
    classify_move,
    fetch_portfolio_data,
    fetch_ticker_data,
    format_price,
)


# ---------------------------------------------------------------------------
# calculate_change_pct
# ---------------------------------------------------------------------------

class TestCalculateChangePct:
    def test_positive_change(self):
        assert calculate_change_pct(110.0, 100.0) == 10.0

    def test_negative_change(self):
        assert calculate_change_pct(90.0, 100.0) == -10.0

    def test_no_change(self):
        assert calculate_change_pct(100.0, 100.0) == 0.0

    def test_zero_previous_returns_zero(self):
        assert calculate_change_pct(50.0, 0.0) == 0.0

    def test_rounded_to_two_decimal_places(self):
        result = calculate_change_pct(100.0, 95.0)
        assert result == 5.26  # 5/95*100 = 5.2631... → 5.26


# ---------------------------------------------------------------------------
# classify_move
# ---------------------------------------------------------------------------

class TestClassifyMove:
    def test_up_for_large_positive(self):
        assert classify_move(5.0) == "up"

    def test_down_for_large_negative(self):
        assert classify_move(-3.0) == "down"

    def test_flat_for_small_positive(self):
        assert classify_move(0.5) == "flat"

    def test_flat_for_small_negative(self):
        assert classify_move(-0.5) == "flat"

    def test_up_at_exact_positive_threshold(self):
        assert classify_move(1.0) == "up"

    def test_down_at_exact_negative_threshold(self):
        assert classify_move(-1.0) == "down"

    def test_flat_just_below_threshold(self):
        assert classify_move(0.99) == "flat"

    def test_custom_threshold(self):
        assert classify_move(1.5, threshold=2.0) == "flat"
        assert classify_move(2.0, threshold=2.0) == "up"


# ---------------------------------------------------------------------------
# format_price
# ---------------------------------------------------------------------------

class TestFormatPrice:
    def test_usd_adds_dollar_sign(self):
        assert format_price(100.50, "USD") == "$100.50"

    def test_cad_adds_dollar_sign(self):
        assert format_price(50.0, "CAD") == "$50.00"

    def test_large_number_has_comma(self):
        assert format_price(1234.56, "USD") == "$1,234.56"

    def test_other_currency_no_symbol(self):
        assert format_price(100.0, "EUR") == "100.00"


# ---------------------------------------------------------------------------
# fetch_ticker_data
# ---------------------------------------------------------------------------

class TestFetchTickerData:
    def _make_mock_info(self, last_price: float | None, prev_close: float | None, currency: str = "USD") -> MagicMock:
        info = MagicMock()
        info.last_price = last_price
        info.previous_close = prev_close
        # Also set fallback attributes that fetch_ticker_data checks via getattr
        info.regularMarketPrice = None
        info.regularMarketPreviousClose = None
        info.currency = currency
        return info

    def test_success_returns_all_required_fields(self):
        mock_info = self._make_mock_info(110.0, 100.0, "USD")
        with patch("market_fetcher.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.fast_info = mock_info
            result = fetch_ticker_data("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["current"] == 110.0
        assert result["prev_close"] == 100.0
        assert result["change_pct"] == 10.0
        assert result["move"] == "up"
        assert result["formatted_price"] == "$110.00"
        assert result["formatted_change"] == "+10.00%"

    def test_returns_error_on_exception(self):
        with patch("market_fetcher.yf.Ticker", side_effect=Exception("network error")):
            result = fetch_ticker_data("FAKE")
        assert "error" in result
        assert result["ticker"] == "FAKE"

    def test_returns_error_when_price_is_none(self):
        mock_info = self._make_mock_info(None, None)
        with patch("market_fetcher.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.fast_info = mock_info
            result = fetch_ticker_data("NONE")
        assert "error" in result

    def test_down_ticker_has_negative_change(self):
        mock_info = self._make_mock_info(90.0, 100.0, "USD")
        with patch("market_fetcher.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.fast_info = mock_info
            result = fetch_ticker_data("DOWN")
        assert result["move"] == "down"
        assert result["change_pct"] < 0
        assert result["formatted_change"].startswith("-")

    def test_cad_ticker_uses_dollar_sign(self):
        mock_info = self._make_mock_info(100.0, 95.0, "CAD")
        with patch("market_fetcher.yf.Ticker") as mock_ticker:
            mock_ticker.return_value.fast_info = mock_info
            result = fetch_ticker_data("SHOP.TO")
        assert result["formatted_price"].startswith("$")


# ---------------------------------------------------------------------------
# fetch_portfolio_data
# ---------------------------------------------------------------------------

class TestFetchPortfolioData:
    def test_empty_watchlist_returns_empty_result(self):
        result = fetch_portfolio_data([])
        assert result["tickers"] == []
        assert result["total_up"] == 0

    def test_counts_movers_correctly(self):
        def fake_fetch(ticker: str):
            data = {"NVDA": 5.0, "AAPL": -2.0, "MSFT": 0.3}
            pct = data.get(ticker, 0.0)
            return {
                "ticker": ticker,
                "current": 100.0,
                "prev_close": 95.0,
                "change_pct": pct,
                "move": "up" if pct >= 1.0 else ("down" if pct <= -1.0 else "flat"),
                "currency": "USD",
                "formatted_price": "$100.00",
                "formatted_change": f"+{pct}%",
            }

        with patch("market_fetcher.fetch_ticker_data", side_effect=fake_fetch):
            result = fetch_portfolio_data(["NVDA", "AAPL", "MSFT"])

        assert result["total_up"] == 1
        assert result["total_down"] == 1
        assert result["total_flat"] == 1

    def test_errors_do_not_appear_in_tickers(self):
        with patch("market_fetcher.fetch_ticker_data", return_value={"ticker": "FAIL", "error": "unavailable"}):
            result = fetch_portfolio_data(["FAIL"])
        assert result["tickers"] == []
        assert len(result["errors"]) == 1
