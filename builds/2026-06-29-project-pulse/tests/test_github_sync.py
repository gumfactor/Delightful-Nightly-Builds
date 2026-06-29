import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from github_sync import fetch_repo_commits, parse_commit, sync_project

RAW_COMMIT = {
    "sha": "abcdef1234567890",
    "commit": {
        "message": "Fix null pointer\n\nMore details here",
        "author": {
            "name": "Jane Smith",
            "date": "2026-06-28T10:00:00Z",
        },
    },
}


def test_parse_commit_extracts_sha():
    result = parse_commit(RAW_COMMIT)
    assert result["sha"] == "abcdef12"


def test_parse_commit_uses_first_line_only():
    result = parse_commit(RAW_COMMIT)
    assert result["message"] == "Fix null pointer"
    assert "\n" not in result["message"]


def test_parse_commit_extracts_author():
    result = parse_commit(RAW_COMMIT)
    assert result["author"] == "Jane Smith"


def test_parse_commit_extracts_date():
    result = parse_commit(RAW_COMMIT)
    assert result["committed_at"] == "2026-06-28T10:00:00Z"


def test_parse_commit_truncates_long_message():
    raw = {
        "sha": "abc123",
        "commit": {
            "message": "A" * 300,
            "author": {"name": "Dev", "date": "2026-06-01T00:00:00Z"},
        },
    }
    result = parse_commit(raw)
    assert len(result["message"]) <= 200


def test_parse_commit_handles_empty_dict():
    result = parse_commit({})
    assert result["sha"] == ""
    assert result["message"] == ""
    assert result["author"] == ""
    assert result["committed_at"] == ""


def test_fetch_repo_commits_returns_parsed_commits():
    with patch("github_sync._make_request", return_value=[RAW_COMMIT]):
        commits = fetch_repo_commits("owner/repo", "fake-token", since_days=30)
    assert len(commits) == 1
    assert commits[0]["sha"] == "abcdef12"


def test_fetch_repo_commits_handles_none_response():
    with patch("github_sync._make_request", return_value=None):
        commits = fetch_repo_commits("owner/repo", "fake-token")
    assert commits == []


def test_fetch_repo_commits_handles_empty_list():
    with patch("github_sync._make_request", return_value=[]):
        commits = fetch_repo_commits("owner/repo", "fake-token")
    assert commits == []


def test_sync_project_stores_commits(tmp_path):
    import database as dbmod

    db_path = str(tmp_path / "test.db")
    dbmod.init_db(db_path)
    proj_id = dbmod.add_project(db_path, "My Code", "desc", "code", ["owner/myrepo"])
    project = dbmod.get_project(db_path, "my-code")

    mock_commits = [
        {"sha": "aaa", "message": "Initial commit", "author": "Dev", "committed_at": "2026-06-28T10:00:00Z"},
        {"sha": "bbb", "message": "Add feature", "author": "Dev", "committed_at": "2026-06-27T10:00:00Z"},
    ]
    with patch("github_sync.fetch_repo_commits", return_value=mock_commits):
        count = sync_project(db_path, project, "fake-token")

    assert count == 2
    acts = dbmod.get_recent_activity(db_path, proj_id, days=30)
    assert len(acts) == 2


def test_sync_project_skips_project_without_repos(tmp_path):
    import database as dbmod

    db_path = str(tmp_path / "test.db")
    dbmod.init_db(db_path)
    dbmod.add_project(db_path, "Writing Project", "desc", "writing", [])
    project = dbmod.get_project(db_path, "writing-project")

    count = sync_project(db_path, project, "fake-token")
    assert count == 0


def test_sync_project_deduplicates_on_second_run(tmp_path):
    import database as dbmod

    db_path = str(tmp_path / "test.db")
    dbmod.init_db(db_path)
    dbmod.add_project(db_path, "My Code", "desc", "code", ["owner/repo"])
    project = dbmod.get_project(db_path, "my-code")

    same_commits = [
        {"sha": "abc", "message": "Same commit", "author": "Dev", "committed_at": "2026-06-28T10:00:00Z"}
    ]
    with patch("github_sync.fetch_repo_commits", return_value=same_commits):
        count1 = sync_project(db_path, project, "fake-token")
        count2 = sync_project(db_path, project, "fake-token")

    assert count1 == 1
    assert count2 == 0


def test_sync_project_handles_api_exception(tmp_path):
    import database as dbmod

    db_path = str(tmp_path / "test.db")
    dbmod.init_db(db_path)
    dbmod.add_project(db_path, "My Code", "desc", "code", ["owner/repo"])
    project = dbmod.get_project(db_path, "my-code")

    with patch("github_sync.fetch_repo_commits", side_effect=Exception("network error")):
        count = sync_project(db_path, project, "fake-token")

    assert count == 0
