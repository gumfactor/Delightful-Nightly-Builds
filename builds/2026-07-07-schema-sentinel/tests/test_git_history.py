import subprocess
from pathlib import Path

import pytest

import git_history


def _git(repo_dir, *args):
    result = subprocess.run(
        ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", *args],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.fixture
def repo_with_history(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    _git(repo_dir, "init", "-q")

    data_file = repo_dir / "data.json"

    data_file.write_text('{"id": 1, "name": "Alice"}')
    _git(repo_dir, "add", "data.json")
    _git(repo_dir, "commit", "-q", "-m", "v1")

    data_file.write_text('{"id": 1, "name": "Alice", "email": "alice@example.com"}')
    _git(repo_dir, "add", "data.json")
    _git(repo_dir, "commit", "-q", "-m", "v2 - add email")

    data_file.write_text('{"id": "1", "name": "Alice", "email": "alice@example.com"}')
    _git(repo_dir, "add", "data.json")
    _git(repo_dir, "commit", "-q", "-m", "v3 - id becomes string")

    return repo_dir


def test_is_git_repo_true_for_real_repo(repo_with_history):
    assert git_history.is_git_repo(str(repo_with_history)) is True


def test_is_git_repo_false_for_non_repo(tmp_path):
    plain_dir = tmp_path / "not_a_repo"
    plain_dir.mkdir()
    assert git_history.is_git_repo(str(plain_dir)) is False


def test_is_git_repo_false_for_missing_path(tmp_path):
    assert git_history.is_git_repo(str(tmp_path / "does_not_exist")) is False


def test_list_revisions_returns_oldest_first(repo_with_history):
    revisions = git_history.list_revisions(str(repo_with_history), "data.json")
    assert len(revisions) == 3
    dates = [r["date"] for r in revisions]
    assert dates == sorted(dates)


def test_list_revisions_limit_keeps_most_recent_chronological(repo_with_history):
    revisions = git_history.list_revisions(str(repo_with_history), "data.json", limit=2)
    assert len(revisions) == 2
    # the two most recent commits, still oldest-first
    dates = [r["date"] for r in revisions]
    assert dates == sorted(dates)


def test_list_revisions_raises_for_untracked_path(repo_with_history):
    with pytest.raises(git_history.GitHistoryError, match="No git history found"):
        git_history.list_revisions(str(repo_with_history), "never_existed.json")


def test_read_file_at_revision_returns_correct_content(repo_with_history):
    revisions = git_history.list_revisions(str(repo_with_history), "data.json")
    first_content = git_history.read_file_at_revision(str(repo_with_history), revisions[0]["sha"], "data.json")
    assert "email" not in first_content
    last_content = git_history.read_file_at_revision(str(repo_with_history), revisions[-1]["sha"], "data.json")
    assert '"id": "1"' in last_content


def test_read_file_at_revision_raises_for_bad_sha(repo_with_history):
    with pytest.raises(git_history.GitHistoryError, match="git show failed"):
        git_history.read_file_at_revision(str(repo_with_history), "deadbeef", "data.json")
