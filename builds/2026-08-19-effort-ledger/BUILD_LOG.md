# Build Log — Effort Ledger

> **Date:** 2026-08-19
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [Session Start]

- Read CLAUDE.md, PROFILE.md, STANDARDS.md
- Checked Step 0: this session's branch (`claude/cool-sagan-5l8qen`) had no PR and was a pure ancestor of `origin/main` with no unmerged commits of its own — fast-forwarded it to latest `main` (no destructive reset needed, `git merge --ff-only` was already up to date) rather than resuming any interrupted build
- Discovered `main` on this repo is far behind reality (last real commit predates 2026-06-19) because every nightly build to date has shipped as its own still-open PR rather than being merged — pulled the current `builds/index.md` and `builds/ideas.md` from the most recently created open PR (#75, `claude/cool-sagan-mrjx2x`, 2026-08-18 "Voxel Lab") via the GitHub API per CLAUDE.md's resync instructions
- Day of year 231 → category index `(231-1)%9 = 5` → **F — Data Explorer**
- Last 7 builds: H, I, A, B, C, D, E — no repeat risk, category F last appeared 2026-08-10 (Ingest Gate), 9 nights ago
- Category F pending backlog: idea #1 (rating 7, 7 tickets) and idea #10 (unrated, 5 tickets) → R=1, lottery_chance=27%. Roll 8 (≤27) triggered a draw; weighted pick (roll 5 of 12) selected idea #1
- Idea #1 ("Canada List CSV Quality Inspector") turned out to be a near-verbatim duplicate of the already-built Ingest Gate (2026-08-10) — marked `skipped` in `builds/ideas.md` with a note explaining the supersession instead of building a duplicate, and moved to fresh-idea generation for Category F (full reasoning in WhyThis.md)
- Generated 3 fresh Category F ideas, selected **Effort Ledger** (grant budget + cross-grant effort-overcommitment auditor); appended the 2 non-winning ideas (#20 Manuscript Citation Cross-Checker, #21 StatsCan Canadian Business Data Explorer) to `builds/ideas.md`
- Decided to build: Effort Ledger
- Build folder created: `builds/2026-08-19-effort-ledger/`

### [PRD Written]

- Goal: audit a research budget CSV and an effort-commitment CSV for indirect-cost math errors and cross-grant effort overcommitment, render as an HTML dashboard
- Scope: MTDC/indirect-cost cross-check with configurable exempt categories and subcontract threshold, missing-fringe/zero-cost/duplicate-line/unknown-category checks, interval-sweep effort-overcommitment detection across overlapping grant periods, grant-name-mismatch/orphan-grant checks, HTML dashboard + terminal summary + annotated CSV exports, optional aggregate-only Claude Haiku narrative with deterministic fallback
- Notable decisions: no hardcoded agency-specific numeric caps (e.g. NIH's salary cap) since those change yearly and would go stale — `--far-rate` has no default and must be supplied explicitly; the $25,000 subcontract-exemption convention is documented as a configurable default to verify, not asserted as a fixed rule

### [Build Phase — Core Logic]

- Implemented `src/models.py` (dataclasses: `BudgetLine`, `EffortLine`, `Flag`, `GrantBudgetSummary`, `OvercommitmentWindow`, `Severity` enum)
- Implemented `src/loader.py`: CSV readers that convert per-row malformed data (bad date, non-numeric cost/percent, missing columns) into `Flag` objects rather than raising, so one bad row never kills the run
- Implemented `src/budget_audit.py`: MTDC computation grouped by `(grant_id, fiscal_year)`, subcontract partial-exemption logic, indirect-cost cross-check against tolerance, missing-fringe/zero-cost/duplicate/unknown-category checks
- Implemented `src/effort_audit.py`: per-line validation plus a date-sweep algorithm per person — builds `+percent`/`-percent` events at `period_start`/`period_end + 1 day`, groups same-date events before evaluating, and walks the sorted event dates tracking a running total and the set of currently-active grants, opening/closing an `OvercommitmentWindow` whenever the running total exceeds the cap. Verified by hand against several overlap shapes before writing tests (exact-cap not flagged, partial overlap flags only the true overlap sub-window, touching-not-overlapping periods correctly net to no double-count since same-day + and − events are summed before evaluation)
- Implemented `src/ai_narrative.py`: builds an aggregate-only summary dict (counts only — no names, dollar figures, or grant IDs), calls Claude Haiku via `urllib.request` when `ANTHROPIC_API_KEY` is set and `--ai` passed, unconditional deterministic-template fallback on any missing key, network error, or malformed response
- Implemented `src/report.py`: renders a self-contained dark-mode HTML dashboard; all dynamic data is JSON-serialized into a `<script type="application/json" id="audit-data">` tag (never string-interpolated into an executable `<script>` block) and read client-side with `JSON.parse`; all DOM insertion uses `createElement`/`textContent`, never `innerHTML`, on data-derived strings
- Implemented `src/main.py`: argparse CLI wiring load → audit → report → terminal summary → CSV export
- Wrote `sample_data/budget.csv` and `sample_data/effort.csv` — a realistic 3-grant, 3-person example seeded with deliberate issues (a wrong indirect line, a missing fringe line, an overlapping-effort overcommitment) so the sample run demonstrates every flag type

### [Tests Written]

- `tests/test_loader.py`, `tests/test_budget_audit.py`, `tests/test_effort_audit.py`, `tests/test_ai_narrative.py`, `tests/test_report.py`, `tests/test_main.py` — covering the happy path, the MTDC/subcontract-threshold math, every flag type, the overlap-window edge cases described in the PRD's Testing Strategy (exact-cap, touching-not-overlapping, partial overlap, nested periods, single-line >100%), the AI narrative's mocked/fallback paths and its privacy-safe payload, an HTML-injection payload check on the rendered report, and a CLI-level regression test for a row-numbering bug (below)

### [Tests Run — First Pass]

Tests: 43 passed, 0 failed. All 43 passed on the first full run; the hand-derived expected overlap windows in `test_effort_audit.py` matched the sweep-line algorithm's actual output exactly.

### [Manual Verification — Bug Found and Fixed]

- Ran `python3 src/main.py --budget sample_data/budget.csv --effort sample_data/effort.csv --far-rate 0.55 --output /tmp/report.html --ai` with no `ANTHROPIC_API_KEY` set. Terminal summary and AI-fallback narrative were correct, but inspecting the generated `effort_flagged.csv` by eye caught a real bug the 43 passing tests had missed: M. Chen's effort row (row 7 of `effort.csv`) was annotated with `subcontract_threshold_applied` — a budget-only flag code that has nothing to do with effort data. Root cause: `budget.csv` and `effort.csv` both start their own row numbering at row 2, and `main.py`'s CLI wiring built one `row_number -> flag codes` map from the *merged* flag list and reused it for both CSV writers, so a flag on budget row 7 leaked onto effort row 7 whenever both files happened to have a flagged/matching row number.
- Fixed by keeping `budget_flags` and `effort_flags` as separate lists throughout `run_audit`/`main` and passing only the file-appropriate list to each annotated-CSV writer (`src/main.py`). Added `tests/test_main.py::test_annotated_csvs_do_not_cross_contaminate_row_numbers`, a CLI-level regression test with a budget row 7 and an unrelated effort row 7, asserting each file's flags stay scoped to its own file.
- Re-ran the CLI end-to-end: `effort_flagged.csv` row 7 (M. Chen) now has an empty `Flags` column as expected; `budget_flagged.csv` row 7 (the Subcontract line) correctly keeps `subcontract_threshold_applied`.

### [Tests Run — Final]

Tests: 44 passed, 0 failed (`python -m pytest tests/ -v`).

### [Manual Verification — Live Browser]

- Used the pre-installed system Chromium (via Node's `playwright` package, `executablePath: /opt/pw-browsers/chromium`) to load the generated `report.html` headlessly and exercise it: 6 hero-stat cards, 3 budget rows, 7 flag rows, and the timeline `<canvas>` all rendered; clicking a budget column header re-sorted the table (verified lowest-total grant sorted first ascending); typing "overcommitment" into the flags search correctly filtered to 2 rows; toggling the "info" severity chip off correctly dropped the flag count from 7 to 4 (the 3 info-severity flags). Zero page errors, zero console errors, zero dialogs.
- Regenerated the report with a `</script><script>...</script><img src=x onerror=...>` payload injected into every text field (person name, grant name, grant ID, AI briefing) and reloaded it in the same headless Chromium harness: zero of the injected `window.__xss_fired` globals were ever set, the payload appeared as inert literal text in both the budget and flags tables, and `document.querySelectorAll('body script').length` was exactly 2 — the one legitimate JSON-data `<script>` tag and the one legitimate app-logic `<script>` tag, confirming the payload's embedded `</script>` sequences never prematurely closed the real script blocks. This confirmed the `<` → `<` escaping added to `src/report.py` (`json.dumps(...).replace("<", "\\u003c")`) actually holds under a real HTML parser, not just the unit-test string check.

### [Documentation]

- Wrote `FutureFeatures.md` (5+ concrete suggestions), `Manual.md` (quick start, configuration table, troubleshooting, known limitations)

### [Final]

Build complete. Success criteria reviewed. All tests passing.
