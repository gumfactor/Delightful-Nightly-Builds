"""Tests for weather_fetcher.py — hourly scoring and forecast parsing."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from weather_fetcher import get_best_windows, parse_forecast_response, score_hour


# ---------------------------------------------------------------------------
# score_hour
# ---------------------------------------------------------------------------

class TestScoreHour:
    def test_ideal_running_conditions_score_high(self):
        scores = score_hour(temp_c=15.0, wind_kph=5.0, precip_prob=0.0)
        assert scores["run"] >= 80

    def test_extreme_heat_lowers_run_score(self):
        scores = score_hour(temp_c=40.0, wind_kph=5.0, precip_prob=0.0)
        assert scores["run"] < 50

    def test_freezing_temperatures_lower_run_score(self):
        scores = score_hour(temp_c=-10.0, wind_kph=5.0, precip_prob=0.0)
        assert scores["run"] < 50

    def test_heavy_rain_lowers_all_scores(self):
        clear = score_hour(temp_c=20.0, wind_kph=5.0, precip_prob=0.0)
        rainy = score_hour(temp_c=20.0, wind_kph=5.0, precip_prob=100.0)
        assert rainy["run"] < clear["run"]
        assert rainy["golf"] < clear["golf"]
        assert rainy["boat"] < clear["boat"]

    def test_high_wind_hurts_golf_more_than_running(self):
        calm_golf = score_hour(20.0, 5.0, 0.0)["golf"]
        windy_golf = score_hour(20.0, 35.0, 0.0)["golf"]
        calm_run = score_hour(20.0, 5.0, 0.0)["run"]
        windy_run = score_hour(20.0, 35.0, 0.0)["run"]
        assert (calm_golf - windy_golf) > (calm_run - windy_run)

    def test_scores_are_never_negative(self):
        scores = score_hour(temp_c=-30.0, wind_kph=80.0, precip_prob=100.0)
        assert scores["run"] >= 0.0
        assert scores["golf"] >= 0.0
        assert scores["boat"] >= 0.0

    def test_scores_start_at_100_for_perfect_conditions(self):
        scores = score_hour(temp_c=18.0, wind_kph=3.0, precip_prob=0.0)
        assert scores["run"] == 100.0
        assert scores["golf"] == 100.0

    def test_ideal_boating_conditions_score_high(self):
        scores = score_hour(temp_c=24.0, wind_kph=12.0, precip_prob=0.0)
        assert scores["boat"] >= 80

    def test_no_wind_slightly_hurts_boating(self):
        some_wind = score_hour(24.0, 10.0, 0.0)["boat"]
        no_wind = score_hour(24.0, 0.0, 0.0)["boat"]
        assert some_wind > no_wind


# ---------------------------------------------------------------------------
# get_best_windows
# ---------------------------------------------------------------------------

class TestGetBestWindows:
    def _make_hours(self, hour_scores: list[tuple[int, float]]) -> list[dict]:
        return [
            {"hour": h, "time": f"2026-06-22T{h:02d}:00", "scores": {"run": s, "golf": s, "boat": s}}
            for h, s in hour_scores
        ]

    def test_returns_top_n_sorted_descending(self):
        hours = self._make_hours([(7, 90), (9, 70), (12, 60), (15, 50)])
        best = get_best_windows(hours, "run", top_n=2)
        assert len(best) == 2
        assert best[0]["scores"]["run"] >= best[1]["scores"]["run"]

    def test_filters_out_nighttime_hours(self):
        hours = self._make_hours([(2, 99), (4, 95), (8, 70), (14, 60)])
        best = get_best_windows(hours, "run", top_n=5)
        assert all(h["hour"] >= 6 for h in best)

    def test_returns_fewer_than_top_n_if_not_enough_daylight(self):
        hours = self._make_hours([(10, 80)])
        best = get_best_windows(hours, "run", top_n=3)
        assert len(best) == 1

    def test_returns_empty_for_no_hours(self):
        assert get_best_windows([], "run", top_n=3) == []

    def test_winner_has_highest_score_for_activity(self):
        hours = self._make_hours([(8, 60), (10, 90), (14, 75)])
        best = get_best_windows(hours, "run", top_n=1)
        assert best[0]["hour"] == 10


# ---------------------------------------------------------------------------
# parse_forecast_response
# ---------------------------------------------------------------------------

class TestParseForecastResponse:
    def _make_data(self, times, temps=None, winds=None, precips=None):
        n = len(times)
        return {
            "hourly": {
                "time": times,
                "apparent_temperature": temps or [20.0] * n,
                "wind_speed_10m": winds or [10.0] * n,
                "precipitation_probability": precips or [0.0] * n,
            }
        }

    def test_filters_to_target_date_only(self):
        data = self._make_data(["2026-06-22T08:00", "2026-06-23T08:00"], [20.0, 25.0])
        result = parse_forecast_response(data, date(2026, 6, 22))
        assert len(result) == 1
        assert result[0]["temp_c"] == 20.0

    def test_returns_empty_if_no_matching_hours(self):
        data = self._make_data(["2026-06-23T08:00"])
        result = parse_forecast_response(data, date(2026, 6, 22))
        assert result == []

    def test_uses_default_values_for_none_entries(self):
        data = self._make_data(
            ["2026-06-22T10:00"],
            temps=[None],
            winds=[None],
            precips=[None],
        )
        result = parse_forecast_response(data, date(2026, 6, 22))
        assert len(result) == 1
        assert result[0]["temp_c"] == 15.0
        assert result[0]["wind_kph"] == 0.0
        assert result[0]["precip_prob"] == 0.0

    def test_each_hour_has_scores_dict(self):
        data = self._make_data(["2026-06-22T12:00"])
        result = parse_forecast_response(data, date(2026, 6, 22))
        assert "scores" in result[0]
        assert "run" in result[0]["scores"]

    def test_skips_hours_with_invalid_time_format(self):
        data = {
            "hourly": {
                "time": ["not-a-time", "2026-06-22T08:00"],
                "apparent_temperature": [20.0, 22.0],
                "wind_speed_10m": [10.0, 10.0],
                "precipitation_probability": [0.0, 0.0],
            }
        }
        result = parse_forecast_response(data, date(2026, 6, 22))
        assert len(result) == 1

    def test_hour_field_matches_time_string(self):
        data = self._make_data(["2026-06-22T14:00"])
        result = parse_forecast_response(data, date(2026, 6, 22))
        assert result[0]["hour"] == 14

    def test_handles_empty_hourly_data(self):
        result = parse_forecast_response({"hourly": {}}, date(2026, 6, 22))
        assert result == []
