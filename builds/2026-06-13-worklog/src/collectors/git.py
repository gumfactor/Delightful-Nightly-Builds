"""
Git activity collector — reads commits, branch state, and dirty files from
the local repository via subprocess git calls.  No shell=True; no user input
in command arguments.
"""

from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.ledger import make_event_id, utcnow


def _git(args: list[str], cwd: Path) -> str:
    """Run a git command; return stdout. Raises RuntimeError on non-zero exit."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def get_current_branch(git_root: Path) -> str:
    try:
        return _git(["rev-parse", "--abbrev-ref", "HEAD"], git_root)
    except RuntimeError:
        return "unknown"


def get_head_sha(git_root: Path) -> Optional[str]:
    try:
        return _git(["rev-parse", "HEAD"], git_root)
    except RuntimeError:
        return None


def get_dirty_files(git_root: Path) -> list[str]:
    """Return list of modified/untracked files (relative paths)."""
    try:
        # Use subprocess directly to avoid _git's .strip() eating the leading
        # space that is significant in git status --porcelain format ("XY path").
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(git_root),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return []
        files = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            if len(line) < 3:
                continue
            # Porcelain v1: exactly 2-char status code + 1 space + path
            path_part = line[3:]
            if " -> " in path_part:
                path_part = path_part.split(" -> ")[-1]
            files.append(path_part.strip())
        return files
    except Exception:
        return []


def parse_commit_log(raw: str) -> list[dict]:
    """
    Parse the output of `git log --format=...` into commit dicts.
    Format used: SHA|author_name|author_email|unix_timestamp|subject
    """
    commits = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        sha, author_name, author_email, ts_str, subject = parts
        try:
            ts_int = int(ts_str)
            ts = datetime.fromtimestamp(ts_int, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        except (ValueError, OSError):
            ts = utcnow()

        commits.append(
            {
                "sha": sha.strip(),
                "author_name": author_name.strip(),
                "author_email": author_email.strip(),
                "timestamp": ts,
                "subject": subject.strip(),
            }
        )
    return commits


def collect_commits(
    git_root: Path,
    project_id: str,
    since_days: int = 30,
    max_count: int = 200,
) -> list[dict]:
    """
    Collect recent commits and return them as ledger-ready event dicts.
    Also fetches per-commit file stats (--numstat) for file-overlap correlation.
    """
    fmt = "%H|%an|%ae|%at|%s"
    try:
        raw = _git(
            [
                "log",
                f"--since={since_days} days ago",
                f"--max-count={max_count}",
                f"--format={fmt}",
            ],
            git_root,
        )
    except RuntimeError:
        return []

    commit_metas = parse_commit_log(raw)
    events = []

    for meta in commit_metas:
        # Get file stats for this commit
        try:
            stat_raw = _git(
                ["diff-tree", "--no-commit-id", "-r", "--numstat", meta["sha"]],
                git_root,
            )
            files_changed = []
            additions, deletions = 0, 0
            for stat_line in stat_raw.splitlines():
                parts = stat_line.split("\t")
                if len(parts) == 3:
                    try:
                        additions += int(parts[0]) if parts[0] != "-" else 0
                        deletions += int(parts[1]) if parts[1] != "-" else 0
                    except ValueError:
                        pass
                    files_changed.append(parts[2])
        except RuntimeError:
            files_changed = []
            additions = deletions = 0

        event_id = make_event_id("git", meta["sha"], "commit")
        events.append(
            {
                "id": event_id,
                "timestamp": meta["timestamp"],
                "project_id": project_id,
                "type": "commit",
                "actor_kind": "human",
                "actor_name": meta["author_name"],
                "summary": meta["subject"],
                "status": "completed",
                "provider": "git",
                "source_ref": meta["sha"],
                "source_url": None,
                "metadata": {
                    "sha": meta["sha"],
                    "author_email": meta["author_email"],
                    "files_changed": files_changed,
                    "additions": additions,
                    "deletions": deletions,
                },
            }
        )

    return events


def collect_dirty_state(git_root: Path, project_id: str) -> list[dict]:
    """Produce a single dirty-tree snapshot event if there are uncommitted changes."""
    dirty = get_dirty_files(git_root)
    if not dirty:
        return []

    branch = get_current_branch(git_root)
    head = get_head_sha(git_root) or "unknown"
    source_ref = f"dirty:{head[:12]}"
    event_id = make_event_id("git", source_ref, "dirty_file")

    return [
        {
            "id": event_id,
            "timestamp": utcnow(),
            "project_id": project_id,
            "type": "dirty_file",
            "actor_kind": "human",
            "actor_name": None,
            "summary": f"{len(dirty)} uncommitted change(s) on {branch}",
            "status": "open",
            "provider": "git",
            "source_ref": source_ref,
            "source_url": None,
            "metadata": {"branch": branch, "head": head, "files": dirty},
        }
    ]
