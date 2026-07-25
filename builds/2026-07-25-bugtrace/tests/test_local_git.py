import subprocess

import pytest

from src.local_git import LocalGitError, get_local_commit_diff, get_local_fix_commits


@pytest.fixture
def temp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test User")

    (repo / "a.txt").write_text("hello\n")
    git("add", "a.txt")
    git("commit", "-q", "-m", "Add initial file")

    (repo / "a.txt").write_text("hello world\n")
    git("add", "a.txt")
    git("commit", "-q", "-m", "fix typo in greeting")

    (repo / "b.txt").write_text("unrelated\n")
    git("add", "b.txt")
    git("commit", "-q", "-m", "Add unrelated feature file")

    return repo


def test_get_local_fix_commits_returns_all_commits(temp_repo):
    commits = get_local_fix_commits(str(temp_repo))
    assert len(commits) == 3
    messages = [c["message"] for c in commits]
    assert "fix typo in greeting" in messages


def test_get_local_fix_commits_respects_limit(temp_repo):
    commits = get_local_fix_commits(str(temp_repo), limit=1)
    assert len(commits) == 1


def test_get_local_commit_diff_returns_patch_content(temp_repo):
    commits = get_local_fix_commits(str(temp_repo))
    fix_sha = next(c["sha"] for c in commits if "fix typo" in c["message"])
    diff = get_local_commit_diff(str(temp_repo), fix_sha)
    assert "hello world" in diff


def test_invalid_repo_path_raises():
    with pytest.raises(LocalGitError):
        get_local_fix_commits("/definitely/not/a/real/path")


def test_non_git_directory_raises(tmp_path):
    empty_dir = tmp_path / "not_a_repo"
    empty_dir.mkdir()
    with pytest.raises(LocalGitError):
        get_local_fix_commits(str(empty_dir))


def test_unsafe_sha_rejected(temp_repo):
    with pytest.raises(LocalGitError):
        get_local_commit_diff(str(temp_repo), "--upload-pack=/bin/sh")
