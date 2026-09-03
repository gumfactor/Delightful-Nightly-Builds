# Build Log — Promptbook

## [08:20 UTC] Step 0 — Resume check
Most recent build folder: `builds/2026-06-18-regex-dojo` (local `main`). Its `BUILD_LOG.md` ends with
"Build complete. Success criteria reviewed. All tests passing." — no resume needed.

Local `main` is far behind the actual build history: ~30 nightly-build PRs exist on GitHub
(none ever merged), most recent is PR #87 (`2026-09-02`, CiteForge, branch `claude/cool-sagan-1luptx`).
Per CLAUDE.md Step 1, resynced `builds/index.md` and `builds/ideas.md` from that branch before
orienting, rather than trusting the stale local copies.

## [08:22 UTC] Step 1 — Orient
- Read `PROFILE.md`, `STANDARDS.md`, resynced `builds/index.md` (80 total builds, last date 2026-09-02).
- Day of year = 246 → `category_index = (246-1) % 9 = 2` → **Category C — Personal Knowledge Tool**.

## [08:25 UTC] Step 2 — Decide
- Category C backlog (from resynced `builds/ideas.md`): 4 pending rows (#3 Lab Research Project
  Tracker — already superseded by Teamwork.com use per its own notes, kept pending but low-fit;
  #15 Lab Method/SOP KB; #16 AI Workflow & Prompt Cookbook; #28 Highlight Vault; #29 Supervision
  Notebook). All unrated (`—`) → R=0 numeric ratings → `lottery_chance = min(75, 25 + 0*2) = 25%`.
- Rolled `random.randint(1,100)` → **92**. 92 > 25 → lottery missed → fresh-idea generation (Step 2d).
- Full reasoning and candidate comparison in `WhyThis.md`.

## [08:35 UTC] Step 3-4 — PRD + build folder
Wrote `PRD.md` covering scope, the real JSONL transcript schema (verified by reading this build
container's own session transcript file before writing the parser — see WhyThis.md), the SQLite
schema, the deterministic score formula, folder structure, and testing strategy.

## [09:10 UTC] Step 5 — Build
Built `src/extract.py` (prompt-turn extraction), `src/episode.py` (post-prompt signal detection:
tool use, edits, test-run pass/fail, git commits, unresolved-error detection), `src/classify.py`
(deterministic keyword task-type classifier), `src/score.py` (deterministic 0-10 scorer),
`src/storage.py` (SQLite, incremental ingest via per-file line-count tracking), `src/ingest.py`
(orchestration), `src/ai_enrich.py` (optional Claude Haiku note + deterministic fallback,
injectable transport for testing), `src/render.py` (self-contained HTML dashboard), `src/cli.py` +
`main.py` (ingest/search/stats/render commands).

A first full test run (80/81 passing) caught a real classifier bug: the feature-type regex's
`(a|an|the|new)?` optional-modifier group only allowed *one* modifier word between the verb and
the noun, so "add a new endpoint" (two stacked modifiers, "a" then "new") fell through to the
"other" default instead of "feature". Fixed by changing the group to `(?:(?:a|an|the|new)\s+)*`
(zero or more modifiers) and added a dedicated regression test
(`test_feature_with_stacked_modifiers`).

Also caught and fixed a design gap before it shipped, not via a failing test: the original score
formula (commit +3, test-pass +2, edit +1) could only ever reach 6, making the CLI's `--ai`
enrichment threshold (`min_score=7`) permanently unreachable dead code. Rebalanced to commit +4 /
test-pass +3 / edit +2 / unresolved-error -3 (max achievable 9) so "7+" is a real, reachable bar,
and updated the affected reference-case tests accordingly.

## [09:20 UTC] Step 6 — Tests
`python -m pytest tests/ -v` (via the pre-installed `/root/.local/bin/pytest`, since project-level
`pip install` is denied in this sandbox — `requirements.txt` still pins `pytest==8.3.3` for the
user's own environment): **Tests: 81 passed, 0 failed.**

## [09:30 UTC] Step 7 — Manual, non-mocked verification
Ran `python main.py ingest --claude-dir /root/.claude/projects` against this build container's
own real, live session transcript (this very session) — not a fixture. It correctly extracted
exactly **1** genuine human-authored prompt out of ~100 raw JSONL lines (the rest being
assistant turns, tool_use/tool_result pairs, and bookkeeping lines), scored it **5/10**
(test-run+pass [+3] and edit-with-no-unresolved-error [+2], correctly reflecting that this very
session had already run a passing pytest suite and made edits, with no unresolved error and no
commit yet), and classified it `test` — all field values (`tools_used`, `files_edited: 26`,
`entrypoint: remote_trigger`, `git_branch: claude/cool-sagan-dlvwei`) matched this session's
actual real state exactly.

Inserted one additional synthetic row carrying a live
`</script><script>window.__xss=true;</script><img onerror>` payload directly into the real
database, rendered the dashboard, and verified live in headless Chromium (global npm Playwright
1.56.1, pre-installed Chromium binary): 2 cards rendered, `window.__xss`/`__xss2` never set (XSS
confirmed inert), live search filtering correctly narrowed from 2 cards to 1 and to the "no
matches" empty state, zero page/console errors, zero dialogs, and zero horizontal overflow at a
375px mobile viewport.

The real `data/promptbook.db` generated during this verification (containing this session's own
prompt text) is intentionally excluded from the commit via `.gitignore` — it is user-local
runtime state, not a build artifact, matching every other build's local-persistence pattern.

## [09:40 UTC] Step 7 — Success criteria review
1. ✓ `ingest` against a real Claude Code session directory extracted exactly the genuine
   human-authored prompt — zero tool-result echoes or sidechain turns leaked in, verified against
   this container's own live transcript (not just fixtures).
2. ✓ Every stored prompt gets a deterministic `task_type`/`score` with no AI call — hand-computed
   reference cases in `test_score.py` (11 cases) and `test_classify.py` (13 cases) cover every
   formula branch and one case per task type.
3. ✓ Re-running `ingest` on an unchanged source inserts zero duplicate rows — `test_ingest.py`'s
   idempotency test and the `prompt_uuid` primary key both enforce this; also true in the live run
   (a second `ingest` against `/root/.claude/projects` reported 0 new prompts).
4. ✓ `render` produces a standalone HTML file, searchable/filterable client-side, and a live XSS
   payload rendered inert in headless Chromium (2 real script tags, `window.__xss` never set).
5. ✓ All tests pass: **81 passed, 0 failed** (`python -m pytest tests/ -v`), well above the
   15-test minimum.

Security checklist (STANDARDS.md): no hardcoded credentials/secrets (only an obviously-fake
`"fake-key"` string in test fixtures), no `eval()`/`exec()`, no `innerHTML` anywhere in the
renderer, no `os.system()`/`subprocess` calls, no file paths built from unsanitized user input,
all files live under this build folder, `data/promptbook.db` (runtime-only, contains this
container's own real prompt text) is `.gitignore`d rather than committed.

## [09:45 UTC] Step 8 — Documentation
- `Manual.md`: install/run instructions, all 4 CLI commands, the exact scoring table, 5 documented
  limitations, and privacy notes.
- `FutureFeatures.md`: 7 concrete enhancements.
- `skill/SKILL.md`: companion Claude Code Skill so `ingest`/`search`/`stats` can be invoked from
  inside a coding session.

Build complete. Success criteria reviewed. All tests passing.
