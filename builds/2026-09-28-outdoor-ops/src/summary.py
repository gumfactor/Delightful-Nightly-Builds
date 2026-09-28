"""Builds the aggregate weekly summary used by the dashboard and the AI note."""

from __future__ import annotations

from typing import List, Mapping

FACTOR_KEYS = ["temp", "wind", "precip", "aqi", "uv"]


def _limiting_factor(row: Mapping, params: dict) -> str:
    """Return the factor name with the lowest score for this row+activity params."""
    from . import scoring

    conditions = scoring.DayConditions(
        temp_max=row["temp_max"],
        wind_max=row["wind_max"],
        precip_prob_max=row["precip_prob_max"],
        aqi_max=row["aqi_max"],
        uv_index_max=row["uv_index_max"],
    )
    factors = {
        "temp": scoring.temp_score(conditions.temp_max, params["ideal_low"], params["ideal_high"],
                                    params["cold_penalty"], params["hot_penalty"]),
        "wind": scoring.wind_score(conditions.wind_max, params["wind_threshold"], params["wind_penalty"]),
        "precip": scoring.precip_score(conditions.precip_prob_max, params["precip_threshold"], params["precip_penalty"]),
        "aqi": scoring.aqi_score(conditions.aqi_max),
        "uv": scoring.uv_score(conditions.uv_index_max, params["uv_threshold"], params["uv_penalty"]),
    }
    return min(factors, key=lambda k: factors[k])


def build_week_summary(days: List[Mapping]) -> dict:
    """days: list of dicts/rows with forecast_date, running_score, golf_score, and raw factor fields."""
    from . import scoring

    if not days:
        raise ValueError("Cannot build a week summary from zero days")

    best_running = max(days, key=lambda d: (d["running_score"], -_precip(d)))
    worst_running = min(days, key=lambda d: (d["running_score"], _precip(d)))
    best_golf = max(days, key=lambda d: (d["golf_score"], -_precip(d)))
    worst_golf = min(days, key=lambda d: (d["golf_score"], _precip(d)))

    return {
        "best_running_day": best_running["forecast_date"],
        "best_running_score": best_running["running_score"],
        "worst_running_day": worst_running["forecast_date"],
        "worst_running_score": worst_running["running_score"],
        "running_limiting_factor": _limiting_factor(worst_running, scoring.RUNNING_PARAMS),
        "best_golf_day": best_golf["forecast_date"],
        "best_golf_score": best_golf["golf_score"],
        "worst_golf_day": worst_golf["forecast_date"],
        "worst_golf_score": worst_golf["golf_score"],
        "golf_limiting_factor": _limiting_factor(worst_golf, scoring.GOLF_PARAMS),
    }


def _precip(row: Mapping) -> float:
    return row["precip_prob_max"] if row["precip_prob_max"] is not None else 0.0
