"""Tests for dedup.merge_commits — pure logic, no I/O."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dedup import merge_commits


def _github_commit(repo, sha, message):
    return {"hash": sha[:8], "sha": sha, "message": message, "source": "github", "repo": repo}


def _local_commit(repo, sha, message):
    return {"hash": sha[:8], "sha": sha, "message": message, "source": "local_unpushed", "repo": repo}


def test_github_only_returns_all():
    """When there are no local commits, all GitHub commits are returned."""
    g = {"repo-a": [_github_commit("repo-a", "aaa" * 14, "Pushed commit")]}
    result = merge_commits(g, {})
    assert len(result["repo-a"]) == 1
    assert result["repo-a"][0]["source"] == "github"


def test_local_only_returns_all():
    """When there are no GitHub commits, all local commits are returned."""
    loc = {"repo-a": [_local_commit("repo-a", "bbb" * 14, "Unpushed commit")]}
    result = merge_commits({}, loc)
    assert len(result["repo-a"]) == 1
    assert result["repo-a"][0]["source"] == "local_unpushed"


def test_duplicate_sha_keeps_github_version():
    """A commit present in both sources (same SHA) appears only once, as GitHub."""
    sha = "ccc" * 14
    g = {"repo-a": [_github_commit("repo-a", sha, "Commit")]}
    loc = {"repo-a": [_local_commit("repo-a", sha, "Commit")]}
    result = merge_commits(g, loc)
    sources = [c["source"] for c in result["repo-a"]]
    assert sources == ["github"]


def test_distinct_shas_both_appear():
    """Commits with different SHAs from both sources all appear in the output."""
    sha_g = "ddd" * 14
    sha_l = "eee" * 14
    g = {"repo-a": [_github_commit("repo-a", sha_g, "Pushed")]}
    loc = {"repo-a": [_local_commit("repo-a", sha_l, "Unpushed")]}
    result = merge_commits(g, loc)
    assert len(result["repo-a"]) == 2


def test_empty_inputs_return_empty():
    """Both empty inputs produce an empty output."""
    result = merge_commits({}, {})
    assert result == {}
