"""Project identity and database path resolution."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Optional


CONFIG_FILENAME = ".worklog.json"
DB_DIR = Path.home() / ".worklog"


def find_git_root(start: Path = Path.cwd()) -> Optional[Path]:
    """Walk up from `start` until a .git directory is found, or return None."""
    current = start.resolve()
    while True:
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def _run_git(args: list[str], cwd: Path) -> str:
    """Run a git command and return stdout. Raises RuntimeError on failure."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def derive_project_id(git_root: Path) -> str:
    """
    Produce a stable project identifier from the remote URL when available,
    falling back to an absolute path hash.  Uses only the last two path
    segments of the remote URL so the ID is portable across machines.
    """
    try:
        remote = _run_git(["remote", "get-url", "origin"], git_root)
        # Normalise: strip .git suffix, extract owner/repo
        remote = remote.removesuffix(".git")
        parts = remote.replace(":", "/").split("/")
        key = "/".join(parts[-2:]) if len(parts) >= 2 else remote
    except RuntimeError:
        key = str(git_root)

    # Produce a short deterministic slug: last two path components + 8-char hash
    slug_parts = git_root.parts[-2:] if len(git_root.parts) >= 2 else git_root.parts
    slug = "-".join(slug_parts).lower().replace(" ", "_")
    short_hash = hashlib.sha256(key.encode()).hexdigest()[:8]
    return f"{slug}-{short_hash}"


def load_local_config(git_root: Path) -> dict:
    """Load optional .worklog.json from the repo root."""
    config_path = git_root / CONFIG_FILENAME
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}


def get_db_path(project_id: str) -> Path:
    """Return the SQLite database path for a project, creating the directory."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return DB_DIR / f"{project_id}.db"


class ProjectContext:
    """Resolved identity and paths for the current repository."""

    def __init__(
        self,
        git_root: Path,
        project_id: str,
        db_path: Path,
        local_config: dict,
    ) -> None:
        self.git_root = git_root
        self.project_id = project_id
        self.db_path = db_path
        self.local_config = local_config

    @classmethod
    def resolve(cls, cwd: Optional[Path] = None) -> "ProjectContext":
        """Detect the project from the current working directory."""
        start = Path(cwd) if cwd else Path.cwd()
        git_root = find_git_root(start)
        if git_root is None:
            raise RuntimeError(
                f"No git repository found at or above '{start}'. "
                "Run worklog from inside a git repository."
            )
        local_config = load_local_config(git_root)
        project_id = local_config.get("project_id") or derive_project_id(git_root)
        db_path = get_db_path(project_id)
        return cls(git_root, project_id, db_path, local_config)
