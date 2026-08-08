# Build Log — Panel Prep

> **Date:** 2026-08-08
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for an interrupted build. Most recent local dated folder is `2026-06-18-regex-dojo`, whose BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Step 1: `builds/index.md` on this branch/`main` is far behind — the most recent open PR (`claude/cool-sagan-7wrkhd`, #64, 2026-08-07 "Waymark") carries the current catalog (57 builds total, last build date 2026-08-07). Fetched and read that copy per CLAUDE.md's instructions rather than the stale local one.
- Day of year for 2026-08-08 (UTC) is 220. `category_index = (220 - 1) % 9 = 3` → **Category D — Creative / Generative**.
- Checked `builds/ideas.md` (also fetched from the current PR branch) for pending Category D rows: zero. Lottery is skipped per Step 2c; proceeding straight to fresh idea generation (Step 2d).
- Topic diversity check on the last 10 builds (2026-07-29 through 2026-08-07): C, D, E, F, G, H, I, A, B, C — categories are well distributed and no single topic domain (investing, GitHub metrics, etc.) repeats more than twice. Prior Category D builds (AI Lecture Builder 2/10, WeatherSong, Research Question Forge, Bridgework, Vizstract) rule out: single-shot lecture/prose generation, weather-driven audio, taxonomy-cross-product text generators (used twice already), and SVG visual-abstract rendering.
- Calibration note in CLAUDE.md ("every build has scored 4/10 or below") is stale against the fetched index (Qualtrics 9/10, and several unrated ambitious builds) — a known, previously-flagged issue (see AgentLint, 2026-07-16). Not modifying CLAUDE.md per its own instruction; using the *current* full index as the real prior instead of the stale calibration line.
- Decided to build: **Panel Prep** — a grant "mock study section" simulator: a deterministic NIH-style completeness/rigor checklist over a pasted Specific Aims/Significance/Innovation/Approach draft, plus three reviewer-persona critiques (deterministic weighted scoring always available; optional Claude Haiku narrative critique per persona) with per-project version history so score trend across drafts is visible.
- Build folder created: `builds/2026-08-08-panel-prep/`.

### [00:20 UTC] PRD Written

- Goal: turn a pasted/loaded grant-proposal draft into an NIH-style mock study-section critique (deterministic completeness checklist + three reviewer-persona scores) with version-over-time tracking.
- Scope: section parser, deterministic checklist engine, deterministic + optional-AI persona reviewer, SQLite version history per project, terminal + self-contained dark-mode HTML report with a score-trend chart.
- Notable constraints/decisions: NIH scoring restricted to Significance / Innovation / Approach / overall Impact only (never Investigator or Environment — those require CV/facilities information this tool is never given, and fabricating a score for them would be dishonest). Deterministic fallback must be independently useful, not just an "AI unavailable" placeholder, mirroring the pattern that scored well in Protocol Forge and Bridgework.

### [00:55 UTC] Build Phase — Core Logic

- Implemented `src/parsing.py` (header-based section splitter: Markdown `#`/`##`, ALL-CAPS lines, and `Header:` lines, all mapped through an alias table; falls back to treating the whole document as the Aims section when no recognized header is found).
- Implemented `src/checklist.py` (a fixed, per-section list of regex-based completeness/rigor checks — same "deterministic rule engine, no ML" shape as Protocol Forge's compliance engine).
- Implemented `src/reviewer.py` (three fixed personas, each with a distinct section-weighting; deterministic score derived from weighted checklist pass-rate; deterministic rationale bullets drawn from the actually-failed checks in that persona's focus sections; optional Claude Haiku call per persona for richer narrative critique, following the exact deterministic-first/AI-preferred/unconditional-fallback pattern used in `2026-08-06-manuscript-pipeline/src/parsing.py`, including the same `model: claude-haiku-4-5-20251001` call shape). A deterministic "resume of discussion" paragraph (score-variance framing + top shared concerns) is always generated — no fourth AI call.
- Implemented `src/db.py` (SQLite: `projects` + `versions`, version numbers auto-incrementing per project, nothing ever overwritten).
- Implemented `src/render.py` (terminal renderer + self-contained dark-mode HTML dashboard). Reused the manuscript-pipeline's `_safe_json_for_script` `<script type="application/json">` + `textContent`/`createElement` pattern verbatim for XSS safety, plus a Chart.js 4.4.4 CDN trend line with a DOM-table fallback when the CDN is unavailable.
- Implemented `src/main.py` (argparse CLI: `submit`, `list`, `history`, `render`).

### [01:20 UTC] Tests Written and Run

- Wrote `tests/test_parsing.py`, `tests/test_checklist.py`, `tests/test_reviewer.py`, `tests/test_db.py`, `tests/test_render.py`, `tests/test_main.py` — 57 tests total, covering the happy path per module, edge cases (empty input, no headers, all-checks-fail, all-checks-pass, malformed/absent AI response, no API key present), and an injected `</script><script>...</script>`-breakout payload verified inert in the rendered HTML.
- All Anthropic API calls are mocked in tests via `unittest.mock.patch` on `urllib.request.urlopen`; a dedicated test asserts `urlopen` is never called when no API key is supplied, so zero live network calls happen in the suite.

Tests: 57 passed, 0 failed.

### [01:35 UTC] Verify — Step 7

- Success criteria checked against `PRD.md` (all met — see below).
- STANDARDS.md security checklist run against every file in `src/` (`grep` for `eval(`/`exec(`, `os.system`/`subprocess`, `innerHTML`, hardcoded secrets, `.env` files — all clean).
- Manually verified end-to-end outside pytest: `submit` on the complete `sample_proposal.txt` scored a perfect 1.0/100% on every persona and check; a second, deliberately sparse revision to the same project scored 9.0/0%, confirming the deterministic scorer is genuinely monotonic on real input, not just in unit tests. `history`, `list`, and `render` all ran correctly against that two-version project. A live `</script><script>alert('xss')</script>` payload placed directly in the Approach section text was confirmed present (and correct) inside the report's embedded JSON payload via `json.loads`, but never appears as a literal, unescaped `<script>` tag anywhere in the surrounding HTML (`<script>` unicode-escaped only) — zero executable breakout. A separate manual run with `urllib.request.urlopen` mocked and `ANTHROPIC_API_KEY` unset confirmed exactly zero network calls end-to-end through the real CLI `submit` path.

### [01:40 UTC] Documentation

- `FutureFeatures.md` — 8 concrete suggestions across quick wins, medium effort, and ambitious extensions.
- `Manual.md` — quick start, all four commands documented, sample input file format, troubleshooting table.

Build complete. Success criteria reviewed. All tests passing.
