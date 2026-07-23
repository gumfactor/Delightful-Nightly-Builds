# Build Log — Canada List CSV Quality Inspector

### [Step 0] Resume check
No incomplete build found. Most recent local/branch build (2026-06-18 Regex Dojo locally; 2026-07-22 Bayes Lab on the most recent open PR branch `claude/cool-sagan-psb5dt`) both end with "Build complete. Success criteria reviewed." — nothing to resume. Starting fresh for 2026-07-23.

### [Step 1] Orient
Read CLAUDE.md, PROFILE.md, STANDARDS.md. Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-psb5dt`, PR #49, 2026-07-22) since local `main`/current branch only has 5 build folders through 2026-06-18 and is far behind — 30 nightly builds have shipped as unmerged open PRs since. Read the resynced index (42 total builds logged, last build 2026-07-22 Bayes Lab) and ideas backlog (37 entries) before deciding.

### [Step 2] Decide
- Day of year for 2026-07-23 = 204. `category_index = (204-1) % 9 = 5` → **F — Data Explorer**.
- Filtered `builds/ideas.md` for pending Category F rows: 4 matches (#1 CSV Quality Inspector, rating 7; #10 SEC EDGAR Financial History Extractor; #19 ClinicalTrials.gov Explorer; #20 Citation & Publication Landscape Explorer).
- R (count with numeric rating) = 1. `lottery_chance = min(75, 25 + 1*2) = 27%`.
- Rolled random 1–100 via `python3 -c "import random; print(random.randint(1,100))"` → **86**. 86 > 27 → lottery did not fire, proceeded to fresh-idea generation (Step 2d).
- Topic diversity check on last 10 builds (2026-07-13 → 2026-07-22): neuroscience circuits/teaching (CircuitLab, Bridgework), grant funding (GrantScope), research-methods literacy (Confound Hunter), dev tooling (AgentLint), life admin (Deadline Guardian), Canadian economics/ownership (CanEcon Pulse, CanFile), ethics protocol (Protocol Forge), Bayesian stats (Bayes Lab). No domain saturated 3+ times; investment/finance absent entirely from the last 10.
- Generated 3 fresh candidates for Category F (see WhyThis.md for full reasoning): (A) Canada List CSV Quality Inspector — rule-engine QC report + cleaned CSV for business-directory CSV ingestion, redesigned from backlog #1 as a Python/HTML report rather than a browser+Playwright tool; (B) ClinicalTrials.gov Explorer (backlog #19); (C) SEC EDGAR Financial History Extractor (backlog #10).
- Selected (A) — see WhyThis.md for the full comparison. Marked backlog #1 `built` in `builds/ideas.md`; appended (B) and (C) as new non-winning rows (fresh path); no Idea Brief exists for #1, so none to read.

### [Step 3] Build folder created
`builds/2026-07-23-canada-list-csv-quality-inspector/` with `tests/` and `src/` subfolders.

### [Step 4/5] Build
Wrote `src/schema.py` (canonical province/ownership data, name normalization), `src/qc_engine.py` (structural/required-field/format/encoding checks), `src/duplicates.py` (exact + near-duplicate clustering via union-find), `src/ai_enrichment.py` (optional Claude Haiku enrichment over `urllib`, deterministic fallback), `src/report_html.py` (self-contained dark-mode HTML dashboard), `src/main.py` (CLI orchestrator).

**Bug caught and fixed during self-review, before any test was written against it:** the HTML report embeds row data as JSON inside a `<script type="application/json">` tag. A field value containing the literal substring `</script` (e.g. a business name used as an XSS test payload) would terminate that script tag early in the browser's HTML parser, regardless of being inside a JSON string — a real injection vector. Fixed by escaping every `</` to `<\/` in the embedded JSON before writing the template (`report_html.py`). Verified live in headless Chromium below.

**Design fix during build:** initially, duplicate-cluster membership was tracked only in the separate `duplicate_clusters` report section, not folded into each row's own `QC_Flags`/`Recommended_Action`. That meant the cleaned CSV — the artifact meant to drive real ingestion decisions — wouldn't show anything about duplicates at the row level. Added `_apply_duplicate_flags()` in `main.py` so every row in a duplicate cluster gets a `warning`-severity flag (`exact_duplicate` / `near_duplicate`), surfacing as `review` in `Recommended_Action`. Deliberately `warning`, not `error`/auto-drop: apparent duplicates (e.g. two locations of the same franchise) can be legitimate distinct entries, so a human should confirm before removal.

Built a synthetic `tests/fixtures/sample_directory.csv` (15 rows, fabricated business names) seeding one instance of every issue type: missing required field, ragged row, invalid province, invalid website, out-of-range ownership percentage, non-numeric ownership percentage, unmapped ownership status, invalid email, one exact-duplicate pair, one near-duplicate pair (legal-suffix-stripped name match + same province), and one row with a `<script>` tag in the business name for XSS verification. No real personal or business data used anywhere.

### [Test] Step 6 — Test run
Installed `pytest` (not preinstalled in this container). Ran `python -m pytest tests/ -v`.

[UTC] Tests: 66 passed, 0 failed.

### [Verify] Step 7 — Live browser verification
Ran the CLI end-to-end against the fixture (`python -m src.main tests/fixtures/sample_directory.csv --out-dir ...`) and loaded the generated `report.html` in headless Chromium (pre-installed at `/opt/pw-browsers/chromium`) via Playwright:
- Stat tiles read 15/5/7/3/2, matching the pipeline's own computed summary exactly.
- All 15 rows rendered in the table; search filter ("Silver Creek" → 2 rows) and the drop-only filter (→ 5 rows) both worked; column sort by `business_name` correctly put the row with an empty name first.
- 2 duplicate-cluster cards rendered (the exact pair and the near-duplicate pair).
- The Chart.js CDN was blocked by this container's egress proxy (`net::ERR_TUNNEL_CONNECTION_FAILED`, expected per CLAUDE.md's network-policy note) — the text-table fallback engaged correctly: canvas `display:none`, fallback table `display:block` with 11 issue-type rows, zero page errors.
- The `<script>alert(1)</script>` business name rendered as inert visible text in the row table; zero `dialog` events (no `alert()` fired), zero `pageerror` events, and the string `<script>alert(1)</script>` does not appear as a live tag anywhere in the rendered DOM — confirming the `</script` escaping fix works against a real hostile payload, not just the unit test's string assertions.

Security checklist (STANDARDS.md) run against every file created tonight:
- No `.env` files
- No hardcoded credentials/API keys (Anthropic key is read from `os.environ` only, never a literal)
- No real personal data — fixture CSV uses fabricated business names
- No `eval()`/`exec()` anywhere
- No `innerHTML` assignment from user-controlled data — the HTML report builds all row/cluster DOM via `createElement`/`textContent`; the only `innerHTML` use is `body.innerHTML = ''` to clear the table (a literal empty string, not user data)
- No `os.system()`/`subprocess` calls anywhere in the build
- No file-path traversal — `input_csv`/`--schema`/`--out-dir` are user-supplied CLI args used directly with `pathlib.Path`/`argparse`, the same pattern as every prior CLI build in this catalog; this is a local tool operated by the user on their own filesystem, not a server accepting untrusted input
- No reads from paths outside the build's own folder at build/dev time (the CLI's runtime file arguments are the tool's entire purpose, exactly like every other CLI build in this catalog)

All 5 PRD success criteria met (see PRD.md).

Also fixed a docs bug caught during this verification pass: `python src/main.py ...` fails with `ModuleNotFoundError: No module named 'src'` because Python only puts the script's own directory on `sys.path`, not its parent, so the `from src import ...` package-relative imports in `main.py` can't resolve. Corrected the documented invocation (in `main.py`'s docstring and `PRD.md`) to `python -m src.main ...`, run from the build folder root — verified this works and reproduces the exact same 15/5/7/3/2 row-count distribution as the pytest suite.

Ran an additional manual end-to-end smoke test (not part of the pytest suite, run directly to sanity-check the wiring) with a mocked Claude response standing in for a real `ANTHROPIC_API_KEY`: the exact-duplicate cluster correctly skips the AI call (no judgment needed for byte-identical rows), the near-duplicate cluster gets `ai_confirmed=True` with the mocked reasoning attached, and row 8's unmapped `ownership_status` gets an AI-suggested canonical mapping appended to its flag message. Confirms the full AI-enrichment wiring (not just the isolated unit-level mocks in `test_ai_enrichment.py`) is correct end-to-end.

Build complete. Success criteria reviewed. All tests passing.
