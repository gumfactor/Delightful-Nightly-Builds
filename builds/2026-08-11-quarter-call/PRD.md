# PRD — Quarter Call

> **Build date:** 2026-08-11
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project
> **Day of week:** Tuesday

---

## Goal

A browser game that shows you a real historical stock price chart and asks you to call whether the price went up, down, or flat over the following quarter — trained on genuine market history, not synthetic data.

## User Story

As a quantitative-investing-interested user who already follows AI infrastructure/semiconductor names and market structure as a hobby, I want to practice reading real price charts and calling their forward direction with immediate, honest feedback against what actually happened, so that I get sharper, humbler intuition about how (un)predictable short-term stock moves really are — without touching real money.

## Scope

### In Scope
- A curated bank of 48 historical "rounds" (ticker + decision date), spanning 11 GICS-style sectors and 2016–2023, each decision date at least one full quarter before "today" so the outcome is always settled.
- `fetch_data.py`: a Python 3 script using `yfinance`, run locally by the user, that downloads real daily closes around each decision date, computes the trailing 6-month chart window, the forward-quarter (63 trading day) outcome, and writes a static `data/rounds-data.js` file (`const ROUNDS_DATA = [...]`) consumed by the game. Ships with `ROUNDS_DATA = null` until the user runs it — no fabricated data is ever shown.
- Canvas 2D chart renderer (native, no library) drawing the 6-month price line up to the decision date.
- Practice mode: draws a random round from the bank (no immediate repeats until the bank is exhausted, then reshuffles).
- Daily Challenge mode: UTC-date-seeded deterministic round (same round for everyone on a given day), 5 rounds per challenge, one playthrough per UTC day (gated, persisted in localStorage), shareable emoji-grid result (🟩 correct / 🟥 wrong, matching the Wordle-style convention already used by Lexicon and Confound Hunter in this catalog).
- Sector + industry badges and two chart-derived metrics (trailing 6-month return %, annualized volatility %) shown before the guess — both computed directly from the same closes rendered in the chart, so they can never disagree with what's on screen.
- Three guess buttons: Up / Down / Flat (±5% band). On guess, reveal panel shows the real forward-quarter chart continuation, the actual % move, and updates streak/accuracy stats.
- Persistent localStorage stats: current streak, best streak, total played, accuracy %, and per-sector accuracy breakdown.
- Optional AI historical-context note on reveal: a direct browser call to the Anthropic Messages API using a session-only, never-persisted API key the user pastes in; the prompt sends only the round's aggregate public data (ticker, sector, date range, % move) — never anything else. Unconditional deterministic-template fallback when no key is set, so the game is fully playable with zero network calls.
- An honest "no data yet" banner (with the exact `fetch_data.py` command to run) shown instead of gameplay when `ROUNDS_DATA` is null — the state the repo ships in, since this build container's egress proxy blocks Yahoo Finance.
- A note-to-self explainer panel on efficient markets / random walk framing, so the game doesn't imply real predictive skill is being taught.

### Out of Scope
- Real-time or live market data — every round is historical and fully settled (this is a pattern-recognition trainer, not a forecasting tool or real trading signal).
- Multiplayer or server-backed leaderboards — single-player, fully local.
- Fundamentals-at-decision-date (P/E, market cap as of that historical date) — `yfinance` historical fundamentals are unreliable/inconsistent for past dates, so only chart-derived technical metrics are shown, which are always internally consistent.
- Account system / cloud sync of stats — localStorage only, matching every other browser build in this catalog.

## Tech Stack

- **Language:** Vanilla HTML/CSS/JS (classic `<script>` tags, no ES modules, so it opens directly via `file://`) + Python 3 for the offline data-fetch script.
- **Framework:** None.
- **Dependencies:** `yfinance` (Python, `fetch_data.py` only, not shipped/required to play), `@playwright/test` (dev/test only). No CDN dependencies at runtime — chart rendering is native Canvas 2D.
- **Runtime requirement:** Open `index.html` directly in a browser to play (ships with the "no data" banner until `python3 fetch_data.py` is run once locally with `pip install yfinance`).

## Data Structure

`data/rounds-data.js` (committed as `ROUNDS_DATA = null;`; regenerated locally by `fetch_data.py`):

```js
const ROUNDS_DATA = [
  {
    id: "AAPL-2019-03-29",
    ticker: "AAPL",
    company: "Apple Inc.",
    sector: "Technology",
    industry: "Consumer Electronics",
    decisionDate: "2019-03-29",
    chart: [{ date: "2018-09-28", close: 55.19 }, /* ... ~126 trading days ... */],
    metrics: { trailingReturnPct: 12.4, annualizedVolatilityPct: 27.8 },
    forward: {
      endDate: "2019-06-28",
      endClose: 49.48,
      pctChange: -10.3,
      outcome: "down",
      chart: [/* forward continuation points, same shape */]
    }
  },
  /* ... 48 rounds total ... */
];
```

