"""Unit tests for src/report.py — HTML report generation."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fetcher import TickerData
from src.report import generate_report, _change_class, _build_summary, _format_thesis_cell, _build_group_header


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


# ── Thesis column ─────────────────────────────────────────────────────────────

def test_thesis_cell_no_entries_renders_dash():
    html = _format_thesis_cell(None, 180.0)
    assert "—" in html


def test_thesis_cell_shows_note_text():
    entries = [{"id": 1, "date": "2026-06-01T10:00:00+00:00", "note": "Strong moat.", "price_at_note": 150.0}]
    html = _format_thesis_cell(entries, 180.0)
    assert "Strong moat." in html


def test_thesis_cell_shows_price_at_note():
    entries = [{"id": 1, "date": "2026-06-01T10:00:00+00:00", "note": "Thesis.", "price_at_note": 150.0}]
    html = _format_thesis_cell(entries, 180.0)
    assert "150.00" in html


def test_thesis_cell_shows_positive_since_change():
    entries = [{"id": 1, "date": "2026-06-01T10:00:00+00:00", "note": "Thesis.", "price_at_note": 100.0}]
    html = _format_thesis_cell(entries, 120.0)
    assert "since-up" in html
    assert "+20.0%" in html


def test_thesis_cell_shows_negative_since_change():
    entries = [{"id": 1, "date": "2026-06-01T10:00:00+00:00", "note": "Thesis.", "price_at_note": 100.0}]
    html = _format_thesis_cell(entries, 80.0)
    assert "since-down" in html
    assert "-20.0%" in html


def test_thesis_cell_no_price_at_note_omits_since():
    entries = [{"id": 1, "date": "2026-06-01T10:00:00+00:00", "note": "Thesis.", "price_at_note": None}]
    html = _format_thesis_cell(entries, 180.0)
    assert "since" not in html


def test_thesis_cell_long_note_truncated():
    long_note = "A" * 100
    entries = [{"id": 1, "date": "2026-06-01T10:00:00+00:00", "note": long_note, "price_at_note": None}]
    html = _format_thesis_cell(entries, None)
    assert "…" in html


def test_report_includes_thesis_column_header():
    html = generate_report([_make_ticker()], generated_at=_fixed_time())
    assert "Thesis" in html


def test_report_thesis_data_appears_in_output():
    ticker = _make_ticker("NVDA", price=1100.0)
    theses = {
        "NVDA": [{"id": 1, "date": "2026-01-01T00:00:00+00:00", "note": "AI infrastructure play.", "price_at_note": 850.0}]
    }
    html = generate_report([ticker], theses=theses, generated_at=_fixed_time())
    assert "AI infrastructure play." in html
    assert "850.00" in html


def test_report_no_thesis_data_renders_dash():
    ticker = _make_ticker("AAPL")
    html = generate_report([ticker], theses={}, generated_at=_fixed_time())
    assert "—" in html


# ── Currency column ───────────────────────────────────────────────────────────

def test_report_includes_currency_column_header():
    html = generate_report([_make_ticker()], generated_at=_fixed_time())
    assert "Currency" in html


def test_report_currency_usd_appears_in_row():
    ticker = _make_ticker(currency="USD")
    html = generate_report([ticker], generated_at=_fixed_time())
    assert "USD" in html


def test_report_currency_cad_appears_in_row():
    ticker = _make_ticker(symbol="VFV.TO", currency="CAD")
    html = generate_report([ticker], generated_at=_fixed_time())
    assert "CAD" in html


# ── Sortable table ────────────────────────────────────────────────────────────

def test_report_includes_sort_attributes_on_headers():
    html = generate_report([_make_ticker()], generated_at=_fixed_time())
    assert 'data-sort="num"' in html
    assert 'data-sort="str"' in html


def test_report_includes_sort_script():
    html = generate_report([_make_ticker()], generated_at=_fixed_time())
    assert "<script>" in html
    assert "parseNum" in html


# ── Ticker grouping ───────────────────────────────────────────────────────────

def test_group_header_renders_name():
    html = _build_group_header("Core Holdings")
    assert "Core Holdings" in html
    assert 'class="group-header"' in html


def test_report_group_header_appears_in_output():
    tickers = [_make_ticker("AAPL"), _make_ticker("MSFT")]
    groups = {"AAPL": "Core Holdings", "MSFT": "Core Holdings"}
    html = generate_report(tickers, groups=groups, generated_at=_fixed_time())
    assert "Core Holdings" in html


def test_report_multiple_groups_all_appear():
    tickers = [_make_ticker("AAPL"), _make_ticker("MSFT"), _make_ticker("NVDA")]
    groups = {"AAPL": "Core", "MSFT": "Core", "NVDA": "Speculative"}
    html = generate_report(tickers, groups=groups, generated_at=_fixed_time())
    assert "Core" in html
    assert "Speculative" in html


def test_report_ungrouped_tickers_render_without_header():
    tickers = [_make_ticker("AAPL"), _make_ticker("MSFT")]
    html = generate_report(tickers, groups=None, generated_at=_fixed_time())
    assert '<tr class="group-header">' not in html


def test_group_header_escapes_html():
    html = _build_group_header('<script>alert(1)</script>')
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
