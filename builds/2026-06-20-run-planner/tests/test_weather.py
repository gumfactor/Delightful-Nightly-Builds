"""Tests for weather.py — scoring functions and forecast parsing."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import weather


# ---------------------------------------------------------------------------
# temp_score
# ---------------------------------------------------------------------------

def test_temp_score_optimal_low_end():
    # 5–15°C is peak zone → 90–100
    assert weather.temp_score(10.0) >= 90.0


def test_temp_score_optimal_high_end():
    assert weather.temp_score(15.0) >= 90.0


def test_temp_score_warm_is_lower():
    # 27°C should score less than 15°C
    assert weather.temp_score(27.0) < weather.temp_score(15.0)


def test_temp_score_hot_is_low():
    assert weather.temp_score(35.0) < 30.0


def test_temp_score_freezing_is_low():
    assert weather.temp_score(-15.0) <= 10.0


def test_temp_score_cold_but_runnable():
    # Near 0°C — unpleasant but doable
    score = weather.temp_score(0.0)
    assert 30.0 <= score <= 60.0


# ---------------------------------------------------------------------------
# wind_score
# ---------------------------------------------------------------------------

def test_wind_score_calm_is_perfect():
    assert weather.wind_score(0.0) == 100.0


def test_wind_score_light_breeze():
    assert weather.wind_score(10.0) == 100.0


def test_wind_score_strong_wind_is_reduced():
    assert weather.wind_score(40.0) < 60.0


def test_wind_score_hurricane_is_minimum():
    assert weather.wind_score(100.0) <= 10.0


# ---------------------------------------------------------------------------
# precip_score
# ---------------------------------------------------------------------------

def test_precip_score_clear_is_perfect():
    assert weather.precip_score(0.0) == 100.0


def test_precip_score_low_prob_still_high():
    assert weather.precip_score(10.0) == 100.0


def test_precip_score_high_prob_is_low():
    assert weather.precip_score(80.0) < 20.0


def test_precip_score_certain_rain_is_very_low():
    assert weather.precip_score(100.0) <= 5.0


# ---------------------------------------------------------------------------
# composite_score
# ---------------------------------------------------------------------------

def test_composite_score_ideal_conditions():
    # 10°C, 5km/h wind, 0% rain → near max
    score = weather.composite_score(10.0, 5.0, 0.0)
    assert score >= 90.0


def test_composite_score_terrible_conditions():
    # 35°C, 60km/h wind, 90% rain → very low
    score = weather.composite_score(35.0, 60.0, 90.0)
    assert score < 40.0


def test_composite_score_is_weighted_average():
    # Check that weights sum correctly: 0.45 + 0.30 + 0.25 = 1.0
    ts = weather.temp_score(10.0)
    ws = weather.wind_score(5.0)
    ps = weather.precip_score(0.0)
    expected = round(ts * 0.45 + ps * 0.30 + ws * 0.25, 1)
    assert weather.composite_score(10.0, 5.0, 0.0) == expected


# ---------------------------------------------------------------------------
# score_label
# ---------------------------------------------------------------------------

def test_score_label_excellent():
    assert weather.score_label(95.0) == "Excellent"


def test_score_label_good():
    assert weather.score_label(80.0) == "Good"


def test_score_label_fair():
    assert weather.score_label(65.0) == "Fair"


def test_score_label_poor():
    assert weather.score_label(50.0) == "Poor"


def test_score_label_boundary_90_is_excellent():
    assert weather.score_label(90.0) == "Excellent"


def test_score_label_boundary_75_is_good():
    assert weather.score_label(75.0) == "Good"


# ---------------------------------------------------------------------------
# parse_forecast
# ---------------------------------------------------------------------------

def _mock_raw():
    """Minimal Open-Meteo-shaped dict for testing parse_forecast."""
    return {
        "hourly": {
            "time": ["2026-06-20T06:00", "2026-06-20T07:00", "2026-06-20T08:00"],
            "apparent_temperature": [12.0, 13.5, None],
            "wind_speed_10m": [8.0, 12.0, 6.0],
            "precipitation_probability": [5.0, 10.0, 20.0],
        }
    }


def test_parse_forecast_returns_correct_count():
    result = weather.parse_forecast(_mock_raw())
    assert len(result) == 3


def test_parse_forecast_first_hour_fields():
    result = weather.parse_forecast(_mock_raw())
    h = result[0]
    assert h["time"] == "2026-06-20T06:00"
    assert h["apparent_temp_c"] == 12.0
    assert h["wind_speed_kmh"] == 8.0
    assert h["precip_probability"] == 5.0
    assert "score" in h
    assert "label" in h


def test_parse_forecast_none_temperature_defaults_to_15():
    result = weather.parse_forecast(_mock_raw())
    # Third hour has None temp → defaults to 15.0
    assert result[2]["apparent_temp_c"] == 15.0


def test_parse_forecast_empty_raw():
    result = weather.parse_forecast({})
    assert result == []


# ---------------------------------------------------------------------------
# best_windows
# ---------------------------------------------------------------------------

def test_best_windows_filters_nighttime():
    hours = [
        {"time": "2026-06-20T02:00", "score": 99.0},  # 2am — excluded
        {"time": "2026-06-20T08:00", "score": 80.0},  # 8am — included
        {"time": "2026-06-20T14:00", "score": 75.0},  # 2pm — included
    ]
    result = weather.best_windows(hours, top_n=5)
    assert len(result) == 2
    assert result[0]["time"] == "2026-06-20T08:00"


def test_best_windows_sorted_by_score_descending():
    hours = [
        {"time": "2026-06-20T08:00", "score": 70.0},
        {"time": "2026-06-20T10:00", "score": 90.0},
        {"time": "2026-06-20T12:00", "score": 80.0},
    ]
    result = weather.best_windows(hours, top_n=3)
    scores = [h["score"] for h in result]
    assert scores == sorted(scores, reverse=True)


def test_best_windows_respects_top_n():
    hours = [
        {"time": f"2026-06-20T{h:02d}:00", "score": float(h)}
        for h in range(6, 21)
    ]
    result = weather.best_windows(hours, top_n=3)
    assert len(result) == 3
