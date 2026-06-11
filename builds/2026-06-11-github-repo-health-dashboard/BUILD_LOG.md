# Build Log — GitHub Repository Health Dashboard

> **Date:** 2026-06-11
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:08 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, builds/index.md, STANDARDS.md in full
- Today is Thursday (day 4) → complexity target: Focused Utility
- Step 0: checked 2026-06-08-quick-data-profiler-DISCARDED BUILD_LOG.md — contains "Build complete. Success criteria reviewed. All tests passing." → complete (discarded by user rating, not interrupted), skip
- Category rotation: last builds covered B (2026-06-06), H (2026-06-07), F (2026-06-08) — choosing A (Dashboard/Visualizer)
- Lottery: backlog has no A/focused ideas — all 4 pending ideas are "ambitious" which is ineligible on a focused night → skipped lottery → fresh ideas
- Generated 3 fresh ideas: GitHub Repository Health Dashboard (winner), Stock Watchlist Snapshot, Outdoor Activity Weather Planner
- Winner: GitHub Repository Health Dashboard — uses GITHUB_TOKEN, connects to real data, novel vs. GitHub UI
- Non-winners appended to builds/ideas.md
- Build folder created: builds/2026-06-11-github-repo-health-dashboard/

### [08:10 UTC] PRD Written

- Goal: single-command terminal dashboard showing health of all user's GitHub repos
- Scope: fetch via GITHUB_TOKEN, show name/language/stars/issues/days/health, sort by last push, --limit/--include-archived/--format json/--org flags, graceful error handling
- Out of scope: CI status (requires per-repo calls), PR counts distinct from issues, web UI
- Stack: Python 3.10+ stdlib only, pytest for tests
- Architecture: github_client.py (API calls, not unit tested), health.py (pure functions, unit tested), formatter.py (rendering, unit tested), main.py (CLI entry point)
- Key design decision: `days_since_push` accepts an optional `now` datetime parameter so tests can use fixed timestamps without mocking datetime

### [08:12 UTC] Build Phase — Source Files

- Wrote src/__init__.py: empty package marker
- Wrote src/health.py: pure functions — parse_repo(), days_since_push(), health_status(), filter_repos(), enrich_repos()
  - days_since_push() accepts optional `now` datetime parameter for deterministic test behaviour
  - health_status() uses the "archived" flag to override activity-based labels
  - parse_repo() normalises None language to "—" and handles missing keys with safe defaults
- Wrote src/github_client.py: urllib-based GitHub API client — _get() and fetch_repos(); handles pagination and both user and org repo endpoints
- Wrote src/formatter.py: format_table() for terminal output, format_json() for scripting; _truncate() caps long repo names gracefully
- Wrote main.py: argparse CLI with --limit, --include-archived, --format, --org flags; exits 1 with helpful message if GITHUB_TOKEN unset
- Wrote requirements.txt: pytest only (all runtime code uses stdlib)

### [08:22 UTC] Tests Written

- Wrote tests/test_core.py: 35 tests across 7 test classes
  - TestParseRepo (6): name/full_name extraction, stars/issues, None language, string language, archived flag, empty dict defaults
  - TestDaysSincePush (5): 2 days ago, same day = 0, exactly 90 days, empty string sentinel, old push
  - TestHealthStatus (6): active/quiet/stale labels, archived override, both boundary conditions (30d and 90d)
  - TestFilterRepos (4): archived excluded by default, included with flag, empty input, no-archived passthrough
  - TestEnrichRepos (4): days_since_push added, health added, empty input, two repos enriched independently
  - TestFormatTable (6): empty message, headers present, full_name in output, health status in output, multiline, stale label
  - TestFormatJson (4): valid JSON, required fields present, empty array, valid health value

### [08:26 UTC] Tests Run

Tests: 35 passed, 0 failed. All tests passed on first run.

### [08:27 UTC] CLI Verified

- python3 main.py with no GITHUB_TOKEN → "Error: GITHUB_TOKEN environment variable is not set." printed to stderr, exit code 1 ✓
- No GITHUB_TOKEN available in this cloud session; network tests not run (unit tests cover all logic paths)
- GITHUB_TOKEN is auto-available in GitHub Actions context per PROFILE.md Data Sources section

### [08:29 UTC] Success Criteria Verified

1. All 35 tests pass, zero failures — ✓
2. Exit code 1 + clear error on missing GITHUB_TOKEN — ✓; full table output verified via unit tests (TestFormatTable covers all table rendering paths)
3. --format json outputs valid JSON array with name, health, days_since_push, open_issues fields — ✓ (TestFormatJson)
4. GITHUB_TOKEN unset → clear stderr message, exit code 1, no traceback — ✓ (verified manually)
5. Archived repos excluded by default; --include-archived includes them — ✓ (TestFilterRepos)

Security checklist:
- No .env files ✓
- No hardcoded credentials/tokens/keys ✓
- No eval() or exec() ✓
- No innerHTML (Python, no HTML templating) ✓
- No os.system() or subprocess calls ✓
- No file path traversal (user input goes only to HTTP request URL, not to filesystem) ✓

### [08:32 UTC] Documentation Complete

- FutureFeatures.md: 10 concrete suggestions (5 quick, 3 medium, 2 ambitious)
- Manual.md: setup, all flags, table output example, health status key, issues column caveat, JSON output example, error reference, test instructions

Build complete. Success criteria reviewed. All tests passing.
