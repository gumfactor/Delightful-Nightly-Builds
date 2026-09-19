# Build Log — Grant Horizon

> **Date:** 2026-09-19
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [Session Start]

- Step 0: checked `builds/` for incomplete builds. Most recent dated folder was `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — done, nothing to resume. (Note: the local working tree was several months stale relative to `main`/open PR branches; the `2026-06-19` onward builds exist only on the remote, not in this local checkout, but none of them show an incomplete state either — the most recent remote build, `2026-09-18` Eligible Spend, is `complete` per `builds/index.md`.)
- Read PROFILE.md, STANDARDS.md, `builds/index.md`.
- Resynced `builds/index.md` and `builds/ideas.md` from the most recently opened PR branch (`claude/cool-sagan-wdz89b`, PR #102, 2026-09-18) per Step 1/Step 9's instructions — the local `main`-based copies were significantly behind (missing ~60 rows and several backlog corrections that only ever landed on unmerged branches).
- Day of year 262 → category_index = 0 → Category A — Dashboard / Visualizer.
- Category A backlog lottery: 4 pending rows, R=1, lottery_chance=27%, rolled 90 → fresh generation (see `WhyThis.md`).
- Decided to build: Grant Horizon — NIH RePORTER live funding-landscape dashboard for the lab's named research subfields.
- Build folder created: `builds/2026-09-19-grant-horizon/`.

### [PRD Written]

- Goal: sync live NIH RePORTER funding-award data for configured research topics into local SQLite, render a dashboard with funding trends, top institutions, and agency mix.
- Scope: `sync` + `report` CLI, deterministic aggregation layer, dashboard with Chart.js + DOM-table fallback, optional `--ai` briefing with PI names deliberately excluded from the AI prompt, CSV export.
- Notable constraint: direct connectivity check to `api.reporter.nih.gov` was denied by this session's sandboxed network policy before any code was written, consistent with this repo's documented build-container egress restriction. The HTTP transport is isolated behind one injectable function; every other layer is tested against fixture JSON shaped to the documented v2 API schema. A `sample_output/` folder (built from the same fixture, not a live sync) ships so the user can see real rendered output before running their own live sync. This mirrors the precedent set by Dominion Index (2026-09-10) and Preprint Pulse (2026-09-13) for the same constraint.

### [Build Phase 1 — Core modules]

Building `src/slug.py`, `src/reporter_client.py`, `src/storage.py`, `src/aggregate.py` first (pure/testable, no I/O side effects beyond the injected transport and SQLite path).

### [Build Phase 2 — Briefing + rendering]

Building `src/briefing.py` (AI + deterministic fallback) and `src/render.py` (HTML dashboard + CSV export), then `src/main.py` wiring the CLI.

Wrote 57 tests across `tests/test_slug.py` (5), `tests/test_reporter_client.py` (10), `tests/test_storage.py` (5), `tests/test_aggregate.py` (10, hand-computed fixture — see comments in the file for the worked totals), `tests/test_briefing.py` (8), `tests/test_render.py` (10), `tests/test_main.py` (9).

First `pytest` run caught one real bug in the test suite itself, not the code: `test_build_dashboard_data_top_institutions_ranked` asserted "Inst A" ranks first, but the hand-computed fixture actually gives Inst B $200k (one project) vs. Inst A's $150k ($100k + $50k across two projects) — the code's ranking was correct; the test's expected value was wrong. Fixed the test assertion, not the code, after re-deriving the totals by hand.

`python3 -m pyflakes src/*.py tests/*.py` caught two unused imports (`aggregate` in `src/main.py` — aggregation is only used indirectly via `render.build_dashboard_data`; `pytest` in `tests/test_briefing.py` — no `pytest.raises` used in that file). Removed both.

### [Tests Run]

Tests: 57 passed, 0 failed. (`python -m pytest tests/ -v`, from the build folder root)

### [Verify]

Manually verified beyond pytest, using the pre-installed headless Chromium via Playwright (`NODE_PATH=/opt/node22/lib/node_modules node ...`, `executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'`):

- Generated `sample_output/` from a 47-project synthetic fixture (`random.seed(19)`, 5 topics, realistic institutions/PIs/award amounts) since this build container's egress proxy denies a direct connection to `api.reporter.nih.gov` (confirmed via a denied connectivity check before any code was written).
- Loaded `sample_output/dashboard.html`: hero stats matched the fixture's true totals exactly ($17,878,546.71 across 47 projects, 5 topics); zero console errors beyond the Chart.js CDN request being genuinely blocked by this container's network policy, with the DOM-table fallback rendering correctly in its place (29 fallback trend rows, top-institutions fallback table populated); search ("psychopathy" → 11 matching rows) and column-sort (click "Award" → highest award first, $165,529) both work; zero horizontal overflow at a 375px mobile viewport.
- Ran a dedicated hostile-payload fixture (`</script><script>window.__xss=true;</script><img src=x onerror=...>` injected into a project title, institution name, PI name, and the AI briefing text simultaneously): zero dialogs, zero page errors, zero injected `window.__xss*` globals of any kind, exactly the page's own 3 `<script>` tags present, zero injected `<img>` nodes, and the hostile title rendered back as literal inert text in the project table.
- Ran the actual CLI end-to-end (not just the library functions) — `main.run_sync` then `main.run_report` against a mocked transport — confirming `sync`'s upsert count, `report`'s terminal summary numbers, and both output files being written to the requested directory.
- Security checklist from `STANDARDS.md`: no `eval`/`exec`, no `innerHTML` assignment anywhere in `src/`, no `os.system`/`subprocess` calls, no hardcoded credentials or real personal data, no `.env` files, no file paths reaching outside the build folder. Confirmed by direct grep of `src/` and `tests/`.

Success criteria from `PRD.md`, checked individually:
1. All tests pass (57/57, zero failures) — done.
2. `sync` normalizes and upserts fixture-shaped records with correct dedup on re-run — covered by `test_storage.py::test_upsert_dedupes_on_topic_and_project_num` and the live CLI smoke test above (mocked transport, real `main.run_sync`).
3. `report`'s dashboard hero stats, per-topic totals, and top-institution ranking exactly match a hand-computed fixture — covered by `test_render.py` and independently re-verified in-browser against the 47-project sample (hero total $17,878,546.71 matched the Python-side computed total exactly).
4. Dashboard is safe against a hostile project title/institution name — verified in-browser as above (zero dialogs/errors/injected globals/injected DOM nodes).
5. `report --ai` with no `ANTHROPIC_API_KEY` makes zero network calls and still produces a complete briefing — covered by `test_briefing.py::test_generate_briefing_with_no_api_key_makes_zero_network_calls` (`urllib.request.urlopen` monkeypatched to raise `AssertionError` if ever invoked).

All 5 criteria met. No scope reductions were needed.

### [Docs]

- `FutureFeatures.md`: 8 concrete suggestions (3 quick wins, 2 medium-effort, 3 ambitious), plus integration points naming Throughline, Eligible Spend, and Preprint Pulse by name, and a known-limitations table.
- `Manual.md`: quick start, topic/fiscal-year configuration, dashboard section guide, CSV export, configuration table, troubleshooting table, known limitations (including the documented multi-PI award-attribution simplification).
- `sample_output/README.md`: explains the synthetic-fixture origin of the sample, why (build-container network policy), how it was generated, and everything verified against it beyond pytest.

Build complete. Success criteria reviewed. All tests passing.

### [Post-PR: Codex review — 3 findings addressed]

PR #103 drew an automated Codex review with 3 findings, all verified as real bugs (not nitpicks) and fixed:

1. **P1 — `report` didn't actually restrict to the requested scope.** `run_report` called `storage.all_projects(conn)` unconditionally, so a `report --topics ... --fy-start ... --fy-end ...` narrower than a prior, broader `sync` still pulled in every stored row — the dashboard labeled itself with the requested range but the hero stats, tables, and CSV export silently included out-of-scope data. Fixed by adding `storage.filtered_projects(conn, topics, fy_start, fy_end)` and using it in `run_report` instead. Covered by 3 new `test_storage.py` tests and a new end-to-end `test_main.py` test that syncs mixed-scope rows into a real SQLite file and asserts the dashboard's embedded JSON only reflects the in-scope one.

2. **P1 — cross-topic totals double-counted awards matching more than one topic.** Storage is correctly keyed on `(topic, project_num)` so one real award matching two configured topics (e.g. a grant touching both "empathy neuroscience" and "affective neuroscience") is stored as two rows — right for each topic's own total, wrong for the hero total, top-institutions, and agency-breakdown numbers, which summed both rows as if they were two different awards. Fixed with a new `aggregate.dedupe_by_project()` (keeps first-seen row per `project_num`), applied to hero/top_institutions/agency_breakdown in `render.build_dashboard_data` but deliberately NOT to the per-topic panels (already inherently unique per topic) or the project table/CSV (each topic-match row is informative on its own — documented inline so the table's row count legitimately exceeding `hero.total_projects` doesn't look like a new bug later). Covered by 2 new `test_aggregate.py` tests and 1 new `test_render.py` integration test.

3. **P2 — a resync never removed rows NIH stopped returning.** `sync` only ever upserted; if a project was corrected, withdrawn, or no longer matched a topic's search, its old row lingered in every future `report` forever. Fixed by adding `storage.reconcile_topic(conn, topic, fiscal_years, seen_project_nums)` (deletes any row for that topic/fiscal-year range not present in the latest fetch) and calling it after every topic's upsert in `run_sync`. Covered by 4 new `test_storage.py` tests plus a manual two-sync CLI run (mocked transport: first sync returns a project, second sync returns none for that topic) confirming the stale row is actually gone from the database afterward, not just from a single in-memory result.

All fixes are additive/corrective only — no scope was removed. Test count: 57 → 68, all passing (`python -m pytest tests/ -v`). `sample_output/` was regenerated from the same synthetic fixture (its numbers were unaffected, since that fixture has no cross-topic duplicate `project_num`s — confirms the fix doesn't change the common case). Re-ran `pyflakes src/*.py tests/*.py` — clean.
