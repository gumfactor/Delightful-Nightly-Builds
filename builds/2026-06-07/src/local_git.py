"""Scan local directories for git repos and return unpushed commits."""

import subprocess
from pathlib import Path
from typing import Optional

_SEP = "\x1f"


def find_git_repos(roots: list[str]) -> list[str]:
    """Return paths to all git repos found directly inside each root directory.

    Checks the root itself, then scans one level of subdirectories. Silently
    skips roots that don't exist.
    """
    repos: list[str] = []
    for root in roots:
        root_path = Path(root).expanduser()
        if not root_path.exists():
            continue
        if (root_path / ".git").exists():
            repos.append(str(root_path))
        for child in sorted(root_path.iterdir()):
            if child.is_dir() and (child / ".git").exists():
                repos.append(str(child))
    return repos


def get_repo_name(path: str) -> str:
    """Return the top-level directory name of the git repo at path."""
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).name
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return Path(path).resolve().name


def _has_upstream(path: str) -> bool:
    """Return True if the current branch has a configured remote tracking branch."""
    result = subprocess.run(
        ["git", "-C", path, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.returncode == 0


def get_unpushed_commits(
    path: str, hours: int, author: Optional[str] = None
) -> list[dict]:
    """Return commits that exist locally but have not been pushed to the remote.

    On branches with a tracking remote: uses @{u}..HEAD (exact unpushed set).
    On branches with no upstream: falls back to commits in the last N hours
    (may include already-pushed commits; caller should deduplicate via SHA).
    """
    if _has_upstream(path):
        rev_range = ["@{u}..HEAD"]
    else:
        rev_range = [f"--since={hours} hours ago"]

    cmd = [
        "git",
        "-C",
        path,
        "log",
        *rev_range,
        f"--pretty=format:%H{_SEP}%s{_SEP}%an{_SEP}%ai",
        "--no-merges",
    ]
    if author:
        cmd.extend(["--author", author])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0:
        return []

    repo = get_repo_name(path)
    commits: list[dict] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(_SEP)
        if len(parts) != 4:
            continue
        commits.append(
            {
                "hash": parts[0][:8],
                "sha": parts[0],
                "message": parts[1],
                "author": parts[2],
                "timestamp": parts[3],
                "repo": repo,
                "source": "local_unpushed",
            }
        )
    return commits
