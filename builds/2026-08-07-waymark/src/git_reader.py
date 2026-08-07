"""Reads commit history from a local git repository via `git log`.

Read-only: never writes to, or otherwise mutates, the target repository.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"
HEADER_END = "\x02"

LOG_FORMAT = f"{RECORD_SEP}%H{FIELD_SEP}%an{FIELD_SEP}%aI{FIELD_SEP}%s{FIELD_SEP}%b{HEADER_END}"


class NotAGitRepoError(Exception):
    """Raised when the given path is not a git repository."""


class GitCommandError(Exception):
    """Raised when the underlying `git` invocation fails."""


def _run_git(repo_path: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitCommandError("git executable not found on PATH") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "not a git repository" in stderr.lower():
            raise NotAGitRepoError(f"{repo_path} is not a git repository")
        raise GitCommandError(stderr or "git command failed")

    return result.stdout


def validate_repo(repo_path: Path) -> None:
    """Raise NotAGitRepoError if repo_path does not contain a git repository."""
    resolved = Path(repo_path).expanduser().resolve()
    if not resolved.is_dir():
        raise NotAGitRepoError(f"{resolved} does not exist or is not a directory")
    _run_git(resolved, ["rev-parse", "--is-inside-work-tree"])


def _parse_numstat_line(line: str) -> tuple[int, int]:
    parts = line.split("\t")
    if len(parts) < 2:
        return 0, 0
    ins_raw, del_raw = parts[0], parts[1]
    insertions = int(ins_raw) if ins_raw.isdigit() else 0
    deletions = int(del_raw) if del_raw.isdigit() else 0
    return insertions, deletions


def _parse_record(record: str) -> dict[str, Any] | None:
    if HEADER_END not in record:
        return None
    header, _, numstat_block = record.partition(HEADER_END)
    fields = header.split(FIELD_SEP)
    if len(fields) < 5:
        return None
    commit_hash, author, committed_at, subject, body = fields[0], fields[1], fields[2], fields[3], fields[4]

    files_changed = 0
    insertions = 0
    deletions = 0
    for line in numstat_block.splitlines():
        line = line.strip("\n")
        if not line.strip():
            continue
        ins, dele = _parse_numstat_line(line)
        files_changed += 1
        insertions += ins
        deletions += dele

    return {
        "commit_hash": commit_hash,
        "author": author,
        "committed_at": committed_at,
        "subject": subject,
        "body": body.strip(),
        "files_changed": files_changed,
        "insertions": insertions,
        "deletions": deletions,
    }


def read_commits(repo_path: Path, exclude_hashes: set[str] | None = None) -> list[dict[str, Any]]:
    """Return every commit in the repo's history as a list of dicts.

    exclude_hashes, if given, skips commits whose hash is already known
    (incremental indexing) rather than re-parsing/re-storing them.
    """
    resolved = Path(repo_path).expanduser().resolve()
    validate_repo(resolved)
    exclude_hashes = exclude_hashes or set()

    raw = _run_git(resolved, ["log", "--all", "--numstat", f"--pretty=format:{LOG_FORMAT}"])
    if not raw.strip():
        return []

    commits = []
    for chunk in raw.split(RECORD_SEP):
        if not chunk.strip():
            continue
        parsed = _parse_record(chunk)
        if parsed is None:
            continue
        if parsed["commit_hash"] in exclude_hashes:
            continue
        commits.append(parsed)
    return commits
