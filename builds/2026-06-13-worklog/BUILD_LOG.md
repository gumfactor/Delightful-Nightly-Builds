# Build Log — worklog: Cross-Agent Project Activity Workstreams

> **Date:** 2026-06-13
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:12 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, builds/index.md, STANDARDS.md, builds/ideas.md, and the idea brief in full
- Today is Saturday (day 6) → complexity target: Ambitious Project
- Step 0: checked 2026-06-08 BUILD_LOG.md — contains "Build complete. Success criteria reviewed. All tests passing." → complete, skip
- Category rotation: day of year 164, (164-1) % 9 = 1 → Category B — Productivity Utility
- Lottery: filtered pool has IDs 4 and 5 (both Category B, pending); R=2, lottery_chance=29%; rolled 17 ≤ 29 → lottery fires; ID 4 (9 tickets) vs ID 5 (8 tickets), ticket 7 drawn → ID 4 wins
- Selected: Cross-Agent Project Activity Workstreams — rated 9, has dedicated Idea Brief
- Read idea brief `builds/idea-briefs/cross-agent-project-activity-workstreams.md` in full before writing PRD
- Build folder created: builds/2026-06-13-worklog/

### [08:25 UTC] PRD Written

- Goal: Python CLI collecting Git + GitHub + checkpoint events into SQLite ledger, correlating into workstreams, producing standup/resume/why outputs
- Key design decisions:
  - SQLite via stdlib sqlite3 (no ORM, direct schema control, reliable dedup via deterministic IDs)
  - GitHub via urllib.request (stdlib) + GITHUB_TOKEN; graceful degradation when absent
  - Checkpoint capture via YAML file (pyyaml) + --from-stdin mode for hook compatibility
  - Workstream correlation: deterministic only — issue refs, branch names, file overlap, temporal proximity
  - No LLM-assisted summarization (keeps build self-contained, fast, and testable)
- Idea Brief Traceability section written in PRD; deviations documented

### [08:30 UTC] Build Phase — Core Modules

Wrote source files in dependency order:
- `src/config.py`: project discovery via git root walk, stable project ID from remote URL or path hash, `.worklog.json` local config, `ProjectContext` resolver
- `src/ledger.py`: SQLite schema (events, workstreams, decisions, schema_version tables), deterministic IDs via sha256, `insert_event` with dedup, `insert_decision`, `upsert_workstream`, query helpers
- `src/collectors/git.py`: `collect_commits` via `git log --format=...` + `git diff-tree --numstat`, `collect_dirty_state`, `get_dirty_files` using raw subprocess (not `_git()`) to preserve leading spaces in porcelain format
- `src/collectors/github.py`: GitHub REST API via `urllib.request` + GITHUB_TOKEN; extracts owner/repo from remote URL; collects issues and PRs; graceful degradation when token absent
- `src/checkpoint.py`: YAML parsing with schema version check, `checkpoint_to_events` producing one event + N decision rows, hook-compatible `--from-stdin` mode
- `src/correlation.py`: 5-pass deterministic correlation — issue refs, branch names, file overlap (7-day window), temporal proximity (<2h), uncorrelated fallback
- `src/freshness.py`: compares stored commit SHA against live HEAD; flags stale checkpoints
- `src/views.py`: `render_standup`, `render_resume`, `render_why`, `render_workstreams`, `render_events`
- `main.py`: argparse CLI with subcommands; `ProjectContext.resolve()` on startup

### [09:15 UTC] Tests Written

Wrote 62 tests across 5 test files:
- `test_ledger.py`: schema creation, idempotency, insert/dedup for events and decisions, query filters, workstream upsert
- `test_collectors_git.py`: commit log parsing (single, multi, malformed, empty, timestamp format), git integration tests against an isolated temp repo
- `test_checkpoint.py`: valid YAML parse, schema version rejection, missing objective/provider errors, event production, decision extraction, status from unresolved/validation fields, deduplication
- `test_correlation.py`: issue ref extraction, empty input, issue ref grouping, branch grouping, file overlap (within/beyond 7 days), all events assigned workstream
- `test_views.py`: standup sections and content, checkpoint next_steps in standup, why finds/shows/misses decisions, workstream listing, events view filtering

### [09:30 UTC] Test Failures and Fixes

First run: 9 failures. Fixed three root causes:

1. **`correlate_events` returned `[]` (not `([], {})`) on empty input** — test expected tuple unpacking; fixed to return consistent `([], {})`.

2. **`test_views.py` fixture passed metadata as pre-encoded JSON string** — `insert_event` then double-encoded it, causing `_meta()` to return the string instead of a parsed dict. Fixed by passing metadata as Python dicts in the fixture.

3. **`get_dirty_files` parsed porcelain incorrectly after `_git()` stripped leading spaces** — `_git()` calls `.strip()` on stdout; for ` M README.md` this strips the leading space, giving `M README.md`; then `line[3:]` = `EADME.md`. Fixed by having `get_dirty_files` use a direct `subprocess.run` call with `rstrip()` semantics, preserving the leading space.

4. **Git test repo commits failed due to signing** — test environment enforces commit signing. Fixed by adding `git -c commit.gpgsign=false` to all fixture commit calls.

### [09:45 UTC] Tests Run

Tests: 62 passed, 0 failed.

### [09:50 UTC] Success Criteria Verified

1. **62 tests pass, 0 failures** — ✓
2. **`python3 main.py sync` against live repo** — stored 37 new event(s), 4 workstreams detected, no error ✓
3. **`python3 main.py checkpoint --file session.yaml`** — ingested 1 event + 2 decisions; re-run produced 0 new rows (deduplication confirmed) ✓
4. **`standup` and `resume` produce non-empty, different outputs** — standup shows Done/In Progress with commit SHAs; resume shows objective, accomplished, decisions, next steps ✓
5. **Freshness warning when stored HEAD doesn't match current HEAD** — injected stale SHA → `⚠ STALE: stored HEAD 000000000000 != current HEAD 14b0104e60d4` appeared at top of resume ✓

Security checklist:
- No credentials, API keys, or tokens hardcoded ✓
- No eval() or exec() ✓
- No shell=True or os.system() ✓
- Subprocess calls use fixed argument lists only; no user input in shell commands ✓
- No innerHTML ✓
- No file path traversal — user paths go to Path() directly; not used in shell commands ✓

### [10:10 UTC] Documentation Complete

- `FutureFeatures.md`: 10 concrete suggestions across Quick Wins / Medium / Ambitious, plus integration points and known limitations table
- `Manual.md`: full command reference, checkpoint YAML format, correlation signal table, troubleshooting table, known limitations

Build complete. Success criteria reviewed. All tests passing.

