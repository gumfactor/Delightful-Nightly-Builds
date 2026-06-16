# PRD — Spaced Repetition Flashcards

## Goal

A browser-based flashcard app implementing the SM-2 spaced repetition algorithm with localStorage persistence and three pre-built decks targeting the user's active learning goals, so review sessions surface only the right cards at the right time.

## User Story

As someone learning Bayesian statistics and Git while maintaining Python research skills, I want to open a single HTML file each day and review a short queue of flashcards where the algorithm shows me weaker cards more often, so I retain knowledge progressively without wasting time on material I already know well.

## Scope — In

- **SM-2 algorithm** (full implementation):
  - Ease factor (EF) per card, starts at 2.5, minimum 1.3
  - Interval progression: rep 0 → 1 day, rep 1 → 6 days, rep ≥ 2 → round(prev × EF)
  - Rating qualities: 0 (Again), 2 (Hard), 3 (Good), 5 (Easy)
  - EF adjustment formula: EF += 0.1 − (5−q) × (0.08 + (5−q) × 0.02)
  - Fail (q < 3) resets repetitions to 0 and interval to 1
- **Card states**: new (never rated), due (due date ≤ today), learned (future due date)
- **Daily study queue**: due cards first (oldest due date first), then new cards up to limit of 20/day
- **Three pre-built decks**:
  1. Bayesian Statistics — 20 cards (prior/posterior, MCMC, credible intervals, diagnostics)
  2. Python Research Patterns — 15 cards (pandas, scipy, argparse, pathlib, pytest)
  3. Git & GitHub Workflows — 15 cards (undo, stash, bisect, blame, branch management)
- **Persistence**: all card states saved to `localStorage` as JSON under key `srf_state_v1`
- **UI**:
  - Header: app title + deck selector tabs
  - Stats bar: due count, new count, done count (current session)
  - Card view: question shown first, "Show Answer" button reveals answer + rating buttons
  - Rating buttons: Again (red) / Hard (amber) / Good (green) / Easy (blue)
  - Done screen: shown when queue is exhausted for the session
- **Dark theme** (mobile-first, comfortable for phone review)
- **Mobile-responsive**: works at 375px width without horizontal overflow
- Single `index.html` — no server, no build step, no external CDN

## Scope — Out

- User deck creation or card editing in the UI
- Markdown or rich text rendering in cards
- Audio, images, or LaTeX rendering
- Cloud sync or export
- Undo last rating
- Statistics history / retention graphs (FutureFeatures)

## Tech Stack

- Vanilla HTML5 / CSS3 / ES6+ JavaScript
- `localStorage` for persistence
- Playwright (Chromium) for tests — minimum 23 tests

## Data Structure

**Deck format (embedded in HTML):**
```json
{
  "deckId": {
    "name": "Deck Display Name",
    "cards": [
      { "id": "unique-card-id", "front": "Question text", "back": "Answer text" }
    ]
  }
}
```

**Card state in localStorage (key: `srf_state_v1`):**
```json
{
  "deckId::cardId": {
    "ef": 2.5,
    "interval": 1,
    "repetitions": 0,
    "due": "2026-06-16",
    "lastRating": null
  }
}
```

## Folder Structure

```
builds/2026-06-16-spaced-repetition-flashcards/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html               ← single-file web app (all CSS + JS inline)
├── playwright.config.js
└── tests/
    └── flashcards.spec.js   ← 23 Playwright tests
```

## Testing Strategy

Tests live in `tests/flashcards.spec.js` and are run with `npx playwright test` from the build folder.

**SM-2 algorithm tests (via `page.evaluate`)** — test the `window.SM2` object directly without UI interaction:
1. Rating 0 resets repetitions to 0
2. Rating 0 resets interval to 1
3. Rating 3 on first repetition sets interval to 1
4. Rating 3 on second repetition sets interval to 6
5. Rating 3 on third repetition multiplies interval by EF
6. Rating 5 increases EF by 0.1
7. Rating 0 decreases EF by approximately 0.8
8. EF never drops below 1.3 floor
9. `isDue` returns true when due date is today
10. `isDue` returns false when due date is in the future
11. `isNew` returns true for a fresh card (no prior rating)
12. `isNew` returns false after any rating

**UI interaction tests (Playwright clicks/assertions):**
13. Page loads without console errors
14. Three deck tabs are visible
15. Stats bar shows due and new counts
16. "Show Answer" button is visible on card front
17. Clicking "Show Answer" reveals the card back
18. Four rating buttons are visible after reveal
19. Clicking "Good" advances to the next card (card front changes)
20. Switching deck tabs loads a different deck
21. Done screen appears when all cards are pre-scheduled for the future
22. Page has a dark background
23. No horizontal overflow at 375px viewport width

## Success Criteria

1. All 23 Playwright tests pass with zero failures
2. On a fresh install, opening `index.html` immediately shows the first card of the Bayesian deck, with a queue of all 20 cards
3. Rating a card saves its new state to `localStorage` — confirmed by page reload showing the card due on its scheduled future date (no longer in the new queue)
4. Switching decks shows cards from that deck's content with correct counts in the stats bar
5. The page is usable on a 375px-wide mobile screen with no horizontal scroll
