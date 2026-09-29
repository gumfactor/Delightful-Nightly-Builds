"""Project discovery, identity and configuration."""
import fnmatch
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .redact import strip_url_credentials

CONFIG_NAME = ".worklog.json"


class WorklogError(Exception):
    """User-facing error (printed without a traceback)."""


def git(root: Path, *args: str, check: bool = True) -> str:
    """Run git with an argument list (never a shell string). Returns stdout."""
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace")
    if check and proc.returncode != 0:
        raise WorklogError(f"git {' '.join(args[:2])} failed: {proc.stderr.strip()}")
    return proc.stdout if proc.returncode == 0 else ""


@dataclass
class Config:
    name: Optional[str] = None
    exclude_paths: list[str] = field(default_factory=list)
    exclude_branches: list[str] = field(default_factory=list)
    exclude_providers: list[str] = field(default_factory=list)
    default_branch: Optional[str] = None
    github_repo: Optional[str] = None  # "owner/name" override
    max_commits: int = 500

    def path_excluded(self, path: str) -> bool:
        return any(fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path.split("/")[-1], pat)
                   for pat in self.exclude_paths)

    def branch_excluded(self, branch: str) -> bool:
        return any(fnmatch.fnmatch(branch, pat) for pat in self.exclude_branches)


def load_config(root: Path) -> Config:
    path = root / CONFIG_NAME
    if not path.exists():
        return Config()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise WorklogError(f"{CONFIG_NAME} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise WorklogError(f"{CONFIG_NAME} must contain a JSON object")
    known = {name for name in Config.__dataclass_fields__}
    return Config(**{key: value for key, value in raw.items() if key in known})


def find_root(start: Path) -> Path:
    start = Path(start)
    proc = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise WorklogError(f"{start} is not inside a git repository")
    return Path(proc.stdout.strip())


def normalize_remote(url: str) -> str:
    """git@github.com:o/r.git and https://tok@github.com/o/r -> github.com/o/r"""
    url = strip_url_credentials(url.strip())
    match = re.match(r"^[\w.\-]+@([^:/]+):(.+)$", url)
    if match:
        url = f"{match.group(1)}/{match.group(2)}"
    url = re.sub(r"^[a-z+]+://", "", url, flags=re.I)
    url = re.sub(r"\.git$", "", url).rstrip("/")
    return url.lower()


def github_slug(remote: Optional[str]) -> Optional[str]:
    """'github.com/owner/name' -> 'owner/name' (None for non-GitHub remotes)."""
    if not remote:
        return None
    match = re.match(r"^github\.com/([^/]+)/([^/]+)$", remote)
    return f"{match.group(1)}/{match.group(2)}" if match else None


@dataclass
class Project:
    root: Path
    git_dir: Path
    project_id: str
    name: str
    remote: Optional[str]
    default_branch: str
    config: Config


def detect_default_branch(root: Path, config: Config) -> str:
    if config.default_branch:
        return config.default_branch
    head = git(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False).strip()
    if head:
        return head.split("/", 1)[-1]
    branches = set(git(root, "for-each-ref", "--format=%(refname:short)", "refs/heads").split())
    for candidate in ("main", "master", "trunk", "develop"):
        if candidate in branches:
            return candidate
    current = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False).strip()
    return current or "main"


def discover(start: Path) -> Project:
    root = find_root(start)
    config = load_config(root)
    remote_url = git(root, "remote", "get-url", "origin", check=False).strip()
    if not remote_url:
        remotes = git(root, "remote", check=False).split()
        remote_url = git(root, "remote", "get-url", remotes[0], check=False).strip() if remotes else ""
    remote = normalize_remote(remote_url) if remote_url else None
    if remote:
        anchor = remote
    else:
        roots = git(root, "rev-list", "--max-parents=0", "HEAD", check=False).split()
        anchor = roots[0] if roots else str(root)
    name = config.name or (remote.rsplit("/", 1)[-1] if remote else root.name)
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"
    project_id = f"{slug}-{hashlib.sha1(anchor.encode()).hexdigest()[:8]}"
    git_dir = Path(git(root, "rev-parse", "--absolute-git-dir").strip())
    return Project(root=root, git_dir=git_dir, project_id=project_id, name=name, remote=remote,
                   default_branch=detect_default_branch(root, config), config=config)


_ISSUE_REF = re.compile(r"(?<![\w/])#(\d{1,6})\b")
_BRANCH_ISSUE = re.compile(r"(?:^|[/_-])(?:issue|gh)[-_](\d{1,6})(?=[-_/]|$)")


def refs_from_text(text: str) -> list[str]:
    """Explicit '#41' style references (issues and PRs share GitHub's number space)."""
    return [f"gh:{num}" for num in _ISSUE_REF.findall(text or "")]


def refs_from_branch(branch: str) -> list[str]:
    """'feature/41-csv' or 'issue-41-csv' -> gh:41. Bare version-like names are ignored."""
    found = set(_BRANCH_ISSUE.findall(branch))
    leaf_match = re.match(r"^(?:[\w.\-]+/)?(\d{1,6})[-_]", branch)
    if leaf_match:
        found.add(leaf_match.group(1))
    return [f"gh:{num}" for num in sorted(found)]
