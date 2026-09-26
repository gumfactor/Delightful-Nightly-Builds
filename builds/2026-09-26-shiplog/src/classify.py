"""Commit classification: conventional-commit parsing, keyword fallback, and
revert/re-revert cancellation."""
from __future__ import annotations

import re
from dataclasses import dataclass

from git_log import RawCommit

KNOWN_TYPES = {
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
}

CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<subject>.+)$"
)
MERGE_PR_RE = re.compile(r"^Merge pull request #(?P<num>\d+) from ")
REVERT_RE = re.compile(r'^Revert\s+"(?P<original>.+)"\s*$')
BREAKING_FOOTER_RE = re.compile(r"BREAKING[ -]CHANGE:")

# Checked in order; first match wins. Each entry: (category, [substrings]).
KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("fix", ["fix", "bug", "correct", "patch", "resolve", "hotfix"]),
    ("feat", ["add ", "implement", "introduce", "support for", "new feature"]),
    ("docs", ["docs", "readme", "documentation", "typo in comment"]),
    ("refactor", ["refactor", "rename", "restructure", "simplify"]),
    ("perf", ["perf", "performance", "optimi", "speed up"]),
    ("test", ["test", "spec"]),
    ("ci", ["ci ", "workflow", "pipeline", "github actions"]),
    ("build", ["build", "webpack", "bundle", "vite config"]),
    ("chore", ["chore", "bump ", "dependency", "dependencies", "release"]),
]


@dataclass
class Commit:
    sha: str
    subject: str
    body: str
    author_date: str
    type: str
    scope: str | None
    breaking: bool
    pr_number: int | None
    source: str  # "conventional" | "keyword" | "github-pr"
    raw_subject: str = ""  # unparsed first commit-message line, used for revert matching


def _keyword_classify(text: str) -> str:
    lowered = text.lower()
    for category, needles in KEYWORD_RULES:
        for needle in needles:
            if needle in lowered:
                return category
    return "other"


def extract_pr_number(subject: str) -> int | None:
    match = MERGE_PR_RE.match(subject)
    return int(match.group("num")) if match else None


def classify_commit(raw: RawCommit) -> Commit:
    pr_number = extract_pr_number(raw.subject)

    revert_match = REVERT_RE.match(raw.subject)
    if revert_match:
        return Commit(
            sha=raw.sha, subject=raw.subject, body=raw.body, author_date=raw.author_date,
            type="revert", scope=None, breaking=False, pr_number=pr_number, source="keyword",
            raw_subject=raw.subject,
        )

    match = CONVENTIONAL_RE.match(raw.subject)
    if match and match.group("type").lower() in KNOWN_TYPES:
        commit_type = match.group("type").lower()
        scope = match.group("scope")
        breaking = bool(match.group("bang")) or bool(BREAKING_FOOTER_RE.search(raw.body))
        subject = match.group("subject")
        return Commit(
            sha=raw.sha, subject=subject, body=raw.body, author_date=raw.author_date,
            type=commit_type, scope=scope, breaking=breaking, pr_number=pr_number, source="conventional",
            raw_subject=raw.subject,
        )

    breaking = bool(BREAKING_FOOTER_RE.search(raw.body))
    commit_type = _keyword_classify(raw.subject)
    return Commit(
        sha=raw.sha, subject=raw.subject, body=raw.body, author_date=raw.author_date,
        type=commit_type, scope=None, breaking=breaking, pr_number=pr_number, source="keyword",
        raw_subject=raw.subject,
    )


def cancel_reverts(commits: list[Commit]) -> tuple[list[Commit], list[tuple[Commit, Commit]]]:
    """Drop matched revert / original-commit pairs. Returns (surviving, cancelled_pairs)."""
    remaining = list(commits)
    cancelled: list[tuple[Commit, Commit]] = []

    reverts = [c for c in remaining if c.type == "revert"]
    for revert in reverts:
        match = REVERT_RE.match(revert.subject)
        if not match:
            continue
        original_subject = match.group("original")
        for candidate in remaining:
            if candidate is revert:
                continue
            if candidate.type == "revert":
                continue
            match_text = candidate.raw_subject or candidate.subject
            if match_text == original_subject:
                cancelled.append((candidate, revert))
                break

    cancelled_shas = set()
    for original, revert in cancelled:
        cancelled_shas.add(original.sha)
        cancelled_shas.add(revert.sha)

    surviving = [c for c in remaining if c.sha not in cancelled_shas]
    return surviving, cancelled


SECTION_MAP: dict[str, str] = {
    "feat": "Features",
    "fix": "Fixes",
    "perf": "Fixes",
    "docs": "Maintenance",
    "chore": "Maintenance",
    "refactor": "Maintenance",
    "test": "Maintenance",
    "ci": "Maintenance",
    "build": "Maintenance",
    "style": "Maintenance",
    "other": "Uncategorized",
}

SECTION_ORDER = ["Breaking Changes", "Features", "Fixes", "Maintenance", "Uncategorized"]


def group_sections(commits: list[Commit]) -> dict[str, list[Commit]]:
    sections: dict[str, list[Commit]] = {name: [] for name in SECTION_ORDER}
    for commit in commits:
        if commit.breaking:
            sections["Breaking Changes"].append(commit)
            continue
        section = SECTION_MAP.get(commit.type, "Uncategorized")
        sections[section].append(commit)
    return {name: items for name, items in sections.items() if items}