`localStorage["quarterCallStats"]`:
```json
{
  "streak": 0, "bestStreak": 0, "totalPlayed": 0, "totalCorrect": 0,
  "sectorStats": { "Technology": { "played": 0, "correct": 0 }, "...": {} },
  "practiceShuffleOrder": ["AAPL-2019-03-29", "..."], "practiceShuffleIndex": 0,
  "dailyHistory": { "2026-08-11": { "completed": true, "results": ["correct","wrong","correct","correct","wrong"] } }
}
```

## Folder Structure

```
builds/2026-08-11-quarter-call/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── fetch_data.py
├── requirements.txt
├── playwright.config.js
├── package.json
├── src/
│   ├── chart.js          (Canvas 2D rendering: renderChart, renderReveal)
│   ├── game.js            (pure logic: classifyOutcome thresholds already applied at fetch time, guess evaluation, seededDailyRounds, daysBetween)
│   ├── stats.js           (localStorage read/write, per-sector aggregation)
│   ├── ai.js               (optional Anthropic browser call + deterministic fallback template)
│   └── app.js              (DOM wiring, mode switching, render loop)
├── data/
│   └── rounds-data.js      (ROUNDS_DATA = null until fetch_data.py is run)
├── tests/
│   ├── test_fetch_data.py           (pytest, mocked yfinance)
│   ├── fixtures/
│   │   ├── rounds-fixture.js        (small synthetic dataset, clearly labeled test-only)
│   │   └── test-harness.html        (loads app.js/chart.js/game.js/stats.js/ai.js against the fixture data)
│   └── quarter-call.spec.js         (Playwright, drives test-harness.html)
```

## Testing Strategy

- **Frameworks:** `pytest` for `fetch_data.py`'s pure data logic; `@playwright/test` for the game.
- **Test file locations:** `tests/test_fetch_data.py`; `tests/quarter-call.spec.js`.
- **Run commands:** `python -m pytest tests/ -v` and `npx playwright test`.
- **What will be tested:**
  - `fetch_data.py`: forward-outcome classification (up/down/flat thresholds, boundary cases at exactly ±5%), chart-window trimming to ~126 trading days, insufficient-history rounds are skipped with a logged warning rather than crashing, sector/industry fallback when `ticker.info` raises or omits fields, trailing-return/volatility math against a hand-computed reference series, JS output is syntactically valid and round-trips through a JS parser, **zero real network calls** (mocked `yfinance.Ticker`).
  - Game: shipped `index.html` with `ROUNDS_DATA = null` shows the honest "run fetch_data.py" banner and disables play; a full guess→reveal cycle against fixture data for each of up/down/flat outcomes (correct and incorrect guesses); streak/best-streak/accuracy update correctly and persist across a reload; Daily Challenge is deterministic (same UTC date ⇒ same 5 rounds, verified via `page.evaluate` clock override) and blocks a second playthrough the same day; the emoji-share string matches the actual result sequence; `daysBetween`/date-seeding is verified against known day counts (guarding the exact 0-indexed-month bug called out in this catalog's Lexicon build log); XSS: a `<script>`/`<img onerror>` payload injected into a fixture round's `company` field renders as inert text with zero dialogs/executed code; AI call is fully mocked via `page.route` — asserts zero network calls with no key, exactly one call with a key present, and that the outgoing request body contains only the round's aggregate fields (never the full chart array).

## Success Criteria

1. All tests pass (zero failures) — minimum 15 across both suites.
2. `fetch_data.py` run against mocked `yfinance` data produces a syntactically valid `rounds-data.js` with correctly classified outcomes and chart-consistent metrics.
3. The shipped build (`ROUNDS_DATA = null`) shows the honest empty state and never fabricates market data — verified live in headless Chromium.
4. A full Practice-mode round (guess → reveal → stats update) and a full 5-round Daily Challenge (with the one-play-per-day gate and correct share string) both work end-to-end against fixture data, verified live in headless Chromium.
5. No user-controlled or file data is ever inserted via `innerHTML`; a live script-injection payload is confirmed inert.

---

## Scope Changes

None — built as scoped. The only constraint accepted up front (not a mid-build cut) is that this build container cannot fetch live Yahoo Finance data (403 from the egress proxy, confirmed live), so `data/rounds-data.js` ships as `ROUNDS_DATA = null` and the 48-round bank is generated by the user running `fetch_data.py` locally, per CLAUDE.md's "design for the user's runtime" guidance and the same pattern the 2026-08-09 Portfolio Lab build established.
