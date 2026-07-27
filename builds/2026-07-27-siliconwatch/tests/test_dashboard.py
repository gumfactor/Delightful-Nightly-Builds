from dashboard import CHARTJS_VERSION, render_dashboard


def make_snapshot(ticker="NVDA", name="NVIDIA Corporation", subsector="GPU / AI Accelerators", **overrides):
    row = {
        "ticker": ticker,
        "name": name,
        "subsector": subsector,
        "price": 120.0,
        "market_cap": 3_000_000_000_000,
        "pe_trailing": 42.0,
        "pe_forward": 35.0,
        "peg_ratio": 1.5,
        "profit_margin": 0.55,
        "revenue_growth": 0.6,
        "target_mean_price": 140.0,
        "week52_low": 80.0,
        "week52_high": 150.0,
        "since_prev_pct": 1.2,
        "since_1y_pct": 45.0,
        "since_1y_reliable": True,
    }
    row.update(overrides)
    return row


AGGREGATES = {
    "total_market_cap": 3_000_000_000_000,
    "avg_pe_trailing": 42.0,
    "avg_profit_margin": 0.55,
    "growth_positive_count": 1,
    "companies_tracked": 1,
    "top_mover": {"ticker": "NVDA", "name": "NVIDIA Corporation", "pct": 45.0},
    "laggard": {"ticker": "NVDA", "name": "NVIDIA Corporation", "pct": 45.0},
}


def render(snapshots, sector_pe_trend=None, narrative_source="template"):
    price_history = {s["ticker"]: [("2026-07-25", 100.0), ("2026-07-27", 105.0)] for s in snapshots}
    return render_dashboard(
        snapshots,
        price_history,
        sector_pe_trend or [("2026-07-27", 42.0)],
        AGGREGATES,
        "A deterministic test narrative.",
        narrative_source,
        generated_at="2026-07-27T09:00:00Z",
    )


def test_render_dashboard_is_valid_self_contained_html():
    html_out = render([make_snapshot()])
    assert html_out.strip().startswith("<!DOCTYPE html>")
    assert html_out.strip().endswith("</html>")


def test_render_dashboard_includes_pinned_chartjs_version():
    html_out = render([make_snapshot()])
    assert f"chart.js@{CHARTJS_VERSION}" in html_out


def test_render_dashboard_escapes_html_injection_payload():
    payload = "<img src=x onerror=alert(1)>"
    html_out = render([make_snapshot(ticker=payload)])
    assert f"<td>{payload}</td>" not in html_out
    assert "&lt;img src=x onerror=alert(1)&gt;" in html_out


def test_render_dashboard_includes_all_configured_tickers():
    snapshots = [make_snapshot(ticker="NVDA"), make_snapshot(ticker="AMD"), make_snapshot(ticker="TSM")]
    html_out = render(snapshots)
    for ticker in ("NVDA", "AMD", "TSM"):
        assert f'value="{ticker}"' in html_out


def test_render_dashboard_shows_placeholder_with_single_snapshot_date():
    html_out = render([make_snapshot()], sector_pe_trend=[("2026-07-27", 42.0)])
    assert "second `sync`" in html_out


def test_render_dashboard_omits_placeholder_with_multiple_snapshot_dates():
    html_out = render(
        [make_snapshot()],
        sector_pe_trend=[("2026-07-20", 40.0), ("2026-07-27", 42.0)],
    )
    assert "second `sync`" not in html_out


def test_render_dashboard_labels_ai_narrative_source():
    html_out = render([make_snapshot()], narrative_source="ai")
    assert "AI-generated sector narrative" in html_out


def test_render_dashboard_labels_template_narrative_source():
    html_out = render([make_snapshot()], narrative_source="template")
    assert "Deterministic sector summary" in html_out


def test_render_dashboard_embeds_price_history_data():
    html_out = render([make_snapshot(ticker="NVDA")])
    assert "2026-07-25" in html_out
    assert "105.0" in html_out


def test_render_dashboard_includes_filter_chips_per_subsector():
    snapshots = [
        make_snapshot(ticker="NVDA", subsector="GPU / AI Accelerators"),
        make_snapshot(ticker="MU", subsector="Memory"),
    ]
    html_out = render(snapshots)
    assert 'data-subsector="GPU / AI Accelerators"' in html_out
    assert 'data-subsector="Memory"' in html_out
