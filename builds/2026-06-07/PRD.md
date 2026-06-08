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

- **Language:** Python 3.9+
- **Framework:** None (argparse + subprocess from stdlib)
- **Dependencies:** stdlib only (argparse, subprocess, pathlib, datetime); pytest for tests
- **Runtime requirement:** `python3 main.py [paths...] [options]` — no install required beyond git and Python 3

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
├── main.py                       ← CLI entry point
├── requirements.txt              ← pytest only
├── src/
│   ├── __init__.py
│   ├── git_log.py                ← subprocess git calls → list of commit dicts
│   └── standup.py                ← pure formatting logic
└── tests/
    ├── test_standup.py           ← formatter tests using mock data (8 tests)
    └── test_git_log.py           ← git reader tests using real temp repo (9 tests)
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

<!-- No scope changes during this build. -->
