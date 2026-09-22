"""Beaufort wind-force classification and boating-comfort scoring.

Both are deterministic, documented formulas -- no AI, no lookups against
opaque tables. The comfort score is a weighted blend of five piecewise-linear
sub-scores, chosen so the result responds smoothly to input changes rather
than jumping between discrete buckets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

# (upper_bound_knots_exclusive, beaufort_number, name)
# Upper bound of None means "and above". Boundaries are the real
# Beaufort scale, expressed in knots.
_BEAUFORT_TABLE: List[tuple] = [
    (1.0, 0, "Calm"),
    (4.0, 1, "Light Air"),
    (7.0, 2, "Light Breeze"),
    (11.0, 3, "Gentle Breeze"),
    (17.0, 4, "Moderate Breeze"),
    (22.0, 5, "Fresh Breeze"),
    (28.0, 6, "Strong Breeze"),
    (34.0, 7, "Near Gale"),
    (41.0, 8, "Gale"),
    (48.0, 9, "Strong Gale"),
    (56.0, 10, "Storm"),
    (64.0, 11, "Violent Storm"),
    (None, 12, "Hurricane Force"),
]


@dataclass(frozen=True)
class BeaufortLevel:
    number: int
    name: str


def classify_beaufort(wind_knots: float) -> BeaufortLevel:
    """Classify a mean wind speed (knots) into its Beaufort force number/name."""
    if wind_knots < 0:
        raise ValueError(f"wind_knots must be non-negative, got {wind_knots}")
    for upper, number, name in _BEAUFORT_TABLE:
        if upper is None or wind_knots < upper:
            return BeaufortLevel(number=number, name=name)
    raise AssertionError("unreachable: table always terminates with an open upper bound")


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _wind_subscore(wind_knots: float) -> float:
    """Ideal boating wind is a gentle-to-moderate breeze (7-16 kn).

    Below that it's flat calm (fine, but a mild penalty since it's the
    lightest sailing/drift-fishing has no wind at all); above it climbs
    toward "call off the trip" territory.
    """
    if wind_knots < 7.0:
        # 0 kn -> 80, 7 kn -> 100 (calm is pleasant but not "ideal")
        return _clamp(80.0 + (20.0 / 7.0) * wind_knots)
    if wind_knots <= 16.0:
        return 100.0
    if wind_knots <= 28.0:
        # 16 kn -> 100, 28 kn -> 20 (strong breeze territory closing out)
        return _clamp(100.0 - (80.0 / 12.0) * (wind_knots - 16.0))
    # Near gale and above: essentially unusable for a small boat.
    return _clamp(20.0 - (wind_knots - 28.0) * 2.0)


def _gust_subscore(wind_knots: float, gust_knots: float) -> float:
    """Penalize a large gust factor (turbulent, unpredictable conditions)."""
    if gust_knots < wind_knots:
        gust_knots = wind_knots  # guard against malformed data
    factor = 0.0 if wind_knots <= 0 else (gust_knots - wind_knots) / max(wind_knots, 1.0)
    # factor 0 -> 100, factor 1.0 (gusts double the steady wind) -> 40, factor 2.0+ -> 0
    return _clamp(100.0 - factor * 60.0)


def _precip_subscore(precip_probability: float) -> float:
    """Linear penalty: 0% probability -> 100, 100% -> 0."""
    return _clamp(100.0 - precip_probability)


def _temp_subscore(temp_c: float) -> float:
    """Ideal comfortable range 18-27C, tapering off outside it."""
    if 18.0 <= temp_c <= 27.0:
        return 100.0
    if temp_c < 18.0:
        return _clamp(100.0 - (18.0 - temp_c) * 6.0)
    return _clamp(100.0 - (temp_c - 27.0) * 6.0)


def _cloud_subscore(cloud_cover_pct: float) -> float:
    """Mild penalty for overcast skies; not weighted heavily."""
    return _clamp(100.0 - cloud_cover_pct * 0.5)


# Documented weights -- must sum to 1.0.
WEIGHTS = {
    "wind": 0.35,
    "gust": 0.15,
    "precip": 0.25,
    "temp": 0.20,
    "cloud": 0.05,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def comfort_score(
    wind_knots: float,
    gust_knots: float,
    precip_probability: float,
    temp_c: float,
    cloud_cover_pct: float,
    daylight_hours: float,
) -> float:
    """Compute the 0-100 boating comfort score for one window.

    A window with zero daylight overlap is unusable (can't take the boat
    out in the dark) and always scores 0, regardless of how favorable the
    weather numbers look.
    """
    if daylight_hours <= 0:
        return 0.0

    score = (
        WEIGHTS["wind"] * _wind_subscore(wind_knots)
        + WEIGHTS["gust"] * _gust_subscore(wind_knots, gust_knots)
        + WEIGHTS["precip"] * _precip_subscore(precip_probability)
        + WEIGHTS["temp"] * _temp_subscore(temp_c)
        + WEIGHTS["cloud"] * _cloud_subscore(cloud_cover_pct)
    )
    return round(_clamp(score), 1)
