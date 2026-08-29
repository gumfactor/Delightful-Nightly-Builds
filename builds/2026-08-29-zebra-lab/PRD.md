# PRD — Zebra Lab

> **Build date:** 2026-08-29
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project
> **Day of week:** Saturday

---

## Goal

A browser logic-grid deduction game (in the tradition of the classic "Zebra Puzzle") where every puzzle is procedurally generated from a real research-methods taxonomy — population, study design, confound-control method, and threat to validity — with a from-scratch constraint solver that proves each generated puzzle has exactly one valid solution before it is ever shown to the player.

## User Story

As a psychology professor and lab director who has already built two vignette-judgment games about research methods (Confound Hunter, Heuristic Hunt), I want a genuinely different puzzle mechanic — real step-by-step logical deduction instead of "spot the flaw in this scenario" — so that the research-methods category rotation stays fresh and the game exercises a different cognitive skill (systematic elimination) rather than repeating an existing mechanic.

## Scope

### In Scope
- A from-scratch constraint-satisfaction (CSP) backtracking solver operating on N "studies" (numbered positions) × K attribute categories, each a bijection between positions and category values
- A puzzle generator that: picks a random valid solution, enumerates every true clue for the allowed clue types, greedily adds clues until the solver proves a unique solution, then runs a minimality pass that removes every clue that can be removed without breaking uniqueness
- Four clue types: `eq` (two values occur in the same study), `neq` (two values occur in different studies), `adjacent` (the two studies are numbered next to each other), `less` (one study's number is lower than the other's)
- Three chapters of increasing difficulty, gated by solve count:
  - Chapter 1 "Intro": 4 studies × 3 categories (Population, Study Design, Sample Size), clue types `eq`/`neq` only
  - Chapter 2 "Standard": 5 studies × 4 categories (Population, Study Design, Confound Control, Threat to Validity), adds `adjacent`
  - Chapter 3 "Expert": same categories as Chapter 2, adds `less`, and the minimality pass runs an extra pruning round for a tighter (harder) clue set
  - Chapter 2 unlocks after 3 solves in Chapter 1; Chapter 3 unlocks after 3 solves in Chapter 2
- Answer grid: one `<select>` per (study, category) cell; clue list panel; "Check Solution" button (unlimited attempts, each attempt counted) that reports only how many studies are *entirely* correct, never which ones
- Hint button: reveals one complete study's correct assignment (all categories), capped at 2 per puzzle, each use counted against the puzzle's final score
- Daily Challenge: one Chapter-2-difficulty puzzle per UTC calendar day, generated from a deterministic seed derived from the date so every player who opens it on the same day gets the same puzzle; one completion recorded per day; a shareable emoji-grid result string (🟩 = solved with 0 checks/hints wasted, 🟨 = solved with some used, ⬛ = an incomplete attempt slot) that never reveals puzzle content
- Practice mode: generate a fresh puzzle in any unlocked chapter at any time, unlimited
- Persistent localStorage stats: puzzles solved per chapter, current/best daily streak, total checks and hints used, fastest solve (fewest checks) per chapter
- Optional AI explainer panel shown after a puzzle is solved: composes a short, accurate research-methods explanation of one Confound-Control-Method / Threat-to-Validity pairing drawn from the solved puzzle. If the user has entered an Anthropic API key (session-only, browser `sessionStorage`, sent only in a direct client-side call to `api.anthropic.com`), a Claude Haiku call polishes the phrasing; with no key, a deterministic template composed from two small, factually-reviewed snippet tables produces the same explanation with no network call
- Colorblind-safe UI (text + shape indicators, not color-only), keyboard-accessible selects, mobile-responsive layout

### Out of Scope
- A secondary "pencil marks" / candidate-elimination notes grid (the answer-grid selects already let a player track working hypotheses by changing selections; a dedicated elimination-marking UI is a good future addition, not required for the core deduction loop to work)
- Puzzle sizes larger than 5×4 (search space and clue-authoring complexity grow fast; 5×4 already exercises the solver fully)
- Server-side / multiplayer leaderboards (this is a local, self-contained browser tool per STANDARDS.md — no persistent cloud infrastructure)
- Any live external data source (deliberately self-contained; the only optional network call is the user's own direct, opt-in Anthropic API request)

## Tech Stack

- **Language:** HTML / CSS / JavaScript (vanilla, classic `<script>` tags — no ES modules, no bundler, so `index.html` opens directly via `file://`)
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev-only, for tests)
- **Runtime requirement:** Open `index.html` directly in any modern browser. No install, no server, no build step.

