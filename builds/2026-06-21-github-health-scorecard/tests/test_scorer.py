import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scorer import (
    compute_score,
    enrich_repo,
    health_css,
    health_label,
    score_ci,
    score_issues,
    score_recency,
)

REF = datetime(2026, 6, 21, 12, 0, 0, tzinfo=timezone.utc)


# ── Recency scoring ──────────────────────────────────────────────────────────

def test_score_recency_today():
    pushed = "2026-06-21T10:00:00Z"
    assert score_recency(pushed, REF) == 30


def test_score_recency_3_days():
    pushed = "2026-06-18T10:00:00Z"
    assert score_recency(pushed, REF) == 25


def test_score_recency_2_weeks():
    pushed = "2026-06-07T10:00:00Z"
    assert score_recency(pushed, REF) == 15


def test_score_recency_60_days():
    pushed = "2026-04-22T10:00:00Z"
    assert score_recency(pushed, REF) == 5


def test_score_recency_6_months():
    pushed = "2025-12-21T10:00:00Z"
    assert score_recency(pushed, REF) == 0


def test_score_recency_boundary_7_days():
    pushed = "2026-06-14T12:00:00Z"
    assert score_recency(pushed, REF) == 25


def test_score_recency_boundary_30_days():
    pushed = "2026-05-22T12:00:00Z"
    assert score_recency(pushed, REF) == 15


def test_score_recency_invalid_date():
    assert score_recency("not-a-date", REF) == 0


# ── CI scoring ───────────────────────────────────────────────────────────────

def test_score_ci_passing():
    assert score_ci("passing") == 40


def test_score_ci_failing():
    assert score_ci("failing") == 10


def test_score_ci_running():
    assert score_ci("running") == 30


def test_score_ci_no_ci():
    assert score_ci("no-ci") == 20


def test_score_ci_unknown_defaults_to_no_ci():
    assert score_ci("some-unknown-value") == 20


# ── Issues scoring ───────────────────────────────────────────────────────────

def test_score_issues_zero():
    assert score_issues(0) == 30


def test_score_issues_boundary_1():
    assert score_issues(1) == 20


def test_score_issues_boundary_5():
    assert score_issues(5) == 20


def test_score_issues_boundary_6():
    assert score_issues(6) == 10


def test_score_issues_boundary_20():
    assert score_issues(20) == 10


def test_score_issues_boundary_21():
    assert score_issues(21) == 0


def test_score_issues_large():
    assert score_issues(100) == 0


# ── Composite score ──────────────────────────────────────────────────────────

def test_compute_score_healthy():
    score = compute_score("2026-06-21T10:00:00Z", "passing", 0, REF)
    assert score == 100  # 30 + 40 + 30


def test_compute_score_stale():
    score = compute_score("2025-01-01T10:00:00Z", "failing", 50, REF)
    assert score == 10  # 0 + 10 + 0


# ── Health labels ────────────────────────────────────────────────────────────

def test_health_label_healthy():
    assert health_label(80) == "Healthy"
    assert health_label(100) == "Healthy"


def test_health_label_good():
    assert health_label(60) == "Good"
    assert health_label(79) == "Good"


def test_health_label_fair():
    assert health_label(40) == "Fair"
    assert health_label(59) == "Fair"


def test_health_label_needs_attention():
    assert health_label(20) == "Needs Attention"
    assert health_label(39) == "Needs Attention"


def test_health_label_stale():
    assert health_label(0) == "Stale"
    assert health_label(19) == "Stale"


# ── CSS class ────────────────────────────────────────────────────────────────

def test_health_css_classes():
    assert health_css(100) == "healthy"
    assert health_css(70) == "good"
    assert health_css(50) == "fair"
    assert health_css(30) == "attention"
    assert health_css(10) == "stale"


# ── enrich_repo ──────────────────────────────────────────────────────────────

def test_enrich_repo_ci_passing():
    repo = {
        "name": "myrepo",
        "full_name": "user/myrepo",
        "language": "Python",
        "description": "A test repo",
        "private": False,
        "archived": False,
        "open_issues_count": 2,
        "pushed_at": "2026-06-21T10:00:00Z",
    }
    ci_run = {"status": "completed", "conclusion": "success"}
    result = enrich_repo(repo, ci_run, REF)
    assert result["ci_status"] == "passing"
    assert result["health_score"] == 90  # 30 + 40 + 20
    assert result["health_label"] == "Healthy"


def test_enrich_repo_no_ci():
    repo = {
        "name": "quiet",
        "full_name": "user/quiet",
        "language": "JavaScript",
        "description": "",
        "private": False,
        "archived": False,
        "open_issues_count": 0,
        "pushed_at": "2026-06-21T10:00:00Z",
    }
    result = enrich_repo(repo, None, REF)
    assert result["ci_status"] == "no-ci"
    assert result["health_score"] == 80  # 30 + 20 + 30


def test_enrich_repo_failing_stale():
    repo = {
        "name": "oldrepo",
        "full_name": "user/oldrepo",
        "language": None,
        "description": None,
        "private": True,
        "archived": False,
        "open_issues_count": 30,
        "pushed_at": "2025-01-01T00:00:00Z",
    }
    ci_run = {"status": "completed", "conclusion": "failure"}
    result = enrich_repo(repo, ci_run, REF)
    assert result["ci_status"] == "failing"
    assert result["health_score"] == 10  # 0 + 10 + 0
    assert result["health_label"] == "Stale"
    assert result["language"] == "—"
    assert result["description"] == ""
