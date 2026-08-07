# Build Log — Waymark

> **Date:** 2026-08-07
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:17 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md
- Resynced `builds/index.md` from the most recent open PR branch (`claude/cool-sagan-l2yxkz`, PR #63, 2026-08-06 Manuscript Pipeline) — main is behind, last merge was 2026-06-18
- Step 0: checked for interrupted builds — local build folders are all June and already complete; the most recent PR (#63, 2026-08-06) is a complete, already-open PR, not an interrupted session on this branch. Nothing to resume.
- Day of year 219 → category_index = 2 → Category C — Personal Knowledge Tool
- `builds/ideas.md` has zero pending Category C rows → skipped lottery, generated fresh ideas
- Scanned last 10 builds and all 5 prior Category C builds for topic overlap
- Decided to build: Waymark — automatic git-history decision knowledge base, directly responding to 2026-06-06's "would score higher with auto-capture of git state" feedback
- Build folder created: builds/2026-08-07-waymark/

### [08:20 UTC] PRD Written

- Goal: mine git commit history across local repos into a searchable, cross-project decision knowledge base with zero manual entry
- Scope: index/search/render/enrich/list-repos CLI commands, SQLite storage, deterministic decision scorer, optional Claude Haiku enrichment, self-contained dark-mode HTML dashboard
- Notable constraints: AI enrichment must make zero network calls without `ANTHROPIC_API_KEY`; git operations are real (not mocked) in tests since git is a local tool, not an external network API; only the Anthropic HTTP call is mocked

### [08:20 UTC] Build Phase

Building src/ modules in dependency order: db.py (schema), git_reader.py (subprocess-based git log parsing), scorer.py (pure decision-worthiness heuristic), enrich.py (optional Anthropic enrichment with unconditional deterministic fallback), render.py (self-contained HTML dashboard with escaped JSON payload), cli.py (argparse entrypoint wiring it together), main.py entry point.

Design decisions:
- `git log` invoked via `subprocess.run([...], shell=False)` with a fixed argument list — no shell interpolation, no injection surface, even though the repo path is user-supplied (that's the tool's entire purpose, same pattern as the existing Git Standup Reporter build)
- Default DB path `~/.waymark/waymark.db` so the index aggregates across all repos the user points it at, matching the "cross-project memory" goal; fully overridable with `--db` so tests never touch the real home directory
- AI enrichment sends only commit subject/body/file list/stat counts to Claude, never full diff content

### [08:45 UTC] Tests Written and Run

Wrote 64 tests across 6 files: test_scorer.py (15, pure heuristic logic), test_git_reader.py (9, against real temp git repos — git itself is a local tool, not mocked), test_db.py (12, SQLite layer including incremental indexing and search filters), test_enrich.py (8, all Anthropic HTTP calls mocked via unittest.mock, explicit assertion that zero network calls happen without a key), test_render.py (8, including a script-injection payload in a commit subject verified to survive as inert escaped JSON rather than breaking out of the embedded `<script>` tag), test_cli.py (12, full command wiring including the incremental re-index and error path for a non-git directory).

First run hit a real bug: `git_reader.py`'s record-separator constant was `\x00` (NUL), which `subprocess` rejects when embedded in a CLI argument (`ValueError: embedded null byte`) — every test that shelled out to git failed. Fixed by switching to `\x1e`/`\x1f` (ASCII record/unit separators), which are safe as argv content and still effectively guaranteed not to collide with real commit message text.

Tests: 64 passed, 0 failed.

### [08:50 UTC] Manual Smoke Test

Ran the CLI against this actual repository (`/home/user/Delightful-Nightly-Builds`, 56 commits) as a real-world check beyond the test suite: `index` correctly walked and scored all 56 commits (31 scored ≥5, decision-worthy), `search --min-score 5` returned a sensibly-ranked list, `render` produced a working dashboard. Confirms the tool is genuinely useful against real history, not just synthetic test fixtures. Smoke-test artifacts were written to `/tmp` and are not part of this build's output.

Ran the STANDARDS.md security checklist against every created file: no hardcoded credentials (test fixtures use an obvious `sk-test-key` placeholder), no `eval`/`exec`/`os.system`, no `innerHTML` assignment of untrusted data (the one `innerHTML` use clears a list to an empty string; all real content goes through `textContent`), no `.env` files.

### [08:52 UTC] Documentation and Catalog Updates

Wrote FutureFeatures.md (9 concrete suggestions across quick-win/medium/ambitious tiers) and Manual.md (quick start, full command reference, configuration, troubleshooting, known limitations). Appended the 3 non-winning fresh ideas from tonight's generation (Concept Atlas, Grant Boilerplate Miner, Course Concept Map) to `builds/ideas.md` as IDs 13–15, category C, status pending. Updated `builds/index.md`: appended the Full Catalog row, refreshed the Stats block (57 total, 54 complete, last build date 2026-08-07), and rotated the Last 7 Builds section.

Build complete. Success criteria reviewed. All tests passing.
