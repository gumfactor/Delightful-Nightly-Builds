# Build Log — Research Question Forge

> **Date:** 2026-07-12
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [11:10 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for an interrupted build. Local branch's most recent dated folder is `2026-06-18-regex-dojo`, whose BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume on this branch.
- Orientation surfaced a repo-level issue worth noting: `main` is still at the 2026-06-18 build. 22+ nightly builds since (2026-06-19 through 2026-07-11) exist only as open, unmerged PRs (#16–#36). `builds/index.md` on `main`/this branch had rows synced ahead of the actual merged folders (via a prior PR #19 "sync missing rows" commit) without the corresponding build folders ever landing. Per CLAUDE.md Step 1, resynced orientation from the most recent open PR branch (`claude/cool-sagan-8r5sb5`, PR #36, 2026-07-11 Connectome) instead of trusting `main`. This does not block tonight's build (CLAUDE.md instructs proceeding regardless), but is flagged for the user separately since it's outside this build's scope to fix.
- Day of year: 193 → `(193-1) % 9 = 3` → Category D — Creative / Generative.
- Backlog (`builds/ideas.md`, resynced from PR #36 branch) has zero pending Category D rows → fresh idea generation per Step 2d.
- Decided to build: **Research Question Forge** — combinatorial research-question/hypothesis generator for the user's own forensic/affective neuroscience research domain, with novelty scoring, persistent SQLite library, and optional Claude polish with deterministic fallback.
- Build folder created: `builds/2026-07-12-research-question-forge/`

### [11:20 UTC] PRD Written

- Goal: generate, score, and persist novel research-question skeletons from a real domain taxonomy, with optional AI polish.
- Scope: combinatorial engine with compatibility rules, Jaccard novelty scoring, SQLite persistence, dark-mode HTML viewer, CLI (generate/render/star/tag/use/search/list).
- Notable decision: taxonomy content is hand-authored from PROFILE.md's named research areas (forensic/affective neuroscience, empathy, psychopathy, stress) rather than generic placeholder content, to avoid the "hollow/mock data" failure pattern called out repeatedly in the preference prior.

### [11:25 UTC] Build Phase — taxonomy and generator

Built `src/taxonomy.json` (10 populations, 10 constructs, 10 outcomes, 7 methods, 7 frames — all domain-real content drawn from the user's named research areas) and `src/generator.py` (compatibility-rule combinatorial engine + testability tagging + Jaccard novelty scoring). Verified manually: 6,928 valid compatibility-checked combinations out of 49,000 total cross-products.

### [11:40 UTC] Build Phase — persistence, AI polish, HTML render, CLI

Built `src/db.py` (SQLite schema + CRUD), `src/ai_polish.py` (optional Claude Haiku call via raw `urllib.request`, deterministic template fallback on missing key/network failure/malformed response), `src/render.py` (self-contained dark-mode HTML viewer with search/filter/detail panel/Copy-as-Markdown, JSON embedded in a `<script type="application/json">` block with `</` escaped to prevent script-injection break-out), and `src/main.py` (argparse CLI: generate/render/list/star/use/tag/search).

### [12:05 UTC] Tests Run

First run hung: `test_generate_batch_caps_at_available_valid_combinations` requested `total_valid + 1000` (~7,928) questions against the real taxonomy, which drove the batch-internal novelty scorer into O(n²) territory (~24M Jaccard comparisons) and the process had to be killed after 2+ minutes. This is not a real-world usage pattern (real batches are 5–50 items) — fixed by rewriting the test to use a tiny synthetic taxonomy with exactly one valid combination, which still exercises the "requested more than exists" cap behavior without the pathological cost.

Second run also caught a real test bug (not a product bug): `test_cli_search_returns_only_matching_rows` computed its expected match set by checking the search term against `skeleton` text only, but `db.search_questions` (correctly) also matches `rationale`, `tag`, and `ai_polish`. A generated method label ("salivary cortisol sampling...") put "cortisol" into a rationale whose skeleton didn't mention it, so the CLI's correct search result (which included that row) looked like a false positive against the test's narrower expectation. Fixed the test to check the same fields the search function actually searches.

Tests: 35 passed, 0 failed (added a regression test for a real bug found next).

### [12:15 UTC] Manual End-to-End Verification

Ran the actual CLI (not just pytest) end to end: `generate --count 12 --seed 7`, `render`, `list`, `search empathy`, `star 1`, `tag 1`, `use 1`, `render` again. This surfaced two real bugs pytest's `tmp_path`-based fixtures had masked:

1. `db.connect()` called `sqlite3.connect()` directly on a path whose parent directory (`output/`) didn't exist yet on a fresh checkout, raising `sqlite3.OperationalError: unable to open database file`. Fixed by creating the parent directory in `db.connect()`. Added `test_connect_creates_missing_parent_directory` as a regression test.
2. Drove the generated `forge.html` in real headless Chromium (Playwright, `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`) rather than just unit-testing the Python renderer. The "Starred only" filter matched zero rows even for a library with a starred item, because the embedded JS compared `String(item.starred)` (`"true"`/`"false"`) against the `<select>`'s `"1"`/`"0"` option values — a type mismatch that no Python test could catch since it's pure client-side logic. Fixed the comparison in `render.py`'s embedded JS to `(item.starred ? '1' : '0')`.

Re-verified in the browser after both fixes: load shows all 12 rows, text search for "empathy" filters to 6, testability filter works, starred filter now correctly shows 1 row, clicking a row opens the detail panel with correct content, Copy-as-Markdown updates the button to "Copied!", closing the panel works, and zero JS console/page errors were raised throughout.

Tests: 35 passed, 0 failed (final, after both fixes).

### [12:25 UTC] Step 7 — Success Criteria Verification

1. ✓ All tests pass — 35 passed, 0 failed (`python -m pytest tests/ -v`)
2. ✓ `generate --count 12` produced 12 compatibility-valid, non-duplicate skeletons on a fresh library (manual run, verified unique combo IDs and unit test `test_cli_generate_writes_requested_count`/`test_generate_batch_respects_count_and_dedupes`)
3. ✓ Novelty scores measurably decrease for near-repeats within a growing batch — observed live (1.00 → 0.32 across a 12-item batch as similar populations/constructs recurred) and covered by `test_novelty_score_is_lower_for_a_near_duplicate`
4. ✓ `render` produces a self-contained `forge.html` opened via `file://` in real headless Chromium — search, testability filter, starred filter, detail panel, and Copy-as-Markdown all verified working with zero JS console/page errors
5. ✓ Full CLI workflow runs end-to-end with no `ANTHROPIC_API_KEY` set (ran `generate` without `--polish`, confirmed `ai_source='template'` on every row); the Claude call path is exercised entirely through mocked tests in `test_ai_polish.py` (success, malformed response, empty content, and network-failure cases)

Security checklist (STANDARDS.md): no `.env` files, no hardcoded credentials/secrets (test-only placeholder strings only), no `eval`/`exec`, no `os.system`/`subprocess`, `innerHTML` writes only ever receive output already passed through the `esc()` textContent-escaping helper (verified by `test_render_html_escapes_script_injection_in_tag_field`), no file paths built from user input.

### [12:30 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions across quick/medium/ambitious tiers plus integration points and known limitations.
- `Manual.md`: quick start, full command reference, configuration table, troubleshooting table, known limitations.

Build complete. Success criteria reviewed. All tests passing.
