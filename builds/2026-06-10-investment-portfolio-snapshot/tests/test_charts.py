"""Unit tests for src/charts.py — SVG sparkline generation."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.charts import make_sparkline, _trend_color, _normalize_prices, _COLOR_UP, _COLOR_DOWN, _COLOR_FLAT


# ── _trend_color ──────────────────────────────────────────────────────────────

def test_trend_color_uptrend():
    assert _trend_color([100.0, 105.0, 110.0]) == _COLOR_UP


def test_trend_color_downtrend():
    assert _trend_color([110.0, 105.0, 100.0]) == _COLOR_DOWN


def test_trend_color_flat():
    assert _trend_color([100.0, 100.0, 100.0]) == _COLOR_FLAT


def test_trend_color_single_point():
    assert _trend_color([100.0]) == _COLOR_FLAT


def test_trend_color_empty():
    assert _trend_color([]) == _COLOR_FLAT


# ── _normalize_prices ─────────────────────────────────────────────────────────

def test_normalize_prices_range():
    """Normalized y-coords must stay within [2, height-2]."""
    prices = [50.0, 75.0, 100.0, 60.0, 90.0]
    height = 28
    ys = _normalize_prices(prices, height)
    assert all(2 <= y <= height - 2 for y in ys)


def test_normalize_prices_flat_returns_midpoint():
    """All-same prices should land on the vertical midpoint."""
    prices = [100.0, 100.0, 100.0]
    height = 28
    ys = _normalize_prices(prices, height)
    assert all(y == height / 2 for y in ys)


def test_normalize_prices_count_preserved():
    prices = [10.0, 20.0, 30.0, 40.0]
    ys = _normalize_prices(prices, 28)
    assert len(ys) == 4


def test_normalize_prices_highest_price_has_lowest_y():
    """In SVG, y=0 is top; so highest price → lowest y-coordinate."""
    prices = [100.0, 200.0]
    ys = _normalize_prices(prices, 28)
    # prices[1]=200 is higher → should have smaller y
    assert ys[1] < ys[0]


# ── make_sparkline ────────────────────────────────────────────────────────────

def test_sparkline_returns_svg_tag():
    svg = make_sparkline([100.0, 110.0, 105.0])
    assert svg.strip().startswith("<svg")
    assert "</svg>" in svg


def test_sparkline_empty_data_returns_placeholder():
    svg = make_sparkline([])
    assert "<svg" in svg
    assert "</svg>" in svg
    # Placeholder uses a <line> element
    assert "<line" in svg


def test_sparkline_single_point_no_crash():
    svg = make_sparkline([100.0])
    assert "<svg" in svg
    # Single point renders as a circle, not a polyline
    assert "<circle" in svg


def test_sparkline_uptrend_uses_green():
    svg = make_sparkline([100.0, 110.0, 120.0])
    assert _COLOR_UP in svg


def test_sparkline_downtrend_uses_red():
    svg = make_sparkline([120.0, 110.0, 100.0])
    assert _COLOR_DOWN in svg


def test_sparkline_flat_uses_gray():
    svg = make_sparkline([100.0, 100.0, 100.0])
    assert _COLOR_FLAT in svg


def test_sparkline_has_polyline_for_multiple_points():
    svg = make_sparkline([100.0, 105.0, 102.0, 108.0])
    assert "<polyline" in svg


def test_sparkline_has_endpoint_dot():
    svg = make_sparkline([90.0, 95.0, 100.0])
    assert "<circle" in svg


def test_sparkline_width_in_viewbox():
    svg = make_sparkline([100.0, 105.0])
    assert 'viewBox="0 0 80 28"' in svg
