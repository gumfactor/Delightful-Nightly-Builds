import pytest

from src import scoring


@pytest.mark.parametrize(
    "knots,expected_number,expected_name",
    [
        (0.0, 0, "Calm"),
        (0.9, 0, "Calm"),
        (1.0, 1, "Light Air"),
        (3.9, 1, "Light Air"),
        (4.0, 2, "Light Breeze"),
        (6.9, 2, "Light Breeze"),
        (7.0, 3, "Gentle Breeze"),
        (10.9, 3, "Gentle Breeze"),
        (11.0, 4, "Moderate Breeze"),
        (16.9, 4, "Moderate Breeze"),
        (17.0, 5, "Fresh Breeze"),
        (21.9, 5, "Fresh Breeze"),
        (22.0, 6, "Strong Breeze"),
        (27.9, 6, "Strong Breeze"),
        (28.0, 7, "Near Gale"),
        (33.9, 7, "Near Gale"),
        (34.0, 8, "Gale"),
        (40.9, 8, "Gale"),
        (41.0, 9, "Strong Gale"),
        (47.9, 9, "Strong Gale"),
        (48.0, 10, "Storm"),
        (55.9, 10, "Storm"),
        (56.0, 11, "Violent Storm"),
        (63.9, 11, "Violent Storm"),
        (64.0, 12, "Hurricane Force"),
        (100.0, 12, "Hurricane Force"),
    ],
)
def test_beaufort_boundaries(knots, expected_number, expected_name):
    level = scoring.classify_beaufort(knots)
    assert level.number == expected_number
    assert level.name == expected_name


def test_beaufort_rejects_negative_wind():
    with pytest.raises(ValueError):
        scoring.classify_beaufort(-1.0)


def test_score_zero_when_no_daylight():
    score = scoring.comfort_score(
        wind_knots=10.0, gust_knots=12.0, precip_probability=0.0,
        temp_c=22.0, cloud_cover_pct=10.0, daylight_hours=0,
    )
    assert score == 0.0


def test_score_is_bounded_0_to_100():
    extreme = scoring.comfort_score(
        wind_knots=90.0, gust_knots=150.0, precip_probability=100.0,
        temp_c=-10.0, cloud_cover_pct=100.0, daylight_hours=4,
    )
    assert 0.0 <= extreme <= 100.0

    ideal = scoring.comfort_score(
        wind_knots=12.0, gust_knots=13.0, precip_probability=0.0,
        temp_c=22.0, cloud_cover_pct=0.0, daylight_hours=6,
    )
    assert 0.0 <= ideal <= 100.0


def test_increasing_precip_never_increases_score():
    base_kwargs = dict(wind_knots=10.0, gust_knots=12.0, temp_c=22.0, cloud_cover_pct=20.0, daylight_hours=6)
    scores = [
        scoring.comfort_score(precip_probability=p, **base_kwargs)
        for p in (0, 20, 40, 60, 80, 100)
    ]
    assert scores == sorted(scores, reverse=True)


def test_increasing_gust_factor_never_increases_score():
    scores = []
    for gust in (10.0, 15.0, 20.0, 30.0, 50.0):
        scores.append(
            scoring.comfort_score(
                wind_knots=10.0, gust_knots=gust, precip_probability=0.0,
                temp_c=22.0, cloud_cover_pct=20.0, daylight_hours=6,
            )
        )
    assert scores == sorted(scores, reverse=True)


def test_extreme_temperature_scores_lower_than_ideal_temperature():
    ideal = scoring.comfort_score(
        wind_knots=10.0, gust_knots=11.0, precip_probability=0.0,
        temp_c=22.0, cloud_cover_pct=20.0, daylight_hours=6,
    )
    freezing = scoring.comfort_score(
        wind_knots=10.0, gust_knots=11.0, precip_probability=0.0,
        temp_c=-5.0, cloud_cover_pct=20.0, daylight_hours=6,
    )
    scorching = scoring.comfort_score(
        wind_knots=10.0, gust_knots=11.0, precip_probability=0.0,
        temp_c=40.0, cloud_cover_pct=20.0, daylight_hours=6,
    )
    assert freezing < ideal
    assert scorching < ideal


def test_three_condition_profiles_rank_as_expected():
    """calm/sunny should clearly beat windy/showery, which should clearly
    beat a dangerous-gust profile -- the three PRD-named test profiles."""
    calm_sunny = scoring.comfort_score(
        wind_knots=5.0, gust_knots=6.0, precip_probability=5.0,
        temp_c=22.0, cloud_cover_pct=10.0, daylight_hours=6,
    )
    windy_showery = scoring.comfort_score(
        wind_knots=22.0, gust_knots=25.0, precip_probability=80.0,
        temp_c=12.0, cloud_cover_pct=95.0, daylight_hours=6,
    )
    dangerous_gust = scoring.comfort_score(
        wind_knots=35.0, gust_knots=70.0, precip_probability=50.0,
        temp_c=16.0, cloud_cover_pct=80.0, daylight_hours=6,
    )
    assert calm_sunny > windy_showery > dangerous_gust >= 0


def test_weights_sum_to_one():
    assert abs(sum(scoring.WEIGHTS.values()) - 1.0) < 1e-9
