from datetime import date, timedelta

from canpulse import analysis


def monthly(values, start=date(2020, 1, 1)):
    pts, d = [], start
    for v in values:
        pts.append([d.isoformat(), v])
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return pts


def series(sid, pts, unit="index", freq="M", higher="neutral"):
    return {"id": sid, "label": sid, "unit": unit, "freq": freq, "higher_is": higher, "group": "g", "source": "x", "points": pts}


def test_yoy_percent_for_level_series():
    pts = monthly([100] * 12 + [110])
    assert round(analysis.change(pts, 365, True), 2) == 10.0


def test_yoy_point_change_for_rate_series():
    pts = monthly([5.0] * 12 + [6.5])
    assert round(analysis.change(pts, 365, False), 2) == 1.5


def test_change_none_without_enough_history():
    assert analysis.change(monthly([1, 2, 3]), 365, True) is None


def test_percentile_rank_extremes_and_ties():
    vals = [1, 2, 3, 4]
    assert analysis.percentile_rank(vals, 4) == 87.5
    assert analysis.percentile_rank(vals, 0) == 0
    assert analysis.percentile_rank([], 1) == 50.0


def test_zscore_none_for_constant_or_short():
    assert analysis.zscore([2, 2, 2, 2], 2) is None
    assert analysis.zscore([1, 2], 2) is None


def test_trend_detects_direction():
    assert analysis.trend(monthly(list(range(20))), "M") == "rising"
    assert analysis.trend(monthly(list(range(20, 0, -1))), "M") == "falling"
    assert analysis.trend(monthly([5.0] * 20), "M") == "flat"


def test_classify_polarity():
    assert analysis.classify("u", "bad", "rising", 0.5, 6)[0] == "bad"
    assert analysis.classify("g", "good", "rising", 0.5, 1)[0] == "good"
    assert analysis.classify("x", "neutral", "rising", 0.5, 1)[0] == "neutral"


def test_classify_outlier_is_watch():
    assert analysis.classify("g", "good", "rising", 2.4, 1)[0] == "watch"


def test_curve_inverted_flagged():
    assert analysis.classify("curve", "neutral", "flat", 0, -0.4)[0] == "watch"


def test_derived_curve_aligns_on_common_dates_only():
    ten = series("gov10y", [["2024-01-02", 3.5], ["2024-01-03", 3.6]], "%", "D")
    two = series("gov2y", [["2024-01-03", 4.0], ["2024-01-04", 4.1]], "%", "D")
    out = analysis.build_derived({"gov10y": ten, "gov2y": two})
    assert out["curve"]["points"] == [["2024-01-03", -0.4]]


def test_derived_real_rate_uses_rate_in_force_and_cpi_yoy():
    cpi = series("cpi", monthly([100] * 12 + [103]))  # 3% y/y in Jan 2021
    rate = series("policy_rate", [["2019-12-01", 1.0], ["2021-01-01", 5.0]], "%", "D")
    out = analysis.build_derived({"cpi": cpi, "policy_rate": rate})
    assert out["real_rate"]["points"][-1] == ["2021-01-01", 2.0]


def test_analyze_series_flags_stale_data():
    s = series("u", monthly([5.0] * 30), "%", "M", "bad")
    st = analysis.analyze_series(s, today=date(2023, 6, 1))
    assert st["stale"] is True and st["age_days"] > 75
    fresh = analysis.analyze_series(s, today=date(2022, 7, 15))
    assert fresh["stale"] is False


def test_analyze_all_includes_derived_and_skips_empty():
    ten = series("gov10y", [["2024-01-03", 3.6]], "%", "D")
    two = series("gov2y", [["2024-01-03", 4.0]], "%", "D")
    empty = series("x", [], "%", "D")
    _, stats = analysis.analyze_all({"gov10y": ten, "gov2y": two, "x": empty}, today=date(2024, 1, 5))
    assert "curve" in stats and "x" not in stats
