"""Read-only git log access. Never mutates the target repository."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass

RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"
PRETTY_FORMAT = f"%H{FIELD_SEP}%aI{FIELD_SEP}%s{FIELD_SEP}%b{RECORD_SEP}"


@dataclass
class RawCommit:
    sha: str
    author_date: str
    subject: str
    body: str


class GitLogError(RuntimeError):
    """Raised when the target path is not a usable git repository or the ref is invalid."""


def _run_git(repo_path: str, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", repo_path, *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GitLogError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def is_git_repo(repo_path: str) -> bool:
    try:
        _run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
        return True
    except GitLogError:
        return False


def is_valid_ref(repo_path: str, ref: str) -> bool:
    try:
        _run_git(repo_path, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
        return True
    except GitLogError:
        return False


def latest_tag(repo_path: str, until_ref: str) -> str | None:
    try:
        out = _run_git(repo_path, ["describe", "--tags", "--abbrev=0", until_ref])
        return out.strip() or None
    except GitLogError:
        return None


def resolve_range(repo_path: str, since: str | None, until: str) -> tuple[str | None, bool]:
    """Return (range_expr_or_date_flag_value, since_is_date).

    If since resolves to a git ref, returns ("since..until"-style lower bound ref, False).
    If since is not a valid ref (treated as a date string), returns (since, True).
    If since is None, tries to find the latest tag reachable from until; if none exists,
    returns (None, False) meaning "from the beginning of history".
    """
    if since is not None:
        if is_valid_ref(repo_path, since):
            return since, False
        return since, True  # treat as a date string for --since=

    tag = latest_tag(repo_path, until)
    return tag, False


def fetch_commits(repo_path: str, since: str | None, until: str = "HEAD") -> tuple[list[RawCommit], str]:
    """Fetch commits in (since, until] on the first-parent chain.

    Returns (commits, range_label). Raises GitLogError for an invalid until ref.
    """
    if not is_git_repo(repo_path):
        raise GitLogError(f"'{repo_path}' is not a git repository")
    if not is_valid_ref(repo_path, until):
        raise GitLogError(f"'{until}' is not a valid git ref")

    lower_bound, since_is_date = resolve_range(repo_path, since, until)

    args = ["log", "--first-parent", f"--pretty=format:{PRETTY_FORMAT}"]
    if since_is_date:
        args.append(f"--since={lower_bound}")
        args.append(until)
        range_label = f"{lower_bound}..{until}"
    elif lower_bound:
        args.append(f"{lower_bound}..{until}")
        range_label = f"{lower_bound}..{until}"
    else:
        args.append(until)
        range_label = f"start..{until}"

    raw = _run_git(repo_path, args)
    commits: list[RawCommit] = []
    for record in raw.split(RECORD_SEP):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split(FIELD_SEP)
        if len(parts) != 4:
            continue
        sha, author_date, subject, body = parts
        commits.append(RawCommit(sha=sha, author_date=author_date, subject=subject, body=body.strip("\n")))
    return commits, range_label
