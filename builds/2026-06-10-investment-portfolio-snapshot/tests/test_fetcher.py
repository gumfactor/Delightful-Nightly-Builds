"""Unit tests for src/fetcher.py — normalization and formatter functions."""

import math
import sys
from pathlib import Path

import pytest

# Allow imports from build root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetcher import (
    TickerData,
    _nan_to_none,
    normalize_info,
    format_price,
    format_change,
    format_market_cap,
    format_volume,
    format_pe,
    format_52w_range,
)


# ── _nan_to_none ──────────────────────────────────────────────────────────────

def test_nan_to_none_converts_nan():
    assert _nan_to_none(float("nan")) is None


def test_nan_to_none_passes_float():
    assert _nan_to_none(3.14) == 3.14


def test_nan_to_none_passes_none():
    assert _nan_to_none(None) is None


def test_nan_to_none_passes_int():
    assert _nan_to_none(42) == 42


# ── normalize_info ────────────────────────────────────────────────────────────

def _base_info(**kwargs) -> dict:
    """Minimal valid yfinance info dict."""
    defaults = {
        "symbol": "TEST",
        "longName": "Test Corp",
        "currentPrice": 100.0,
        "previousClose": 95.0,
        "currency": "USD",
        "fiftyTwoWeekHigh": 120.0,
        "fiftyTwoWeekLow": 80.0,
        "trailingPE": 25.0,
        "marketCap": 2_500_000_000,
        "volume": 5_000_000,
    }
    defaults.update(kwargs)
    return defaults


def test_normalize_info_basic_fields():
    info = _base_info()
    result = normalize_info(info, [90.0, 95.0, 100.0])
    assert result.symbol == "TEST"
    assert result.name == "Test Corp"
    assert result.price == 100.0
    assert result.currency == "USD"
    assert result.error is None


def test_normalize_info_change_pct_calculated():
    info = _base_info(currentPrice=100.0, previousClose=95.0)
    result = normalize_info(info, [])
    # (100 - 95) / 95 * 100 ≈ 5.263%
    assert result.change_pct is not None
    assert abs(result.change_pct - 5.2631578) < 0.0001


def test_normalize_info_change_pct_none_when_no_prev_close():
    info = _base_info(previousClose=None)
    # Remove the key entirely to simulate missing
    del info["previousClose"]
    result = normalize_info(info, [])
    assert result.change_pct is None


def test_normalize_info_label_overrides_name():
    info = _base_info()
    result = normalize_info(info, [], label="My Apple")
    assert result.name == "My Apple"


def test_normalize_info_nan_pe_becomes_none():
    info = _base_info(trailingPE=float("nan"))
    result = normalize_info(info, [])
    assert result.pe_ratio is None


def test_normalize_info_market_cap_cast_to_int():
    info = _base_info(marketCap=2_500_000_000.9)
    result = normalize_info(info, [])
    assert isinstance(result.market_cap, int)
    assert result.market_cap == 2_500_000_000


def test_normalize_info_history_stored():
    prices = [100.0, 101.5, 99.8, 103.2]
    result = normalize_info(_base_info(), prices)
    assert result.history == prices


# ── format_price ──────────────────────────────────────────────────────────────

def test_format_price_usd():
    assert format_price(150.5, "USD") == "$150.50"


def test_format_price_cad():
    assert format_price(200.0, "CAD") == "$200.00"


def test_format_price_none():
    assert format_price(None) == "—"


def test_format_price_comma_separator():
    assert format_price(1500.0, "USD") == "$1,500.00"


# ── format_change ─────────────────────────────────────────────────────────────

def test_format_change_positive():
    assert format_change(2.5) == "+2.50%"


def test_format_change_negative():
    assert format_change(-1.3) == "-1.30%"


def test_format_change_zero():
    assert format_change(0.0) == "+0.00%"


def test_format_change_none():
    assert format_change(None) == "—"


# ── format_market_cap ─────────────────────────────────────────────────────────

def test_format_market_cap_trillions():
    assert format_market_cap(2_850_000_000_000) == "2.85T"


def test_format_market_cap_billions():
    assert format_market_cap(2_300_000_000) == "2.30B"


def test_format_market_cap_millions():
    assert format_market_cap(5_000_000) == "5.00M"


def test_format_market_cap_none():
    assert format_market_cap(None) == "—"


# ── format_volume ─────────────────────────────────────────────────────────────

def test_format_volume_millions():
    assert format_volume(5_000_000) == "5.0M"


def test_format_volume_thousands():
    assert format_volume(75_000) == "75K"


def test_format_volume_none():
    assert format_volume(None) == "—"


# ── format_pe ─────────────────────────────────────────────────────────────────

def test_format_pe_value():
    assert format_pe(25.678) == "25.7"


def test_format_pe_none():
    assert format_pe(None) == "—"


# ── format_52w_range ──────────────────────────────────────────────────────────

def test_format_52w_range_both():
    result = format_52w_range(80.0, 120.5)
    assert "80.00" in result
    assert "120.50" in result


def test_format_52w_range_both_none():
    assert format_52w_range(None, None) == "—"


def test_format_52w_range_one_missing():
    result = format_52w_range(None, 120.0)
    assert "?" in result
    assert "120.00" in result
