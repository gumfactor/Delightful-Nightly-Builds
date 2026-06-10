"""Unit tests for src/report.py — HTML report generation."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetcher import TickerData
from src.report import generate_report, _change_class, _build_summary


def _make_ticker(
    symbol: str = "AAPL",
    name: str = "Apple",
    price: float | None = 180.0,
    change_pct: float | None = 1.5,
    week52_high: float | None = 200.0,
    week52_low: float | None = 150.0,
    pe_ratio: float | None = 28.5,
    market_cap: int | None = 2_800_000_000_000,
    volume: int | None = 60_000_000,
    history: list | None = None,
    currency: str = "USD",
    error: str | None = None,
) -> TickerData:
    return TickerData(
        symbol=symbol,
        name=name,
        price=price,
        change_pct=change_pct,
        week52_high=week52_high,
        week52_low=week52_low,
        pe_ratio=pe_ratio,
        market_cap=market_cap,
        volume=volume,
        history=history if history is not None else [170.0, 175.0, 180.0],
        currency=currency,
        error=error,
    )


# ── _change_class ─────────────────────────────────────────────────────────────

def test_change_class_positive():
    assert _change_class(1.5) == "up"


def test_change_class_negative():
    assert _change_class(-0.5) == "down"


def test_change_class_zero():
    assert _change_class(0.0) == "flat"


def test_change_class_none():
    assert _change_class(None) == "flat"


# ── _build_summary ────────────────────────────────────────────────────────────

def test_summary_counts_gainers_losers():
    tickers = [
        _make_ticker("A", change_pct=1.0),
        _make_ticker("B", change_pct=-0.5),
        _make_ticker("C", change_pct=2.0),
    ]
    html = _build_summary(tickers)
    # Should show 2 gainers and 1 loser in some form
    assert "2" in html
    assert "1" in html


def test_summary_excludes_error_tickers_from_gainers():
    tickers = [
        _make_ticker("A", change_pct=1.0),
        _make_ticker("B", error="fetch failed", change_pct=None),
    ]
    html = _build_summary(tickers)
    # Total tickers = 2, but gainers should only count non-error ones
    assert "2" in html  # total count
    assert "1" in html  # 1 gainer


# ── generate_report ───────────────────────────────────────────────────────────

def _fixed_time() -> datetime:
    return datetime(2026, 6, 10, 8, 0, 0, tzinfo=timezone.utc)


def test_report_contains_all_symbols():
    tickers = [_make_ticker("AAPL"), _make_ticker("MSFT"), _make_ticker("NVDA")]
    html = generate_report(tickers, generated_at=_fixed_time())
    assert "AAPL" in html
    assert "MSFT" in html
    assert "NVDA" in html


def test_report_contains_timestamp():
    html = generate_report([_make_ticker()], generated_at=_fixed_time())
    assert "2026-06-10" in html
    assert "08:00 UTC" in html


def test_report_is_valid_html_structure():
    html = generate_report([_make_ticker()], generated_at=_fixed_time())
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "<head>" in html
    assert "<body>" in html
    assert "</html>" in html


def test_report_handles_error_ticker():
    bad = _make_ticker("FAIL", error="Connection timeout")
    html = generate_report([bad], generated_at=_fixed_time())
    assert "FAIL" in html
    assert "Connection timeout" in html


def test_report_handles_empty_watchlist():
    html = generate_report([], generated_at=_fixed_time())
    assert "<!DOCTYPE html>" in html
    assert "<table" in html


def test_report_positive_change_gets_up_class():
    ticker = _make_ticker(change_pct=2.5)
    html = generate_report([ticker], generated_at=_fixed_time())
    assert 'class="change up"' in html


def test_report_negative_change_gets_down_class():
    ticker = _make_ticker(change_pct=-1.0)
    html = generate_report([ticker], generated_at=_fixed_time())
    assert 'class="change down"' in html


def test_report_none_fields_render_dashes():
    ticker = _make_ticker(price=None, change_pct=None, pe_ratio=None, market_cap=None)
    html = generate_report([ticker], generated_at=_fixed_time())
    # Multiple "—" dashes should appear for missing fields
    assert html.count("—") >= 3


def test_report_includes_sparkline_svg():
    ticker = _make_ticker(history=[100.0, 105.0, 110.0])
    html = generate_report([ticker], generated_at=_fixed_time())
    assert "<svg" in html
    assert "<polyline" in html


def test_report_includes_footer():
    html = generate_report([_make_ticker()], generated_at=_fixed_time())
    assert "Yahoo Finance" in html
