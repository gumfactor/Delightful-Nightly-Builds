"""Tests for standup.format_standup() — pure formatting logic with no git calls."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.standup import format_standup


SAMPLE_COMMITS_MYAPP = [
    {
        "hash": "abc12345",
        "message": "Add login page",
        "author": "Alice",
        "timestamp": "2026-06-07 10:00:00 +0000",
        "repo": "myapp",
        "source": "github",
    },
    {
        "hash": "def67890",
        "message": "Fix typo in README",
        "author": "Alice",
        "timestamp": "2026-06-07 09:00:00 +0000",
        "repo": "myapp",
        "source": "github",
    },
]


def test_format_standup_text_contains_commit_messages():
    """Normal commits appear verbatim in text output."""
    result = format_standup({"myapp": SAMPLE_COMMITS_MYAPP}, hours=24)
    assert "Add login page" in result
    assert "Fix typo in README" in result


def test_format_standup_empty_dict_returns_nothing_message():
    """Empty commits_by_repo produces a human-readable 'nothing committed' line."""
    result = format_standup({}, hours=24)
    assert "Nothing committed" in result
    assert "24" in result


def test_format_standup_empty_lists_returns_nothing_message():
    """Repos with empty commit lists count as no commits."""
    result = format_standup({"myapp": [], "other": []}, hours=24)
    assert "Nothing committed" in result


def test_format_standup_singular_hour_label():
    """hours=1 produces 'hour' not 'hours' in the nothing-committed message."""
    result = format_standup({}, hours=1)
    assert "1 hour" in result
    assert "1 hours" not in result


def test_format_standup_groups_output_by_repo():
    """Commits from two repos appear in separate sections."""
    commits_by_repo = {
        "repo-alpha": [
            {
                "hash": "aaa11111",
                "message": "Alpha feature",
                "author": "Bob",
                "timestamp": "2026-06-07",
                "repo": "repo-alpha",
            }
        ],
        "repo-beta": [
            {
                "hash": "bbb22222",
                "message": "Beta fix",
                "author": "Bob",
                "timestamp": "2026-06-07",
                "repo": "repo-beta",
            }
        ],
    }
    result = format_standup(commits_by_repo, hours=24)
    assert "repo-alpha" in result
    assert "repo-beta" in result
    assert "Alpha feature" in result
    assert "Beta fix" in result


def test_format_standup_markdown_has_section_headers():
    """Markdown format produces ## and ### headers."""
    result = format_standup({"myapp": SAMPLE_COMMITS_MYAPP}, hours=24, format_type="markdown")
    assert "## Standup" in result
    assert "### myapp" in result


def test_format_standup_text_uses_bracket_repo_label():
    """Text format labels repos with [repo-name] brackets."""
    result = format_standup({"myapp": SAMPLE_COMMITS_MYAPP}, hours=24, format_type="text")
    assert "[myapp]" in result


def test_local_unpushed_commit_tagged_in_text_output():
    """Commits with source='local_unpushed' show (local) tag in text output."""
    commits = [{"hash": "aaa11111", "message": "WIP change", "author": "A",
                "timestamp": "2026-06-07", "repo": "myapp", "source": "local_unpushed"}]
    result = format_standup({"myapp": commits}, hours=24, format_type="text")
    assert "(local)" in result


def test_local_unpushed_commit_tagged_in_markdown_output():
    """Commits with source='local_unpushed' show *(local)* tag in markdown output."""
    commits = [{"hash": "aaa11111", "message": "WIP change", "author": "A",
                "timestamp": "2026-06-07", "repo": "myapp", "source": "local_unpushed"}]
    result = format_standup({"myapp": commits}, hours=24, format_type="markdown")
    assert "*(local)*" in result


def test_github_commit_has_no_local_tag():
    """Commits with source='github' do not get the (local) tag."""
    commits = [{"hash": "bbb22222", "message": "Pushed fix", "author": "A",
                "timestamp": "2026-06-07", "repo": "myapp", "source": "github"}]
    result = format_standup({"myapp": commits}, hours=24, format_type="text")
    assert "(local)" not in result


def test_format_standup_repos_sorted_alphabetically():
    """Repositories appear in alphabetical order regardless of dict insertion order."""
    commits_by_repo = {
        "zzz-last": [
            {
                "hash": "zzz00000",
                "message": "Z work",
                "author": "C",
                "timestamp": "2026-06-07",
                "repo": "zzz-last",
            }
        ],
        "aaa-first": [
            {
                "hash": "aaa00000",
                "message": "A work",
                "author": "C",
                "timestamp": "2026-06-07",
                "repo": "aaa-first",
            }
        ],
    }
    result = format_standup(commits_by_repo, hours=24)
    aaa_pos = result.index("[aaa-first]")
    zzz_pos = result.index("[zzz-last]")
    assert aaa_pos < zzz_pos
