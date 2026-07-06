# PRD — Synapse Sort

> **Build date:** 2026-07-06
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project
> **Day of week:** Monday

---

## Goal

A daily category-sorting puzzle game (in the style of NYT Connections) with a hand-curated puzzle bank drawn from the user's own intellectual life — neuroscience/psychology, AI & agentic workflows, investing/markets, Canadian business, and running/golf/boating.

## User Story

As a psychology professor and indie builder who enjoys daily puzzle games and wants something personally resonant rather than generic trivia, I want to play a short, sharp daily "find the connection" puzzle drawn from my own fields and interests, so that I get a two-minute mental warm-up that feels made for me instead of a mass-market clone.

## Scope

### In Scope
- 4x4 grid of 16 words/phrases; find four hidden groups of 4 that share a category
- Curated bank of 30 hand-written puzzles spanning 5 personal-interest domains (neuroscience/psych, AI & agents, investing/markets, Canadian business, fitness/outdoors), each with 4 categories tagged by difficulty (yellow=easy, green=medium, blue=hard, purple=tricky)
- Deterministic "daily puzzle" selection: today's puzzle is derived from the UTC calendar date so it's stable across reloads and the same for the whole day, cycling through the bank
- Archive/Practice mode: browse and play any of the 30 puzzles by title, independent of daily stats
- Select up to 4 tiles, submit a guess; correct guesses lock that category into a solved row (color + label); incorrect guesses count against a 4-mistake limit
- "One away" hint when exactly 3 of the 4 selected tiles belong to the same true category
- Shuffle button to re-randomize tile layout without changing puzzle state
- Deselect-all button
- Win screen (all 4 categories solved) and lose screen (4 mistakes reached, reveals remaining answers) with a shareable emoji result grid (copy-to-clipboard, no external service)
- Local stats: games played, wins, current streak, best streak, average mistakes — tracked only for daily plays, persisted in `localStorage`; practice-mode plays do not affect streak
- Colorblind-safe design: each difficulty tier also carries a text label, not color alone
- Dark/light mode via `prefers-color-scheme` plus a manual toggle
- Mobile-responsive layout (grid reflows on narrow screens)

### Out of Scope
- Server-side puzzle delivery or accounts — everything ships as static files, played via `file://` or any static server
- AI-generated puzzle content at runtime — puzzles are authored once, at build time, and shipped as static data (no `ANTHROPIC_API_KEY` was available in this session's environment, and a static client-side game has no secure way to call it at runtime anyway)
- Puzzle editor / user-submitted puzzles
- Multiplayer or leaderboards
- Automatic daily puzzle rotation beyond the 30-puzzle bank (it wraps around after 30 days — documented as a known limitation)

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic scripts — no bundler, no ES modules, so it opens directly via `file://`)
- **Framework:** None
- **Dependencies:** None (no CDN libraries needed for this build)
- **Runtime requirement:** Open `index.html` directly in any modern browser; no install, no server, no API key needed

## Data Structure

Puzzle bank lives in `src/puzzles.js` as a global `const PUZZLES = [...]` array (classic script, no imports needed). Each puzzle:

```js
{
  id: "p01",
  title: "Short descriptive title (shown in archive list)",
  categories: [
    { name: "Category label revealed on solve", difficulty: "yellow", items: ["ITEM A", "ITEM B", "ITEM C", "ITEM D"] },
    { name: "...", difficulty: "green",  items: [...] },
    { name: "...", difficulty: "blue",   items: [...] },
    { name: "...", difficulty: "purple", items: [...] }
  ]
}
```

Invariants enforced by both authoring and tests: exactly 4 categories per puzzle, exactly 4 items per category (16 unique item strings total per puzzle), one difficulty of each tier per puzzle.

Runtime state (`src/game.js`) is in-memory only: current puzzle, tile order, selected tiles, solved categories, mistake count, guess history (for the share grid). Persisted state (`src/storage.js`) is `localStorage` only:

```js
// key: "synapseSort.stats"
{
  gamesPlayed: number,
  wins: number,
  currentStreak: number,
  bestStreak: number,
  totalMistakes: number,
  lastPlayedDate: "YYYY-MM-DD",   // UTC, daily mode only
  history: { "YYYY-MM-DD": { won: bool, mistakes: number } }
}
```

## Folder Structure

```
builds/2026-07-06-synapse-sort/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── playwright.config.js
├── src/
│   ├── styles.css
│   ├── puzzles.js
│   ├── storage.js
│   └── game.js
└── tests/
    ├── puzzle-data.spec.js
    ├── daily-selection.spec.js
    ├── gameplay.spec.js
    ├── win-lose.spec.js
    └── stats-archive.spec.js
```

## Testing Strategy

- **Framework:** Playwright
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Puzzle bank integrity: 30 puzzles, each with 4 categories x 4 unique items, one of each difficulty tier
  - Deterministic daily puzzle index: same UTC date always yields the same puzzle; index wraps correctly (modulo) across the bank length, including far-future dates
  - Grid renders all 16 tiles on load; tile selection toggles, max 4 selected enforced, submit button only enabled at exactly 4 selected
  - Correct guess locks a category into the solved area with its label and difficulty color; incorrect guess increments mistakes and clears selection
  - "One away" message appears only when exactly 3 of 4 selected tiles share a true category
  - Loss triggers at 4 mistakes and reveals all remaining answers; win triggers when all 4 categories are solved
  - Share-grid text is generated correctly from guess history (colored square per guess, in order)
  - Shuffle changes tile order but not tile identity or count; deselect-all clears the current selection
  - Stats persist to `localStorage` correctly after a win (streak increments) and after a loss (streak resets), and are not touched by practice-mode play
  - Archive mode loads a specific non-daily puzzle by id, independent from the daily puzzle

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests
2. The 30-puzzle bank passes data-integrity checks (4x4 structure, no in-puzzle duplicates, one of each difficulty)
3. A full game can be played end-to-end in a browser to both a win and a loss, with correct stats and share-grid output
4. Daily puzzle selection is stable within a day and different across most days, verified deterministically in tests
5. The build is fully self-contained — opens via `file://` with zero network calls, zero credentials, zero external dependencies

---

## Scope Changes

None — the AI-generation angle (using `ANTHROPIC_API_KEY` to author puzzles) was dropped before the PRD was written because the key was not present in this session's environment; puzzle content is instead hand-authored directly, which the PRD reflects as the actual plan rather than a deviation discovered mid-build.
