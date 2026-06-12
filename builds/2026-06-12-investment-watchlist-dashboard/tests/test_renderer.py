"""
Tests for src/renderer.py — pure rendering functions.
Uses synthetic processed ticker dicts so no network calls are needed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.renderer import render_html, render_text, _change_class


def _make_ticker(
    symbol: str,
    name: str,
    price: float = 100.0,
    change_pct: float = 1.5,
) -> dict:
    """Build a minimal processed ticker dict for renderer tests."""
    change_abs = price * (change_pct / 100)
    return {
        "symbol": symbol,
        "label": symbol,
        "name": name,
        "price": price,
        "prev_close": price - change_abs,
        "change_abs": change_abs,
        "change_pct": change_pct,
        "volume": 1_000_000,
        "week52_low": price * 0.8,
        "week52_high": price * 1.2,
        "week52_position": 50.0,
        "market_cap": price * 1e9,
        "pe_ratio": 25.0,
        "analyst_target": price * 1.1,
        "notes": "",
        "fmt_price": f"${price:.2f}",
        "fmt_change_abs": f"+${change_abs:.2f}",
        "fmt_change_pct": f"+{change_pct:.2f}%",
        "fmt_volume": "1.0M",
        "fmt_market_cap": "$1.00B",
        "fmt_pe": "25.0x",
        "fmt_target": f"${price * 1.1:.2f}",
        "fmt_52low": f"${price * 0.8:.2f}",
        "fmt_52high": f"${price * 1.2:.2f}",
    }


# ── _change_class ─────────────────────────────────────────────────────────────

def test_change_class_positive():
    assert _change_class(1.5) == "positive"


def test_change_class_negative():
    assert _change_class(-0.5) == "negative"


def test_change_class_zero():
    assert _change_class(0.0) == "neutral"


def test_change_class_none():
    assert _change_class(None) == "neutral"


# ── render_html ───────────────────────────────────────────────────────────────

def test_render_html_contains_all_ticker_symbols():
    tickers = [
        _make_ticker("AAPL", "Apple Inc.", 185.0, 1.2),
        _make_ticker("MSFT", "Microsoft Corp", 420.0, -0.8),
        _make_ticker("NVDA", "NVIDIA Corp", 900.0, 3.5),
    ]
    html = render_html(tickers, title="Test Watchlist")
    assert "AAPL" in html
    assert "MSFT" in html
    assert "NVDA" in html


def test_render_html_positive_ticker_has_positive_class():
    tickers = [_make_ticker("UP", "Going Up", 100.0, 2.0)]
    html = render_html(tickers)
    assert 'change-positive' in html


def test_render_html_negative_ticker_has_negative_class():
    tickers = [_make_ticker("DOWN", "Going Down", 100.0, -1.5)]
    html = render_html(tickers)
    assert 'change-negative' in html


def test_render_html_has_valid_structure():
    tickers = [_make_ticker("TEST", "Test Corp")]
    html = render_html(tickers, title="My Dashboard")
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert "<head>" in html
    assert "<body>" in html
    assert "<title>My Dashboard</title>" in html


def test_render_html_no_external_urls():
    """Ensure the generated HTML contains no external CDN or network resource URLs."""
    tickers = [_make_ticker("TEST", "Test Corp")]
    html = render_html(tickers)
    # Should not reference any external scripts or stylesheets
    assert "cdn." not in html.lower()
    assert "unpkg.com" not in html.lower()
    assert "jsdelivr.net" not in html.lower()
    assert "googleapis.com" not in html.lower()


def test_render_html_summary_shows_correct_gainer_loser_count():
    tickers = [
        _make_ticker("A", "Alpha", 100.0, 2.0),   # gainer
        _make_ticker("B", "Beta", 100.0, -1.0),   # loser
        _make_ticker("C", "Gamma", 100.0, 3.0),   # gainer
    ]
    html = render_html(tickers)
    # Summary block should show 3 tickers, 2 gainers, 1 loser
    assert ">3<" in html or ">3 " in html or "<span class=\"summary-value\">3<" in html
    assert ">2<" in html or "<span class=\"summary-value\">2<" in html
    assert ">1<" in html or "<span class=\"summary-value\">1<" in html


# ── render_text ───────────────────────────────────────────────────────────────

def test_render_text_contains_all_symbols():
    tickers = [
        _make_ticker("AAPL", "Apple Inc."),
        _make_ticker("MSFT", "Microsoft"),
    ]
    text = render_text(tickers)
    assert "AAPL" in text
    assert "MSFT" in text


def test_render_text_contains_header_and_footer():
    tickers = [_make_ticker("TEST", "Test Corp")]
    text = render_text(tickers)
    assert "Investment Watchlist" in text
    assert "Gainers:" in text
    assert "Losers:" in text
    assert "Total:" in text
