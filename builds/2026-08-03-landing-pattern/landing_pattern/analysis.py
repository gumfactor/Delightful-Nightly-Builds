"""Pure PR readiness / conflict-risk analysis. No network or filesystem I/O."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

LABEL_PRIORITY: dict[str, int] = {
    "conflict": 0,
    "ci_failing": 1,
    "changes_requested": 2,
    "ci_pending": 3,
    "awaiting_review": 4,
    "behind_base": 5,
    "unknown": 6,
}


def utcnow() -> datetime:
    """Current time in UTC. Isolated so callers can inject a fixed `now` in tests."""
    return datetime.now(timezone.utc)


def parse_iso8601(value: str) -> datetime:
    """Parse a GitHub-style ISO 8601 timestamp, including a trailing 'Z'."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def age_days(created_at: str, now: datetime) -> int:
    """Whole days between `created_at` (ISO 8601) and `now`. Never negative."""
    created = parse_iso8601(created_at)
    delta = now - created
    return max(delta.days, 0)


def classify_readiness(pr: dict[str, Any]) -> str:
    """Classify a single PR into exactly one readiness label.

    Expects `pr` to have: draft (bool), mergeable_state (str), ci_state (str),
    review_state (str). Missing fields default to the most conservative value.
    """
    if pr.get("draft"):
        return "draft"

    mergeable_state = pr.get("mergeable_state", "unknown")
    ci_state = pr.get("ci_state", "none")
    review_state = pr.get("review_state", "none")

    if mergeable_state == "dirty":
        return "conflict"
    if ci_state in ("failure", "error"):
        return "ci_failing"
    if review_state == "changes_requested":
        return "changes_requested"
    if ci_state == "pending":
        return "ci_pending"
    if review_state == "review_required":
        return "awaiting_review"
    if mergeable_state == "behind":
        return "behind_base"
    if mergeable_state == "clean" and ci_state in ("success", "none") and review_state in ("approved", "none"):
        return "ready"
    return "unknown"


def build_overlap_graph(prs: list[dict[str, Any]]) -> dict[int, dict[int, list[str]]]:
    """Map each PR number to the other PR numbers it shares changed files with.

    Returns {pr_number: {other_pr_number: [shared_file_paths, ...]}}, symmetric.
    """
    graph: dict[int, dict[int, list[str]]] = {pr["number"]: {} for pr in prs}
    for i, pr_a in enumerate(prs):
        files_a = set(pr_a.get("files", []))
        for pr_b in prs[i + 1 :]:
            files_b = set(pr_b.get("files", []))
            shared = sorted(files_a & files_b)
            if shared:
                graph[pr_a["number"]][pr_b["number"]] = shared
                graph[pr_b["number"]][pr_a["number"]] = shared
    return graph


def recommend_merge_order(prs: list[dict[str, Any]], now: datetime) -> dict[str, Any]:
    """Classify every PR and produce a two-batch merge order plus a blocked list.

    Batch 1: ready PRs with no changed-file overlap with an earlier PR already
             claimed into Batch 1 — safe to merge back-to-back, oldest first.
    Batch 2: ready PRs that DO overlap a Batch-1 PR's files — mergeable in
             principle, but will need a rebase after Batch 1 lands.
    Blocked: everything else (not ready, not draft), sorted by how actionable
             the blocker is, then by age (oldest first within the same reason).
    Drafts:  listed separately, lowest priority, oldest first.
    """
    labeled = [
        {**pr, "label": classify_readiness(pr), "age_days": age_days(pr["created_at"], now)}
        for pr in prs
    ]

    overlap_graph = build_overlap_graph(prs)

    ready = sorted((p for p in labeled if p["label"] == "ready"), key=lambda p: p["created_at"])

    claimed_files: set[str] = set()
    batch1: list[dict[str, Any]] = []
    batch2: list[dict[str, Any]] = []
    batch1_numbers: set[int] = set()

    for pr in ready:
        pr_files = set(pr.get("files", []))
        if claimed_files & pr_files:
            conflicts_with = sorted(
                other for other in overlap_graph.get(pr["number"], {}) if other in batch1_numbers
            )
            batch2.append(
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "age_days": pr["age_days"],
                    "conflicts_with": conflicts_with,
                }
            )
        else:
            batch1.append(pr)
            batch1_numbers.add(pr["number"])
            claimed_files |= pr_files

    blocked = sorted(
        (p for p in labeled if p["label"] not in ("ready", "draft")),
        key=lambda p: (LABEL_PRIORITY.get(p["label"], 99), -p["age_days"]),
    )

    drafts = sorted((p for p in labeled if p["label"] == "draft"), key=lambda p: p["created_at"])

    return {
        "batch1": [
            {"number": p["number"], "title": p["title"], "age_days": p["age_days"]} for p in batch1
        ],
        "batch2": batch2,
        "blocked": [
            {
                "number": p["number"],
                "title": p["title"],
                "label": p["label"],
                "age_days": p["age_days"],
            }
            for p in blocked
        ],
        "drafts": [
            {"number": p["number"], "title": p["title"], "age_days": p["age_days"]} for p in drafts
        ],
        "overlap_graph": {k: v for k, v in overlap_graph.items() if v},
    }


def build_report(prs: list[dict[str, Any]], repo: str, now: datetime) -> dict[str, Any]:
    """Full report: every PR labeled, plus the recommended merge order."""
    order = recommend_merge_order(prs, now)
    all_labeled = [
        {
            "number": pr["number"],
            "title": pr["title"],
            "url": pr.get("url", ""),
            "label": classify_readiness(pr),
            "age_days": age_days(pr["created_at"], now),
            "files": pr.get("files", []),
        }
        for pr in prs
    ]
    return {
        "repo": repo,
        "synced_at": now.isoformat(),
        "prs": all_labeled,
        "batch1": order["batch1"],
        "batch2": order["batch2"],
        "blocked": order["blocked"],
        "drafts": order["drafts"],
        "overlap_graph": order["overlap_graph"],
    }
