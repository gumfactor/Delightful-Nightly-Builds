"""Tests for src/analytics.py, including hand-computed fixture values.

See BUILD_LOG.md for the closed-form derivation of the fixture in
test_rs_ratio_and_momentum_against_hand_computed_fixture: with a
perfectly symmetric 3-sector deviation pattern {+d, 0, -d} around the
cross-sectional mean, the sample z-score collapses to {+1, 0, -1}
regardless of the magnitude of d -- this is a real mathematical property
of z-scoring three symmetric points, not a bug, and is exactly why the
expected RS-Ratio values below are a clean 101 / 100 / 99 plateau.
"""

import pytest

from src.analytics import (
    InsufficientDataError,
    classify_quadrant,
    compute_rotation,
    compute_rs_lines,
    _cross_sectional_zscores,
    _sma,
)


def test_sma_returns_none_before_window_is_full():
    series = [1.0, 2.0, 3.0]
    assert _sma(series, window=3, index=1) is None


def test_sma_hand_computed():
    series = [1.0, 2.0, 3.0, 4.0, 5.0]
    # window=3 ending at index 3 (values 2,3,4) -> mean 3.0
    assert _sma(series, window=3, index=3) == pytest.approx(3.0)


def test_cross_sectional_zscore_hand_computed():
    # mean=2, sample std (ddof=1) of [1,2,3] = 1.0 -> z = [-1, 0, 1]
    result = _cross_sectional_zscores({"A": 1.0, "B": 2.0, "C": 3.0})
    assert result["A"] == pytest.approx(-1.0)
    assert result["B"] == pytest.approx(0.0)
    assert result["C"] == pytest.approx(1.0)


def test_cross_sectional_zscore_zero_std_guard():
    result = _cross_sectional_zscores({"A": 5.0, "B": 5.0, "C": 5.0})
    assert result == {"A": 0.0, "B": 0.0, "C": 0.0}


def test_cross_sectional_zscore_single_value_guard():
    result = _cross_sectional_zscores({"A": 5.0})
    assert result == {"A": 0.0}


def test_cross_sectional_zscore_ignores_none_values():
    result = _cross_sectional_zscores({"A": 1.0, "B": 2.0, "C": 3.0, "D": None})
    assert result["D"] is None
    assert result["A"] == pytest.approx(-1.0)


def test_classify_quadrant_leading():
    assert classify_quadrant(105, 105) == "Leading"


def test_classify_quadrant_weakening():
    assert classify_quadrant(105, 95) == "Weakening"


def test_classify_quadrant_lagging():
    assert classify_quadrant(95, 95) == "Lagging"


def test_classify_quadrant_improving():
    assert classify_quadrant(95, 105) == "Improving"


def test_classify_quadrant_exact_boundary_is_leading():
    # Fixed convention documented in PRD.md: exactly 100/100 counts as Leading.
    assert classify_quadrant(100, 100) == "Leading"
    assert classify_quadrant(100, 99.999) == "Weakening"
    assert classify_quadrant(99.999, 100) == "Improving"


def test_compute_rs_lines_hand_computed():
    prices = {
        "BENCH": [("d1", 100.0), ("d2", 100.0)],
        "A": [("d1", 110.0), ("d2", 120.0)],
    }
    rs = compute_rs_lines(prices, benchmark="BENCH")
    assert rs["A"] == [("d1", 110.0), ("d2", 120.0)]


def test_compute_rs_lines_missing_benchmark_raises():
    with pytest.raises(InsufficientDataError):
        compute_rs_lines({"A": [("d1", 1.0)]}, benchmark="BENCH")


def test_compute_rs_lines_mismatched_length_raises():
    prices = {
        "BENCH": [("d1", 100.0), ("d2", 100.0)],
        "A": [("d1", 110.0)],
    }
    with pytest.raises(InsufficientDataError):
        compute_rs_lines(prices, benchmark="BENCH")


def _symmetric_fixture(n=20):
    """Benchmark flat; A rises 0.5/day, B flat, C falls 0.5/day -- see module docstring."""
    bench = [("2026-01-%02d" % (i + 1), 100.0) for i in range(n)]
    a = [("2026-01-%02d" % (i + 1), 100.0 + 0.5 * i) for i in range(n)]
    b = [("2026-01-%02d" % (i + 1), 100.0) for i in range(n)]
    c = [("2026-01-%02d" % (i + 1), 100.0 - 0.5 * i) for i in range(n)]
    return {"BENCH": bench, "A": a, "B": b, "C": c}


def test_rs_ratio_and_momentum_against_hand_computed_fixture():
    prices = _symmetric_fixture(n=20)
    results = compute_rotation(
        prices, benchmark="BENCH", ratio_window=5, momentum_window=5, tail_length=10
    )

    assert results["A"].latest.rs_ratio == pytest.approx(101.0)
    assert results["B"].latest.rs_ratio == pytest.approx(100.0)
    assert results["C"].latest.rs_ratio == pytest.approx(99.0)

    # Hand-derived: RS-Ratio plateaus after the transient, so the 5-day
    # difference (raw momentum) is 0 for every sector -> all z-scores 0 -> 100.
    assert results["A"].latest.rs_momentum == pytest.approx(100.0)
    assert results["B"].latest.rs_momentum == pytest.approx(100.0)
    assert results["C"].latest.rs_momentum == pytest.approx(100.0)

    assert results["A"].latest.quadrant == "Leading"
    assert results["B"].latest.quadrant == "Leading"  # exact-100 boundary convention
    assert results["C"].latest.quadrant == "Improving"


def test_compute_rotation_tail_length_and_order():
    prices = _symmetric_fixture(n=20)
    results = compute_rotation(
        prices, benchmark="BENCH", ratio_window=5, momentum_window=5, tail_length=3
    )
    tail = results["A"].tail
    assert len(tail) == 3
    assert tail[0].date < tail[1].date < tail[2].date


def test_compute_rotation_insufficient_history_raises():
    prices = _symmetric_fixture(n=5)  # ratio_window(5)+momentum_window(5) needs 10+ days
    with pytest.raises(InsufficientDataError):
        compute_rotation(prices, benchmark="BENCH", ratio_window=5, momentum_window=5)


def test_compute_rotation_previous_point_is_one_day_before_latest():
    prices = _symmetric_fixture(n=20)
    results = compute_rotation(prices, benchmark="BENCH", ratio_window=5, momentum_window=5)
    assert results["A"].previous is not None
    assert results["A"].previous.date == "2026-01-19"
    assert results["A"].latest.date == "2026-01-20"
