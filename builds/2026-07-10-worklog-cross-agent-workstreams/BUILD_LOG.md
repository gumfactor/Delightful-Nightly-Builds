# Build Log — Worklog: Cross-Agent Project Activity Workstreams

> **Date:** 2026-07-10
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:00 UTC] Session Start

- Checked `builds/` for an incomplete prior session: the most recent dated folder
  (`2026-06-18-regex-dojo`) has a completed `BUILD_LOG.md` ending in "Build complete. Success
  criteria reviewed." — nothing to resume.
- Read `PROFILE.md`, `STANDARDS.md`, and resynced `builds/index.md` from the most recent open
  PR branch (`claude/cool-sagan-hoqqsk`, PR #34) rather than the stale copy on `main` — `main`
  is ~28 builds behind; the open-PR branch has the current catalog (29 total builds, 26
  complete, 3 discarded).
- Day of year 191 → category rotation index `(191-1) % 9 = 1` → Category B (Productivity
  Utility).
- Filtered `builds/ideas.md` to pending Category B ideas: found two rated entries (ID 4 "Cross-
  Agent Project Activity Workstreams" @9, ID 7 "Morning Briefing" @8). Cross-checked both
  against `builds/index.md` and found ID 7 duplicates the already-shipped, already-rated
  2026-06-22 build of the same name — marked it `built` retroactively rather than let it stay
  eligible for future draws. Did the same for ID 9 (GitHub Actions Performance Analyzer),
  already realized as 2026-06-28's "ci-pulse".
- Category B pool after cleanup: 1 idea (ID 4). R=1 → lottery_chance = 27%. Rolled 3/100 →
  draw. Single-candidate pool → ID 4 selected, marked `built`.
- Read the linked Idea Brief in full before writing the PRD.
- Decided to build: Worklog — a stdlib-only Python CLI implementing the brief's "first useful
  release" scope (project discovery, git collector, GitHub issues/PRs collector, checkpoint
  ingestion, SQLite event ledger, deterministic workstream correlation, and the standup/
  resume/why/timeline/workstreams/show-event/search views).
- Build folder created: `builds/2026-07-10-worklog-cross-agent-workstreams/`

### [00:20 UTC] PRD Written

- Goal: automatically correlate Git, GitHub, and AI-agent checkpoint activity into evidence-
  backed workstreams queryable via standup/resume/why views.
- Scope: full brief loop present end-to-end (capture → normalize → correlate → view), but
  narrowed to issues+PRs only from GitHub (no reviews/CI check-runs), no AI-provider-specific
  session parsers, no dashboard, no model-assisted synthesis — all consistent with the brief's
  own "first release" non-goals.
- Notable constraints: zero third-party dependencies so the tool runs anywhere Python 3 is
  installed; JSON checkpoint format instead of YAML (brief's example is illustrative, not a
  hard requirement) to avoid a PyYAML dependency.

### [00:35 UTC] Build Phase — Core modules

- Implemented `worklog/util.py` (UTC time helpers, deterministic event-id hashing, slugify,
  regex-based secret redaction for checkpoint free text).
- Implemented `worklog/project.py` (git-root discovery, GitHub owner/repo extraction from both
  HTTPS and SSH remote URL forms, branch/HEAD/dirty-state snapshot).
- Implemented `worklog/ledger.py` (SQLite schema: events/workstreams/sync_state; dedup-safe
  upsert keyed on deterministic event id; workstream upsert; query helpers used by every view).
- Implemented `worklog/git_collector.py` (commits/branches/tags via `git` subprocess with
  `--porcelain`/`-z`-safe parsing; no full diffs stored, only changed-file lists and stats per
  the brief's guidance to avoid storing full source diffs).
- Implemented `worklog/checkpoint.py` (schema validation with clear error messages, defaults
  for optional fields, secret redaction applied to `objective`/`accomplished`/`decisions`/
  `unresolved`/`next_steps` text before persistence).
- Implemented `worklog/github_collector.py` (issues + PRs via GitHub REST API using
  `urllib.request` directly — no SDK dependency — reading `GITHUB_TOKEN` from the environment;
  returns an explicit "skipped: <reason>" result instead of raising when no token or non-GitHub
  remote, so `sync` degrades gracefully).
- Implemented `worklog/correlate.py` (deterministic signal ladder: explicit checkpoint hint →
  issue/PR number reference → active non-default branch → touched-file overlap with recent
  commits (Jaccard ≥ 0.2) → dated general bucket; every event's correlation records its signal
  + confidence rather than presenting a guess as settled fact).
- Implemented `worklog/views.py` (standup grouping, resume with staleness checks against live
  git HEAD and rebase detection via `git merge-base --is-ancestor`, why decision search,
  timeline, workstreams list, show-event, search).
- Implemented `worklog/cli.py` + `worklog/__main__.py` (argparse dispatch for all subcommands).

### [01:10 UTC] Tests Written and Run

- Wrote `tests/conftest.py` with a real temporary git repo fixture (uses actual `git init` /
  `git commit` via subprocess, not mocked) so collector tests exercise real git plumbing.
- GitHub collector tests mock `urllib.request.urlopen` — no real network calls made or
  required; verified both the authenticated-request path and every graceful-degradation path
  (no token, non-GitHub remote, HTTP error).
- Tests: 99 passed, 0 failed. (`python -m pytest tests/ -v`)

### [01:15 UTC] Manual Verification — two real bugs found and fixed

Ran the CLI end-to-end against real git repos (not just the pytest fixtures) before trusting
the test suite, per this repo's own precedent of catching CDN/network issues only visible at
runtime. Found two genuine bugs the unit tests as originally written didn't catch:

1. **Dirty-file parsing truncated the first filename.** `run_git()` calls `.strip()` on all
   captured stdout for convenience (most callers want a single trimmed value). `git status
   --porcelain` lines can start with a literal leading space (" M file", the unstaged-modified
   status code), and that global `.strip()` silently ate the leading space of the *first*
   line only, shifting every downstream slice by one character (`README.md` became
   `EADME.md`). Fixed by having `_working_tree_state()` read raw, unstripped subprocess output
   instead of going through `run_git()`. Added a regression test
   (`test_discover_project_dirty_file_first_in_status_keeps_full_filename`) that would have
   caught this.
2. **Branch commits split into two workstreams instead of one.** Manually syncing a repo with
   a feature branch (an issue-referencing first commit, a plain follow-up commit) showed them
   landing in *separate* workstreams instead of one. Root cause was two compounding issues:
   `git log`'s default newest-first order let the follow-up commit claim a fresh branch-only
   workstream before the earlier issue-referencing commit had a chance to establish the
   higher-confidence issue-based anchor; and `collect_commits()` was collecting the *entire*
   history reachable from the checked-out branch (including commits shared with `main`), which
   also mislabeled old shared commits with whatever branch happened to be checked out at sync
   time. Fixed by (a) collecting commits oldest-first, and (b) scoping feature-branch
   collection to `git log <default-branch>..<branch>` (commits unique to that branch) rather
   than the full reachable history. Added both a collector-level regression test
   (`test_collect_commits_on_feature_branch_excludes_shared_main_history`) and a CLI-level one
   (`test_sync_correlates_branch_commits_to_earlier_issue_reference`).
- Re-ran the full suite after both fixes: still zero failures, test count grew from 99 to 103.
- Verified graceful GitHub degradation against this actual repo
  (`gumfactor/Delightful-Nightly-Builds`): correctly detected as
  `github:gumfactor/Delightful-Nightly-Builds`, correctly scoped commit collection to
  `main..claude/cool-sagan-9twrha` (0 new commits, since this branch hadn't committed
  anything yet at sync time), and the GitHub call returned `403 Forbidden` — this session's
  `GITHUB_TOKEN` is the same non-functional proxy placeholder that the 2026-07-09 Pipeline
  Pulse and 2026-06-28 ci-pulse builds already documented — and `sync` reported that plainly
  instead of crashing, exactly as designed.

### [01:35 UTC] Verify — Step 7

- Ran the STANDARDS.md security checklist against every file in this build folder: no `.env`
  files, no hardcoded credentials/tokens (GitHub token and Anthropic key are both read from
  `os.environ` only, never written to source or ledger), no `eval`/`exec`, no `innerHTML` (no
  browser UI in this build), no `subprocess` call built from unsanitized user input (git
  ref/path arguments are passed as argv list elements, never shell-interpolated), no file
  paths taken directly from user input without resolving against the discovered repo root.
- Checked each PRD success criterion by hand against real temp repos plus a live checkpoint
  file (see Manual.md Quick Start for the exact commands used) — all 6 criteria hold, including
  after the two bug fixes above.

### [01:45 UTC] Documentation

- `FutureFeatures.md`: 8 concrete follow-ups (review/CI ingestion, semantic why-search, MCP
  server wrapper, cross-project "where was I" view, agent-native checkpoint auto-writers, etc.)
- `Manual.md`: quick start, full command reference, checkpoint file contract, troubleshooting,
  known limitations.

Build complete. Success criteria reviewed. All tests passing.
