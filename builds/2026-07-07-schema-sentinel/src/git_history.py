"""Read-only git history access for the `history` subcommand.

Every function here only ever invokes `git log` or `git show` via
subprocess.run with an argument list (never shell=True), and never mutates
the target repository.
"""
from __future__ import annotations

import os
import subprocess
from typing import List, Optional


class GitHistoryError(Exception):
    """Raised when a git repository or path cannot be read."""


def is_git_repo(repo_dir: str) -> bool:
    if not os.path.isdir(repo_dir):
        return False
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def list_revisions(repo_dir: str, path: str, limit: Optional[int] = None) -> List[dict]:
    """Return revisions touching `path`, oldest first, as {"sha", "date"} dicts."""
    cmd = ["git", "log", "--format=%H|%ad", "--date=iso-strict"]
    if limit:
        cmd += ["-n", str(limit)]
    cmd += ["--", path]

    result = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise GitHistoryError(
            f"git log failed for '{path}' in '{repo_dir}': {result.stderr.strip()}"
        )

    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise GitHistoryError(
            f"No git history found for '{path}' in '{repo_dir}' — "
            "check the path is correct and tracked by git."
        )

    revisions = [dict(zip(("sha", "date"), line.split("|", 1))) for line in lines]
    revisions.reverse()
    return revisions


def read_file_at_revision(repo_dir: str, sha: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{sha}:{path}"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitHistoryError(
            f"git show failed for {sha}:{path}: {result.stderr.strip()}"
        )
    return result.stdout
