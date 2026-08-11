# Build Log — Quarter Call

> **Date:** 2026-08-11
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Checked `builds/` locally and the most recent open PR (#67, `claude/cool-sagan-yghab4`, 2026-08-10 "Ingest Gate"). Its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — no interrupted build to resume.
- Read `PROFILE.md`, `STANDARDS.md`, and `builds/index.md` synced from that same branch (60 builds logged, last build 2026-08-10).
- `date -u +%j` → day 223. `category_index = (223-1) % 9 = 6` → **Category G — Game/Puzzle**.
- Checked `builds/ideas.md` for pending Category G rows: #11 (Market Cap Higher or Lower) and #12 (Stock Chart Direction Quiz), both blank rating (5 tickets each, R=0 rated ⇒ lottery_chance = min(75, 25+0) = 25%).
- Rolled 1–100 via shell `$RANDOM`: **22** ≤ 25 → lottery draw happens.
- Rolled 1–10 to pick between the two 5-ticket ideas: **6** → tickets 6–10 = idea #12. Selected: **Stock Chart Direction Quiz**.
- No linked Idea Brief on this row, so proceeding straight to PRD.
- Build folder created: `builds/2026-08-11-quarter-call/`

### [00:15 UTC] PRD Written

- Goal: a browser game that shows a real historical stock price chart and asks the player to call whether the price went up, down, or flat over the following quarter — using genuine historical closes, never synthetic data.
- Key design decision: the build container's egress proxy returns 403 on `query1.finance.yahoo.com` (confirmed live during this session — see below). Following CLAUDE.md's "design for the user's runtime" guidance and the precedent set by the 2026-08-09 Portfolio Lab build, the game ships **honest by default**: `data/rounds-data.js` commits as `ROUNDS_DATA = null` and a `fetch_data.py` script (using `yfinance`, run locally by the user) populates it with 48 real curated historical rounds spanning 11 sectors and 2016–2023. No fabricated market data is ever shown in the shipped product.
- Confirmed the network block live: `urllib.request.urlopen('https://query1.finance.yahoo.com/...')` → `403 Forbidden` via the proxy tunnel. This is a build-environment constraint per CLAUDE.md, not a reason to fake data.
- Scope: Practice mode (random draw from the 48-round bank) + Daily Challenge (UTC-date-seeded, one play/day, shareable emoji result), canvas-drawn price chart with a post-guess "reveal" continuation into the real forward quarter, sector/industry badges, two metrics computed directly from the same displayed closes (trailing 6-month return, annualized volatility — never a separate, possibly-stale data source), persistent localStorage stats (streak, accuracy, per-sector breakdown), optional direct-browser Claude Haiku historical-context note on reveal (session-only key, aggregate-only prompt).

### [00:30 UTC] Build Phase — fetch_data.py

- Wrote `fetch_data.py`: `RoundSpec`/`CURATED_ROUNDS` (48 hand-curated (ticker, historical decision date) pairs across 11 sectors, dates 2016-03-31 through 2020-12-31 — all safely settled with a full forward quarter in the past), `classify_outcome` (±5% flat band), `annualized_volatility`/`trailing_return_pct` (both computed from the same close series the chart will show), `build_round` (windows a raw history into a 6-month trailing chart + 1-quarter forward outcome, returns `None` when either side has insufficient real data rather than fabricating), `fetch_history` (the only function that touches `yfinance`, imported lazily so the module is importable without the package installed), `to_js`, and `main`.
- Checked PyPI reachability: `pip index versions yfinance` succeeded (latest `1.5.2`, pinned in `requirements.txt`) — confirms the *package registry* is reachable even though the *data host* (query1.finance.yahoo.com) is blocked, consistent with CLAUDE.md's guidance that this is a build-environment constraint, not a redesign signal.
- Shipped `data/rounds-data.js` as `const ROUNDS_DATA = null;` with a comment explaining why, matching the 2026-08-09 Portfolio Lab precedent.

### [00:50 UTC] Build Phase — pytest suite

- Wrote `tests/test_fetch_data.py` (22 tests): pure-function coverage for outcome classification (including exact ±5% boundary), volatility/return math, `build_round` happy path + three insufficient-data skip cases, `to_js` JSON round-trip, `main()` end-to-end against a monkeypatched `fetch_history` (zero real network calls — verified via a call counter), per-ticker fetch-exception resilience, all-tickers-fail exit code, and curated-data integrity (unique IDs, ≥10 sectors, every decision date pre-2024).
- First run: 4 failures, all in my own test fixtures, not `fetch_data.py` itself — the hand-built histories didn't leave enough trading days after the decision date to clear `FORWARD_WINDOW_DAYS` (63). Fixed by adding a `make_history_around()` helper that generates generous before/after padding around any decision date. Re-ran: **22 passed, 0 failed.**

### [01:15 UTC] Build Phase — frontend

- Built `src/game.js` (pure: `daysBetween` using `Date.UTC(y, m-1, d)` — explicitly guarding the exact 0-indexed-month bug this catalog's Lexicon build log documented finding and fixing —, a seeded `mulberry32` PRNG for deterministic shuffling, `dailyChallengeRounds`, `getNextPracticeRound`, `evaluateGuess`), `src/stats.js` (localStorage-backed streak/accuracy/per-sector/daily-history persistence), `src/chart.js` (native Canvas 2D line chart + a two-tone trailing/forward reveal chart), `src/ai.js` (direct-browser Anthropic call sending only aggregate round fields, unconditional deterministic fallback), `src/app.js` (DOM wiring — every dynamic value set via `textContent`/`dataset`, never `innerHTML`), `src/styles.css`, and `index.html`.
- Built a fixture test harness (`tests/fixtures/rounds-fixture.js` + `tests/fixtures/test-harness.html`) that loads the same `src/*.js` modules against synthetic-but-clearly-labeled fixture rounds instead of the real (null) shipped dataset, plus `tests/fixtures/rounds-fixture-node.js` so Node-side test code can look up a fixture round's real outcome by ticker without duplicating the dataset.

### [01:40 UTC] Build Phase — Playwright suite

- Wrote `tests/quarter-call.spec.js` (22 tests) covering: the real shipped `index.html`'s honest empty state, Practice mode happy path (round rendering, chart drawing, correct/incorrect reveal, streak math, double-click guard, full-bank-cycle-without-repeat, accuracy math, localStorage persistence across reload), XSS safety (an `<img onerror>` + `</script><script>` payload in fixture round data confirmed to render as inert text with zero dialogs and the target globals never set), Daily Challenge (same-date determinism via `page.clock.setFixedTime`, full 5-round completion + emoji share string, same-day replay blocked), the pure `daysBetween`/`dailyChallengeRounds` date math, and the optional AI note (mocked via `page.route`: zero calls with no key, exactly one call with a key and an aggregate-only request body, graceful fallback on a mocked 500).
- First run: 7 failures. Two root causes, both real bugs, not test issues:
  1. **CSS bug:** `main { display: grid; ... }` (an author-stylesheet rule) was silently overriding the UA stylesheet's `[hidden] { display: none }` for the `#app` and `#reveal-panel` elements, because author-origin CSS always wins over UA-origin CSS regardless of selector specificity — so `.hidden = true` set the attribute correctly but the element stayed visually visible. Fixed by adding an explicit `[hidden] { display: none !important; }` rule.
  2. **Test harness bug:** `rounds-fixture-node.js` used `vm.runInContext` to load the classic-script fixture file, but top-level `const`/`let` declarations don't become sandbox-object properties (only `var`/function declarations do) — so `sandbox.ROUNDS_DATA` was `undefined`. Fixed by appending `this.ROUNDS_DATA = ROUNDS_DATA;` to the executed source so the const gets explicitly assigned onto the vm context's global object while still in scope.
  3. Separately, two AI-note tests timed out trying to `fill()` the API-key input, which lived inside `[data-testid="reveal-panel"]` — hidden until *after* the first guess, but the key needs to be set *before* guessing (the reveal fetches the AI note immediately). This was a real UX bug, not just a test problem: there was no way to set the key before your first guess in the shipped UI either. Moved the API-key input out of the reveal panel to sit permanently visible above the stats panel.
- Re-ran after all three fixes: **22 passed, 0 failed.**

### [02:00 UTC] Manual QA pass (headless Chromium, both viewports)

- Screenshotted all 5 primary states (no-data banner, Practice round, reveal panel, Daily Challenge round, desktop layout) at 420×900 (mobile) and 1280×900 (desktop) via a standalone Playwright script. Zero `pageerror`/console-error events across all navigations and interactions. Visual review: dark theme renders correctly, guess buttons are color-coded and legible, chart lines draw correctly at both viewport sizes, sector/industry badges wrap cleanly, stats panel is readable. No additional bugs found beyond the three already fixed above.
- Security checklist: grepped the build for `innerHTML` (only appears in a code comment explaining its absence), `eval(`/`exec(`, hardcoded `api_key=`/`secret=`/`password=` literals, and `os.system`/`subprocess` — all clean.

### [02:10 UTC] Tests Run

Tests: 44 passed, 0 failed. (22 pytest — `python -m pytest tests/ -v`; 22 Playwright — `npx playwright test`.)

### [02:15 UTC] Step 7 — Verify Success Criteria

1. ✓ All tests pass (44/44, minimum 15 required).
2. ✓ `fetch_data.py` run against mocked `yfinance` data (in `test_main_writes_output_file_using_mocked_fetch_history`) produces a syntactically valid `rounds-data.js` with correctly classified outcomes and chart-consistent metrics — verified by parsing the JSON back out and checking the round's fields.
3. ✓ The shipped build (`ROUNDS_DATA = null`) shows the honest empty state and never fabricates market data — verified live in headless Chromium (`Honest empty state` test suite, 2/2 passing) and by manual screenshot.
4. ✓ A full Practice-mode round (guess → reveal → stats update) and a full 5-round Daily Challenge (one-play-per-day gate, correct share string) both work end-to-end against fixture data — verified live in headless Chromium (20/20 remaining Playwright tests passing).
5. ✓ No user-controlled or file data is ever inserted via `innerHTML` — grep-confirmed, and the XSS test live-verifies an injected `<img onerror>`/`</script><script>` payload renders as inert text with zero dialogs and zero fired globals.

Security checklist (STANDARDS.md): no `.env` files; no hardcoded credentials (the Anthropic key is a runtime-only, session-held, never-persisted browser variable); no `eval()`/`exec()`; no `innerHTML` from user/file data; no `os.system()`/`subprocess` calls anywhere (pure client-side JS + a local-only Python fetch script with zero shell invocation); no file-path traversal (browser build has no filesystem access; `fetch_data.py` only ever writes to its own `data/` subdirectory); all files confined to this build folder.

### [Docs] Step 8 — Documentation

- `WhyThis.md`: lottery draw, roll 22/25%-chance then roll 6/10 for the ticket draw between the two pending Category G ideas.
- `FutureFeatures.md`: 7 concrete suggestions across Quick Wins / Medium Effort / Ambitious Extensions, plus integration points and known limitations.
- `Manual.md`: quick start, mode explanations, configuration, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
