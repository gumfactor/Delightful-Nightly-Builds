import json
import math
from datetime import datetime, timedelta

import pytest

import fetch_data


def make_history(start_date: str, num_days: int, prices):
    """Build a (date_str, close) history for num_days sequential dates starting
    at start_date, using prices(i) to compute each close."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    return [
        ((start + timedelta(days=i)).strftime("%Y-%m-%d"), prices(i))
        for i in range(num_days)
    ]


def make_history_around(decision_date: str, days_before=200, days_after=150, prices=None):
    """Build a (date_str, close) history spanning days_before/days_after around
    decision_date, with decision_date itself included. Returns (history, decision_idx).
    Generous enough on both sides to clear MIN_CHART_DAYS/MIN_FORWARD_DAYS."""
    if prices is None:
        prices = lambda i: 100.0 + i * 0.05
    start = datetime.strptime(decision_date, "%Y-%m-%d") - timedelta(days=days_before)
    total_days = days_before + days_after + 1
    history = [
        ((start + timedelta(days=i)).strftime("%Y-%m-%d"), prices(i))
        for i in range(total_days)
    ]
    return history, days_before


# --- classify_outcome --------------------------------------------------------

def test_classify_outcome_up():
    assert fetch_data.classify_outcome(12.3) == "up"


def test_classify_outcome_down():
    assert fetch_data.classify_outcome(-8.1) == "down"


def test_classify_outcome_flat_inside_band():
    assert fetch_data.classify_outcome(2.0) == "flat"
    assert fetch_data.classify_outcome(-2.0) == "flat"


def test_classify_outcome_exact_boundary_is_flat():
    # Boundary values equal to the band width are flat, not up/down.
    assert fetch_data.classify_outcome(fetch_data.FLAT_BAND_PCT) == "flat"
    assert fetch_data.classify_outcome(-fetch_data.FLAT_BAND_PCT) == "flat"


# --- annualized_volatility ----------------------------------------------------

def test_annualized_volatility_zero_for_constant_prices():
    closes = [100.0] * 30
    assert fetch_data.annualized_volatility(closes) == 0.0


def test_annualized_volatility_positive_for_varying_prices():
    closes = [100, 102, 99, 105, 98, 103, 101, 107, 96, 110]
    vol = fetch_data.annualized_volatility(closes)
    assert vol > 0.0


def test_annualized_volatility_handles_short_series():
    assert fetch_data.annualized_volatility([100.0]) == 0.0
    assert fetch_data.annualized_volatility([]) == 0.0


# --- trailing_return_pct -------------------------------------------------------

def test_trailing_return_pct_positive():
    assert fetch_data.trailing_return_pct([100.0, 110.0]) == pytest.approx(10.0)


def test_trailing_return_pct_negative():
    assert fetch_data.trailing_return_pct([100.0, 80.0]) == pytest.approx(-20.0)


def test_trailing_return_pct_empty_list_returns_zero():
    assert fetch_data.trailing_return_pct([]) == 0.0


# --- build_round ---------------------------------------------------------------

def _spec(decision_date="2020-01-15"):
    return fetch_data.RoundSpec("TEST", decision_date, "Test Co.", "Technology", "Software")


def test_build_round_happy_path_computes_correct_outcome_and_metrics():
    decision_date = "2019-08-01"
    # Flat 100.0 through the decision date, then a clean ramp up over the forward window.
    history, decision_idx = make_history_around(decision_date, prices=None)
    history = [
        (d, 100.0 if i <= decision_idx else 100.0 + (i - decision_idx) * 1.5)
        for i, (d, _) in enumerate(history)
    ]
    spec = _spec(decision_date=decision_date)
    result = fetch_data.build_round(spec, history)

    assert result is not None
    assert result["id"] == f"TEST-{spec.decision_date}"
    assert result["sector"] == "Technology"
    assert result["forward"]["outcome"] == "up"
    assert result["forward"]["pctChange"] > fetch_data.FLAT_BAND_PCT
    assert result["metrics"]["trailingReturnPct"] == 0.0
    assert len(result["chart"]) >= fetch_data.MIN_CHART_DAYS
    assert len(result["forward"]["chart"]) >= fetch_data.MIN_FORWARD_DAYS


def test_build_round_flat_outcome_within_band():
    decision_date = "2019-08-01"
    history, _ = make_history_around(
        decision_date, prices=lambda i: 100.0 + (0.5 if i % 2 == 0 else -0.5)
    )
    spec = _spec(decision_date=decision_date)
    result = fetch_data.build_round(spec, history)
    assert result is not None
    assert result["forward"]["outcome"] == "flat"


def test_build_round_skips_when_insufficient_chart_history():
    # Only 40 days before the decision date, below MIN_CHART_DAYS.
    history = make_history("2020-01-01", 40, lambda i: 100.0 + i)
    decision_date = history[-1][0]
    forward = make_history(
        (datetime.strptime(decision_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
        80,
        lambda i: 140.0 + i,
    )
    full_history = history + forward
    spec = _spec(decision_date=decision_date)
    assert fetch_data.build_round(spec, full_history) is None


def test_build_round_skips_when_insufficient_forward_history():
    history = make_history("2019-06-01", 200, lambda i: 100.0 + i * 0.1)
    decision_date = history[-1][0]
    # Only 20 forward days available, below MIN_FORWARD_DAYS.
    forward = make_history(
        (datetime.strptime(decision_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
        20,
        lambda i: 120.0 + i,
    )
    full_history = history + forward
    spec = _spec(decision_date=decision_date)
    assert fetch_data.build_round(spec, full_history) is None


def test_build_round_returns_none_when_decision_date_beyond_history():
    history = make_history("2019-06-01", 100, lambda i: 100.0 + i)
    spec = _spec(decision_date="2030-01-01")
    assert fetch_data.build_round(spec, history) is None


# --- to_js -----------------------------------------------------------------

def test_to_js_produces_a_valid_const_assignment_with_parseable_json():
    rounds = [{"id": "TEST-2020-01-15", "ticker": "TEST", "forward": {"outcome": "up"}}]
    js = fetch_data.to_js(rounds)
    assert js.startswith("//")
    assert "const ROUNDS_DATA = " in js
    json_text = js.split("const ROUNDS_DATA = ", 1)[1].rstrip(";\n")
    parsed = json.loads(json_text)
    assert parsed == rounds


# --- main() with mocked fetch_history (no real network calls) -----------------

def test_main_writes_output_file_using_mocked_fetch_history(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    monkeypatch.setattr(fetch_data, "OUTPUT_FILE", tmp_path / "rounds-data.js")

    call_count = {"n": 0}

    def fake_fetch_history(ticker, decision_date):
        call_count["n"] += 1
        history, _ = make_history_around(decision_date, prices=lambda i: 50.0 + i * 0.2)
        return history

    monkeypatch.setattr(fetch_data, "fetch_history", fake_fetch_history)
    monkeypatch.setattr(
        fetch_data,
        "CURATED_ROUNDS",
        [fetch_data.RoundSpec("AAA", "2019-08-01", "AAA Co.", "Technology", "Software")],
    )

    exit_code = fetch_data.main()

    assert exit_code == 0
    assert call_count["n"] == 1  # confirms only the mock was hit, never a real API
    output = (tmp_path / "rounds-data.js").read_text()
    assert "const ROUNDS_DATA = " in output
    json_text = output.split("const ROUNDS_DATA = ", 1)[1].rstrip(";\n")
    rounds = json.loads(json_text)
    assert len(rounds) == 1
    assert rounds[0]["ticker"] == "AAA"


def test_main_skips_ticker_on_fetch_exception_without_crashing(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    monkeypatch.setattr(fetch_data, "OUTPUT_FILE", tmp_path / "rounds-data.js")

    def flaky_fetch_history(ticker, decision_date):
        if ticker == "BAD":
            raise ConnectionError("simulated network failure")
        history, _ = make_history_around(decision_date, prices=lambda i: 50.0 + i * 0.2)
        return history

    monkeypatch.setattr(fetch_data, "fetch_history", flaky_fetch_history)
    monkeypatch.setattr(
        fetch_data,
        "CURATED_ROUNDS",
        [
            fetch_data.RoundSpec("BAD", "2019-08-01", "Bad Co.", "Technology", "Software"),
            fetch_data.RoundSpec("GOOD", "2019-08-01", "Good Co.", "Technology", "Software"),
        ],
    )

    exit_code = fetch_data.main()
    assert exit_code == 0
    output = (tmp_path / "rounds-data.js").read_text()
    json_text = output.split("const ROUNDS_DATA = ", 1)[1].rstrip(";\n")
    rounds = json.loads(json_text)
    assert len(rounds) == 1
    assert rounds[0]["ticker"] == "GOOD"


def test_main_returns_nonzero_when_all_tickers_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_data, "DATA_DIR", tmp_path)
    monkeypatch.setattr(fetch_data, "OUTPUT_FILE", tmp_path / "rounds-data.js")
    monkeypatch.setattr(
        fetch_data, "fetch_history", lambda ticker, decision_date: (_ for _ in ()).throw(ConnectionError())
    )
    monkeypatch.setattr(
        fetch_data,
        "CURATED_ROUNDS",
        [fetch_data.RoundSpec("BAD", "2019-08-01", "Bad Co.", "Technology", "Software")],
    )

    exit_code = fetch_data.main()
    assert exit_code == 1
    assert not (tmp_path / "rounds-data.js").exists()


# --- curated data integrity ----------------------------------------------------

def test_curated_rounds_have_unique_ids():
    ids = [f"{spec.ticker}-{spec.decision_date}" for spec in fetch_data.CURATED_ROUNDS]
    assert len(ids) == len(set(ids))


def test_curated_rounds_cover_at_least_ten_sectors():
    sectors = {spec.sector for spec in fetch_data.CURATED_ROUNDS}
    assert len(sectors) >= 10


def test_curated_rounds_decision_dates_are_historically_settled():
    # Every curated decision date must be old enough that a full forward
    # quarter is already in the past relative to when this catalog entry was
    # written (2026), so outcomes never depend on data that doesn't exist yet.
    cutoff = datetime(2024, 1, 1)
    for spec in fetch_data.CURATED_ROUNDS:
        decision_dt = datetime.strptime(spec.decision_date, "%Y-%m-%d")
        assert decision_dt < cutoff, f"{spec.ticker} decision date {spec.decision_date} is too recent"
