"""Pure analysis functions for GitHub Actions run data — no I/O, fully testable."""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


def parse_duration_s(run: dict[str, Any]) -> float | None:
    """Return run duration in seconds, or None if timestamps are missing/invalid."""
    start_str = run.get("run_started_at") or run.get("created_at")
    end_str = run.get("updated_at")
    if not start_str or not end_str:
        return None
    try:
        start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        duration = (end - start).total_seconds()
        return max(0.0, duration)
    except (ValueError, TypeError):
        return None


def is_completed(run: dict[str, Any]) -> bool:
    """Return True only for runs that have finished (not queued or in_progress)."""
    return run.get("status") == "completed"


def is_failure(run: dict[str, Any]) -> bool:
    """Return True for runs concluded with failure or error."""
    return run.get("conclusion") in ("failure", "startup_failure", "timed_out")


def compute_workflow_stats(
    runs: list[dict[str, Any]],
    repo: str,
    workflow_name: str,
) -> dict[str, Any]:
    """Compute per-workflow metrics from a list of run objects."""
    completed = [r for r in runs if is_completed(r)]
    if not completed:
        return {
            "repo": repo,
            "workflow_name": workflow_name,
            "total_runs": len(runs),
            "success_count": 0,
            "failure_count": 0,
            "failure_rate": 0.0,
            "avg_duration_s": 0.0,
            "p95_duration_s": 0.0,
            "durations": [],
        }

    durations = [d for r in completed if (d := parse_duration_s(r)) is not None]
    failures = sum(1 for r in completed if is_failure(r))
    successes = len(completed) - failures

    avg_duration = statistics.mean(durations) if durations else 0.0
    if len(durations) >= 2:
        sorted_d = sorted(durations)
        idx = int(len(sorted_d) * 0.95)
        p95_duration = sorted_d[min(idx, len(sorted_d) - 1)]
    elif durations:
        p95_duration = durations[0]
    else:
        p95_duration = 0.0

    failure_rate = failures / len(completed) if completed else 0.0

    return {
        "repo": repo,
        "workflow_name": workflow_name,
        "total_runs": len(runs),
        "success_count": successes,
        "failure_count": failures,
        "failure_rate": round(failure_rate, 4),
        "avg_duration_s": round(avg_duration, 1),
        "p95_duration_s": round(p95_duration, 1),
        "durations": durations,
    }


def compute_weekly_trend(
    runs: list[dict[str, Any]],
    reference_date: datetime | None = None,
) -> list[dict[str, Any]]:
    """Group completed runs by ISO week and compute weekly avg duration and failure rate."""
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)

    weeks: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        if not is_completed(run):
            continue
        date_str = run.get("run_started_at") or run.get("created_at")
        if not date_str:
            continue
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            week_key = dt.strftime("%Y-W%W")
            weeks[week_key].append(run)
        except (ValueError, TypeError):
            continue

    result = []
    for week_key in sorted(weeks.keys()):
        week_runs = weeks[week_key]
        durations = [d for r in week_runs if (d := parse_duration_s(r)) is not None]
        failures = sum(1 for r in week_runs if is_failure(r))
        result.append({
            "week": week_key,
            "run_count": len(week_runs),
            "avg_duration_s": round(statistics.mean(durations), 1) if durations else 0.0,
            "failure_count": failures,
            "failure_rate": round(failures / len(week_runs), 4) if week_runs else 0.0,
        })
    return result


def compute_global_stats(workflow_stats: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-workflow stats into a global summary."""
    if not workflow_stats:
        return {
            "total_runs": 0,
            "total_failures": 0,
            "repos_with_ci": 0,
            "total_ci_minutes": 0.0,
            "overall_failure_rate": 0.0,
            "slowest_workflow": "",
            "most_failed_workflow": "",
        }

    total_runs = sum(s["total_runs"] for s in workflow_stats)
    total_failures = sum(s["failure_count"] for s in workflow_stats)
    repos_with_ci = len({s["repo"] for s in workflow_stats})

    total_ci_seconds = sum(
        s["avg_duration_s"] * s["total_runs"] for s in workflow_stats
    )
    total_ci_minutes = round(total_ci_seconds / 60, 1)

    overall_failure_rate = round(total_failures / total_runs, 4) if total_runs else 0.0

    slowest = max(workflow_stats, key=lambda s: s["avg_duration_s"], default=None)
    most_failed = max(workflow_stats, key=lambda s: s["failure_count"], default=None)

    return {
        "total_runs": total_runs,
        "total_failures": total_failures,
        "repos_with_ci": repos_with_ci,
        "total_ci_minutes": total_ci_minutes,
        "overall_failure_rate": overall_failure_rate,
        "slowest_workflow": f"{slowest['repo']}/{slowest['workflow_name']}" if slowest else "",
        "most_failed_workflow": f"{most_failed['repo']}/{most_failed['workflow_name']}" if most_failed else "",
    }


def rank_by_improvement_potential(
    workflow_stats: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rank workflows by improvement impact: avg_duration * failure_rate * total_runs.

    High duration AND high failure rate AND high frequency = highest priority.
    """
    def impact_score(stat: dict[str, Any]) -> float:
        duration_weight = stat["avg_duration_s"] / 60.0
        failure_weight = stat["failure_rate"] + 0.01
        return duration_weight * failure_weight * stat["total_runs"]

    return sorted(workflow_stats, key=impact_score, reverse=True)


def format_duration(seconds: float) -> str:
    """Format seconds into a human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs:02d}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins:02d}m"
