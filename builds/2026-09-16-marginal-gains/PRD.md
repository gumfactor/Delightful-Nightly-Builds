# PRD — Marginal Gains

> **Build date:** 2026-09-16
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project
> **Day of week:** Wednesday

---

## Goal

A browser puzzle game where the player allocates a limited weekly hour budget across several simultaneous, diminishing-returns projects and is scored against a dynamic-programming solver's provably optimal allocation.

## User Story

As an academic/entrepreneurial multi-project operator who names "managing many simultaneous projects" and "administrative overhead" as recurring friction points (PROFILE.md), I want a short, replayable puzzle that trains the actual skill of splitting limited time across competing diminishing-returns priorities, so that I get sharper real-world intuition for when to spread effort versus concentrate it — and a few minutes of genuinely fun play along the way.

## Scope

### In Scope
- A curated pool of 16 flavor-text project cards spanning 5 categories (Research, Teaching, Admin, Canada List, Writing), tagged and reusable across rounds
- A per-project value-table generator: a startup threshold (0–3 hours before any value accrues), a weight, and a diminishing-returns cap, producing an explicit, monotonic non-decreasing value array — never a hardcoded outcome
- A dynamic-programming knapsack solver (`solveOptimal`) that computes the true maximum achievable total value for any drawn project set and hour budget, used both to score the player and as the ground truth a brute-force test cross-checks
- **Tutorial** — a single-project guided walkthrough: a live slider drives a hand-drawn Canvas 2D value-curve chart and a running marginal-gain readout, teaching the "front-load several things a little" intuition before real play
- **Daily Challenge** — UTC-date-seeded deterministic project set (6 projects, 40-hour budget), one attempt per UTC day (gated in localStorage), shareable text result (grade + % of optimal + per-project over/under emoji row)
- **Practice Mode** — freely repeatable rounds at 3 difficulty tiers (4/24hrs, 6/40hrs, 8/56hrs), fresh `Math.random`-seeded project draw each time
- Allocation UI: per-project +1/+5/-1/-5 steppers with a live remaining-budget bar, disabled Lock-In while over budget
- Results screen: total score % of optimal, letter grade, per-project player-vs-optimal hours/value table, the single most-underinvested and most-overinvested project called out
- **Mastery Dashboard**: localStorage history of completed rounds — average % of optimal, current/best Daily Challenge streak, per-category average performance
- Optional **AI Advisor**: a session-only (never persisted) Anthropic API key field; on Lock-In, an opt-in direct-browser call to Claude Haiku sends only the already-computed project names/hours/values (never invents numbers) for a 2–3 sentence coaching note; an unconditional deterministic template fallback runs with zero network calls when no key is supplied
- Dark-mode UI, mobile-responsive, all dynamic text inserted via `textContent`/`createElement` (no `innerHTML` from generated or AI-returned strings)

### Out of Scope
- Multiplayer or server-synced leaderboards (no backend; this is a self-contained `file://` game)
- Real integration with the user's actual calendar/task tools (Teamwork.com, Coda) — the project pool is illustrative flavor text, not the user's real task list, so there is nothing real to sync
- Saving/exporting allocation history outside localStorage (no file export in v1 — noted in FutureFeatures.md)
- Difficulty tiers beyond the 3 Practice presets (no fully custom budget/project-count editor in v1)

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic `<script>` tags — no ES modules, no bundler, opens directly via `file://`)
- **Framework:** None
- **Dependencies:** None at runtime (no CDN libraries — the value-curve chart is hand-drawn Canvas 2D, matching the catalog's convention for builds that need to open via `file://` with zero network dependency). Dev-only: `@playwright/test` for testing.
- **Runtime requirement:** Open `index.html` directly in a browser. No install, no server, no build step.

## Data Structure

**Project pool entry** (`src/engine.js`, `PROJECT_POOL`, 16 static entries):
```js
{ id: "grant-report", name: "Grant Progress Report", category: "Admin", blurb: "..." }
```

**Drawn project instance** (generated per round by `drawProjects(rng, count)`):
```js
{
  id, name, category, blurb,
  threshold: 0-3,        // hours before any value accrues
  weight: 6-14,           // scales the value curve
  maxHours: 6-16,          // hours at which the curve flattens
  values: [Int, ...]      // values[h] = value at h hours allocated, h = 0..min(budget, capAllocatable)
}
```

**Round state** (`game.js`, in-memory + localStorage):
```js
{
  mode: "tutorial" | "daily" | "practice",
  date: "2026-09-16",              // daily mode only
  budget: 40,
  projects: [ProjectInstance, ...],
  allocation: { [projectId]: hours },
  optimal: { total: Int, allocation: { [projectId]: hours } },
  locked: false
}
```

**localStorage keys**:
- `marginalgains_daily_v1` — `{ date, allocation, score, grade, completed: true }`, gates the one-per-day Daily Challenge
- `marginalgains_history_v1` — array of `{ mode, date, score, grade, category_gaps: { [category]: Int } }`, capped at the most recent 200 entries, feeds the Mastery Dashboard

## Folder Structure

```
builds/2026-09-16-marginal-gains/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── package.json
├── package-lock.json
├── playwright.config.js
├── src/
│   ├── engine.js        (project pool, RNG, value-table generation, DP solver, grading)
│   ├── game.js           (view/state controller, DOM rendering, localStorage)
│   ├── ai.js              (AI Advisor: prompt build, direct Anthropic fetch, deterministic fallback)
│   └── styles.css
└── tests/
    ├── engine.spec.js    (Node-level: RNG determinism, value-table shape, DP solver correctness incl. brute-force cross-check)
    └── game.spec.js       (Playwright browser e2e: tutorial, practice play-through, daily gate, scoring UI, dashboard, XSS safety, mobile viewport)
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - `engine.js` loaded directly under Node (the identical file the browser loads, via a `module.exports` guard that is a no-op in-browser) so solver correctness is tested against the real code, not a reimplementation
  - Value-table generation is monotonic non-decreasing and zero below threshold, for many random parameter draws
  - Daily Challenge RNG is deterministic for a fixed UTC date string and differs across different dates
  - DP solver (`solveOptimal`) matches brute-force enumeration on small instances (2–3 projects, budget ≤ 10) across many random instances — the core correctness guarantee, since every player score is a percentage of this solver's output
  - DP solver handles edge cases: zero budget, a single project, a budget larger than the sum of every project's `maxHours`
  - Grading thresholds map score percentages to the correct letter grade at each boundary
  - Full browser play-through: Tutorial slider updates the chart and readout live; a Practice round can be allocated, locked in, and shows a results breakdown; over-budget allocation disables Lock-In; Daily Challenge blocks a second attempt on the same UTC date and shows the "come back tomorrow" state; Mastery Dashboard reflects a completed round's stats; an injected `<script>`/`<img onerror>` payload in a mocked AI coaching response renders as inert text with zero dialogs/page errors; the deterministic AI fallback message appears with no key supplied and makes zero network requests; the page renders without horizontal overflow at a 375px-wide mobile viewport

## Success Criteria

1. All tests pass (zero failures)
2. The DP solver's optimum is cross-checked against brute-force enumeration and never beaten by any allocation on at least 25 randomized small instances
3. A full round (Tutorial → Practice → Lock-In → Results → Dashboard) is playable end-to-end in a real browser with zero console/page errors
4. Daily Challenge is deterministic per UTC date and enforces exactly one attempt per day via localStorage
5. No AI-returned or player-influenced string is ever inserted via `innerHTML`; a live script-injection payload is confirmed inert in headless Chromium

---

## Scope Changes

None — the full scope above was built as planned.
