"""Read-only git plumbing helpers for reconciling builds/index.md against repo state.

Every function accepts an injectable `runner` (defaults to `subprocess.run`) so tests
never touch the real filesystem or network. All git invocations use argument lists
(never shell=True), so branch/ref names discovered from git output can never be
interpreted as shell syntax.
"""
from __future__ import annotations

import subprocess
from typing import Callable, Optional

Runner = Callable[..., subprocess.CompletedProcess]


class GitError(RuntimeError):
    """Raised when a git command fails."""


def _run(args: list[str], cwd: str, runner: Runner) -> str:
    result = runner(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        # returncode 1 is a normal "false" answer for commands like
        # merge-base --is-ancestor; anything else is a real failure.
        raise GitError(
            f"git {' '.join(args)} failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout


def find_repo_root(start_path: str, runner: Runner = subprocess.run) -> str:
    """Return the absolute path to the git repo root containing start_path."""
    out = _run(["rev-parse", "--show-toplevel"], cwd=start_path, runner=runner)
    root = out.strip()
    if not root:
        raise GitError(f"{start_path} is not inside a git repository")
    return root


def detect_default_branch(cwd: str, runner: Runner = subprocess.run) -> str:
    """Return 'main' or 'master', whichever exists on origin. Prefers 'main'."""
    for candidate in ("main", "master"):
        result = runner(
            ["git", "rev-parse", "--verify", f"origin/{candidate}"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return candidate
    raise GitError("Could not find origin/main or origin/master")


def detect_owner_repo(cwd: str, runner: Runner = subprocess.run) -> Optional[tuple[str, str]]:
    """Parse 'owner/repo' out of the origin remote URL. Returns None if unparseable."""
    out = _run(["remote", "get-url", "origin"], cwd=cwd, runner=runner).strip()
    if not out:
        return None
    cleaned = out.removesuffix(".git")
    if cleaned.startswith("git@"):
        # git@github.com:owner/repo
        _, _, tail = cleaned.partition(":")
    else:
        # https://github.com/owner/repo
        tail = cleaned.split("github.com/", 1)[-1]
    parts = [p for p in tail.split("/") if p]
    if len(parts) < 2:
        return None
    return parts[-2], parts[-1]


def list_remote_branches(
    cwd: str, default_branch: str, runner: Runner = subprocess.run
) -> list[str]:
    """List remote branch refs (e.g. 'origin/claude/cool-sagan-xxxxx'), excluding
    origin/HEAD and the default branch."""
    out = _run(
        ["for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"],
        cwd=cwd,
        runner=runner,
    )
    excluded = {"origin/HEAD", f"origin/{default_branch}"}
    return [line for line in out.splitlines() if line and line not in excluded]


def list_build_folders_at_ref(
    cwd: str, ref: str, runner: Runner = subprocess.run
) -> set[str]:
    """List top-level entries under builds/ at the given ref (folder names only,
    e.g. '2026-06-18-regex-dojo')."""
    out = _run(["ls-tree", "--name-only", f"{ref}:builds/"], cwd=cwd, runner=runner)
    folders = set()
    for line in out.splitlines():
        line = line.strip()
        if not line or line in ("index.md", "ideas.md", "idea-briefs"):
            continue
        folders.add(line)
    return folders


def folder_added_by_branch(
    cwd: str, default_branch: str, branch: str, runner: Runner = subprocess.run
) -> set[str]:
    """Return the set of top-level builds/ folder names this branch adds relative
    to the default branch (i.e. new folders not present on the default branch)."""
    out = _run(
        [
            "diff",
            "--name-only",
            f"origin/{default_branch}...{branch}",
            "--",
            "builds/",
        ],
        cwd=cwd,
        runner=runner,
    )
    folders = set()
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("builds/"):
            continue
        remainder = line[len("builds/") :]
        top = remainder.split("/", 1)[0]
        if top and top not in ("index.md", "ideas.md", "idea-briefs"):
            folders.add(top)
    return folders


def build_folder_branch_map(
    cwd: str, default_branch: str, branches: list[str], runner: Runner = subprocess.run
) -> dict[str, str]:
    """Map each builds/ folder name to the first remote branch found that
    introduces it (folders already merged to the default branch are excluded
    by the caller before this is consulted)."""
    mapping: dict[str, str] = {}
    for branch in branches:
        for folder in folder_added_by_branch(cwd, default_branch, branch, runner=runner):
            mapping.setdefault(folder, branch)
    return mapping
