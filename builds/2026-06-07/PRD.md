# PRD — Git Standup Reporter

> **Build date:** 2026-06-07
> **Category:** H — Developer Tool
> **Complexity:** Focused Utility
> **Day of week:** Sunday → Focused Utility

---

## Goal

A Python CLI that reads git commit history across one or more repositories and formats a standup-ready summary of what was committed in the last N hours.

## User Story

As a researcher and solo founder who manages multiple simultaneous git projects, I want to run a single command from any project directory and get a clean summary of what I committed in the last 24 hours, so that I can write standups, re-establish session context, and track my own progress across projects without manually reviewing git logs.

## Scope

### In Scope

- Accept one or more git repository paths as positional arguments (default: current directory)
- `--hours N` flag to control the lookback window (default: 24)
- `--author NAME` flag to filter commits by author substring (default: auto-detected from `git config user.name`)
- `--all-authors` flag to skip author filtering and show everyone's commits
- `--format text|markdown` flag to choose output format (default: `text`)
- Group output by repository name
- Sort repos alphabetically in output
- Graceful handling of invalid paths, non-git directories, and missing git binary
- Both plain text and markdown output modes
- Full test suite covering formatter logic and real git interaction

### Out of Scope

- Interactive TUI or browser interface
- Persistent storage or logging of standup history
- Push/pull/remote status information
- File diff or change statistics (line counts, insertions/deletions)
- Integration with Slack, email, or any external service
- Configuration files or persistent preferences

## Tech Stack

- **Language:** Python 3.11+ (required for `tomllib`)
- **Framework:** None (stdlib only)
- **Dependencies:** stdlib only (tomllib, urllib.request, subprocess, pathlib, json, datetime); pytest for tests
- **Runtime requirement:** `python main.py` from the build folder — requires `standup.toml` and `GITHUB_TOKEN` environment variable

## Data Structure

Stateless. Reads directly from git log via subprocess. No files are written.

Commit dict schema (internal, not persisted):
```python
{
    "hash":      str,  # 8-character abbreviated commit hash
    "message":   str,  # commit subject line (first line only)
    "author":    str,  # author name from git log
    "timestamp": str,  # ISO 8601 date from git log %ai format
    "repo":      str,  # repository directory name (top-level basename)
}
```

## Folder Structure

```
builds/2026-06-07/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── SETUP_WINDOWS.md              ← Windows Task Scheduler setup guide
├── main.py                       ← entry point; reads config, calls all modules
├── standup.toml                  ← local config (not committed; see standup.toml.example)
├── standup.toml.example          ← template config file
├── requirements.txt              ← pytest only
├── src/
│   ├── __init__.py
│   ├── config.py                 ← TOML config loader
│   ├── github_api.py             ← GitHub API client (list repos, get commits)
│   ├── local_git.py              ← local repo scanner + unpushed commit reader
│   ├── dedup.py                  ← SHA-based merge and deduplication
│   ├── journal.py                ← JSONL journal writer
│   ├── standup.py                ← pure formatting logic
│   └── git_log.py                ← original local git reader (kept for historical record)
└── tests/
    ├── test_standup.py           ← formatter tests (11 tests)
    ├── test_config.py            ← config loading tests (5 tests)
    ├── test_github_api.py        ← GitHub API tests with mocked responses (5 tests)
    ├── test_local_git.py         ← local git scanner tests (5 tests)
    ├── test_dedup.py             ← deduplication logic tests (5 tests)
    ├── test_journal.py           ← JSONL journal tests (5 tests)
    └── test_git_log.py           ← original git reader tests (10 tests, historical)
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_standup.py`, `tests/test_git_log.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - `format_standup()` with normal commit data → output contains messages and repo names
  - `format_standup()` with empty dict → "Nothing committed" message
  - `format_standup()` with `hours=1` → singular "hour" not "hours"
  - `format_standup()` with two repos → both appear grouped in output
  - `format_standup()` markdown mode → `##` and `###` headers present
  - `format_standup()` text mode → `[repo-name]` bracket syntax present
  - `format_standup()` repo ordering → sorted alphabetically
  - `get_commits_since()` happy path → finds commit in real temp repo
  - `get_commits_since()` author filter → correct filtering by author substring
  - `get_commits_since()` invalid path → returns `[]`
  - `get_commits_since()` non-git directory → returns `[]`
  - `get_repo_name()` → returns top-level directory basename
  - `get_repo_name()` invalid path → falls back gracefully (no exception)
  - `get_default_author()` → returns configured name from temp repo
  - `get_default_author()` invalid path → returns empty string
  - Commit dict structure → all expected keys present, hash is 8 chars

## Success Criteria

1. All tests pass (zero failures, minimum 17 tests across two test files)
2. `python3 main.py .` run from any git repository prints a standup report without error
3. `python3 main.py . --format markdown` produces output with `##` and `###` headers
4. `python3 main.py /nonexistent/path` exits gracefully with an informative "Nothing committed" message, no crash or traceback
5. Running with `--hours 0` or a path with no recent commits shows the "Nothing committed" message instead of an empty or broken output

---

## Scope Changes

**Extended 2026-06-08 in a human-assisted session.**

The original build was a local-only git log CLI driven by command-line arguments. After review, the following scope changes were made to make the tool practically useful:

**Added:**
- GitHub API data source — fetches pushed commits from all repos under the configured username, auto-discovering new repos without requiring a manual list
- Local unpushed commit scanner — scans `local_roots` directories for git repos and returns commits not yet pushed to remote
- SHA-based deduplication — merges both sources without double-counting commits that appear in both
- JSONL journal — appends each run to a structured history file for future querying
- `standup.toml` config file — replaces command-line arguments as the primary configuration mechanism; `GITHUB_TOKEN` read from environment variable
- Windows Task Scheduler setup guide (`SETUP_WINDOWS.md`)
- `source` field added to commit dicts (`"github"` or `"local_unpushed"`) — displayed as `(local)` tag in output

**Removed:**
- Command-line argument interface (`paths`, `--author`, `--all-authors`, `--format`, `--hours` flags) — all settings now live in `standup.toml`

**Rationale:** The original build required manual invocation and only saw local commits. The extension makes it self-running (Task Scheduler) and comprehensive (GitHub API + local scan), which is the minimum required for the tool to be genuinely useful rather than just theoretically useful.
