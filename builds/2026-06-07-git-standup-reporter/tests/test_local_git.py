"""Tests for local_git — uses real temp git repos via pytest fixtures."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.local_git import find_git_repos, get_repo_name, get_unpushed_commits


@pytest.fixture()
def temp_repo(tmp_path):
    """Create a minimal git repo with one commit, no remote."""
    repo = tmp_path / "my-project"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@test.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Tester"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "commit.gpgsign", "false"], check=True)
    (repo / "README.md").write_text("hello")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "Initial commit"], check=True, capture_output=True)
    return repo


def test_find_git_repos_discovers_children(tmp_path, temp_repo):
    """find_git_repos returns repos found as direct children of the root."""
    found = find_git_repos([str(tmp_path)])
    assert str(temp_repo) in found


def test_find_git_repos_skips_nonexistent_root():
    """A root path that doesn't exist produces no results and no error."""
    found = find_git_repos(["/this/does/not/exist"])
    assert found == []


def test_get_repo_name_returns_directory_name(temp_repo):
    """get_repo_name returns the basename of the repo's top-level directory."""
    name = get_repo_name(str(temp_repo))
    assert name == "my-project"


def test_get_unpushed_commits_no_upstream(temp_repo):
    """Without a remote, commits in the time window are returned as local_unpushed."""
    commits = get_unpushed_commits(str(temp_repo), hours=24)
    assert len(commits) == 1
    assert commits[0]["message"] == "Initial commit"
    assert commits[0]["source"] == "local_unpushed"
    assert len(commits[0]["sha"]) == 40


def test_get_unpushed_commits_invalid_path():
    """An invalid path returns an empty list without raising."""
    commits = get_unpushed_commits("/not/a/repo", hours=24)
    assert commits == []
