"""Tests for git_reader — parses real git log output from real temp repos."""

from __future__ import annotations

from pathlib import Path

import pytest

from src import git_reader


def test_read_commits_returns_all_commits(tmp_git_repo: Path):
    commits = git_reader.read_commits(tmp_git_repo)
    assert len(commits) == 3


def test_read_commits_captures_subject_and_body(tmp_git_repo: Path):
    commits = git_reader.read_commits(tmp_git_repo)
    breaking_commit = next(c for c in commits if c["subject"].startswith("refactor!"))
    assert "plugin-based renderer" in breaking_commit["subject"]
    assert "breaking change" in breaking_commit["body"]


def test_read_commits_captures_diff_stats(tmp_git_repo: Path):
    commits = git_reader.read_commits(tmp_git_repo)
    initial_commit = next(c for c in commits if c["subject"] == "chore: initial commit")
    assert initial_commit["files_changed"] == 1
    assert initial_commit["insertions"] >= 1


def test_read_commits_on_empty_repo_returns_empty_list(empty_git_repo: Path):
    commits = git_reader.read_commits(empty_git_repo)
    assert commits == []


def test_read_commits_excludes_known_hashes(tmp_git_repo: Path):
    all_commits = git_reader.read_commits(tmp_git_repo)
    known = {all_commits[0]["commit_hash"]}
    remaining = git_reader.read_commits(tmp_git_repo, exclude_hashes=known)
    assert len(remaining) == len(all_commits) - 1
    assert all(c["commit_hash"] != all_commits[0]["commit_hash"] for c in remaining)


def test_validate_repo_raises_on_non_git_directory(tmp_path: Path):
    not_a_repo = tmp_path / "not_a_repo"
    not_a_repo.mkdir()
    with pytest.raises(git_reader.NotAGitRepoError):
        git_reader.validate_repo(not_a_repo)


def test_validate_repo_raises_on_missing_directory(tmp_path: Path):
    missing = tmp_path / "does_not_exist"
    with pytest.raises(git_reader.NotAGitRepoError):
        git_reader.validate_repo(missing)


def test_read_commits_on_non_git_path_raises(tmp_path: Path):
    not_a_repo = tmp_path / "plain_dir"
    not_a_repo.mkdir()
    with pytest.raises(git_reader.NotAGitRepoError):
        git_reader.read_commits(not_a_repo)


def test_commit_hashes_are_unique_and_full_length(tmp_git_repo: Path):
    commits = git_reader.read_commits(tmp_git_repo)
    hashes = [c["commit_hash"] for c in commits]
    assert len(hashes) == len(set(hashes))
    assert all(len(h) == 40 for h in hashes)
