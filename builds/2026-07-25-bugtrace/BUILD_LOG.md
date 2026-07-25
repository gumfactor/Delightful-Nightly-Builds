# Build Log — BugTrace: Personal Bug-Pattern Miner

> **Date:** 2026-07-25
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:15 UTC] Session Start

- Step 0: checked `builds/` for an interrupted prior session. Only 5 dated folders exist locally (this branch was forked from an old `main`); the most recent, `2026-06-18-regex-dojo`, ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed.
- Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-cp7wow`, PR #50, 2026-07-24 Heuristic Hunt) since local `main`/this branch are many builds behind, per CLAUDE.md's resync instructions. Confirmed via BUILD_LOG.md on that branch that the 2026-07-24 build is also complete.
- Read PROFILE.md, resynced builds/index.md (43 total builds logged), and STANDARDS.md.
- Day of year 206 → category rotation index `(206-1) % 9 = 7` → Category H — Developer Tool.
- Backlog lottery: 1 pending Category H idea (#9, no rating) → 25% draw chance. Rolled 73 via `$RANDOM` → fresh-idea path taken (full reasoning in WhyThis.md).
- Generated 3 fresh Category H candidates; selected **BugTrace: Personal Bug-Pattern Miner** — a CLI that mines commit history for bug-fix commits and classifies root-cause patterns (keyword-based, with optional Claude Haiku second opinion) to build a personal "what kind of bugs do I actually write" dashboard.
- Build folder created: `builds/2026-07-25-bugtrace/`

### [08:20 UTC] PRD Written

- Goal: mine fix-commit history across repos, classify root-cause pattern, persist in SQLite, render dashboard.
- Scope: fix-commit detection, secret redaction, keyword taxonomy classifier, optional AI classifier with fallback, GitHub API client + local-git fallback (no token required), SQLite dedupe store, terminal/JSON/HTML report.
- Notable decision: added a local `git log`/`git show` fallback path (`--repo-path`) so the tool is fully useful with zero credentials, not just GITHUB_TOKEN — strengthens the "genuinely useful out of the box" bar from CLAUDE.md's calibration note.

### [08:25 UTC] Build Phase — Core modules

Implemented in order: `fix_detector.py` (message-heuristic fix-commit detection, excludes merges/reverts), `redact.py` (secret redaction applied to every diff before storage/display/AI), `classify.py` (12-category deterministic keyword taxonomy, priority-ordered rules, `test_only_fix` special-cased via changed-file paths), `ai_classify.py` (optional Claude Haiku batch classification against the same taxonomy, with per-item fallback to the keyword classifier on any parse/network failure, plus a separate `ai_coaching_summary` used by the HTML report), `github_client.py` (stdlib `urllib` GitHub REST client — repo listing, commit listing, commit detail/diff — with a `request_fn` injection point for testing and a `GitHubAPIError` wrapper), `local_git.py` (subprocess-based local git log/show fallback requiring no token, with `_validate_repo_path`/`_validate_sha` guards against argument injection since it's list-form `subprocess.run`, never `shell=True`), `store.py` (SQLite, `INSERT OR IGNORE` dedupe on `(repo, sha)` so a commit is never re-classified once stored), `report_text.py` and `report_html.py` (terminal summary and a self-contained dark-mode HTML dashboard — Chart.js 4.4.4 pinned CDN with a text-table fallback if the CDN fails to load, all commit-derived text inserted via `textContent`/`createElement`, data embedded in a `<script type="application/json">` block with `</` escaped to prevent early tag closure), and `cli.py` (argparse `sync`/`report`/`show` subcommands wiring everything together).

Decision: added `--repo-path` (local git, zero credentials) as a first-class sync target alongside `--repos`/`--all` (GitHub API), so the tool is genuinely useful with no environment configuration at all — directly supports PRD success criterion 5.

### [08:55 UTC] Tests Written

80 pytest tests across 10 files, covering: fix-commit detection (positive/negative/merge/revert exclusion), secret redaction (API keys, AWS example key, bearer tokens, untouched normal code), all 12 taxonomy categories individually plus the priority-ordering that keeps them from colliding, the AI classifier's prompt construction, response parsing, and three distinct fallback paths (no key, network error, malformed response, partial response), the GitHub client's pagination/fork-filtering/error-wrapping (fully mocked via a `request_fn` injection point — no live network call anywhere in the suite), the local-git fallback against a real throwaway git repo created in a pytest `tmp_path` fixture (safe, no network involved), SQLite dedupe/aggregation, both report renderers (including a script-injection payload in a commit message asserted to land as inert JSON text, never an executed tag), and end-to-end CLI flows (sync → report in all three formats, dedupe on re-sync, `--ai` flag wiring, a GitHub target skipped gracefully with no token).

### [09:05 UTC] Tests Run

Tests: 80 passed, 0 failed. (`python -m pytest tests/ -v` from `builds/2026-07-25-bugtrace/`)

Note: `pytest` and `playwright` (Python bindings) were not preinstalled in this build container and were installed via `pip install --user` to run the suite and do a manual live-browser check respectively; neither is a runtime dependency of BugTrace itself (both `requirements.txt` and the manual-verification tooling are separate — the shipped tool is stdlib-only).

### [09:10 UTC] Manual End-to-End Verification

Ran the actual CLI against this repository's own real git history (`python3 main.py sync --repo-path <this repo> --since-months 24`): correctly identified 15 real fix-commits from the last 24 months, classified them via the keyword taxonomy, and produced correct terminal, JSON, and HTML reports. A second `sync` run over the same repo correctly synced 0 new commits (dedupe confirmed against real data, not just fixtures).

Loaded the generated HTML report in headless Chromium (`/opt/pw-browsers/chromium-1194`, Python Playwright bindings installed for this one-off check): zero page errors, zero uncaught exceptions. The build container's egress proxy blocked the Chart.js CDN as expected per CLAUDE.md's network-policy note — the graceful text-table fallback engaged correctly with the exact data (verified row-by-row against the JSON export), and the client-side search/filter box was exercised live (filtering to a real commit message and to a deliberately non-matching query, both rendered correctly). This confirms the same pattern CanEcon Pulse (2026-07-18) validated: CDN-blocked-in-container, works-for-the-user-locally.

### [09:15 UTC] Security Checklist (STANDARDS.md)

- No `.env` files in the build folder
- No hardcoded credential values (only regex *patterns* for detecting/redacting secrets, and one AWS-published example key used as a redaction test fixture)
- No `eval()`/`exec()` anywhere in `src/` or `main.py`
- `innerHTML` appears only as `= ""` (clearing a container before rebuilding it via `createElement`/`textContent`) — confirmed via grep, never assigned from commit-derived data; verified live in headless Chromium with a script-injection payload in a commit message, which rendered as inert text
- No `shell=True` and no `os.system()` anywhere; `local_git.py` uses list-form `subprocess.run` exclusively, with `_validate_repo_path`/`_validate_sha` guards
- All file I/O stays within paths the user explicitly passes (db path, output path, repo path) — no hardcoded paths outside the build folder, no traversal of user input
- Diff content is redacted for secret-like patterns before it is ever stored, displayed, or sent to the optional Anthropic API call

### [09:20 UTC] Success Criteria Review

1. All tests pass, zero failures, 80 tests (well over the 15 minimum) — met
2. `sync` against a local repo (no token) correctly detects/classifies fix commits and dedupes on re-run — met, confirmed both in pytest and against this repo's real history
3. `--ai` path exercised with a mocked successful response, a network-error fallback, a malformed-response fallback, and a partial-response per-item fallback — met
4. `report --format html` renders correctly in headless Chromium with zero page errors, degrades gracefully with the CDN blocked, and safely escapes a script-injection payload in a commit message — met, verified live
5. Tool runs end-to-end with zero configuration (no GITHUB_TOKEN, no ANTHROPIC_API_KEY) against a local repo path — met

Build complete. Success criteria reviewed. All tests passing.
