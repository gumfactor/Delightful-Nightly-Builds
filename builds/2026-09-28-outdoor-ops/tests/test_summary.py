import pytest

from src import summary


def make_day(date, running_score, golf_score, temp_max=12.0, wind_max=5.0,
             precip_prob_max=0.0, aqi_max=20.0, uv_index_max=2.0):
    return {
        "forecast_date": date, "running_score": running_score, "golf_score": golf_score,
        "temp_max": temp_max, "wind_max": wind_max, "precip_prob_max": precip_prob_max,
        "aqi_max": aqi_max, "uv_index_max": uv_index_max,
    }


def test_build_week_summary_identifies_best_and_worst_days():
    days = [
        make_day("2026-09-28", running_score=90.0, golf_score=40.0),
        make_day("2026-09-29", running_score=55.0, golf_score=95.0, wind_max=40.0),
        make_day("2026-09-30", running_score=70.0, golf_score=70.0),
    ]
    result = summary.build_week_summary(days)
    assert result["best_running_day"] == "2026-09-28"
    assert result["worst_running_day"] == "2026-09-29"
    assert result["best_golf_day"] == "2026-09-29"
    assert result["worst_golf_day"] == "2026-09-28"


def test_build_week_summary_raises_on_empty_days():
    with pytest.raises(ValueError):
        summary.build_week_summary([])


def test_limiting_factor_identifies_wind_for_windy_worst_golf_day():
    days = [
        make_day("2026-09-28", running_score=90.0, golf_score=95.0),
        make_day("2026-09-29", running_score=85.0, golf_score=30.0, wind_max=50.0),
    ]
    result = summary.build_week_summary(days)
    assert result["golf_limiting_factor"] == "wind"


def test_limiting_factor_identifies_aqi_for_smoky_worst_running_day():
    days = [
        make_day("2026-09-28", running_score=95.0, golf_score=90.0),
        make_day("2026-09-29", running_score=20.0, golf_score=85.0, aqi_max=300.0),
    ]
    result = summary.build_week_summary(days)
    assert result["running_limiting_factor"] == "aqi"
