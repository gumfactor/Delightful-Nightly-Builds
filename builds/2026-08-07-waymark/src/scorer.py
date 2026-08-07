"""Deterministic decision-worthiness scoring for git commits.

Pure functions, no I/O — every rule here is independently testable.
"""

from __future__ import annotations

import re
from typing import Any

CONVENTIONAL_TYPE_WEIGHTS = {
    "feat": 3,
    "fix": 2,
    "refactor": 3,
    "perf": 2,
    "security": 4,
    "revert": 3,
    "remove": 2,
    "deprecate": 3,
    "break": 4,
    "chore": 0,
    "docs": 0,
    "style": -1,
    "test": 0,
    "ci": 0,
    "build": 0,
}

CONVENTIONAL_TYPE_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(\([^)]*\))?(?P<breaking>!)?:\s*(?P<rest>.*)$"
)

DECISION_KEYWORDS = [
    "because",
    "switch to",
    "switched to",
    "migrate",
    "migration",
    "breaking",
    "deprecate",
    "workaround",
    "revert",
    "reverted",
    "abort",
    "instead of",
    "rather than",
    "decided",
    "decision",
    "trade-off",
    "tradeoff",
    "in favor of",
    "rollback",
    "root cause",
]

MERGE_SUBJECT_RE = re.compile(r"^merge\b", re.IGNORECASE)


def _detect_conventional_type(subject: str) -> tuple[str | None, bool]:
    match = CONVENTIONAL_TYPE_RE.match(subject.strip())
    if not match:
        return None, False
    commit_type = match.group("type").lower()
    is_breaking = bool(match.group("breaking"))
    return commit_type, is_breaking


def _keyword_score(text: str) -> int:
    lowered = text.lower()
    hits = sum(1 for kw in DECISION_KEYWORDS if kw in lowered)
    return min(hits * 2, 6)


def _size_score(files_changed: int, insertions: int, deletions: int) -> int:
    total_lines = insertions + deletions
    score = 0
    if files_changed >= 10:
        score += 2
    elif files_changed >= 3:
        score += 1
    if total_lines >= 300:
        score += 2
    elif total_lines >= 50:
        score += 1
    return score


def _body_score(body: str) -> int:
    if not body:
        return 0
    paragraphs = [p for p in body.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2 or len(body) >= 200:
        return 2
    if len(body) >= 60:
        return 1
    return 0


def score_commit(commit: dict[str, Any]) -> int:
    """Return a 0-10 decision-worthiness score for a parsed commit dict."""
    subject = commit.get("subject", "") or ""
    body = commit.get("body", "") or ""
    files_changed = commit.get("files_changed", 0) or 0
    insertions = commit.get("insertions", 0) or 0
    deletions = commit.get("deletions", 0) or 0

    if MERGE_SUBJECT_RE.match(subject.strip()) and not body:
        return 0

    score = 1  # baseline: every real commit carries a little context

    commit_type, is_breaking = _detect_conventional_type(subject)
    if commit_type is not None:
        score += CONVENTIONAL_TYPE_WEIGHTS.get(commit_type, 1)
    if is_breaking:
        score += 2

    score += _keyword_score(f"{subject} {body}")
    score += _size_score(files_changed, insertions, deletions)
    score += _body_score(body)

    return max(0, min(score, 10))


def extract_tags(commit: dict[str, Any]) -> list[str]:
    """Heuristically extract tags: conventional type, plus matched decision keywords."""
    subject = commit.get("subject", "") or ""
    body = commit.get("body", "") or ""
    tags: list[str] = []

    commit_type, is_breaking = _detect_conventional_type(subject)
    if commit_type:
        tags.append(commit_type)
    if is_breaking:
        tags.append("breaking")

    lowered = f"{subject} {body}".lower()
    for kw in DECISION_KEYWORDS:
        if kw in lowered:
            tags.append(kw.replace(" ", "-"))

    seen: set[str] = set()
    deduped = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            deduped.append(tag)
    return deduped


def deterministic_summary(commit: dict[str, Any]) -> str:
    """Always-available, zero-network plain-English summary of a commit."""
    subject = (commit.get("subject") or "").strip() or "(no subject)"
    files_changed = commit.get("files_changed", 0) or 0
    insertions = commit.get("insertions", 0) or 0
    deletions = commit.get("deletions", 0) or 0

    commit_type, is_breaking = _detect_conventional_type(subject)
    type_label = f"{commit_type} " if commit_type else ""
    breaking_label = "breaking " if is_breaking else ""

    scope = f"{files_changed} file{'s' if files_changed != 1 else ''}" if files_changed else "no tracked files"
    stats = f"(+{insertions}/-{deletions})" if (insertions or deletions) else ""

    return f"{breaking_label}{type_label}change touching {scope} {stats}: {subject}".replace("  ", " ").strip()
