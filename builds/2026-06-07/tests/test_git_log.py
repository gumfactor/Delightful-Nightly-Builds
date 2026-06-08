"""Tests for git_log module — uses a real temporary git repository."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.git_log import get_commits_since, get_default_author, get_repo_name


# Skip the entire module if git is not available on this system
if not shutil.which("git"):
    pytest.skip("git binary not found", allow_module_level=True)


@pytest.fixture
def temp_git_repo(tmp_path):
    """Create a temporary git repository containing one commit."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "tester@example.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Test User"],
        check=True,
        capture_output=True,
    )
    # Disable commit signing so tests don't depend on any external signing server
    subprocess.run(
        ["git", "-C", str(repo), "config", "commit.gpgsign", "false"],
        check=True,
        capture_output=True,
    )
    (repo / "README.md").write_text("hello world")
    subprocess.run(
        ["git", "-C", str(repo), "add", "."], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "Initial commit"],
        check=True,
        capture_output=True,
    )
    return str(repo)


def test_get_commits_since_finds_recent_commit(temp_git_repo):
    """Recent commits in a valid repo are returned."""
    commits = get_commits_since(temp_git_repo, hours=24)
    assert len(commits) == 1
    assert commits[0]["message"] == "Initial commit"


def test_commit_dict_has_expected_keys(temp_git_repo):
    """Each commit dict contains exactly the expected keys with correct types."""
    commits = get_commits_since(temp_git_repo, hours=24)
    assert len(commits) == 1
    commit = commits[0]
    assert set(commit.keys()) == {"hash", "message", "author", "timestamp", "repo"}
    assert len(commit["hash"]) == 8
    assert commit["author"] == "Test User"


def test_get_commits_since_author_filter_match(temp_git_repo):
    """Author filter returns commits whose author name contains the given substring."""
    commits = get_commits_since(temp_git_repo, hours=24, author="Test User")
    assert len(commits) == 1


def test_get_commits_since_author_filter_no_match(temp_git_repo):
    """Author filter that matches no commits returns an empty list."""
    commits = get_commits_since(temp_git_repo, hours=24, author="NonexistentAuthor99999")
    assert commits == []


def test_get_commits_since_invalid_path_returns_empty():
    """A completely non-existent path returns an empty list without raising."""
    commits = get_commits_since("/nonexistent/path/that/does/not/exist", hours=24)
    assert commits == []


def test_get_commits_since_non_git_directory_returns_empty(tmp_path):
    """A real directory that is not a git repo returns an empty list."""
    non_repo = tmp_path / "plain_dir"
    non_repo.mkdir()
    commits = get_commits_since(str(non_repo), hours=24)
    assert commits == []


def test_get_repo_name_returns_directory_basename(temp_git_repo):
    """get_repo_name returns the top-level directory name of the repository."""
    name = get_repo_name(temp_git_repo)
    assert name == "test_repo"


def test_get_repo_name_falls_back_gracefully_for_invalid_path():
    """get_repo_name does not raise for an invalid path; returns a non-empty string."""
    name = get_repo_name("/no/such/path/my_project")
    assert isinstance(name, str)
    assert len(name) > 0


def test_get_default_author_returns_configured_name(temp_git_repo):
    """get_default_author reads the git user.name from the repo config."""
    author = get_default_author(temp_git_repo)
    assert author == "Test User"


def test_get_default_author_returns_empty_string_for_invalid_path():
    """get_default_author returns empty string when the path is not a git repo."""
    author = get_default_author("/nonexistent/path")
    assert author == ""
