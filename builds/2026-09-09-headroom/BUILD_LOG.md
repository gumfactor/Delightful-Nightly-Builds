# Build Log — Headroom: RRSP/TFSA Contribution Room & Deadline Tracker

> **Date:** 2026-09-09
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:11 UTC] Session Start

- Checked Step 0: most recent dated build folder (2026-06-18-regex-dojo) ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Resynced builds/index.md and builds/ideas.md from the most recent open PR branch (claude/cool-sagan-0b6px0, PR #93, 2026-09-08) — local index was ~86 builds stale (last local entry 2026-06-24 vs. remote's 2026-09-08).
- Day of year 252 → category_index = (252-1) % 9 = 8 → Category I — Life Admin Helper.
- Category I backlog check: 2 pending ideas (#24 Cross-Domain Habit Log, #25 Recurring Chore/Checklist Tracker), both unrated → R=0 → lottery_chance = 25%. Rolled random 1–100 via `python3 -c "import random; print(random.randint(1,100))"` → 43. 43 > 25 → fresh ideas path.
- Scanned last 10 builds for topic saturation: Zebra Lab, Layer Guard, Fleet Drift, CiteForge, Promptbook, CaseForge, Mediation & Moderation Analysis Lab, Almanac, True Course, Secrets Sentinel — no repeated domain, no action needed.
- Scanned all 8 prior Category I builds for topic coverage (Run Planner, Project Pulse, Ledger Lens, Deadline Guardian, TripKit, Dockside, Macro Kitchen, Renewal Radar) and grepped the full catalog for "RRSP"/"TFSA"/"contribution room" (zero hits).
- Generated 3 fresh candidates, verified real CRA-published TFSA/RRSP historical limit data via WebSearch (cross-checked against two independent result sets, both agreeing and matching the well-known public totals of $102,000 cumulative TFSA room by 2025 / $109,000 by 2026) since a tax-admin tool's core value depends on the numbers being right. Direct WebFetch of canada.ca itself was blocked by the build container's egress proxy (consistent with CLAUDE.md's documented network constraint) but WebSearch worked and returned data the tool cross-referenced against training knowledge before committing to the table.
- Selected: **Headroom** — RRSP/TFSA contribution room and deadline tracker. Full reasoning in WhyThis.md.
- Build folder created: builds/2026-09-09-headroom/

### [08:25 UTC] PRD Written

- Goal: track real RRSP/TFSA contribution room, overcontribution risk, and CRA deadlines from real historical limit data and the actual carryforward/withdrawal-timing/penalty rules.
- Scope: TFSA + RRSP room engines, deadline engine (date-injectable for testability), local JSON store + CSV import, CLI, self-contained HTML dashboard, optional Claude Haiku briefing with deterministic fallback.
- Notable decision: IBKR live-sync explicitly scoped out up front (not cut mid-build) — Trading Book (2026-08-23) already owns this repo's live-brokerage-connection pattern, and IBKR account structures don't cleanly expose "this deposit was a registered contribution" without unverifiable per-institution assumptions. The CRA rule engine itself is the differentiating layer instead, with a CSV/manual ledger as the real-data input (same pattern as Ledger Lens's bank-CSV ingestion).
- `.claude/settings.json` in this session denies `Bash(pip install:*)` (same constraint Trading Book's build hit on 2026-08-23) — designed the whole build stdlib-only from the start, including the optional Anthropic call via `urllib.request` directly rather than the `anthropic` package.

### [09:10 UTC] Build Phase — Core Engines

- `src/limits.py`: hardcoded TFSA (2009-2026) and RRSP (2009-2026) annual dollar limit tables from the WebSearch-verified data, each entry commented with its source characterization; `tfsa_limit(year)`/`rrsp_limit(year)` raise a `LimitTableError` on out-of-range years rather than silently returning 0.
- `src/tfsa.py`: year-by-year room ledger (add annual limit → add prior-year withdrawals-readded → subtract contributions), start year = max(2009, birth_year + 18, resident_since_year), overcontribution 1%/month estimate off the current (as-of) ending balance.
- `src/rrsp.py`: per-year room = min(18% × prior year earned income, that year's dollar limit) − prior year pension adjustment (floored at 0), carried forward indefinitely; supports an optional `opening_balance` seed (the user's real CRA-stated deduction limit as of a given year) since this tool has no way to know pre-tracking history otherwise; $2,000 lifetime grace buffer before the 1%/month penalty estimate; age-71 RRIF conversion flag that stops generating new room once past it.
- `src/deadlines.py`: all functions take an explicit `as_of: date` parameter (never call `date.today()` internally) so tests are fully deterministic regardless of which real day they run on — only `src/cli.py` supplies the real `date.today()` at the entrypoint. RRSP deadline = Dec 31 + 60 days, shifted forward to the next weekday if it lands on a Saturday/Sunday. Verified the weekend-shift logic against real historical CRA deadlines by computing all 2009-2026 raw dates first (`date(y,12,31)+timedelta(days=60)`) and checking weekday: 2013 (→ Sat Mar 1 2014 → real deadline Mon Mar 3 2014) and 2019 (→ Sat Feb 29 2020 → real deadline Mon Mar 2 2020) both matched publicly known real CRA deadlines before being written into a test.
- Hand-computed a multi-year, multi-contribution, one-withdrawal worked example before writing any test assertion (documented in both engines' docstrings/tests): TFSA → $100,000 available; RRSP → $89,660 available. Ran both engines against this exact scenario via a throwaway `python3 -c` snippet and confirmed the code's output matched the hand calculation digit-for-digit before that scenario became `data/sample_headroom.json` and the two `test_full_worked_example_matches_sample_data` tests.

### [09:35 UTC] Build Phase — Storage, CSV Import, CLI, Dashboard, AI Briefing

- `src/storage.py`: load/save `data/headroom.json`; `data/sample_headroom.json` ships with an entirely fabricated profile (birth year 1990, round-number sample transactions) for demos and as a test fixture — no real personal data committed.
- `src/csv_import.py`: auto-detects header names case-insensitively (`date`/`amount`/`account` for contributions, `year`/`earned_income`/`pension_adjustment` for income); raises a clear `CSVImportError` naming the missing column rather than crashing on `KeyError`.
- `src/dashboard.py`: self-contained dark-mode HTML string template; all user-supplied values are serialized once via `json.dumps` (with a defensive `</` → `<\/` escape so no value can prematurely close the surrounding `<script>` tag) into a single `<script type="application/json">` data block, then read back out and inserted into the DOM by inline JS via `textContent`/`createElement` — never string-concatenated into HTML markup. Verified with a script-tag-injection-style value in tests. Chart.js 4.4.4 pinned via CDN with a plain-table fallback if `window.Chart` is undefined.
- `src/ai_briefing.py`: builds an aggregate-only prompt (room balances, deadline dates, overcontribution flags — never individual transactions) and POSTs to the Anthropic Messages API via `urllib.request` when `ANTHROPIC_API_KEY` is set; falls back to a deterministic template sentence otherwise. Tests patch `urllib.request.urlopen` and assert it is never called on the no-key path.
- `src/cli.py` + `main.py`: `init`, `add-contribution`, `add-withdrawal`, `add-income`, `import-csv`, `status`, `report` subcommands via `argparse`.

### [09:50 UTC] Tests Run

First run: 78 passed, 2 failed.
- `test_tfsa.py::test_contributions_reduce_available_room` failed on my own arithmetic: the test asserted the pre-contribution cumulative total through 2020 was $63,500, but that's the total through *2019* — 2020 adds its own $6,000 annual limit first, so the correct pre-contribution figure is $69,500. The engine was right; the test's hand-math was wrong. Fixed the assertion (and its comment) to $69,500 − $6,000.
- `test_ai_briefing.py::test_generate_briefing_falls_back_on_network_error` failed because `generate_briefing`'s except clause listed `urllib.error.URLError`/`HTTPError` explicitly but not bare `OSError`, and the test's mocked failure raised plain `OSError` (a realistic stand-in for a raw socket/connection failure, not just an HTTP-level one). Since `URLError`/`HTTPError`/`TimeoutError` are all already `OSError` subclasses, simplified the except tuple to `(OSError, KeyError, IndexError, ValueError)` — same coverage, and now catches the case the test was actually checking for. Removed the now-unused `import urllib.error`.

Second run after both fixes: 80 passed, 0 failed.

Ran `python -m pytest tests/ -v` from the build folder. Also manually ran the full CLI end to end against a scratch data file (`init`, two `add-contribution` TFSA calls, `add-withdrawal`, seven `add-income` calls, two RRSP `add-contribution` calls, `status`, `report`) reproducing the exact worked example above, and confirmed `status`'s printed figures ($100,000 TFSA / $89,660 RRSP) matched the `available_room` values embedded in the generated dashboard HTML exactly. This session's sandbox denies `rm`, so the scratch directory was moved out of the build folder (to the session scratchpad) rather than deleted, and `.pytest_cache` was moved out the same way — neither is staged for commit.

### [10:05 UTC] Verify — Step 7

Security checklist run against every file in `src/`, `tests/`, `main.py`:
- No `.env` files, no hardcoded API keys/secrets/passwords.
- No `eval()`/`exec()` anywhere.
- No `innerHTML` — dashboard inserts data via a JSON `<script>` block read by `textContent`/DOM APIs on the JS side, never string-built HTML.
- No `os.system()`/`subprocess` calls at all in this build.
- No file paths built from unsanitized user input — `--file` is passed straight to `open()`, matching the CSV-import pattern of prior builds (Ledger Lens, TrialScope); no path-traversal-sensitive operation (no deletion, no writing outside the build folder) depends on it.
- No reads from outside the build's own folder.
- `data/sample_headroom.json` contains only fabricated numbers — confirmed no real name, address, account number, or actual birth year.

Success criteria review against PRD.md:
1. ✓ 80/80 tests pass.
2. ✓ Worked-example tests (`test_tfsa.py::test_full_worked_example_matches_sample_data`, `test_rrsp.py::test_full_worked_example_matches_sample_data`) hand-verified against a multi-year, multi-contribution, one-withdrawal scenario (also shipped as `data/sample_headroom.json`) before being asserted — TFSA $100,000, RRSP $89,660.
3. ✓ `test_deadlines.py` injects fixed `as_of` dates throughout, including the real historical weekend-landing case for tax year 2013 (raw Dec 31 2013 + 60 days = Saturday Mar 1 2014, shifted to Monday Mar 3 2014) and a real leap-year case (tax year 2011 → Feb 29 2012); no test or non-CLI function ever touches `date.today()`.
4. ✓ `test_cli.py::test_report_writes_html_without_api_key` runs the full `report` command end-to-end with `ANTHROPIC_API_KEY` deleted from the environment and confirms a valid HTML file is produced; `test_ai_briefing.py::test_no_api_key_never_calls_network` separately asserts the deterministic-fallback path never calls `urllib.request.urlopen`.
5. ✓ `test_csv_import.py` covers a valid contributions file, a case-insensitive-header file, a valid income file (with and without the optional pension-adjustment column), and three malformed-input cases (missing column, bad date, empty file) all raising `CSVImportError` with no crash.

### [10:10 UTC] Documentation

- FutureFeatures.md: 8 concrete suggestions.
- Manual.md: quick start, all 7 CLI subcommands documented, configuration table, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
