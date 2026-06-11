"""
Unit tests for health.py and formatter.py.
All tests use a fixed NOW datetime so results are deterministic.
No network calls are made — github_client.py is not imported here.
"""
import json
import sys
import os
import pytest
from datetime import datetime, timezone

# Allow imports from the build root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.health import (
    parse_repo,
    days_since_push,
    health_status,
    filter_repos,
    enrich_repos,
)
from src.formatter import format_table, format_json


# ── Shared fixture date ────────────────────────────────────────────────────────

NOW = datetime(2026, 6, 11, 8, 0, 0, tzinfo=timezone.utc)


def make_raw(
    name: str = "testrepo",
    full_name: str = "owner/testrepo",
    language: str = "Python",
    stars: int = 5,
    issues: int = 2,
    pushed_at: str = "2026-06-09T10:00:00Z",
    archived: bool = False,
    private: bool = False,
    html_url: str = "https://github.com/owner/testrepo",
) -> dict:
    """Build a minimal raw GitHub API repo dict."""
    return {
        "name": name,
        "full_name": full_name,
        "language": language,
        "stargazers_count": stars,
        "open_issues_count": issues,
        "pushed_at": pushed_at,
        "archived": archived,
        "private": private,
        "html_url": html_url,
    }


def make_enriched(**kwargs) -> dict:
    """Create an enriched repo dict via the full parse + enrich pipeline."""
    return enrich_repos([make_raw(**kwargs)], now=NOW)[0]


# ── parse_repo ─────────────────────────────────────────────────────────────────

class TestParseRepo:
    def test_extracts_name_and_full_name(self):
        repo = parse_repo(make_raw(name="myrepo", full_name="user/myrepo"))
        assert repo["name"] == "myrepo"
        assert repo["full_name"] == "user/myrepo"

    def test_extracts_stars_and_open_issues(self):
        repo = parse_repo(make_raw(stars=42, issues=7))
        assert repo["stars"] == 42
        assert repo["open_issues"] == 7

    def test_none_language_becomes_dash(self):
        repo = parse_repo(make_raw(language=None))
        assert repo["language"] == "—"

    def test_language_string_preserved(self):
        repo = parse_repo(make_raw(language="TypeScript"))
        assert repo["language"] == "TypeScript"

    def test_archived_flag_extracted_correctly(self):
        repo = parse_repo(make_raw(archived=True))
        assert repo["archived"] is True

    def test_empty_dict_uses_safe_defaults(self):
        repo = parse_repo({})
        assert repo["name"] == "unknown"
        assert repo["stars"] == 0
        assert repo["open_issues"] == 0
        assert repo["archived"] is False
        assert repo["language"] == "—"


# ── days_since_push ────────────────────────────────────────────────────────────

class TestDaysSincePush:
    def test_two_days_ago(self):
        assert days_since_push("2026-06-09T08:00:00Z", now=NOW) == 2

    def test_pushed_same_day_returns_zero(self):
        assert days_since_push("2026-06-11T07:00:00Z", now=NOW) == 0

    def test_exactly_ninety_days_ago(self):
        assert days_since_push("2026-03-13T08:00:00Z", now=NOW) == 90

    def test_empty_string_returns_sentinel_9999(self):
        assert days_since_push("", now=NOW) == 9999

    def test_old_push_returns_large_number(self):
        days = days_since_push("2024-01-01T00:00:00Z", now=NOW)
        assert days > 365


# ── health_status ──────────────────────────────────────────────────────────────

class TestHealthStatus:
    def test_active_when_pushed_yesterday(self):
        repo = parse_repo(make_raw(pushed_at="2026-06-10T08:00:00Z"))
        assert health_status(repo, now=NOW) == "active"

    def test_quiet_when_pushed_50_days_ago(self):
        repo = parse_repo(make_raw(pushed_at="2026-04-22T08:00:00Z"))
        assert health_status(repo, now=NOW) == "quiet"

    def test_stale_when_pushed_150_days_ago(self):
        repo = parse_repo(make_raw(pushed_at="2026-01-12T08:00:00Z"))
        assert health_status(repo, now=NOW) == "stale"

    def test_archived_overrides_recent_push(self):
        repo = parse_repo(make_raw(pushed_at="2026-06-10T08:00:00Z", archived=True))
        assert health_status(repo, now=NOW) == "archived"

    def test_boundary_30_days_is_quiet_not_active(self):
        # exactly 30 days ago should be "quiet" (condition is days < 30 for active)
        repo = parse_repo(make_raw(pushed_at="2026-05-12T08:00:00Z"))
        assert health_status(repo, now=NOW) == "quiet"

    def test_boundary_90_days_is_quiet_not_stale(self):
        # exactly 90 days ago should still be "quiet" (condition is days <= 90)
        repo = parse_repo(make_raw(pushed_at="2026-03-13T08:00:00Z"))
        assert health_status(repo, now=NOW) == "quiet"


