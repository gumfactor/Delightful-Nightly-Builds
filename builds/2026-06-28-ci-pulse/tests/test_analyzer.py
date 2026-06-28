"""Tests for analyzer.py — pure CI metrics computation functions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analyzer import (
    compute_global_stats,
    compute_weekly_trend,
    compute_workflow_stats,
    format_duration,
    is_completed,
    is_failure,
    parse_duration_s,
    rank_by_improvement_potential,
)


# ── parse_duration_s ──────────────────────────────────────────────────────────

def _run(created="2024-01-01T10:00:00Z", updated="2024-01-01T10:05:00Z", started=None) -> dict:
    r = {"created_at": created, "updated_at": updated, "status": "completed", "conclusion": "success"}
    if started is not None:
        r["run_started_at"] = started
    return r


def test_parse_duration_uses_run_started_at():
    run = _run(created="2024-01-01T10:00:00Z", updated="2024-01-01T10:08:00Z", started="2024-01-01T10:02:00Z")
    assert parse_duration_s(run) == 360.0  # 8:00 - 10:02 = 6 min, but updated - started = 6*60


def test_parse_duration_falls_back_to_created_at():
    run = _run(created="2024-01-01T10:00:00Z", updated="2024-01-01T10:05:00Z")
    assert parse_duration_s(run) == 300.0


def test_parse_duration_returns_none_when_missing_updated():
    run = {"created_at": "2024-01-01T10:00:00Z", "status": "completed"}
    assert parse_duration_s(run) is None


def test_parse_duration_clamps_negative_to_zero():
    # updated before started is invalid — clamp to 0
    run = {"run_started_at": "2024-01-01T10:05:00Z", "updated_at": "2024-01-01T10:00:00Z", "status": "completed"}
    assert parse_duration_s(run) == 0.0


def test_parse_duration_handles_bad_timestamps():
    run = {"created_at": "not-a-date", "updated_at": "also-bad", "status": "completed"}
    assert parse_duration_s(run) is None


# ── is_completed / is_failure ─────────────────────────────────────────────────

def test_is_completed_true():
    assert is_completed({"status": "completed"}) is True


def test_is_completed_false_for_queued():
    assert is_completed({"status": "queued"}) is False


def test_is_failure_true_for_failure():
    assert is_failure({"conclusion": "failure"}) is True


def test_is_failure_true_for_timed_out():
    assert is_failure({"conclusion": "timed_out"}) is True


def test_is_failure_false_for_success():
    assert is_failure({"conclusion": "success"}) is False


def test_is_failure_false_for_cancelled():
    assert is_failure({"conclusion": "cancelled"}) is False


# ── compute_workflow_stats ────────────────────────────────────────────────────

def _make_run(conclusion="success", duration_s=60):
    from datetime import datetime, timedelta, timezone
    start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(seconds=duration_s)
    return {
        "status": "completed",
        "conclusion": conclusion,
        "created_at": start.isoformat().replace("+00:00", "Z"),
        "updated_at": end.isoformat().replace("+00:00", "Z"),
        "name": "CI",
    }


def test_compute_workflow_stats_empty_runs():
    stats = compute_workflow_stats([], repo="r", workflow_name="CI")
    assert stats["total_runs"] == 0
    assert stats["failure_rate"] == 0.0
    assert stats["avg_duration_s"] == 0.0


def test_compute_workflow_stats_all_success():
    runs = [_make_run("success", 100), _make_run("success", 200)]
    stats = compute_workflow_stats(runs, repo="r", workflow_name="CI")
    assert stats["failure_rate"] == 0.0
    assert stats["success_count"] == 2
    assert stats["failure_count"] == 0


def test_compute_workflow_stats_failure_rate():
    runs = [_make_run("success", 60), _make_run("failure", 30), _make_run("failure", 45)]
    stats = compute_workflow_stats(runs, repo="r", workflow_name="CI")
    assert abs(stats["failure_rate"] - 2 / 3) < 0.001
    assert stats["failure_count"] == 2


def test_compute_workflow_stats_avg_duration():
    runs = [_make_run("success", 100), _make_run("success", 200), _make_run("success", 300)]
    stats = compute_workflow_stats(runs, repo="r", workflow_name="CI")
    assert abs(stats["avg_duration_s"] - 200.0) < 0.1


def test_compute_workflow_stats_p95():
    # 20 runs at 60s, one at 600s → p95 should be the high outlier
    runs = [_make_run("success", 60)] * 19 + [_make_run("success", 600)]
    stats = compute_workflow_stats(runs, repo="r", workflow_name="CI")
    assert stats["p95_duration_s"] >= 60.0


def test_compute_workflow_stats_skips_in_progress():
    in_progress = {"status": "in_progress", "conclusion": None, "created_at": "2024-01-01T10:00:00Z", "updated_at": "2024-01-01T10:05:00Z"}
    completed = _make_run("success", 60)
    stats = compute_workflow_stats([in_progress, completed], repo="r", workflow_name="CI")
    assert stats["total_runs"] == 2
    assert stats["success_count"] == 1


# ── compute_weekly_trend ──────────────────────────────────────────────────────

def test_compute_weekly_trend_empty():
    result = compute_weekly_trend([])
    assert result == []


def test_compute_weekly_trend_groups_by_week():
    runs = [
        {**_make_run("success", 60), "created_at": "2024-01-08T10:00:00Z", "updated_at": "2024-01-08T10:01:00Z"},
        {**_make_run("failure", 30), "created_at": "2024-01-08T11:00:00Z", "updated_at": "2024-01-08T11:00:30Z"},
        {**_make_run("success", 120), "created_at": "2024-01-15T10:00:00Z", "updated_at": "2024-01-15T10:02:00Z"},
    ]
    result = compute_weekly_trend(runs)
    assert len(result) == 2
    assert result[0]["run_count"] == 2  # week of Jan 8 has 2 runs
    assert result[1]["run_count"] == 1  # week of Jan 15 has 1 run


def test_compute_weekly_trend_failure_rate():
    runs = [
        {**_make_run("success", 60), "created_at": "2024-01-08T10:00:00Z", "updated_at": "2024-01-08T10:01:00Z"},
        {**_make_run("failure", 60), "created_at": "2024-01-08T11:00:00Z", "updated_at": "2024-01-08T11:01:00Z"},
    ]
    result = compute_weekly_trend(runs)
    assert len(result) == 1
    assert abs(result[0]["failure_rate"] - 0.5) < 0.001


# ── compute_global_stats ──────────────────────────────────────────────────────

def test_compute_global_stats_empty():
    result = compute_global_stats([])
    assert result["total_runs"] == 0
    assert result["repos_with_ci"] == 0


def test_compute_global_stats_aggregates_correctly():
    stats = [
        {"repo": "r1", "workflow_name": "CI", "total_runs": 10, "failure_count": 2, "success_count": 8, "avg_duration_s": 120.0, "p95_duration_s": 200.0, "failure_rate": 0.2, "durations": []},
        {"repo": "r2", "workflow_name": "Deploy", "total_runs": 5, "failure_count": 0, "success_count": 5, "avg_duration_s": 60.0, "p95_duration_s": 90.0, "failure_rate": 0.0, "durations": []},
    ]
    result = compute_global_stats(stats)
    assert result["total_runs"] == 15
    assert result["total_failures"] == 2
    assert result["repos_with_ci"] == 2
    assert abs(result["overall_failure_rate"] - 2 / 15) < 0.001


# ── rank_by_improvement_potential ─────────────────────────────────────────────

def test_rank_by_improvement_potential_orders_correctly():
    stats = [
        {"repo": "r", "workflow_name": "fast-good", "avg_duration_s": 30.0, "failure_rate": 0.01, "total_runs": 10, "durations": []},
        {"repo": "r", "workflow_name": "slow-bad", "avg_duration_s": 600.0, "failure_rate": 0.5, "total_runs": 20, "durations": []},
        {"repo": "r", "workflow_name": "medium", "avg_duration_s": 120.0, "failure_rate": 0.1, "total_runs": 5, "durations": []},
    ]
    ranked = rank_by_improvement_potential(stats)
    assert ranked[0]["workflow_name"] == "slow-bad"
    assert ranked[-1]["workflow_name"] == "fast-good"


def test_rank_by_improvement_potential_handles_zero_failure_rate():
    stats = [
        {"repo": "r", "workflow_name": "A", "avg_duration_s": 300.0, "failure_rate": 0.0, "total_runs": 50, "durations": []},
        {"repo": "r", "workflow_name": "B", "avg_duration_s": 60.0, "failure_rate": 0.9, "total_runs": 5, "durations": []},
    ]
    ranked = rank_by_improvement_potential(stats)
    assert len(ranked) == 2


# ── format_duration ───────────────────────────────────────────────────────────

def test_format_duration_seconds():
    assert format_duration(45) == "45s"


def test_format_duration_minutes():
    assert format_duration(125) == "2m 05s"


def test_format_duration_hours():
    assert format_duration(3700) == "1h 01m"
