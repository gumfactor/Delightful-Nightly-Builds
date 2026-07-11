"""Collects commits, branches, and tags from a local git repository."""

from __future__ import annotations

from dataclasses import dataclass, field

from .project import DEFAULT_BRANCHES, run_git

_LOG_SEP = "\x1f"
_REC_SEP = "\x1e"
_LOG_FORMAT = _LOG_SEP.join(["%H", "%aI", "%an", "%ae", "%s"]) + _REC_SEP


@dataclass
class CommitInfo:
    sha: str
    timestamp: str
    author_name: str
    author_email: str
    subject: str
    branch: str
    files: list = field(default_factory=list)


@dataclass
class BranchInfo:
    name: str
    upstream: str
    head_sha: str


@dataclass
class TagInfo:
    name: str
    sha: str


def _local_branch_names(repo_root: str) -> set[str]:
    try:
        output = run_git(["branch", "--format=%(refname:short)"], cwd=repo_root)
    except RuntimeError:
        return set()
    return {name.strip() for name in output.splitlines() if name.strip()}


def resolve_default_branch(repo_root: str) -> str | None:
    """Best-effort local default branch, tried in the same order project.DEFAULT_BRANCHES lists."""
    names = _local_branch_names(repo_root)
    for candidate in DEFAULT_BRANCHES:
        if candidate in names:
            return candidate
    return None


def collect_commits(repo_root: str, branch: str, max_count: int = 500) -> list[CommitInfo]:
    """Collect commits for `branch`, oldest first.

    When `branch` is a non-default feature branch, this collects only commits unique to it
    (`git log <default>..<branch>`), not the full ancestry shared with the default branch.
    Otherwise a commit made on `main` long before a feature branch existed would get tagged
    with whatever branch happens to be checked out at sync time, corrupting branch-based
    workstream correlation with unrelated shared history.

    Oldest-first matters beyond display order too: correlation (see correlate.py) establishes
    a workstream's anchor from whichever event it processes first. `git log`'s default
    newest-first order would let a later commit on a branch (no issue reference) claim a fresh
    branch-only workstream before an earlier commit on the same branch (which does reference
    an issue) has a chance to establish the higher-confidence issue-based anchor — splitting
    one real workstream into two. Processing oldest-first avoids that.
    """
    default_branch = resolve_default_branch(repo_root)
    range_spec = f"{default_branch}..{branch}" if default_branch and default_branch != branch else branch

    log_output = run_git(
        ["log", range_spec, f"--max-count={max_count}", f"--pretty=format:{_LOG_FORMAT}"],
        cwd=repo_root,
    )
    commits: list[CommitInfo] = []
    for record in filter(None, log_output.split(_REC_SEP)):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(_LOG_SEP)
        if len(parts) != 5:
            continue
        sha, timestamp, author_name, author_email, subject = parts
        files = _changed_files(repo_root, sha)
        commits.append(
            CommitInfo(
                sha=sha,
                timestamp=timestamp,
                author_name=author_name,
                author_email=author_email,
                subject=subject,
                branch=branch,
                files=files,
            )
        )
    commits.reverse()
    return commits


def _changed_files(repo_root: str, sha: str) -> list[str]:
    try:
        output = run_git(["show", "--name-only", "--pretty=format:", sha], cwd=repo_root)
    except RuntimeError:
        return []
    return [line for line in output.splitlines() if line.strip()]


def collect_branches(repo_root: str) -> list[BranchInfo]:
    try:
        output = run_git(
            ["for-each-ref", "--format=%(refname:short)|%(upstream:short)|%(objectname)", "refs/heads/"],
            cwd=repo_root,
        )
    except RuntimeError:
        return []
    branches = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 3:
            continue
        name, upstream, head_sha = parts
        branches.append(BranchInfo(name=name, upstream=upstream, head_sha=head_sha))
    return branches


def collect_tags(repo_root: str) -> list[TagInfo]:
    try:
        output = run_git(
            ["for-each-ref", "--format=%(refname:short)|%(objectname)", "refs/tags/"],
            cwd=repo_root,
        )
    except RuntimeError:
        return []
    tags = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("|")
        if len(parts) != 2:
            continue
        name, sha = parts
        tags.append(TagInfo(name=name, sha=sha))
    return tags
