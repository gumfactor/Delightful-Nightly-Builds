from datetime import datetime, timezone
from typing import Optional


def score_recency(pushed_at: str, now: Optional[datetime] = None) -> int:
    """Score 0–30 based on how recently the repo was pushed."""
    if now is None:
        now = datetime.now(timezone.utc)
    try:
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 0
    days = (now - pushed).days
    if days <= 1:
        return 30
    if days <= 7:
        return 25
    if days <= 30:
        return 15
    if days <= 90:
        return 5
    return 0


def score_ci(ci_status: str) -> int:
    """Score 0–40 based on CI status."""
    mapping = {
        "passing": 40,
        "running": 30,
        "no-ci": 20,
        "failing": 10,
    }
    return mapping.get(ci_status, 20)


def score_issues(open_issues: int) -> int:
    """Score 0–30 based on open issue count."""
    if open_issues == 0:
        return 30
    if open_issues <= 5:
        return 20
    if open_issues <= 20:
        return 10
    return 0


def compute_score(pushed_at: str, ci_status: str, open_issues: int,
                  now: Optional[datetime] = None) -> int:
    """Compute composite health score 0–100."""
    return (
        score_recency(pushed_at, now)
        + score_ci(ci_status)
        + score_issues(open_issues)
    )


def health_label(score: int) -> str:
    """Return human-readable health label for a score."""
    if score >= 80:
        return "Healthy"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Fair"
    if score >= 20:
        return "Needs Attention"
    return "Stale"


def health_css(score: int) -> str:
    """Return CSS class name for a score."""
    if score >= 80:
        return "healthy"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    if score >= 20:
        return "attention"
    return "stale"


def enrich_repo(repo: dict, ci_run: Optional[dict], now: Optional[datetime] = None) -> dict:
    """Enrich a raw GitHub repo dict with health score fields."""
    pushed_at = repo.get("pushed_at", "")
    open_issues = repo.get("open_issues_count", 0)

    if ci_run is None:
        ci_status = "no-ci"
    else:
        conclusion = ci_run.get("conclusion")
        run_status = ci_run.get("status")
        if run_status == "in_progress":
            ci_status = "running"
        elif conclusion == "success":
            ci_status = "passing"
        elif conclusion in ("failure", "timed_out"):
            ci_status = "failing"
        else:
            ci_status = "no-ci"

    if now is None:
        now = datetime.now(timezone.utc)
    try:
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        days_since_push = (now - pushed).days
    except (ValueError, AttributeError):
        days_since_push = 9999

    score = compute_score(pushed_at, ci_status, open_issues, now)

    return {
        "name": repo.get("name", ""),
        "full_name": repo.get("full_name", ""),
        "language": repo.get("language") or "—",
        "description": repo.get("description") or "",
        "private": bool(repo.get("private", False)),
        "archived": bool(repo.get("archived", False)),
        "open_issues": open_issues,
        "pushed_at": pushed_at,
        "days_since_push": days_since_push,
        "ci_status": ci_status,
        "health_score": score,
        "health_label": health_label(score),
        "health_css": health_css(score),
    }
