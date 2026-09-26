# Build Log — Shiplog

> **Date:** 2026-09-26
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:14 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md in full.
- Checked for incomplete builds (Step 0): the most recent local dated folder (`2026-06-18-regex-dojo`) ends with "Build complete. Success criteria reviewed. All tests passing." The most recent open PR branch (`claude/cool-sagan-0xsqm2`, PR #109, 2026-09-25, "Agent Relay") also ends with the same completion line. Nothing to resume.
- Resynced `builds/index.md` and `builds/ideas.md` from PR #109's branch (this repo's builds are never merged to `main` — local `main`-derived copies were ~3 months stale: 5 dated folders locally vs. 102 builds on the most recent open PR branch).
- Day of year 269 → `category_index = (269-1) % 9 = 7` → **H — Developer Tool**.
- Category H backlog: 5 pending ideas (#34 Dead Code Detective, #35 Test Flakiness Static Scanner, #36 API Surface/SemVer Diff Checker, #49 License Compliance Auditor, #50 Config Drift Detector), all unrated → `R=0` → `lottery_chance = 25%`. Rolled 38 (`python3 random.randint(1,100)`) → gate missed → fresh generation (Step 2d).
- Reviewed all 10 prior Category H builds (Git Standup Reporter, dep-check, ci-pulse, Schema Sentinel, AgentLint, BugTrace, Landing Pattern, Snipvault, Layer Guard, Secrets Sentinel) to avoid duplication — dependency auditing, CI perf, JSON/CSV schema diffing, agent-instruction-file linting, bug-pattern mining, PR merge-order planning, snippet storage, circular-import/coupling analysis, and secret scanning are all already covered.
- Generated 3 fresh Category H ideas (see `WhyThis.md` for full comparison): **Shiplog** (changelog/release-notes generator from git history with conventional-commit + keyword classification, revert-pair cancellation, semver suggestion, optional Claude polish), **Coverage Gap Radar** (coverage.py + git-churn risk scoring), **Docs-Flag Drift Checker** (README/Manual.md CLI examples vs. actual argparse interface). Selected **Shiplog** — richest deterministic core logic, direct daily/weekly utility across the user's many maintained repos (Canada List, Kwyeter, this very nightly-build repo), and a genuine AI differentiator (turning classified commits into readable release notes) rather than an AI-wrapper-only build.
- No idea brief linked (fresh generation).
- Non-winning ideas logged to `builds/ideas.md` as #73 (Coverage Gap Radar) and #74 (Docs-Flag Drift Checker).
- Build folder created: `builds/2026-09-26-shiplog/`

### [08:20 UTC] PRD Written

- Goal: generate a categorized, human-readable changelog from a local git repo's commit history, with optional AI-polished prose and an HTML velocity report.
- Scope: conventional-commit parser, keyword-based fallback classifier, revert/re-revert cancellation, semver bump suggestion, Markdown + HTML output, optional GitHub PR-title enrichment via `GITHUB_TOKEN`, optional Claude Haiku prose polish, companion Claude Code Skill.
- Notable constraints: all git history reads are local and read-only (`git log`, never `git push`/`git commit` on the target repo); no network calls in tests; `ANTHROPIC_API_KEY`/`GITHUB_TOKEN` both optional at runtime with deterministic fallbacks.

### [08:25 UTC] Build Phase — Core engine

- `src/git_log.py`: read-only `git log --first-parent` wrapper (never mutates the target repo). Uses `%x1e`/`%x1f` as record/field separators to safely parse multi-line commit bodies. `resolve_range()` treats `--since` as a git ref when it validates via `rev-parse --verify`, else falls back to treating it as a date string for `--since=<date>`; with no `--since` given, resolves the latest tag reachable from `--until` via `git describe`, or falls back to full history if the repo has no tags.
- `src/classify.py`: conventional-commit regex parser (type/scope/`!`-breaking/`BREAKING CHANGE:` footer/subject) restricted to the known conventional types so an unrelated `word:` prefix (e.g. `wip:`) doesn't get treated as a real type; ordered keyword fallback classifier for everything else; revert/re-revert cancellation matching a `Revert "..."` commit's quoted text against candidates.
- **Bug caught while writing `test_classify.py`:** the conventional-commit parser strips the `type:` prefix from `Commit.subject` (so `"feat: add risky experiment"` becomes `"add risky experiment"`), but `git`'s own revert commit message quotes the *original, unstripped* subject line. Comparing `revert`'s parsed original text against the already-stripped `Commit.subject` would never match. Fixed by adding a `raw_subject` field to `Commit` (populated with the unparsed first commit-message line in every classification path) and matching reverts against that instead.
- `src/semver.py`: pure section→bump mapping, no I/O.
- `src/github_enrich.py`: zero-network-call by default (short-circuits immediately when `repo`/`token` aren't both supplied); injectable `http_get` for testing; label-to-type mapping refines classification and can only ever add a "breaking" flag, never remove one already set from the commit message itself.
- `src/ai_polish.py`: injectable `call_fn`; deterministic bulleted fallback used whenever no key is supplied (zero calls, verified by a spy in tests) or the call raises any of a specific set of expected failure types; prompt sent to Claude contains only `type`/`scope`/`subject`/`breaking` per commit, never diffs or file paths (a dedicated test asserts no `diff --git`/`@@` markers ever appear in the built prompt).
- `src/render.py`: Markdown + self-contained dark-mode HTML (Chart.js 4.4.4 pinned via CDN) renderer; all user-controlled text (commit subjects, AI-polished prose) is HTML-escaped before insertion; the chart's data payload is JSON-encoded into a `<script>` block with `</` escaped to `<\/` to prevent premature tag closure from a hostile commit subject.
- `src/shiplog.py`: `argparse`-based CLI wrapping the above into a single `generate` subcommand; writes files to `--out` (defaults to the current working directory, never the target repo, unless the user explicitly points `--out` there).
- `skill/SKILL.md`: companion Claude Code Skill so the tool can be invoked as `/shiplog` in a coding session per PROFILE.md's stated preference for pull-tools over scripts.

### [08:40 UTC] Test Phase

- Wrote `tests/test_classify.py`, `tests/test_semver.py`, `tests/test_github_enrich.py`, `tests/test_ai_polish.py`, `tests/test_render.py`, `tests/test_shiplog_cli.py` — 44 tests total.
- First run surfaced a real fixture bug (not a product bug): `test_build_changelog_end_to_end_with_revert_pair` had every synthetic commit append to the same shared `file.txt`, so `git revert` on a non-tip commit produced a genuine merge conflict during the test itself. Fixed by giving each synthetic commit its own file, which is also a more faithful test of the revert-matching logic in isolation from git's own conflict resolution.
- [08:52 UTC] Tests: 44 passed, 0 failed. (`/root/.local/bin/pytest tests/ -v`; project's `python3` had no `pytest` installed globally, found the already-installed `pytest` at `/root/.local/bin/pytest` via `uv tool` rather than attempting a `pip install`.)
- Manual smoke test: ran `python3 src/shiplog.py generate <this-repo's-parent-checkout>` against this very repository's real (pre-resync, June-era) commit history — produced a correct, readable grouped changelog with a `minor` suggested bump from 45 real commits, confirming the tool works against real-world history and not just synthetic fixtures. Output written to a scratch `/tmp` directory, not committed.

### [08:55 UTC] Verify Phase

- Security checklist (STANDARDS.md), grep-verified against `src/` and `tests/`:
  - No `eval()`/`exec()` anywhere.
  - No `innerHTML` in shipped source (only appears inside a test assertion checking its absence, and in `PRD.md`'s own description of that test).
  - `subprocess.run` (`git_log.py`) is the only subprocess call in the build: always invoked as `["git", "-C", path, *args]` with `shell=False` (the default) and each argument passed as a separate list element, never interpolated into a shell string — user-controlled values (`repo_path`, refs) can never be interpreted as shell syntax.
  - No hardcoded credentials — the only `api_key="sk-test"` occurrences are test fixture values passed to injected fakes, never a real key.
  - No `.env` files.
  - All files live under this build folder; only `builds/index.md` and `builds/ideas.md` are touched outside it.
- Success criteria (PRD.md) checked:
  1. ✓ All tests pass, 44 (≥15 required).
  2. ✓ Revert/re-revert cancellation verified end-to-end against a real git repo (`test_build_changelog_end_to_end_with_revert_pair`) and also confirmed manually against this repo's real history (0 cancelled pairs found there, correctly — no revert commits exist in that range).
  3. ✓ Semver bump correctness verified per scenario in `test_semver.py` (breaking/feat/fix/none, plus a maintenance-only case).
  4. ✓ `--ai-polish` with no `ANTHROPIC_API_KEY` verified to make zero calls via a spy (`test_no_api_key_makes_zero_calls_and_uses_deterministic_fallback`) and to fall back cleanly on a simulated failure even when a key *is* present (`test_ai_call_failure_falls_back_to_deterministic_bullets`).
  5. ✓ HTML report confirmed self-contained (only the pinned Chart.js CDN `<script src>` as an external reference) with zero `innerHTML` and a dedicated script-tag-breakout test.

### [09:00 UTC] Documentation Phase

- `FutureFeatures.md`: 7 concrete suggestions (2 quick wins, 2 medium, 2 ambitious, plus a limitations table).
- `Manual.md`: quick start, range selection, output formats, optional GitHub/AI flags explained with exactly what does and doesn't leave the machine, configuration table, troubleshooting table, honest known-limitations section.

Build complete. Success criteria reviewed. All tests passing.
