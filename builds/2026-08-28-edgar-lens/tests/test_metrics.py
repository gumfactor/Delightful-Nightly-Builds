import pytest

from src import metrics

FIXTURE_ROWS = [
    {"fiscal_year": 2021, "revenue": 1000000000, "net_income": 100000000, "operating_income": 120000000,
     "assets": 800000000, "liabilities": 300000000, "equity": 500000000, "cash": 150000000},
    {"fiscal_year": 2022, "revenue": 850000000, "net_income": 80000000, "operating_income": 90000000,
     "assets": 780000000, "liabilities": 320000000, "equity": 460000000, "cash": 120000000},
    {"fiscal_year": 2023, "revenue": 900000000, "net_income": -50000000, "operating_income": -20000000,
     "assets": 750000000, "liabilities": 700000000, "equity": 50000000, "cash": 90000000},
    {"fiscal_year": 2024, "revenue": 700000000, "net_income": -100000000, "operating_income": -80000000,
     "assets": 730000000, "liabilities": 750000000, "equity": -20000000, "cash": 60000000},
]


# --- safe_divide / ratio math -------------------------------------------------

def test_safe_divide_normal():
    assert metrics.safe_divide(10, 4) == 2.5


def test_safe_divide_zero_denominator_returns_none():
    assert metrics.safe_divide(10, 0) is None


def test_safe_divide_none_inputs_return_none():
    assert metrics.safe_divide(None, 5) is None
    assert metrics.safe_divide(5, None) is None


def test_net_margin_hand_worked():
    # 100M net income on 1000M revenue = 10.0%
    assert metrics.net_margin(1000000000, 100000000) == pytest.approx(0.10)


def test_debt_to_equity_hand_worked():
    assert metrics.debt_to_equity(300000000, 500000000) == pytest.approx(0.6)


def test_debt_to_equity_none_when_equity_zero_or_negative():
    assert metrics.debt_to_equity(700000000, 0) is None
    assert metrics.debt_to_equity(700000000, -20000000) is None


def test_yoy_change_hand_worked():
    # 850M vs 1000M = -15.0%
    assert metrics.yoy_change(850000000, 1000000000) == pytest.approx(-0.15)


def test_yoy_change_none_when_previous_zero():
    assert metrics.yoy_change(100, 0) is None


# --- compute_yearly_metrics ---------------------------------------------------

def test_first_year_has_no_yoy_fields():
    enriched = metrics.compute_yearly_metrics(FIXTURE_ROWS)
    assert enriched[0]["revenue_yoy"] is None
    assert enriched[0]["net_margin_delta"] is None
    assert enriched[0]["debt_to_equity_delta"] is None


def test_compute_yearly_metrics_matches_hand_calculation():
    enriched = metrics.compute_yearly_metrics(FIXTURE_ROWS)
    fy2023 = next(r for r in enriched if r["fiscal_year"] == 2023)
    assert fy2023["net_margin"] == pytest.approx(-50000000 / 900000000)
    assert fy2023["debt_to_equity"] == pytest.approx(14.0)
    assert fy2023["revenue_yoy"] == pytest.approx((900000000 - 850000000) / 850000000)
    fy2022 = next(r for r in enriched if r["fiscal_year"] == 2022)
    assert fy2023["net_margin_delta"] == pytest.approx(fy2023["net_margin"] - fy2022["net_margin"])


def test_compute_yearly_metrics_debt_to_equity_delta_none_when_current_undefined():
    enriched = metrics.compute_yearly_metrics(FIXTURE_ROWS)
    fy2024 = next(r for r in enriched if r["fiscal_year"] == 2024)
    # equity is negative in 2024 -> debt_to_equity is None -> delta must be None too
    assert fy2024["debt_to_equity"] is None
    assert fy2024["debt_to_equity_delta"] is None


def test_compute_yearly_metrics_does_not_mutate_input():
    original = [dict(r) for r in FIXTURE_ROWS]
    metrics.compute_yearly_metrics(FIXTURE_ROWS)
    assert FIXTURE_ROWS == original


