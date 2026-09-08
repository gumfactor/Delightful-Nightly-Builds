"""Git repository discovery and commit-history diff walking.

Everything here shells out to the local `git` binary with fixed argument
lists (never `shell=True`, never string-interpolated user input into a
shell command) — repo paths come from directory discovery or an explicit
CLI argument and are always passed as individual subprocess argv entries.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.entropy import find_high_entropy_tokens
from src.patterns import match_vendor_patterns

# Directories never worth descending into while looking for `.git` markers.
_SKIP_DIR_NAMES = frozenset({"node_modules", ".venv", "venv", "__pycache__", ".tox"})

_HUNK_HEADER_PREFIX = "@@ -"


@dataclass
class RawHit:
    """One candidate secret found in one added line of one commit's diff."""

    repo: str
    commit: str
    file: str
    line: int
    pattern_name: str
    matched_text: str
    is_vendor_pattern: bool
    line_content: str


class GitCommandError(RuntimeError):
    """A git subprocess call failed."""


def discover_repos(root: Path) -> list[Path]:
    """Find every git repository (a directory containing `.git`) under root.

    Does not descend into a repo's own `.git` directory or into common
    heavyweight non-repo directories. `root` itself counts as a repo if it
    directly contains `.git`.
    """
    root = Path(root)
    if (root / ".git").exists():
        return [root]

    found: list[Path] = []
    for current_root, dirnames, _ in _walk_pruned(root):
        if ".git" in dirnames:
            found.append(Path(current_root))
            dirnames[:] = []
        else:
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIR_NAMES and not d.startswith(".")]
    return found


def _walk_pruned(root: Path):
    import os

    for current_root, dirnames, filenames in os.walk(root):
        yield current_root, dirnames, filenames


def run_git(repo_path: Path, args: list[str]) -> str:
    """Run a fixed-argument git command against repo_path and return stdout."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitCommandError(f"git {' '.join(args)} failed in {repo_path}: {result.stderr.strip()}")
    return result.stdout


def list_commits(repo_path: Path, all_branches: bool = True, max_commits: int | None = None) -> list[str]:
    """Return commit SHAs, newest first."""
    args = ["log", "--format=%H"]
    if all_branches:
        args.insert(1, "--all")
    if max_commits is not None:
        args.append(f"-n{max_commits}")
    try:
        output = run_git(repo_path, args)
    except GitCommandError:
        return []
    return [line for line in output.splitlines() if line.strip()]


def get_commit_diff(repo_path: Path, sha: str) -> str:
    """Return the unified diff introduced by a single (non-merge) commit."""
    try:
        # --root makes a repo's very first commit (which has no parent to
        # diff against) show its full content as additions, same as any
        # other commit — without it, diff-tree silently returns nothing.
        return run_git(repo_path, ["diff-tree", "--no-commit-id", "-p", "-r", "--root", sha])
    except GitCommandError:
        return ""


def _parse_diff_added_lines(diff_text: str):
    """Yield (file_path, line_number, line_content) for every added line in a diff."""
    current_file: str | None = None
    new_line_number = 0
    is_binary = False

    for raw_line in diff_text.splitlines():
        if raw_line.startswith("diff --git"):
            current_file = None
            is_binary = False
            continue
        if raw_line.startswith("Binary files") and "differ" in raw_line:
            is_binary = True
            continue
        if raw_line.startswith("+++ "):
            path = raw_line[4:].strip()
            if path == "/dev/null":
                current_file = None
            else:
                # Strip the "b/" prefix git uses for the new-file side.
                current_file = path[2:] if path.startswith("b/") else path
            continue
        if is_binary or current_file is None:
            continue
        if raw_line.startswith(_HUNK_HEADER_PREFIX):
            new_line_number = _parse_hunk_new_start(raw_line)
            continue
        if raw_line.startswith("+") and not raw_line.startswith("+++"):
            yield current_file, new_line_number, raw_line[1:]
            new_line_number += 1
        elif raw_line.startswith(" "):
            new_line_number += 1
        # Lines starting with "-" (removed) don't advance the new-file counter.


def _parse_hunk_new_start(hunk_header: str) -> int:
    # Format: @@ -old_start,old_count +new_start,new_count @@ ...
    try:
        plus_part = hunk_header.split("+", 1)[1].split(" ", 1)[0]
        new_start = int(plus_part.split(",")[0])
    except (IndexError, ValueError):
        return 1
    return new_start


def file_still_at_head(repo_path: Path, file_path: str, matched_text: str) -> bool:
    """Return True if matched_text is still present in HEAD's version of file_path."""
    try:
        content = run_git(repo_path, ["show", f"HEAD:{file_path}"])
    except GitCommandError:
        return False
    return matched_text in content


def scan_commit_diff(repo_name: str, sha: str, diff_text: str) -> list[RawHit]:
    """Scan one commit's diff text for vendor-pattern and high-entropy hits."""
    hits: list[RawHit] = []
    for file_path, line_number, line_content in _parse_diff_added_lines(diff_text):
        vendor_matches = match_vendor_patterns(line_content)
        for vendor in vendor_matches:
            match = vendor.regex.search(line_content)
            matched_text = match.group(0) if match else line_content
            hits.append(
                RawHit(
                    repo=repo_name,
                    commit=sha,
                    file=file_path,
                    line=line_number,
                    pattern_name=vendor.name,
                    matched_text=matched_text,
                    is_vendor_pattern=True,
                    line_content=line_content,
                )
            )
        if not vendor_matches:
            for token in find_high_entropy_tokens(line_content):
                hits.append(
                    RawHit(
                        repo=repo_name,
                        commit=sha,
                        file=file_path,
                        line=line_number,
                        pattern_name="High-Entropy Token",
                        matched_text=token,
                        is_vendor_pattern=False,
                        line_content=line_content,
                    )
                )
    return hits


def scan_repo(repo_path: Path, all_branches: bool = True, max_commits: int | None = None) -> list[RawHit]:
    """Scan every commit in a single repo and return all raw hits, newest-commit-first."""
    repo_name = Path(repo_path).name
    hits: list[RawHit] = []
    for sha in list_commits(repo_path, all_branches=all_branches, max_commits=max_commits):
        diff_text = get_commit_diff(repo_path, sha)
        if not diff_text:
            continue
        hits.extend(scan_commit_diff(repo_name, sha, diff_text))
    return hits
