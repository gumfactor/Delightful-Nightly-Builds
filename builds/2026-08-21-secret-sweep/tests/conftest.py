"""Shared pytest fixtures: real temporary git repositories (no mocked git plumbing)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class GitRepo:
    def __init__(self, path: Path):
        self.path = path

    def write(self, relative_path: str, content: str) -> None:
        full = self.path / relative_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")

    def remove(self, relative_path: str) -> None:
        (self.path / relative_path).unlink()

    def run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True, text=True, check=True,
        )

    def commit_all(self, message: str) -> str:
        self.run("add", "-A")
        self.run("commit", "-m", message, "--allow-empty")
        result = self.run("rev-parse", "HEAD")
        return result.stdout.strip()

    def as_posix(self) -> str:
        return str(self.path)


@pytest.fixture
def git_repo(tmp_path) -> GitRepo:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=repo_path, check=True)
    return GitRepo(repo_path)


@pytest.fixture
def empty_git_repo(tmp_path) -> GitRepo:
    repo_path = tmp_path / "empty_repo"
    repo_path.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo_path, check=True)
    return GitRepo(repo_path)
