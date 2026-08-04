"""Pure, deterministic readiness scoring for Dockside.

No I/O of any kind lives in this module - every function takes plain data in
and returns plain data out, which is what makes the whole scoring engine
unit-testable without a network connection or a database.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

DRY_DAY_PRECIP_THRESHOLD_MM = 1.0

# A constraint evaluates to one of:
#   "pass"    - the day satisfies this constraint
#   "fail"    - the day violates this constraint
#   "unknown" - the task cares about this constraint but the data isn't available
#   "n/a"     - the task doesn't use this constraint at all
ConstraintResult = str


@dataclass(frozen=True)
class Observation:
    obs_date: date
    temp_min_c: Optional[float] = None
    temp_max_c: Optional[float] = None
    precip_mm: Optional[float] = None
    wind_speed_max_kmh: Optional[float] = None
    wave_height_max_m: Optional[float] = None
    water_temp_c: Optional[float] = None

    @classmethod
    def from_row(cls, row) -> "Observation":
        return cls(
            obs_date=date.fromisoformat(row["obs_date"]),
            temp_min_c=row["temp_min_c"],
            temp_max_c=row["temp_max_c"],
            precip_mm=row["precip_mm"],
            wind_speed_max_kmh=row["wind_speed_max_kmh"],
            wave_height_max_m=row["wave_height_max_m"],
            water_temp_c=row["water_temp_c"],
        )


@dataclass(frozen=True)
class Task:
    id: int
    name: str
    category: str
    window_start_month: int
    window_end_month: int
    max_wind_kmh: Optional[float] = None
    min_water_temp_c: Optional[float] = None
    dry_days_required: Optional[int] = None
    frost_free_required: bool = False

    @classmethod
    def from_row(cls, row) -> "Task":
        return cls(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            window_start_month=row["window_start_month"],
            window_end_month=row["window_end_month"],
            max_wind_kmh=row["max_wind_kmh"],
            min_water_temp_c=row["min_water_temp_c"],
            dry_days_required=row["dry_days_required"],
            frost_free_required=bool(row["frost_free_required"]),
        )


@dataclass(frozen=True)
class DayEvaluation:
    obs_date: date
    constraints: dict = field(default_factory=dict)
    all_satisfied: bool = False


def _window_status(today_month: int, start: int, end: int) -> str:
    """Classifies today's month against a task's target window.

    Returns "in_window", "upcoming", or "overdue" for a non-wrapping window
    (start <= end). Wrapping windows (start > end, e.g. Nov-Feb) only ever
    return "in_window" or "upcoming" - see Known Limitations in Manual.md for
    why "overdue" isn't computed across a year boundary.
    """
    if start <= end:
        if start <= today_month <= end:
            return "in_window"
        if today_month < start:
            return "upcoming"
        return "overdue"
    if today_month >= start or today_month <= end:
        return "in_window"
    return "upcoming"


def _is_dry_day(obs: Observation) -> Optional[bool]:
    if obs.precip_mm is None:
        return None
    return obs.precip_mm < DRY_DAY_PRECIP_THRESHOLD_MM


def evaluate_dry_streak(task: Task, observations: list) -> dict:
    """Returns {obs_date: ConstraintResult} for the dry-day-streak constraint.

    A day passes iff it is the last day of a run of at least
    dry_days_required consecutive dry days (precip below the threshold)
    ending on that day, inclusive. A day with unknown precipitation breaks
    any in-progress streak and is itself reported as "unknown".
    """
    result = {}
    if task.dry_days_required is None:
        for obs in observations:
            result[obs.obs_date] = "n/a"
        return result

    streak = 0
    for obs in sorted(observations, key=lambda o: o.obs_date):
        is_dry = _is_dry_day(obs)
        if is_dry is None:
            streak = 0
            result[obs.obs_date] = "unknown"
            continue
        streak = streak + 1 if is_dry else 0
        result[obs.obs_date] = "pass" if streak >= task.dry_days_required else "fail"
    return result


def _evaluate_wind(task: Task, obs: Observation) -> ConstraintResult:
    if task.max_wind_kmh is None:
        return "n/a"
    if obs.wind_speed_max_kmh is None:
        return "unknown"
    return "pass" if obs.wind_speed_max_kmh <= task.max_wind_kmh else "fail"


def _evaluate_frost(task: Task, obs: Observation) -> ConstraintResult:
    if not task.frost_free_required:
        return "n/a"
    if obs.temp_min_c is None:
        return "unknown"
    return "pass" if obs.temp_min_c > 0 else "fail"


def _evaluate_water_temp(task: Task, obs: Observation) -> ConstraintResult:
    if task.min_water_temp_c is None:
        return "n/a"
    if obs.water_temp_c is None:
        return "unknown"
    return "pass" if obs.water_temp_c >= task.min_water_temp_c else "fail"


def evaluate_days(task: Task, observations: list) -> list:
    """Evaluates every constraint the task specifies against every observed
    day, returning one DayEvaluation per day sorted by date."""
    dry_results = evaluate_dry_streak(task, observations)
    evaluations = []
    for obs in sorted(observations, key=lambda o: o.obs_date):
        constraints = {
            "wind": _evaluate_wind(task, obs),
            "frost_free": _evaluate_frost(task, obs),
            "water_temp": _evaluate_water_temp(task, obs),
            "dry_streak": dry_results.get(obs.obs_date, "n/a"),
        }
        relevant = [v for v in constraints.values() if v != "n/a"]
        all_satisfied = all(v == "pass" for v in relevant) if relevant else True
        evaluations.append(DayEvaluation(obs.obs_date, constraints, all_satisfied))
    return evaluations


def classify_task_status(task: Task, observations: list, today: date,
                          last_completion_year: Optional[int]):
    """Classifies a task's current readiness.

    Returns a 3-tuple: (status, best_day_evaluation_or_None, all_evaluations).
    status is one of: "done_this_season", "off_season", "overdue",
    "not_ready", "ready_now", "ready_soon".
    """
    if last_completion_year == today.year:
        return "done_this_season", None, []

    window_status = _window_status(today.month, task.window_start_month, task.window_end_month)
    evaluations = evaluate_days(task, observations)

    if window_status == "upcoming":
        return "off_season", None, evaluations

    satisfying = [e for e in evaluations if e.all_satisfied]
    best = satisfying[0] if satisfying else None

    if window_status == "overdue":
        return "overdue", best, evaluations

    # in_window
    if best is None:
        return "not_ready", None, evaluations
    if best.obs_date == today:
        return "ready_now", best, evaluations
    return "ready_soon", best, evaluations


def add_one_year(d: date) -> date:
    """Adds one year to a date, safely handling Feb 29 by rolling back to
    Feb 28 in the (likely non-leap) following year."""
    try:
        return d.replace(year=d.year + 1)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + 1)


def boating_comfort_score(obs: Observation) -> float:
    """0-100 composite "is this a nice day to be on the water" score.

    Higher is better. Wind/precipitation/temperature always contribute; a
    missing value for any of them contributes a neutral 50 rather than
    dragging the score down. Wave height only contributes when available at
    all (many inland sites have no marine coverage), so its absence doesn't
    penalize non-marine sites.
    """
    scores = []

    if obs.wind_speed_max_kmh is not None:
        scores.append(max(0.0, 100.0 - (obs.wind_speed_max_kmh / 40.0) * 100.0))
    else:
        scores.append(50.0)

    if obs.precip_mm is not None:
        scores.append(max(0.0, 100.0 - (obs.precip_mm / 10.0) * 100.0))
    else:
        scores.append(50.0)

    if obs.temp_max_c is not None:
        t = obs.temp_max_c
        if 22 <= t <= 28:
            scores.append(100.0)
        elif t < 22:
            scores.append(max(0.0, 100.0 - (22 - t) * 6.0))
        else:
            scores.append(max(0.0, 100.0 - (t - 28) * 6.0))
    else:
        scores.append(50.0)

    if obs.wave_height_max_m is not None:
        scores.append(max(0.0, 100.0 - (obs.wave_height_max_m / 1.5) * 100.0))

    return round(sum(scores) / len(scores), 1)
