# Build Log — Ledger Lens

> **Date:** 2026-07-08
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:08 UTC] Session Start

- Checked `builds/` locally for an incomplete build (Step 0): most recent local dated folder was `2026-06-18-regex-dojo`, whose BUILD_LOG.md ends with "Build complete. Success criteria reviewed." — done, nothing to resume. Local `main`/session branch is weeks behind, as CLAUDE.md warns it can be, so this was cross-checked against the most recent open PR branch (`claude/cool-sagan-lonk43`, 2026-07-07 "Schema Sentinel") — its BUILD_LOG.md also ends with the completion line. No interrupted build exists anywhere reachable.
- Read PROFILE.md, then resynced `builds/index.md` and `builds/ideas.md` from `origin/claude/cool-sagan-lonk43` (catalog current through 2026-07-07, 31 total builds) and read STANDARDS.md.
- Day of year 189 → `category_index = (189-1) % 9 = 8` → Category I — Life Admin Helper.
- `builds/ideas.md` backlog has zero pending rows tagged Category I → lottery pool empty → fresh idea generation (no draw roll).
- Decided to build: Ledger Lens — CSV-import spending categorizer + budget dashboard. Full reasoning in WhyThis.md.
- Confirmed `ANTHROPIC_API_KEY` is not set in this session's environment (consistent with several recent builds) — AI enrichment/insights must be built with the deterministic fallback as the actually-exercised path, matching precedent (Schema Sentinel, PubMed Radar, BIDS validator).
- Build folder created: `builds/2026-07-08-ledger-lens/`

### [08:13 UTC] PRD Written

- Goal: turn a bank CSV export into a categorized, budget-aware, dark-mode HTML spending dashboard.
- Scope: column auto-detection (incl. split Debit/Credit), rule-based + optional Claude categorization with digit-sequence redaction, recurring-charge detection, monthly aggregation, optional budget comparison, three output modes (terminal/JSON/HTML), cleaned CSV export, bundled synthetic demo data.
- Notable constraint: STANDARDS.md hard-requires a visual/interactive interface for Category I builds — a stdout-only CLI would not satisfy this, so the HTML dashboard is a required deliverable, not a bonus, mirroring the Qualtrics/Schema Sentinel/PubMed Radar precedent of "Python CLI that renders a self-contained HTML report."

### [08:20 UTC] Build Phase — Parsing & Categorization

Building `src/parser.py` (column auto-detection, multi-format date parsing, Debit/Credit column support) and `src/categorize.py` + `src/ai_client.py` (keyword rules across 14 categories; optional Claude Haiku enrichment via raw `urllib.request` — no SDK dependency, matching the stdlib-only pattern used by recent builds — with digit-sequence redaction applied to any description before it would be sent, and a deterministic fallback whenever no key is set or the call fails).

### [08:35 UTC] Build Phase — Analysis, HTML dashboard, CLI

Built `src/analyze.py` (monthly/category aggregation, merchant-normalized recurring detection with amount clustering to handle price changes, budget comparison, deterministic insights template), `src/report_html.py` (dark-mode dashboard: hero stats, Chart.js donut + trend line, recurring list, budget bars, sortable/searchable transaction table, data embedded as JSON in a `<script>` tag), `src/report_terminal.py`, and `src/main.py` (argparse CLI wiring `analyze` with `--budgets`/`--html`/`--json`/`--out-csv`/`--invert-sign`/`--no-ai`). Added a synthetic two-month `sample_transactions.csv` (invented data, no real personal information) so the tool works immediately without the user's own export.

### [Tests] Step 6 — Test run

First run: 33 collected, 2 collection errors — an f-string in `report_html.py` used a backslash-escaped quote inside the expression part, which is a `SyntaxError` in Python <3.12. Fixed by hoisting the recurring-badge HTML fragment into a plain variable before the f-string.

Second run: 48 passed, 0 failed.

Manually smoke-tested the actual CLI (not just pytest) against the bundled sample CSV in both terminal and `--html` modes, and rendered the generated HTML in the pre-installed headless Chromium via Playwright to visually confirm the dashboard. The two Chart.js canvases rendered blank — this session's network egress blocks the Chart.js CDN request (`ERR_TUNNEL_CONNECTION_FAILED`), and the resulting `Chart is not defined` error was throwing inside the single inline `<script>` block, silently aborting the search/sort code that came after it (confirmed live: filtering "netflix" left all 40 rows visible instead of 2). Fixed by guarding both `new Chart(...)` calls behind `typeof Chart === 'undefined'`, with a plain-text fallback message replacing each canvas when the library isn't available — search and sort now work regardless of CDN reachability. Added `test_report_html.py::test_html_guards_chart_calls_against_missing_chartjs` as a regression test, and re-verified live in the browser (search now correctly narrows to 2 rows; no console `pageerror`). This only matters for this sandboxed session's restricted egress — a normal user's browser will load the CDN fine and both charts will render — but the defensive fix costs nothing and makes the report correct either way.

Final run after the fix: 49 passed, 0 failed.

Tests: 49 passed, 0 failed.

### [Verify] Step 7 — Success criteria check

1. All tests pass (zero failures) — confirmed above, 49/49.
2. Ran `python3 src/main.py analyze sample_transactions.csv --budgets budgets.example.json` (terminal) and `--html /tmp/ledger_lens_demo.html --out-csv /tmp/ledger_lens_cleaned.csv` — both produced correct, complete output. The HTML was rendered in a real headless browser (Playwright + Chromium) and visually inspected via screenshot: hero stats, recurring-charges list, budget bars, and the full sortable/searchable transaction table all render correctly and match the terminal numbers exactly ($8400 income / $6726.62 expenses / $1673.38 net across 40 transactions).
3. Every transaction in `sample_transactions.csv` receives a category from the fixed 14-category list — verified by `test_cli.py::test_cli_html_output_categorizes_all_transactions` and confirmed in the live HTML (every row has a category badge, none blank).
4. Recurring charges seeded in the sample data (rent, golf membership, Netflix, Spotify, GitHub, each appearing in both May and June at a stable amount) are correctly flagged in both `test_analyze.py::test_recurring_detection_flags_repeated_merchant` and the live terminal/HTML run — all 5 appear with correct monthly averages and occurrence counts.
5. The full run completes with no `ANTHROPIC_API_KEY` set (this session's actual state) using the deterministic fallback for both categorization and insights — confirmed live; no network call was attempted in that path, and the terminal/HTML insights paragraph is the template-generated one, not an AI response.

Security checklist (STANDARDS.md):
- No `.env` files committed
- No hardcoded credentials/API keys/secrets in source
- No real personal data — `sample_transactions.csv` is synthetic, invented merchant/amount data
- No `eval()`/`exec()` on user-controlled input
- No `innerHTML`-from-user-data XSS vector — transaction descriptions are HTML-escaped before embedding in the report
- No `os.system()`/`subprocess` with user-controlled arguments
- No file-path traversal — input path is read directly via the standard library, never interpolated into a shell command
- All files confined to `builds/2026-07-08-ledger-lens/`

### [Docs] Step 8 — Documentation complete

- FutureFeatures.md: 7 concrete suggestions across quick wins, medium effort, and ambitious extensions
- Manual.md: quick start, full usage guide, configuration table, troubleshooting, known limitations

Build complete. Success criteria reviewed. All tests passing.
