"""
Tests for src/processor.py — all pure functions, no mocking needed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.processor import (
    format_price,
    format_change_pct,
    format_change_abs,
    format_market_cap,
    format_volume,
    format_pe,
    calc_52week_position,
    process_ticker_data,
)


# ── format_price ──────────────────────────────────────────────────────────────

def test_format_price_normal():
    assert format_price(185.50) == "$185.50"


def test_format_price_none_returns_na():
    assert format_price(None) == "N/A"


def test_format_price_zero():
    assert format_price(0.0) == "$0.00"


def test_format_price_large_value():
    assert format_price(1234567.89) == "$1,234,567.89"


# ── format_change_pct ─────────────────────────────────────────────────────────

def test_format_change_pct_positive():
    assert format_change_pct(1.76) == "+1.76%"


def test_format_change_pct_negative():
    assert format_change_pct(-2.34) == "-2.34%"


def test_format_change_pct_zero():
    assert format_change_pct(0.0) == "+0.00%"


def test_format_change_pct_none_returns_na():
    assert format_change_pct(None) == "N/A"


# ── format_market_cap ─────────────────────────────────────────────────────────

def test_format_market_cap_billions():
    assert format_market_cap(2_850_000_000_000) == "$2.85T"


def test_format_market_cap_trillions():
    assert format_market_cap(500_000_000_000) == "$500.00B"


def test_format_market_cap_none_returns_na():
    assert format_market_cap(None) == "N/A"


def test_format_market_cap_millions():
    assert format_market_cap(750_000_000) == "$750.00M"


# ── calc_52week_position ──────────────────────────────────────────────────────

def test_calc_52week_position_midpoint():
    # Price exactly halfway between low and high → 50.0%
    result = calc_52week_position(150.0, 100.0, 200.0)
    assert result == 50.0


def test_calc_52week_position_at_low():
    # Price at 52-week low → 0.0%
    result = calc_52week_position(100.0, 100.0, 200.0)
    assert result == 0.0


def test_calc_52week_position_at_high():
    # Price at 52-week high → 100.0%
    result = calc_52week_position(200.0, 100.0, 200.0)
    assert result == 100.0


def test_calc_52week_position_none_price_returns_none():
    assert calc_52week_position(None, 100.0, 200.0) is None


def test_calc_52week_position_degenerate_range_returns_none():
    # low == high → undefined position
    assert calc_52week_position(100.0, 100.0, 100.0) is None


def test_calc_52week_position_clamped_below_zero():
    # Price below 52-week low (stale data) → clamped to 0
    result = calc_52week_position(90.0, 100.0, 200.0)
    assert result == 0.0


def test_calc_52week_position_clamped_above_hundred():
    # Price above 52-week high (stale data) → clamped to 100
    result = calc_52week_position(210.0, 100.0, 200.0)
    assert result == 100.0


# ── process_ticker_data ───────────────────────────────────────────────────────

def _sample_info() -> dict:
    """Minimal but complete yfinance-style info dict for testing."""
    return {
        "longName": "Apple Inc.",
        "currentPrice": 185.50,
        "previousClose": 182.30,
        "regularMarketVolume": 52_300_000,
        "fiftyTwoWeekLow": 164.08,
        "fiftyTwoWeekHigh": 199.62,
        "marketCap": 2_850_000_000_000,
        "trailingPE": 28.4,
        "targetMeanPrice": 210.00,
    }


def test_process_ticker_data_extracts_all_fields():
    info = _sample_info()
    result = process_ticker_data("AAPL", "Apple", "", info)

    assert result["symbol"] == "AAPL"
    assert result["label"] == "Apple"
    assert result["name"] == "Apple Inc."
    assert result["price"] == 185.50
    assert result["prev_close"] == 182.30
    assert abs(result["change_abs"] - 3.20) < 0.01
    assert abs(result["change_pct"] - 1.757) < 0.01
    assert result["volume"] == 52_300_000
    assert result["week52_low"] == 164.08
    assert result["week52_high"] == 199.62
    assert result["market_cap"] == 2_850_000_000_000
    assert result["pe_ratio"] == 28.4
    assert result["analyst_target"] == 210.00
    assert result["week52_position"] is not None


def test_process_ticker_data_missing_fields_return_none():
    # Minimal info dict with no optional fields
    info = {}
    result = process_ticker_data("EMPTY", "Empty Co", "test note", info)

    assert result["symbol"] == "EMPTY"
    assert result["price"] is None
    assert result["change_abs"] is None
    assert result["change_pct"] is None
    assert result["market_cap"] is None
    assert result["pe_ratio"] is None
    # All preformatted strings should fall back to "N/A"
    assert result["fmt_price"] == "N/A"
    assert result["fmt_change_pct"] == "N/A"
    assert result["fmt_market_cap"] == "N/A"
    assert result["fmt_pe"] == "N/A"


def test_process_ticker_data_notes_preserved():
    info = _sample_info()
    result = process_ticker_data("AAPL", "Apple", "core holding", info)
    assert result["notes"] == "core holding"


def test_process_ticker_data_change_calculations_correct():
    info = {"currentPrice": 200.0, "previousClose": 160.0}
    result = process_ticker_data("X", "X Corp", "", info)
    assert abs(result["change_abs"] - 40.0) < 0.001
    assert abs(result["change_pct"] - 25.0) < 0.001
