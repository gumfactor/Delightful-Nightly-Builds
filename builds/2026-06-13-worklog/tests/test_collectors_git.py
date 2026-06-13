"""Tests for the Git activity collector."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from src.collectors.git import (
    parse_commit_log,
    get_current_branch,
    get_head_sha,
    get_dirty_files,
    collect_commits,
    collect_dirty_state,
)


class TestParseCommitLog:
    def test_parses_single_commit(self):
        raw = "abc1234def|Alice Smith|alice@example.com|1749801600|Add feature X"
        commits = parse_commit_log(raw)
        assert len(commits) == 1
        assert commits[0]["sha"] == "abc1234def"
        assert commits[0]["author_name"] == "Alice Smith"
        assert commits[0]["subject"] == "Add feature X"

    def test_parses_multiple_commits(self):
        raw = (
            "sha1|Author1|a@b.com|1749801600|First commit\n"
            "sha2|Author2|c@d.com|1749715200|Second commit"
        )
        commits = parse_commit_log(raw)
        assert len(commits) == 2
        assert commits[0]["sha"] == "sha1"
        assert commits[1]["sha"] == "sha2"

    def test_skips_malformed_lines(self):
        raw = "not|enough\nabc|Author|email|1749801600|Good commit"
        commits = parse_commit_log(raw)
        assert len(commits) == 1
        assert commits[0]["sha"] == "abc"

    def test_handles_empty_input(self):
        commits = parse_commit_log("")
        assert commits == []

    def test_timestamp_converts_to_iso_utc(self):
        raw = "abc|Author|e@x.com|0|Initial"
        commits = parse_commit_log(raw)
        assert commits[0]["timestamp"].endswith("Z")
        assert "T" in commits[0]["timestamp"]


class TestGitRepo:
    """Integration tests against an isolated temporary git repo."""

    @pytest.fixture
    def git_repo(self, tmp_path):
        """Create a minimal git repo with one commit (signing disabled for isolation)."""
        subprocess.run(["git", "init", "--initial-branch=main"], cwd=tmp_path,
                       capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path,
                       capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path,
                       capture_output=True)
        # Disable commit signing in this isolated test repo
        subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path,
                       capture_output=True)
        subprocess.run(["git", "config", "gpg.format", "openpgp"], cwd=tmp_path,
                       capture_output=True)
        (tmp_path / "README.md").write_text("hello")
        subprocess.run(["git", "add", "README.md"], cwd=tmp_path, capture_output=True)
        result = subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-m", "Initial commit"],
            cwd=tmp_path,
            capture_output=True,
        )
        return tmp_path

    def test_get_current_branch(self, git_repo):
        branch = get_current_branch(git_repo)
        assert branch in ("main", "master", "HEAD")

    def test_get_head_sha(self, git_repo):
        sha = get_head_sha(git_repo)
        assert sha is not None
        assert len(sha) == 40

    def test_get_dirty_files_clean_repo(self, git_repo):
        files = get_dirty_files(git_repo)
        assert isinstance(files, list)
        assert len(files) == 0

    def test_get_dirty_files_with_modification(self, git_repo):
        (git_repo / "README.md").write_text("modified")
        files = get_dirty_files(git_repo)
        assert "README.md" in files

    def test_collect_commits_returns_events(self, git_repo):
        events = collect_commits(git_repo, "test-proj", since_days=7)
        assert len(events) >= 1
        evt = events[0]
        assert evt["type"] == "commit"
        assert evt["provider"] == "git"
        assert evt["project_id"] == "test-proj"
        assert "sha" in evt.get("metadata", {})

    def test_collect_dirty_state_empty_when_clean(self, git_repo):
        evts = collect_dirty_state(git_repo, "test-proj")
        assert evts == []

    def test_collect_dirty_state_detects_changes(self, git_repo):
        (git_repo / "new_file.txt").write_text("untracked")
        evts = collect_dirty_state(git_repo, "test-proj")
        assert len(evts) == 1
        assert evts[0]["type"] == "dirty_file"
        assert "new_file.txt" in evts[0]["metadata"]["files"]
