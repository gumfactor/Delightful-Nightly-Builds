# Build Log — Parity

> **Date:** 2026-09-27
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md, and the most current `builds/index.md` (resynced from open PR #110 / branch `claude/cool-sagan-i9brm2`, the most recently created open PR, since `main`'s copy lags).
- Step 0 check: most recent dated build folder locally is `2026-06-18-regex-dojo`; its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed.
- Day of year 270 → `category_index = (270-1) % 9 = 8` → Category I — Life Admin Helper.
- `builds/ideas.md` has zero `pending` rows tagged Category I → lottery skipped per Step 2c, went straight to fresh idea generation (Step 2d).
- Scanned last 10 builds for topic saturation: grant/finance-adjacent themes (Corporate Ownership Chain Explorer, Grant Horizon, Eligible Spend) appeared 3 times — ruled out another finance/grant build tonight.
- Grepped `builds/index.md` and `builds/ideas.md` for "Teamwork"/"Coda" — never integrated as a live API in 110 prior builds, despite both being named explicitly in PROFILE.md's friction points and Data Sources. Chose this gap over two other fresh candidates (see WhyThis.md).
- Decided to build: **Parity** — a read-only Teamwork.com ↔ Coda task/item reconciliation and drift dashboard.
- Build folder created: `builds/2026-09-27-parity/`

### [08:20 UTC] PRD Written

- Goal: cross-reference live Teamwork tasks against a live Coda table, bucket every item into matched/conflict/teamwork-only/coda-only, and track that gap over repeated syncs.
- Scope: two stdlib HTTP clients (Basic auth for Teamwork, Bearer for Coda), a pure Jaccard-similarity greedy matcher, SQLite persistence for drift history, a CLI with `sync`/`sync --demo`/`history`/`render`/`briefing` subcommands, a self-contained dark-mode dashboard, and an optional Claude Haiku aggregate-only briefing.
- Notable decisions: strictly read-only against both external systems (no write-back) to keep this safe to run against real project data; `--demo` mode against bundled fixtures so the tool is fully inspectable and testable without live credentials, consistent with the CLAUDE.md guidance that a 403/no-credentials situation in the build container is never a reason to fall back to mock-only design — real client code is still written and tested against mocked HTTP, just exercised end-to-end via fixtures for the demo path.

### [08:35 UTC] Build Phase — Matcher

- Wrote `src/matcher.py`: title normalization (casefold, strip non-alphanumeric via regex, collapse whitespace, split to token set), Jaccard similarity, greedy highest-similarity-first pairing with a mutual-exclusion set so no item is matched twice, and bucket classification (`matched_ok`, `status_conflict`, `teamwork_only`, `coda_only`).
- Hand-computed the Jaccard scores for each `test_matcher.py` case before asserting them: "Q3 Report Draft" vs "q3 report draft!!" → identical 4-token sets → 1.0 (matched); "Finish quarterly report" vs "Draft the annual budget report narrative" → 1 shared token ("report") over an 8-token union → 0.125, correctly rejected at the default 0.5 threshold; a two-Teamwork-items-competing-for-one-Coda-row case (1.0 vs 0.75 similarity) confirmed the greedy algorithm claims the stronger match first and leaves the weaker one unmatched rather than double-assigning.
- Designed the CLI/demo fixture pair (`tests/fixtures/teamwork_tasks.json` + `coda_rows.json`, 3 items each) separately from the matcher's own unit-test cases, covering exactly one of each bucket (1 matched_ok, 1 status_conflict, 1 teamwork_only, 1 coda_only) so the end-to-end `--demo` pipeline result is hand-verifiable at a glance.

### [09:05 UTC] Build Phase — API Clients

- Wrote `src/teamwork_client.py` (Basic auth, API-token-as-username per Teamwork's documented convention, paginated `tasks.json` fetch, excludes completed tasks, raises `TeamworkAPIError` on non-2xx) and `src/coda_client.py` (Bearer auth, paginated rows fetch following `nextPageToken`, column extraction by configured name, blank/missing status treated as not-done).
- Both clients accept an injectable `http_get` callable defaulting to a thin `urllib.request` wrapper, so tests substitute a mock transport instead of patching global state — keeps the mocking explicit and avoids monkeypatching `urllib` internals.
- Confirmed via `PROFILE.md`: `TEAMWORK_API_KEY`/`CODA_API_KEY` are listed as "Available if added as GitHub repo secrets" — not present in this build container. This is the same runtime-supplied-credential pattern already used for `ANTHROPIC_API_KEY` elsewhere in the catalog (Ledger Lens, Deadline Guardian, etc.): the tool is written to call the real APIs, and every test mocks the HTTP layer per CLAUDE.md's API-access guidance. No live calls were attempted from this container.

### [09:30 UTC] Build Phase — Persistence, Dashboard, Briefing, CLI

- `src/store.py`: SQLite schema created on first use (`CREATE TABLE IF NOT EXISTS`), a run + its items persist in one transaction, `history()` returns runs oldest-to-newest.
- `src/dashboard.py`: builds one JSON payload (all sync-run history for the trend chart, latest run's items for the tables), `json.dumps` with `</` escaped to `<\/` to prevent premature `</script>` termination, injected into a single self-contained HTML file via a `<script type="application/json">` block read by `textContent` — the page's own script never uses `innerHTML` on untrusted values, only `textContent`/`createElement`. Canvas 2D line chart hand-drawn (no CDN dependency).
- `src/briefing.py`: builds an aggregate-only counts object (bucket totals, run count, trend direction — never a title, URL, or ID) and either calls the Anthropic Messages API via `urllib.request` when `ANTHROPIC_API_KEY` is set, or returns a deterministic template string with zero network calls otherwise.
- `src/main.py`: `argparse` subcommands wiring the above together; `--demo` loads `tests/fixtures/*.json` in place of live HTTP calls, taking the exact same code path through the matcher/store/dashboard afterward.

### [09:55 UTC] Tests Written and Run

First run surfaced 2 failing tests — both were bugs in the tests themselves, not the implementation: `test_render_dashboard_escapes_script_injection_payload` asserted a naive `<script` substring count of 2, not accounting for a harmless literal `<script>` fragment surviving inside the JSON-escaped payload text (inert, since it never forms a real `</script` boundary — the real security property, that the payload round-trips as valid JSON without breaking out of its container, was a separate assertion in the same test and passed); `test_save_run_and_round_trip_counts` asserted a hand-miscalculated `gap_size` of 2 instead of the correct 3 (`status_conflict + teamwork_only + coda_only` = 1+1+1). Fixed both test assertions; re-ran.

Tests: 58 passed, 0 failed.

Ran `python -m pytest tests/ -v` from the build folder (pytest 9.0.2). Grepped `tests/` for `urlopen(` directly — zero results, since every HTTP-touching client (`TeamworkClient`, `CodaClient`, `briefing.generate_briefing`) takes an injectable transport callable that every test replaces with a plain Python function, rather than patching `urllib` internals.

### [10:05 UTC] Manual End-to-End Verification

- `python3 src/main.py sync --config config.example.json --demo` against the bundled fixtures, twice in a row, then `history`: printed exactly `{'matched_ok': 1, 'status_conflict': 1, 'teamwork_only': 1, 'coda_only': 1}` both times, matching the fixture design by hand, and `history` showed two persisted runs with identical per-bucket counts — confirming drift tracking works across repeated syncs.
- `python3 src/main.py render --out dashboard.html` produced a file; `briefing` with no `ANTHROPIC_API_KEY` set printed `"Parity found 1 items in sync, 3 out of sync (1 status conflicts, 1 Teamwork-only, 1 Coda-only) across 2 recorded sync run(s) — the gap is unchanged since the last sync."` — the deterministic fallback, with no network call attempted.
- `pip install` was unavailable in this container, so pytest came from a pre-installed `/root/.local/bin/pytest`, and browser verification used the environment's global Node.js Playwright (`/opt/node22`, v1.56.1) driving `/opt/pw-browsers/chromium-1194` rather than the Python Playwright bindings — same headless-Chromium verification pattern as prior builds (e.g. regex-dojo), different language binding.
- Built a dedicated verification database seeded with hostile payloads (`</script><script>alert(1)</script>` as a Teamwork-only title, `<img src=x onerror=alert(2)>` as a Coda-only title) and rendered its dashboard, then drove it with a throwaway Playwright script: zero dialogs, zero page errors, zero console errors, exactly 2 real `<script>` elements, zero injected `<img>` elements (the payload text appears in `body.innerText` only as inert text, never as a live DOM node), no horizontal overflow at a 375px mobile viewport, and the live search filter on the Coda-only table correctly narrowed to 1 row when searching "img". Both the verification database and dashboard, and the throwaway Playwright script, were added to `.gitignore` and are not part of the committed build.

### [10:15 UTC] Verify — Step 7

Success criteria review:
1. ✓ 58/58 tests pass.
2. ✓ `--demo sync` classifies all four fixture items into the correct buckets, matching the hand-worked example.
3. ✓ `render` produces a self-contained HTML file; script-injection payload verified inert.
4. ✓ Two consecutive `sync --demo` runs + `history` show correct per-run counts.
5. ✓ Grep confirms no un-mocked `urlopen` call anywhere in `tests/`.

Security checklist (STANDARDS.md):
- No `.env` files committed.
- No real credential values anywhere in source — `config.example.json` uses placeholder IDs only; real tokens are read exclusively from environment variables.
- No `eval()`/`exec()`, no `os.system()`/`subprocess` calls anywhere in this build.
- No `innerHTML` assignment from untrusted data — dashboard uses `textContent`/`createElement` exclusively.
- No file paths built from user input.
- All files confined to `builds/2026-09-27-parity/`.

### [10:20 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions (Routine wrapper for scheduled syncs, Slack/email alert on new drift, two-way status write-back behind an explicit `--apply` confirmation flag, multi-doc/multi-project support, semantic-similarity matching, per-project drift breakdown, a "stale coda-only" aging view).
- `Manual.md`: quick start, all five subcommands, configuration table, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
