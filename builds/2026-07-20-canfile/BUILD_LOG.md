# Build Log — CanFile: Canadian Ownership Knowledge Cards

> **Date:** 2026-07-20
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- No incomplete build found in `builds/` — most recent dated folder (2026-06-18-regex-dojo) has a `Build complete...` final entry.
- `main`'s `builds/index.md` was stale (last entry 2026-06-24, 19 builds). Fetched the most recently created open PR branch (`claude/cool-sagan-n7vpur`, 2026-07-19) and read its `builds/index.md`/`builds/ideas.md` instead — 39 builds through 2026-07-19. Copied both files into the working tree.
- Day of year 201 → category_index 2 → Category C (Personal Knowledge Tool).
- Lottery: both pending Category C backlog ideas had blank ratings → 25% draw chance. Rolled 100/100 → fresh-idea path.
- Topic diversity check flagged the neuroscience-research/academic-admin domain as saturated (5 of last 10 builds). Chose CanFile — Canadian Ownership Knowledge Cards, matching backlog idea #13, since it targets The Canada List (a named active project with zero prior builds) using real Wikidata/Wikipedia public APIs. Full reasoning in WhyThis.md.
- Build folder created: builds/2026-07-20-canfile/

### [00:10 UTC] PRD Written

- Goal: local versioned knowledge-card CLI that assesses Canadian company ownership from Wikidata/Wikipedia facts, with a deterministic rule engine and optional Claude enrichment.
- Scope: Wikidata search + claims + one-hop parent/owner country resolution, Wikipedia summary, deterministic + optional-Claude assessment, SQLite versioned storage, CLI (add/show/list/search/export-html), dark-mode HTML index.
- Notable decision: previous 2026-07-11 attempt at a near-identical idea (#13) was not built because `query.wikidata.org`/`www.wikidata.org` returned 403 in that session's build container. Per CLAUDE.md's API-access guidance, this is a build-environment constraint, not a design flaw — tonight's code targets the real APIs and mocks them in every test.

### [00:15 UTC] Build Phase — Wikidata/Wikipedia clients

Wrote `src/wikidata_client.py`: `search_entity()` (wbsearchentities), `get_claims()` (wbgetentities props=claims, extracts P17/P159/P749/P127/P31 entity-id claims), `resolve_labels()` (batch wbgetentities props=labels for a set of QIDs). Wrote `src/wikipedia_client.py`: `get_summary()` against the REST summary endpoint, handling 404/missing page.

### [00:25 UTC] Build Phase — Assessment engine

Wrote `src/assessment.py` with a deterministic rule engine (`deterministic_assessment`) covering: Canadian HQ/country + no parent → canadian/high; foreign parent/owner → foreign/high (with the parent's own country resolved via a second claims fetch); Canadian parent → canadian/high even if HQ record is thin; parent exists but its country unresolved → uncertain/medium; no country data at all → insufficient-data/low. `enrich_with_claude()` wraps the optional Anthropic call (lazy import, only attempted when `ANTHROPIC_API_KEY` is set) and always falls back to the deterministic text on any exception or missing key.

### [00:35 UTC] Build Phase — Storage, HTML report, CLI

Wrote `src/storage.py` (SQLite, auto-incrementing `version` per `company_name`, `list_latest()`/`get_history()`/`search()`). Wrote `src/html_report.py` rendering a self-contained dark-mode HTML index with client-side search/filter and a version-history `<details>` block per card; all dynamic text goes through an `html.escape()` helper, none through `innerHTML`-equivalent raw insertion. Wrote `src/main.py` argparse CLI wiring `add`/`show`/`list`/`search`/`export-html`, catching network/lookup failures without writing partial cards.

### [00:50 UTC] Tests Run

Tests: 27 passed, 0 failed. All Wikidata/Wikipedia/Anthropic calls mocked via `unittest.mock`; no live network calls in the suite.

### [00:55 UTC] Verify — Step 7 success criteria check

1. All tests pass (27, 0 failures) — met.
2. `add` produces a versioned card with real-API-shaped facts, confidence-rated verdict, and cited source URLs — met, verified via mocked end-to-end CLI test.
3. Re-running `add` on the same company creates version 2, `show` returns full history — met, covered by `test_storage.py`.
4. Deterministic path fully functional with zero API keys, Claude only improves the write-up — met, covered by `test_assessment.py` and `test_main_cli.py` (no `ANTHROPIC_API_KEY` in the build environment, so every manual CLI run in this session exercised the deterministic path for real).
5. `export-html` output is self-contained and escapes all dynamic text — met, verified by `test_html_report.py` including an explicit script-injection-attempt fixture.

Security checklist (STANDARDS.md):
- No `.env` files, no hardcoded credentials/secrets — confirmed.
- No `eval()`/`exec()` — confirmed.
- No raw HTML injection of dynamic text — `html.escape()` used throughout `html_report.py`.
- No `subprocess`/`os.system()` calls anywhere in this build.
- No file paths derived from user input (SQLite DB path and HTML output path are both fixed relative to the build folder / CLI-provided output filename used verbatim with `open()`, not concatenated into another path).
- All files confined to `builds/2026-07-20-canfile/`.

### [01:00 UTC] Docs

- `FutureFeatures.md`: 6 concrete enhancements.
- `Manual.md`: CLI usage, all commands, sample session, test command.

Build complete. Success criteria reviewed. All tests passing.
