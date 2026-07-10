"""Repository discovery and stable project identity."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

from . import util

DEFAULT_BRANCHES = {"main", "master", "develop", "trunk", "HEAD"}

_GITHUB_HTTPS_RE = re.compile(r"github\.com[:/]+(?P<owner>[^/]+)/(?P<repo>[^/.]+?)(?:\.git)?/?$")


class NotAGitRepoError(RuntimeError):
    pass


def run_git(args: list[str], cwd: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def parse_github_remote(remote_url: str) -> tuple[str, str] | None:
    """Extract (owner, repo) from a GitHub HTTPS or SSH remote URL, else None."""
    if not remote_url:
        return None
    match = _GITHUB_HTTPS_RE.search(remote_url)
    if not match:
        return None
    return match.group("owner"), match.group("repo")


@dataclass
class ProjectState:
    repo_root: str
    project_id: str
    github_owner_repo: tuple[str, str] | None
    branch: str
    head_sha: str
    remotes: dict = field(default_factory=dict)
    dirty_files: list = field(default_factory=list)
    untracked_files: list = field(default_factory=list)


def discover_project(repo_path: str) -> ProjectState:
    try:
        repo_root = run_git(["rev-parse", "--show-toplevel"], cwd=repo_path)
    except RuntimeError as exc:
        raise NotAGitRepoError(str(exc)) from exc

    try:
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    except RuntimeError:
        branch = "HEAD"

    try:
        head_sha = run_git(["rev-parse", "HEAD"], cwd=repo_root)
    except RuntimeError:
        head_sha = ""

    remotes: dict = {}
    try:
        remote_names = [n for n in run_git(["remote"], cwd=repo_root).splitlines() if n]
        for name in remote_names:
            try:
                remotes[name] = run_git(["remote", "get-url", name], cwd=repo_root)
            except RuntimeError:
                continue
    except RuntimeError:
        pass

    github_owner_repo = None
    for candidate in ("origin", *remotes.keys()):
        if candidate in remotes:
            github_owner_repo = parse_github_remote(remotes[candidate])
            if github_owner_repo:
                break

    if github_owner_repo:
        project_id = f"github:{github_owner_repo[0]}/{github_owner_repo[1]}"
    else:
        project_id = f"local:{util.path_hash(repo_root)}"

    dirty_files, untracked_files = _working_tree_state(repo_root)

    return ProjectState(
        repo_root=repo_root,
        project_id=project_id,
        github_owner_repo=github_owner_repo,
        branch=branch,
        head_sha=head_sha,
        remotes=remotes,
        dirty_files=dirty_files,
        untracked_files=untracked_files,
    )


def is_ancestor(repo_root: str, ancestor_sha: str, descendant_sha: str) -> bool:
    """True if ancestor_sha is an ancestor of (or equal to) descendant_sha.

    Uses `git merge-base --is-ancestor`, whose exit code 1 is a valid negative answer, not an
    error — unlike every other git subcommand this module wraps.
    """
    if not ancestor_sha or not descendant_sha:
        return False
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor_sha, descendant_sha],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(f"git merge-base --is-ancestor failed: {result.stderr.strip()}")
    return result.returncode == 0


def _working_tree_state(repo_root: str) -> tuple[list, list]:
    # `git status --porcelain` lines start with a 2-char status column that can be a leading
    # space (e.g. " M file"). run_git()'s blanket .strip() would eat that leading space on the
    # first line only, silently shifting every downstream slice — so this reads raw output.
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return [], []
    dirty, untracked = [], []
    for line in result.stdout.split("\n"):
        if not line:
            continue
        code, path = line[:2], line[3:]
        if code == "??":
            untracked.append(path)
        else:
            dirty.append(path)
    return dirty, untracked
