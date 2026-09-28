"""Deterministic outdoor-activity suitability scoring.

Each factor score is 0-100 (100 = ideal, 0 = worst). A composite score per
activity is a fixed weighted average of its factor scores. All thresholds
and weights are named constants so the model is auditable and testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def temp_score(temp_c: float, ideal_low: float, ideal_high: float,
                cold_penalty_per_degree: float, hot_penalty_per_degree: float) -> float:
    """100 within [ideal_low, ideal_high]; linear penalty outside it."""
    if ideal_low <= temp_c <= ideal_high:
        return 100.0
    if temp_c < ideal_low:
        return _clamp(100.0 - (ideal_low - temp_c) * cold_penalty_per_degree)
    return _clamp(100.0 - (temp_c - ideal_high) * hot_penalty_per_degree)


def wind_score(wind_kmh: float, threshold_kmh: float, penalty_per_kmh: float) -> float:
    """100 at or under the threshold; linear penalty above it."""
    if wind_kmh <= threshold_kmh:
        return 100.0
    return _clamp(100.0 - (wind_kmh - threshold_kmh) * penalty_per_kmh)


def precip_score(precip_prob_pct: float, threshold_pct: float, penalty_per_pct: float) -> float:
    """100 at or under the threshold probability of precipitation; linear penalty above it."""
    if precip_prob_pct <= threshold_pct:
        return 100.0
    return _clamp(100.0 - (precip_prob_pct - threshold_pct) * penalty_per_pct)


def aqi_score(aqi_us: float) -> float:
    """US EPA AQI tiers mapped to a coarse 0-100 comfort score."""
    if aqi_us <= 50:
        return 100.0
    if aqi_us <= 100:
        return 80.0
    if aqi_us <= 150:
        return 50.0
    if aqi_us <= 200:
        return 20.0
    return 0.0


def uv_score(uv_index: float, threshold: float, penalty_per_unit: float) -> float:
    """100 at or under the threshold UV index; linear penalty above it."""
    if uv_index <= threshold:
        return 100.0
    return _clamp(100.0 - (uv_index - threshold) * penalty_per_unit)


# Activity-specific parameters. Running favors cool, clean air; golf tolerates
# more heat but is far more sensitive to wind and rain (play stops in heavy rain,
# and wind dominates shot control).
RUNNING_PARAMS = dict(
    ideal_low=8.0, ideal_high=16.0, cold_penalty=3.0, hot_penalty=5.0,
    wind_threshold=12.0, wind_penalty=2.5,
    precip_threshold=20.0, precip_penalty=1.5,
    uv_threshold=6.0, uv_penalty=6.0,
    weights=dict(temp=0.25, wind=0.15, precip=0.20, aqi=0.25, uv=0.15),
)

GOLF_PARAMS = dict(
    ideal_low=12.0, ideal_high=24.0, cold_penalty=4.0, hot_penalty=3.0,
    wind_threshold=20.0, wind_penalty=3.0,
    precip_threshold=15.0, precip_penalty=2.5,
    uv_threshold=8.0, uv_penalty=4.0,
    weights=dict(temp=0.20, wind=0.30, precip=0.35, aqi=0.10, uv=0.05),
)


@dataclass(frozen=True)
class DayConditions:
    temp_max: float
    wind_max: float
    precip_prob_max: float
    aqi_max: float
    uv_index_max: float


def _composite_score(conditions: DayConditions, params: dict) -> float:
    factors: Dict[str, float] = {
        "temp": temp_score(conditions.temp_max, params["ideal_low"], params["ideal_high"],
                            params["cold_penalty"], params["hot_penalty"]),
        "wind": wind_score(conditions.wind_max, params["wind_threshold"], params["wind_penalty"]),
        "precip": precip_score(conditions.precip_prob_max, params["precip_threshold"], params["precip_penalty"]),
        "aqi": aqi_score(conditions.aqi_max),
        "uv": uv_score(conditions.uv_index_max, params["uv_threshold"], params["uv_penalty"]),
    }
    weights = params["weights"]
    total = sum(factors[key] * weights[key] for key in weights)
    return round(_clamp(total), 1)


def running_score(conditions: DayConditions) -> float:
    return _composite_score(conditions, RUNNING_PARAMS)


def golf_score(conditions: DayConditions) -> float:
    return _composite_score(conditions, GOLF_PARAMS)


def best_day(days: list, score_key: str) -> dict | None:
    """Return the day dict with the highest score_key, ties broken by lower precip_prob_max."""
    if not days:
        return None
    return min(
        days,
        key=lambda d: (-d[score_key], d.get("precip_prob_max", 0.0)),
    )