## Data Structure

Pure in-memory JS objects, no persistence beyond `localStorage`:

- **Category** `{ id, label, values: [{ id, label }, ...] }` — one implicit `position` category (values are the study numbers themselves) plus 3–4 attribute categories per chapter.
- **Solution** `{ [categoryId]: valueIndex[] }` — for each attribute category, an array indexed by study position holding the assigned value index (a bijection; `position` category is always the identity).
- **Clue** `{ type: 'eq'|'neq'|'adjacent'|'less', a: {category, value}, b: {category, value} }` — always true against the solution it was generated from.
- **Puzzle** `{ chapterId, size, categories, solution, clues, seed }`.
- **localStorage keys:** `zebralab_progress` (solved counts per chapter, unlocked chapters), `zebralab_stats` (checks/hints totals, streaks, fastest solves), `zebralab_daily` (`{date, completed, checksUsed, hintsUsed}`).
- **sessionStorage key:** `zebralab_api_key` (optional, user-entered, never written to localStorage or sent anywhere but `api.anthropic.com`).

## Folder Structure

```
builds/2026-08-29-zebra-lab/
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
│   ├── data.js       — category/chapter definitions
│   ├── logic.js       — solver, clue enumeration, generator, RNG, formatters (pure functions, no DOM)
│   ├── ai.js           — Claude Haiku call + deterministic explanation fallback
│   ├── app.js          — DOM wiring: screens, grid rendering, state, localStorage
│   └── styles.css
└── tests/
    ├── solver.spec.js       — backtracking solver correctness & uniqueness counting
    ├── generator.spec.js    — puzzle generation: minimality, determinism, all chapters
    ├── clues.spec.js        — clue-text formatting matches underlying relation
    ├── ui-grid.spec.js      — answer grid, check solution, hints, mistakes counter
    ├── ui-progress.spec.js  — chapter gating, stats persistence, daily challenge gate
    └── ai.spec.js           — deterministic fallback (no key) and mocked API success/failure paths
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Solver returns the exact known solution when given a full clue set, and correctly reports "not unique" for a deliberately underspecified clue set
  - Generator produces a clue set that is both *sufficient* (solver proves uniqueness) and *minimal* (removing any single clue breaks uniqueness) across multiple random seeds and all three chapters
  - Daily-challenge seeding is deterministic: the same UTC date always produces byte-identical clues and solution across two independent generator runs
  - Different UTC dates produce different puzzles (no accidental seed collision)
  - Clue-text formatter output is logically consistent with the relation it describes (e.g. an `adjacent` clue's two referenced values really are 1 apart in position in the generating solution)
  - Answer grid renders one select per (study × category) cell and "Check Solution" correctly reports the count of fully-correct studies without revealing which
  - Hint button reveals a full study's values and is capped at 2 uses per puzzle
  - Chapter 2 stays locked until 3 Chapter-1 solves are recorded, then unlocks; same for Chapter 3
  - Daily Challenge allows exactly one completion per UTC day and generates a share string that never contains puzzle content
  - Stats (checks/hints totals, streak) persist correctly across a simulated reload (re-reading localStorage)
  - AI explainer falls back to the deterministic template with no key present, and the fallback text correctly reflects the Confound-Control/Threat-to-Validity pairing from the actual solved puzzle
  - AI explainer handles a mocked successful fetch and a mocked failed fetch (network error) without throwing, both times still rendering something useful
  - Edge case: a puzzle with the minimum clue count (Chapter 3, aggressively pruned) still solves correctly against the stored solution

## Success Criteria

1. All tests pass (zero failures)
2. Every generated puzzle (all 3 chapters, at least 20 random seeds each in tests) has a solver-verified unique solution and a minimal clue set
3. The Daily Challenge is deterministic per UTC date and gated to one completion per day
4. Chapter unlock gating and persistent stats survive a page reload (localStorage round-trip)
5. The optional AI panel works correctly both with a live-call mock and with no API key present (deterministic fallback), and never sends anything beyond the puzzle's own category values to any network endpoint

---

## Scope Changes

- Deferred: a dedicated "pencil marks" elimination-notes grid (secondary to the answer grid) was considered during design but cut to keep the core deduction loop (clues → answer grid → check) tight and fully testable in one session. Recorded in FutureFeatures.md as a strong first extension.
