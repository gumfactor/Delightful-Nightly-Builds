from metrics import compute_price_deltas, compute_sector_aggregates


def test_compute_price_deltas_empty_history():
    result = compute_price_deltas([])
    assert result == {
        "latest": None,
        "since_prev_pct": None,
        "since_1y_pct": None,
        "since_1y_reliable": False,
    }


def test_compute_price_deltas_single_point():
    result = compute_price_deltas([("2026-07-27", 100.0)])
    assert result["latest"] == 100.0
    assert result["since_prev_pct"] is None
    assert result["since_1y_pct"] == 0.0
    assert result["since_1y_reliable"] is False


def test_compute_price_deltas_since_prev_day():
    history = [("2026-07-26", 100.0), ("2026-07-27", 110.0)]
    result = compute_price_deltas(history)
    assert result["since_prev_pct"] == 10.0


def test_compute_price_deltas_1y_reliable_when_span_is_long():
    history = [("2025-07-27", 100.0), ("2026-07-27", 150.0)]
    result = compute_price_deltas(history)
    assert result["since_1y_pct"] == 50.0
    assert result["since_1y_reliable"] is True


def test_compute_price_deltas_1y_unreliable_when_span_is_short():
    history = [("2026-07-01", 100.0), ("2026-07-27", 105.0)]
    result = compute_price_deltas(history)
    assert result["since_1y_reliable"] is False


def test_compute_sector_aggregates_basic_totals():
    snapshots = [
        {"ticker": "NVDA", "name": "NVIDIA", "market_cap": 3000.0, "pe_trailing": 40.0, "profit_margin": 0.5, "revenue_growth": 0.6, "since_1y_pct": 80.0},
        {"ticker": "AMD", "name": "AMD", "market_cap": 200.0, "pe_trailing": 60.0, "profit_margin": 0.2, "revenue_growth": -0.1, "since_1y_pct": -10.0},
    ]
    aggregates = compute_sector_aggregates(snapshots)
    assert aggregates["total_market_cap"] == 3200.0
    assert aggregates["avg_pe_trailing"] == 50.0
    assert aggregates["avg_profit_margin"] == 0.35
    assert aggregates["growth_positive_count"] == 1
    assert aggregates["companies_tracked"] == 2
    assert aggregates["top_mover"]["ticker"] == "NVDA"
    assert aggregates["laggard"]["ticker"] == "AMD"


def test_compute_sector_aggregates_ignores_none_values():
    snapshots = [
        {"ticker": "NVDA", "name": "NVIDIA", "market_cap": None, "pe_trailing": None, "profit_margin": None, "revenue_growth": None},
        {"ticker": "AMD", "name": "AMD", "market_cap": 200.0, "pe_trailing": 60.0, "profit_margin": 0.2, "revenue_growth": 0.1},
    ]
    aggregates = compute_sector_aggregates(snapshots)
    assert aggregates["total_market_cap"] == 200.0
    assert aggregates["avg_pe_trailing"] == 60.0
    assert aggregates["growth_positive_count"] == 1


def test_compute_sector_aggregates_no_movers_when_no_deltas():
    snapshots = [{"ticker": "NVDA", "name": "NVIDIA", "market_cap": 100.0, "pe_trailing": 40.0, "profit_margin": 0.5, "revenue_growth": 0.1}]
    aggregates = compute_sector_aggregates(snapshots)
    assert aggregates["top_mover"] is None
    assert aggregates["laggard"] is None


def test_compute_sector_aggregates_empty_list():
    aggregates = compute_sector_aggregates([])
    assert aggregates["total_market_cap"] is None
    assert aggregates["avg_pe_trailing"] is None
    assert aggregates["companies_tracked"] == 0
