"""Shared pytest fixtures for Waymark tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from src import db as db_module


def _git(repo_path: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo_path), *args], check=True, capture_output=True, text=True)


@pytest.fixture
def tmp_git_repo(tmp_path: Path) -> Path:
    """A real, minimal git repo with a small, deterministic commit history."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")

    (repo / "a.py").write_text("print('hello')\n")
    _git(repo, "add", "a.py")
    _git(repo, "commit", "-q", "-m", "chore: initial commit")

    (repo / "a.py").write_text("print('hello world')\n" * 5)
    _git(repo, "add", "a.py")
    _git(
        repo,
        "commit",
        "-q",
        "-m",
        "refactor!: switch to a plugin-based renderer\n\n"
        "We decided to switch to a plugin-based renderer because the old "
        "monolithic renderer could not support the new export formats we need.\n\n"
        "This is a breaking change for anyone importing the old renderer class.",
    )

    (repo / "b.py").write_text("x = 1\n")
    _git(repo, "add", "b.py")
    _git(repo, "commit", "-q", "-m", "fix: correct off-by-one error in loop bound")

    return repo


@pytest.fixture
def empty_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "empty_repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    return repo


@pytest.fixture
def db_conn(tmp_path: Path):
    conn = db_module.connect(tmp_path / "waymark_test.db")
    yield conn
    conn.close()


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "waymark_test.db"
