# PRD — GitHub Repository Health Dashboard

> **Build date:** 2026-06-11
> **Category:** A — Dashboard / Visualizer
> **Complexity:** Focused Utility
> **Day of week:** Thursday → Focused Utility

---

## Goal

Single-command Python CLI that fetches all of the authenticated user's GitHub repositories and renders a clean terminal health dashboard showing staleness, open issues, and activity status across every repo at once.

## User Story

As a researcher and indie founder who maintains a dozen or more GitHub repositories across multiple active projects (neuroscience lab tools, The Canada List platform, Kwyeter, nightly build scripts, etc.), I want to run one command and immediately see which repos are active, which have open issues needing attention, and which have gone quiet — so that I can triage project health without clicking through each repo on GitHub.com.

## Scope

### In Scope
- Fetch authenticated user's repos via GitHub API using `GITHUB_TOKEN` env var
- Display a terminal table with columns: Repository name, Language, Stars, Open Issues, Days since last push, Health status
- Health status labels: `active` (<30 days since push), `quiet` (30–90 days), `stale` (>90 days), `archived`
- Sort repos by last push date, most recent first
- Skip archived repos by default; `--include-archived` flag to include them
- `--limit N` flag to cap output (default 30)
- `--format json` flag to output structured JSON for scripting
- `--org ORG` flag to list repos for a specific GitHub org the user belongs to
- Graceful error if `GITHUB_TOKEN` is unset or API returns a non-200
- Pagination: fetch up to 100 repos per page, respecting `--limit`

### Out of Scope
- CI / GitHub Actions status per repo (requires additional per-repo API call; future feature)
- PR counts distinct from issue counts (GitHub API's `open_issues_count` conflates both; documented in Manual.md)
- Repo content search or file browsing
- Writing to GitHub (no mutations)
- Browser / web UI
- Scheduled / cron mode (standalone CLI is appropriate deployment for an on-demand query)

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** None (stdlib only)
- **Dependencies:** `pytest` (test only); runtime uses `urllib`, `json`, `os`, `argparse`, `datetime` from stdlib
- **Runtime requirement:** `python3 main.py` (GITHUB_TOKEN env var must be set)

## Data Structure

The tool consumes GitHub REST API v3 responses (JSON). Each repo object contains:
```json
{
  "name": "repo-name",
  "full_name": "owner/repo-name",
  "language": "Python",
  "stargazers_count": 3,
  "open_issues_count": 2,
  "pushed_at": "2026-06-09T14:22:00Z",
  "archived": false,
  "private": false,
  "html_url": "https://github.com/owner/repo-name"
}
```

The tool is stateless — no local file is written. All data comes from the API at runtime.

## Folder Structure

```
builds/2026-06-11-github-repo-health-dashboard/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── main.py                   ← CLI entry point (argparse)
├── requirements.txt          ← pytest only
├── src/
│   ├── __init__.py
│   ├── github_client.py      ← GitHub API calls (urllib)
│   ├── health.py             ← Pure logic: parse, score, filter, enrich
│   └── formatter.py          ← Terminal table and JSON rendering
└── tests/
    └── test_core.py          ← pytest unit tests for health.py + formatter.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_core.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - `parse_repo` extracts name, language (null-safe), stars, issues, pushed_at, archived flag
  - `days_since_push` calculates correct integer days from ISO timestamp; handles empty string
  - `health_status` returns correct label for active (<30d), quiet (30–90d), stale (>90d), archived
  - `filter_repos` excludes archived repos by default; includes them when flag is set
  - `enrich_repos` produces dicts with `days_since_push` and `health` fields
  - `format_table` returns a non-empty string containing expected headers
  - `format_table` with empty list returns the no-repos message string
  - `format_json` returns valid JSON parseable by `json.loads`

## Success Criteria

1. All tests pass (zero failures)
2. `python3 main.py` prints a formatted table when `GITHUB_TOKEN` is set; repos are sorted most-recently-pushed first
3. `--format json` outputs a JSON array where each element has `name`, `health`, `days_since_push`, and `open_issues`
4. Running with `GITHUB_TOKEN` unset prints a clear error message to stderr (exit code 1) with no traceback
5. Archived repos do not appear in default output; `--include-archived` flag makes them visible

---

## Scope Changes

<!-- Leave this section blank. If scope changes during the build,
     add a "Scope Changes" entry here explaining what was dropped and why. -->