# --- anomaly flagging ----------------------------------------------------------

def test_flag_anomalies_full_fixture_sequence():
    enriched = metrics.compute_yearly_metrics(FIXTURE_ROWS)
    anomalies = metrics.flag_anomalies(enriched)
    by_fy_type = {(a["fiscal_year"], a["type"]) for a in anomalies}
    assert (2022, "revenue_decline") in by_fy_type
    assert (2023, "margin_compression") in by_fy_type
    assert (2023, "leverage_spike") in by_fy_type
    assert (2023, "swing_to_loss") in by_fy_type
    assert (2024, "revenue_decline") in by_fy_type
    assert (2024, "margin_compression") in by_fy_type
    assert (2024, "negative_equity") in by_fy_type
    assert len(anomalies) == 7


def test_swing_to_loss_does_not_refire_while_already_in_loss():
    enriched = metrics.compute_yearly_metrics(FIXTURE_ROWS)
    anomalies = metrics.flag_anomalies(enriched)
    swing_years = [a["fiscal_year"] for a in anomalies if a["type"] == "swing_to_loss"]
    assert swing_years == [2023]  # not 2024, which was already a loss year


def test_revenue_decline_threshold_boundary():
    rows = [
        {"fiscal_year": 2020, "revenue": 1000, "net_income": None, "operating_income": None,
         "liabilities": None, "equity": None},
        {"fiscal_year": 2021, "revenue": 901, "net_income": None, "operating_income": None,
         "liabilities": None, "equity": None},  # -9.9%, must NOT flag
    ]
    enriched = metrics.compute_yearly_metrics(rows)
    anomalies = metrics.flag_anomalies(enriched)
    assert not any(a["type"] == "revenue_decline" for a in anomalies)

    rows[1]["revenue"] = 900  # exactly -10.0%, must flag
    enriched = metrics.compute_yearly_metrics(rows)
    anomalies = metrics.flag_anomalies(enriched)
    assert any(a["type"] == "revenue_decline" for a in anomalies)


def test_negative_equity_threshold_boundary():
    rows = [
        {"fiscal_year": 2020, "revenue": None, "net_income": None, "operating_income": None,
         "liabilities": None, "equity": 1},
    ]
    assert metrics.flag_anomalies(metrics.compute_yearly_metrics(rows)) == []

    rows[0]["equity"] = 0
    anomalies = metrics.flag_anomalies(metrics.compute_yearly_metrics(rows))
    assert any(a["type"] == "negative_equity" for a in anomalies)

    rows[0]["equity"] = -1
    anomalies = metrics.flag_anomalies(metrics.compute_yearly_metrics(rows))
    assert any(a["type"] == "negative_equity" for a in anomalies)


def test_leverage_spike_threshold_boundary():
    rows = [
        {"fiscal_year": 2020, "revenue": None, "net_income": None, "operating_income": None,
         "liabilities": 100, "equity": 100},  # D/E = 1.0
        {"fiscal_year": 2021, "revenue": None, "net_income": None, "operating_income": None,
         "liabilities": 149, "equity": 100},  # D/E = 1.49, delta 0.49 -> must NOT flag
    ]
    anomalies = metrics.flag_anomalies(metrics.compute_yearly_metrics(rows))
    assert not any(a["type"] == "leverage_spike" for a in anomalies)

    rows[1]["liabilities"] = 150  # D/E = 1.50, delta exactly 0.5 -> must flag
    anomalies = metrics.flag_anomalies(metrics.compute_yearly_metrics(rows))
    assert any(a["type"] == "leverage_spike" for a in anomalies)


def test_flag_anomalies_handles_all_none_row_without_crashing():
    rows = [{"fiscal_year": 2020, "revenue": None, "net_income": None, "operating_income": None,
             "liabilities": None, "equity": None}]
    assert metrics.flag_anomalies(metrics.compute_yearly_metrics(rows)) == []


def test_flag_anomalies_empty_input():
    assert metrics.flag_anomalies([]) == []
