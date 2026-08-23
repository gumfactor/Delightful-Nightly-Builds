"""Tests for src/report.py — payload shaping and XSS-safe embedding."""

import json

import pytest

from src import report


def sample_snapshots():
    return [
        {
            "snapshot_date": "2026-08-19",
            "net_liquidation": 10000.0,
            "total_cash": 5000.0,
            "unrealized_pnl": 100.0,
            "realized_pnl": 20.0,
            "positions": [
                {
                    "symbol": "AAPL",
                    "sec_type": "STK",
                    "currency": "USD",
                    "exchange": "NASDAQ",
                    "quantity": 10.0,
                    "avg_cost": 150.0,
                    "market_price": 160.0,
                    "market_value": 1600.0,
                    "unrealized_pnl": 100.0,
                },
            ],
        },
        {
            "snapshot_date": "2026-08-20",
            "net_liquidation": 10500.0,
            "total_cash": 5000.0,
            "unrealized_pnl": 150.0,
            "realized_pnl": 20.0,
            "positions": [
                {
                    "symbol": "<script>alert(1)</script>",
                    "sec_type": "STK",
                    "currency": "USD",
                    "exchange": "NASDAQ",
                    "quantity": 5.0,
                    "avg_cost": 100.0,
                    "market_price": 90.0,
                    "market_value": 450.0,
                    "unrealized_pnl": -50.0,
                },
            ],
        },
    ]


def _extract_json_payload(html):
    start = html.index('type="application/json">') + len('type="application/json">')
    end = html.index("</script>", start)
    return json.loads(html[start:end])


def test_render_dashboard_embeds_valid_json_payload():
    payload = _extract_json_payload(report.render_dashboard(sample_snapshots()))
    assert payload["latest"]["snapshot_date"] == "2026-08-20"


def test_render_dashboard_neutralizes_closing_script_tag_in_symbol():
    html = report.render_dashboard(sample_snapshots())
    assert "<\\/script>" in html
    assert "alert(1)</script>" not in html


def test_render_dashboard_empty_snapshots_shows_placeholder():
    html = report.render_dashboard([], ai_note=None)
    payload = _extract_json_payload(html)
    assert payload["latest"] is None
    assert "No snapshot yet" in html


def test_render_dashboard_includes_ai_note_text():
    html = report.render_dashboard(sample_snapshots(), ai_note="Portfolio was quiet today.")
    payload = _extract_json_payload(html)
    assert payload["ai_note"] == "Portfolio was quiet today."


def test_build_report_payload_computes_day_change_pct():
    payload = report.build_report_payload(sample_snapshots(), ai_note=None)
    assert payload["latest"]["day_change_pct"] == pytest.approx(5.0)


def test_build_report_payload_groups_allocation_by_sec_type():
    payload = report.build_report_payload(sample_snapshots(), ai_note=None)
    assert payload["latest"]["allocation"] == {"STK": 450.0}


def test_build_aggregate_summary_contains_no_raw_dollar_figures():
    summary = report.build_aggregate_summary(sample_snapshots())
    serialized = json.dumps(summary)
    assert "10000" not in serialized
    assert "1600" not in serialized
    assert "450" not in serialized


def test_build_aggregate_summary_top_movers_sorted_by_magnitude():
    snapshots = sample_snapshots()
    snapshots[-1]["positions"].append(
        {
            "symbol": "MSFT",
            "sec_type": "STK",
            "currency": "USD",
            "exchange": "NASDAQ",
            "quantity": 1.0,
            "avg_cost": 100.0,
            "market_price": 105.0,
            "market_value": 105.0,
            "unrealized_pnl": 5.0,
        }
    )
    summary = report.build_aggregate_summary(snapshots)
    # The first position moved -10% (90 vs avg cost 100), MSFT moved +5% — the
    # bigger-magnitude move should sort first.
    assert summary["top_movers"][0]["symbol"] != "MSFT"


def test_build_aggregate_summary_empty_snapshots_returns_zeroed_summary():
    summary = report.build_aggregate_summary([])
    assert summary == {"day_change_pct": 0.0, "allocation_pct": {}, "top_movers": []}
