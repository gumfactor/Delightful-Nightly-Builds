# Build Log — Impact Ledger

> **Date:** 2026-08-05
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:20 UTC] Session Start

- Checked `builds/` for an incomplete prior session: the most recent dated folder was `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed.
- Note: this branch's local `builds/index.md` was stale (last entry 2026-06-24), while the actual most recent build lives on the newest open PR branch. Resynced `builds/index.md` from `claude/cool-sagan-7kx1am` (PR #61, "Dockside," 2026-08-04) per Step 1's instructions before doing anything else — 54 total builds now visible, not 19.
- Read PROFILE.md, the resynced `builds/index.md`, and STANDARDS.md.
- Day of year 217 → category_index = (217-1) % 9 = 0 → Category A — Dashboard/Visualizer.
- Category A backlog: 3 pending rows after excluding one marked `skipped`. Only ID 3 has a numeric rating (4) → R=1 → lottery_chance = min(75, 25+1×2) = 27%. Rolled 100/100 → above threshold, so fresh idea generation.
- Generated 3 fresh Category A candidates (Impact Ledger, AI Model Release Radar, Canadian Sector Ownership Dashboard); picked Impact Ledger — an OpenAlex-backed personal citation/impact tracking dashboard. Full reasoning and alternatives in WhyThis.md.
- Build folder created: `builds/2026-08-05-impact-ledger/`

### [08:22 UTC] PRD Written

- Goal: track a researcher's own OpenAlex citation history over time and render a dashboard of trends, top papers, and "rising" papers with optional AI commentary.
- Scope: `search-author`/`sync`/`history`/`render` CLI commands, SQLite snapshot persistence, dark-mode HTML dashboard with Chart.js (graceful fallback), optional Claude Haiku commentary with deterministic fallback.
- Notable constraint: the OpenAlex author ID must always be user-supplied (via `search-author` disambiguation), never hardcoded — avoids embedding any real personal data (a name) in source. `OPENALEX_MAILTO`/`--mailto` is optional and never defaults to any real email address.

### [08:25 UTC] Build Phase — OpenAlex client and abstract reconstruction

- Implemented `src/openalex.py`: `search_authors()`, `get_author()`, `iter_author_works()` (cursor-paginated per OpenAlex's recommended pagination pattern), and `reconstruct_abstract()` from `abstract_inverted_index`.
- All HTTP calls funnel through one `_get_json()` helper using `urllib.request`, raising a single `OpenAlexError` on HTTP or network failure — no silent failures, no bare exceptions swallowed.

### [08:35 UTC] Build Phase — SQLite persistence and trend logic

- Implemented `src/db.py`: schema creation, `upsert_author()`, `upsert_work_snapshot()` (same-day re-sync overwrites via `INSERT ... ON CONFLICT(work_id, sync_date) DO UPDATE`, verified by test to never duplicate), `distinct_sync_dates()`, `citation_trend()` (citations summed per distinct date), and `rising_papers()` (velocity = latest minus previous distinct snapshot per work; correctly empty when a work has fewer than 2 snapshots, or when its citation count is unchanged/decreased).

### [08:45 UTC] Build Phase — AI commentary layer

- Implemented `src/ai.py`: `generate_note()` calls Claude Haiku via a direct `urllib` POST (the pattern already used by GrantScope, CanFile, Dockside, etc. in this catalog) only when `ANTHROPIC_API_KEY` is set; any exception (network, HTTP, malformed JSON, missing fields) falls back to a deterministic template. With no key, the function returns the template immediately — verified by a test that patches `urlopen` and asserts it is never called.

### [08:55 UTC] Build Phase — Dashboard renderer

- Implemented `src/dashboard.py`: all dynamic data (author stats, papers, trend, rising papers, AI notes) is serialized to JSON and embedded inside a `<script type="application/json">` block, with `</` sequences escaped to `<\/` to prevent premature closure of that script element. Client-side JS parses that JSON and builds every DOM node via `document.createElement`/`textContent` — never `innerHTML` from a data-derived string — so this protection holds even for a title containing raw markup. Chart.js 4.4.4 loads from a pinned CDN URL; if it's unavailable or fewer than 2 distinct sync dates exist, a plain DOM table renders instead.
- Found and fixed a JS syntax bug during writing: the Chart.js `options` key was accidentally written as `options {{}}` instead of `options: {{}}` inside the f-string template (both curly-brace-escaped for Python's `.format`-style substitution) — would have thrown a syntax error in the browser. Fixed before any test ran against it.

### [09:00 UTC] Build Phase — CLI

- Implemented `src/main.py` with `argparse` subcommands: `search-author QUERY`, `sync --author-id ID [--mailto EMAIL] [--sync-date DATE]`, `history --author-id ID`, `render --author-id ID [--out PATH] [--ai]`. Missing `--author-id` produces argparse's standard usage error (exit code 2) rather than a traceback.

### [09:10 UTC] Tests Written and Run

- Wrote 43 tests across `tests/test_openalex.py` (11), `tests/test_db.py` (11), `tests/test_ai.py` (6), `tests/test_dashboard.py` (8), `tests/test_cli.py` (7). All external HTTP (OpenAlex and Anthropic) is mocked via `unittest.mock.patch` on the `urlopen` call sites — no test makes a live network request.
- First run surfaced one failing test: `test_malicious_script_payload_in_title_is_neutralized` asserted exactly 3 `<script` substrings in the output, but the count was 4. Investigated: the escaping (`</` → `<\/`) is correct and sufficient — only `</script` sequences can prematurely close a `<script>` block; a bare `<script>` string embedded as inert JSON *text* inside an already-open script element poses no real risk. The test's assertion was the bug, not the code. Rewrote it to check the actual security property (the JSON still parses correctly and no unescaped `</script>` breaks out of the data block) instead of a naive substring count.
- Re-run after the test fix: 43 passed, 0 failed.

Tests: 43 passed, 0 failed.

### [09:20 UTC] Verify — Step 7

- Checked all 5 PRD success criteria — see final entry below.
- Ran the STANDARDS.md security checklist manually across all created files: no `.env` files, no hardcoded secrets/tokens/keys, no `eval()`/`exec()`, no `innerHTML` assignment from dynamic data anywhere in `dashboard.py`'s generated JS, no `os.system()`/`subprocess` calls at all, no user input used in file paths beyond the user-supplied `--out`/`--db-path` flags (which are standard CLI output-path arguments, not traversal of untrusted external input), no reads from paths outside the build folder.
- Manually verified live in headless Chromium (the system's globally installed Playwright, `NODE_PATH=/opt/node22/lib/node_modules`, `executablePath: /opt/pw-browsers/chromium`) against a fixture dashboard containing two separate injection payloads: a `</script><script>window.__pwned__=true;alert(1)</script>` payload in a paper title, and a `<img src=x onerror="window.__pwned2__=true">` payload in an AI note. Result: zero dialogs, zero page errors, neither `window.__pwned__` nor `window.__pwned2__` was ever set, and the malicious title rendered as literal escaped text in the table cell (confirmed via `textContent`).
- Also verified live: with 2 synced dates but the Chart.js CDN unreachable (as it genuinely is in this sandboxed environment), the trend section correctly fell back to a plain DOM table showing the right dates/totals (`2026-08-01 → 20`, `2026-08-05 → 25`); the search box correctly filtered the paper table to 1 row on a matching query; clicking the "Citations" column header correctly re-sorted the table.

### [09:30 UTC] Documentation

- `FutureFeatures.md`: 8 concrete suggestions (3 quick wins, 3 medium-effort, 2 ambitious extensions) plus integration points and known limitations.
- `Manual.md`: quick start, full command reference, configuration table, troubleshooting table, known limitations.

### [09:35 UTC] Housekeeping

- `builds/ideas.md` backlog ID 5 ("GitHub Repository Health Scorecard") is a verbatim duplicate of the already-built 2026-06-21 build; it has now been drawn and overridden to fresh generation twice (SiliconWatch, 2026-07-27, and tonight). Marked it `skipped` with a rating note so it stops consuming Category A lottery draws in future sessions. Appended the 2 non-winning fresh ideas generated tonight (IDs 13–14) as new pending rows.

Build complete. Success criteria reviewed. All tests passing.
