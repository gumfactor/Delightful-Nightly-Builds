"""Read git commit history from one or more repository directories."""

import subprocess
from pathlib import Path
from typing import List, Optional


# ASCII unit separator — safe field delimiter; won't appear in git output
_SEP = "\x1f"


def get_repo_name(path: str) -> str:
    """Return the repository's top-level directory basename.

    Falls back to the path's own basename if git is unavailable or the path
    is not inside a git repository.
    """
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


def get_default_author(path: str) -> str:
    """Return the git user.name configured for the given path, or empty string."""
    try:
        result = subprocess.run(
            ["git", "-C", path, "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def get_commits_since(
    path: str, hours: int, author: Optional[str] = None
) -> List[dict]:
    """Return commits from the given repo made in the last N hours.

    Each commit is a dict with keys: hash, message, author, timestamp, repo.
    Returns an empty list if the path is not a git repo, git is missing, or
    git exits with a non-zero status.
    """
    cmd = [
        "git",
        "-C",
        path,
        "log",
        f"--since={hours} hours ago",
        f"--pretty=format:%H{_SEP}%s{_SEP}%an{_SEP}%ai",
    ]
    if author:
        cmd.extend(["--author", author])

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    if result.returncode != 0:
        return []

    repo = get_repo_name(path)
    commits: List[dict] = []

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
                "message": parts[1],
                "author": parts[2],
                "timestamp": parts[3],
                "repo": repo,
            }
        )

    return commits
