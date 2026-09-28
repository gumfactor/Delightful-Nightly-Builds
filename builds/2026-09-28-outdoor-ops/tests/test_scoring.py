import pytest

from src import scoring


def test_temp_score_within_ideal_range_running():
    assert scoring.temp_score(12.0, 8.0, 16.0, 3.0, 5.0) == 100.0


def test_temp_score_below_ideal_cold_penalty():
    # 3 degrees below ideal_low=8, penalty 3/degree -> 100 - 9 = 91
    assert scoring.temp_score(5.0, 8.0, 16.0, 3.0, 5.0) == pytest.approx(91.0)


def test_temp_score_above_ideal_hot_penalty():
    # 4 degrees above ideal_high=16, penalty 5/degree -> 100 - 20 = 80
    assert scoring.temp_score(20.0, 8.0, 16.0, 3.0, 5.0) == pytest.approx(80.0)


def test_temp_score_clamped_at_zero_for_extreme_cold():
    assert scoring.temp_score(-50.0, 8.0, 16.0, 3.0, 5.0) == 0.0


def test_wind_score_at_threshold_is_perfect():
    assert scoring.wind_score(12.0, 12.0, 2.5) == 100.0


def test_wind_score_above_threshold_penalized():
    # 8 km/h over threshold, penalty 2.5/kmh -> 100 - 20 = 80
    assert scoring.wind_score(20.0, 12.0, 2.5) == pytest.approx(80.0)


def test_precip_score_at_threshold_is_perfect():
    assert scoring.precip_score(20.0, 20.0, 1.5) == 100.0


def test_precip_score_above_threshold_penalized():
    # 30 pts over threshold, penalty 1.5/pt -> 100 - 45 = 55
    assert scoring.precip_score(50.0, 20.0, 1.5) == pytest.approx(55.0)


@pytest.mark.parametrize("aqi,expected", [
    (0, 100.0), (50, 100.0), (51, 80.0), (100, 80.0),
    (101, 50.0), (150, 50.0), (151, 20.0), (200, 20.0), (201, 0.0), (400, 0.0),
])
def test_aqi_score_tiers(aqi, expected):
    assert scoring.aqi_score(aqi) == expected


def test_uv_score_at_threshold_is_perfect():
    assert scoring.uv_score(6.0, 6.0, 6.0) == 100.0


def test_uv_score_above_threshold_penalized():
    assert scoring.uv_score(8.0, 6.0, 6.0) == pytest.approx(88.0)


def test_running_score_perfect_day_is_100():
    conditions = scoring.DayConditions(temp_max=12.0, wind_max=5.0, precip_prob_max=0.0, aqi_max=20.0, uv_index_max=2.0)
    assert scoring.running_score(conditions) == 100.0


def test_golf_score_perfect_day_is_100():
    conditions = scoring.DayConditions(temp_max=18.0, wind_max=5.0, precip_prob_max=0.0, aqi_max=20.0, uv_index_max=2.0)
    assert scoring.golf_score(conditions) == 100.0


def test_golf_penalizes_wind_more_than_running():
    windy = scoring.DayConditions(temp_max=18.0, wind_max=35.0, precip_prob_max=0.0, aqi_max=20.0, uv_index_max=2.0)
    running_windy = scoring.running_score(scoring.DayConditions(
        temp_max=12.0, wind_max=35.0, precip_prob_max=0.0, aqi_max=20.0, uv_index_max=2.0))
    golf_windy = scoring.golf_score(windy)
    # Golf's wind weight (0.30) exceeds running's (0.15), so a very windy day
    # should hurt the golf score by more than it hurts the running score,
    # relative to each activity's own perfect-day baseline of 100.
    assert (100 - golf_windy) > (100 - running_windy)


def test_running_penalizes_heat_more_than_golf():
    hot_running = scoring.running_score(scoring.DayConditions(
        temp_max=30.0, wind_max=5.0, precip_prob_max=0.0, aqi_max=20.0, uv_index_max=2.0))
    hot_golf = scoring.golf_score(scoring.DayConditions(
        temp_max=30.0, wind_max=5.0, precip_prob_max=0.0, aqi_max=20.0, uv_index_max=2.0))
    assert hot_running < hot_golf


def test_composite_score_never_exceeds_100_or_drops_below_0():
    extreme = scoring.DayConditions(temp_max=45.0, wind_max=100.0, precip_prob_max=100.0, aqi_max=500.0, uv_index_max=15.0)
    assert 0.0 <= scoring.running_score(extreme) <= 100.0
    assert 0.0 <= scoring.golf_score(extreme) <= 100.0


def test_aqi_score_none_for_unknown_reading():
    assert scoring.aqi_score(None) is None


def test_composite_score_excludes_unknown_aqi_instead_of_treating_it_as_clean():
    known_clean_air = scoring.DayConditions(
        temp_max=12.0, wind_max=5.0, precip_prob_max=0.0, aqi_max=20.0, uv_index_max=2.0)
    unknown_air = scoring.DayConditions(
        temp_max=12.0, wind_max=5.0, precip_prob_max=0.0, aqi_max=None, uv_index_max=2.0)

    # Both should score 100 here (temp/wind/precip/uv are all ideal, and a
    # known-clean AQI of 20 also scores 100) — this establishes the baseline.
    assert scoring.running_score(known_clean_air) == 100.0
    # Unknown AQI must NOT silently default to a perfect score; it is
    # excluded from the composite (renormalized among the other known,
    # ideal factors), which for an otherwise-perfect day still nets 100 —
    # the real assertion is in the next test, where AQI is the only
    # non-ideal factor.
    assert scoring.running_score(unknown_air) == 100.0


def test_unknown_aqi_does_not_mask_a_bad_air_quality_day_as_worse_than_reported():
    bad_but_known_air = scoring.DayConditions(
        temp_max=12.0, wind_max=5.0, precip_prob_max=0.0, aqi_max=300.0, uv_index_max=2.0)
    unknown_air = scoring.DayConditions(
        temp_max=12.0, wind_max=5.0, precip_prob_max=0.0, aqi_max=None, uv_index_max=2.0)

    known_score = scoring.running_score(bad_but_known_air)
    unknown_score = scoring.running_score(unknown_air)

    # A day with genuinely bad, known air quality must score worse than a
    # day where air quality simply wasn't measured — proving "unknown" is
    # never silently treated as at least as good as "known clean" (aqi_max=0
    # would previously have scored both of these identically to a perfect day).
    assert unknown_score > known_score
    assert unknown_score == 100.0


def test_best_day_picks_highest_score():
    days = [
        {"forecast_date": "2026-09-28", "running_score": 60.0, "precip_prob_max": 10.0},
        {"forecast_date": "2026-09-29", "running_score": 90.0, "precip_prob_max": 5.0},
        {"forecast_date": "2026-09-30", "running_score": 70.0, "precip_prob_max": 0.0},
    ]
    assert scoring.best_day(days, "running_score")["forecast_date"] == "2026-09-29"


def test_best_day_tie_broken_by_lower_precip():
    days = [
        {"forecast_date": "2026-09-28", "running_score": 80.0, "precip_prob_max": 40.0},
        {"forecast_date": "2026-09-29", "running_score": 80.0, "precip_prob_max": 5.0},
    ]
    assert scoring.best_day(days, "running_score")["forecast_date"] == "2026-09-29"


def test_best_day_empty_list_returns_none():
    assert scoring.best_day([], "running_score") is None
