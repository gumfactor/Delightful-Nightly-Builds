"""Thin, safe wrappers around the user's local `git` binary.

Every call goes through subprocess.run with an argument list (never
shell=True, never a string built by concatenating user input) and is
scoped to a single repo via `-C <repo_path>`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

MAX_FILE_BYTES = 2_000_000  # skip anything bigger than this — unlikely to be a hand-edited secret file


class NotAGitRepoError(Exception):
    pass


def _run_git(repo_path: str, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
    )


def is_git_repo(repo_path: str) -> bool:
    if not Path(repo_path).is_dir():
        return False
    result = _run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def repo_name(repo_path: str) -> str:
    return Path(repo_path).resolve().name


def list_working_tree_files(repo_path: str) -> list[str]:
    """Tracked + untracked-but-not-ignored files, relative to repo_path (respects .gitignore)."""
    result = _run_git(repo_path, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    if result.returncode != 0:
        return []
    raw = result.stdout.split("\0")
    return [f for f in raw if f]


def read_working_tree_file(repo_path: str, relative_path: str) -> str | None:
    """Return decoded text content, or None if binary / unreadable / too large."""
    full_path = Path(repo_path) / relative_path
    try:
        if not full_path.is_file():
            return None
        if full_path.stat().st_size > MAX_FILE_BYTES:
            return None
        return full_path.read_text(encoding="utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        return None


def has_any_commits(repo_path: str) -> bool:
    result = _run_git(repo_path, ["rev-parse", "--verify", "HEAD"])
    return result.returncode == 0


def read_head_file(repo_path: str, relative_path: str) -> str | None:
    """Return the current HEAD version of a file's text content, or None if absent/binary."""
    result = _run_git(repo_path, ["show", f"HEAD:{relative_path}"])
    if result.returncode != 0:
        return None
    return result.stdout


def get_history_patch(repo_path: str, max_commits: int | None = None) -> str:
    """Full `git log -p --no-merges --unified=0` output for the current branch's history."""
    args = ["log", "-p", "--no-merges", "--unified=0", "--no-color"]
    if max_commits is not None:
        args.extend(["-n", str(max_commits)])
    result = _run_git(repo_path, args, timeout=120)
    if result.returncode != 0:
        return ""
    return result.stdout


def iter_added_lines(patch_text: str):
    """Yield (commit_sha, file_path, line_number, added_line_content) for every added
    content line in a `git log -p --unified=0` patch, in order.

    A small stateful scanner rather than a full diff-parser: only the pieces of the
    unified-diff format needed to attribute an added line to its commit/file/line are
    tracked (commit header, `+++ b/<path>` file header, `@@ -a,b +c,d @@` hunk header).
    """
    current_sha: str | None = None
    current_file: str | None = None
    next_new_line: int | None = None

    for raw_line in patch_text.splitlines():
        if raw_line.startswith("commit "):
            current_sha = raw_line.split(" ", 1)[1].strip()
            current_file = None
            next_new_line = None
            continue
        if raw_line.startswith("+++ "):
            path = raw_line[4:].strip()
            if path == "/dev/null":
                current_file = None
            else:
                current_file = path[2:] if path.startswith("b/") else path
            continue
        if raw_line.startswith("--- "):
            continue
        if raw_line.startswith("@@"):
            # Format: @@ -a,b +c,d @@ ...   -> new-file start line is c
            try:
                plus_part = raw_line.split("+", 1)[1].split(" ", 1)[0]
                new_start = int(plus_part.split(",")[0])
                next_new_line = new_start
            except (IndexError, ValueError):
                next_new_line = None
            continue
        if raw_line.startswith("diff --git"):
            current_file = None
            next_new_line = None
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            if current_sha and current_file and next_new_line is not None:
                yield current_sha, current_file, next_new_line, raw_line[1:]
                next_new_line += 1
            continue
        if raw_line.startswith("-") and not raw_line.startswith("---"):
            # Removed line — doesn't advance the new-file line counter.
            continue