# ── filter_repos ───────────────────────────────────────────────────────────────

class TestFilterRepos:
    def test_archived_excluded_by_default(self):
        repos = [
            parse_repo(make_raw(name="live")),
            parse_repo(make_raw(name="dead", archived=True)),
        ]
        result = filter_repos(repos)
        assert len(result) == 1
        assert result[0]["name"] == "live"

    def test_archived_included_when_flag_set(self):
        repos = [
            parse_repo(make_raw(name="live")),
            parse_repo(make_raw(name="dead", archived=True)),
        ]
        result = filter_repos(repos, include_archived=True)
        assert len(result) == 2

    def test_empty_input_returns_empty(self):
        assert filter_repos([]) == []

    def test_no_archived_repos_returns_all(self):
        repos = [parse_repo(make_raw(name="a")), parse_repo(make_raw(name="b"))]
        assert len(filter_repos(repos)) == 2


# ── enrich_repos ───────────────────────────────────────────────────────────────

class TestEnrichRepos:
    def test_adds_days_since_push(self):
        enriched = enrich_repos([make_raw(pushed_at="2026-06-10T08:00:00Z")], now=NOW)
        assert enriched[0]["days_since_push"] == 1

    def test_adds_health_field(self):
        enriched = enrich_repos([make_raw(pushed_at="2026-06-10T08:00:00Z")], now=NOW)
        assert enriched[0]["health"] == "active"

    def test_empty_input_returns_empty(self):
        assert enrich_repos([], now=NOW) == []

    def test_two_repos_enriched_independently(self):
        raw = [
            make_raw(name="fresh", pushed_at="2026-06-10T08:00:00Z"),
            make_raw(name="old", pushed_at="2026-01-01T08:00:00Z"),
        ]
        enriched = enrich_repos(raw, now=NOW)
        assert enriched[0]["health"] == "active"
        assert enriched[1]["health"] == "stale"


# ── format_table ───────────────────────────────────────────────────────────────

class TestFormatTable:
    def test_empty_list_returns_no_repos_message(self):
        assert "No repositories found" in format_table([])

    def test_output_contains_header_column_names(self):
        output = format_table([make_enriched()])
        assert "Repository" in output
        assert "Language" in output

    def test_output_contains_repo_full_name(self):
        output = format_table([make_enriched(full_name="user/my-cool-project")])
        assert "user/my-cool-project" in output

    def test_output_contains_health_status(self):
        output = format_table([make_enriched(pushed_at="2026-06-10T08:00:00Z")])
        assert "active" in output

    def test_output_is_multiline_string(self):
        output = format_table([make_enriched()])
        assert "\n" in output

    def test_stale_repo_shows_stale_label(self):
        output = format_table([make_enriched(pushed_at="2026-01-01T08:00:00Z")])
        assert "stale" in output


# ── format_json ────────────────────────────────────────────────────────────────

class TestFormatJson:
    def test_output_is_valid_json(self):
        parsed = json.loads(format_json([make_enriched()]))
        assert isinstance(parsed, list)

    def test_json_entry_has_required_fields(self):
        entry = json.loads(format_json([make_enriched(full_name="user/repo")]))[0]
        for field in ("name", "full_name", "health", "days_since_push", "open_issues"):
            assert field in entry, f"Missing field: {field}"

    def test_empty_list_produces_empty_json_array(self):
        assert json.loads(format_json([])) == []

    def test_json_health_value_is_valid_label(self):
        entry = json.loads(format_json([make_enriched(pushed_at="2026-06-10T08:00:00Z")]))[0]
        assert entry["health"] in ("active", "quiet", "stale", "archived")
