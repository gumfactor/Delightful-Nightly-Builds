# PRD — Confound Hunter

## Goal
A browser game that trains research-methods literacy by having the player diagnose the single biggest methodological flaw in short, hand-authored study vignettes.

## User Story
As a professor who teaches research methods and runs a lab, I want a quick, replayable game that sharpens my (and eventually my students') ability to spot classic study-design flaws under time pressure, so that the skill stays sharp between semesters and feels like play rather than another reading assignment.

## Scope

### In Scope
- 30 hand-authored research vignettes spanning a 10-item flaw taxonomy (3 vignettes per flaw type), grouped into 3 chapters of increasing subtlety (obvious → subtle wording → near-miss distractors).
- **Practice mode**: sequential chapters, each a 10-question round with instant per-question feedback (highlighted correct/incorrect option + explanation), a running streak counter, and an end-of-chapter grade (A–F) with a 70%-accuracy pass gate that unlocks the next chapter.
- **Daily Challenge**: a 5-vignette round chosen deterministically from the full 30-item pool by the current UTC date (same date → same 5 vignettes for everyone, matching the "one attempt per day" convention of daily puzzle games), with a shareable emoji result string and a hard gate against replaying the same UTC date.
- **Mastery Dashboard**: per-flaw-type accuracy tracked across every question ever answered (practice + daily), rendered as 10 progress bars, so the player can see exactly which flaw types they personally struggle with.
- Progress (chapter unlocks, best accuracy, mastery counts, daily-challenge state) persisted in `localStorage`; a Reset Progress control clears it.
- Fully self-contained, single-page vanilla HTML/CSS/JS — no build step, no external network calls, opens directly via `file://`.

### Out of Scope
- User-submitted vignettes or an editor for adding new scenarios (a fixed, curated deck is the deliverable for this session — see `FutureFeatures.md`).
- Multiplayer / leaderboards (no backend; this is a local, single-player tool).
- AI-generated vignettes at runtime (would need a runtime `ANTHROPIC_API_KEY` and introduces non-reviewed pedagogical content; the curated 30-vignette deck is intentionally hand-vetted for the launch version).
- Difficulty beyond 3 chapters (30 vignettes is the right ambitious-but-shippable size for one session; expanding the deck is a future-feature).

## Tech Stack
- Vanilla HTML/CSS/JS, classic `<script>` tags (no ES modules, no bundler) — opens directly via `file://`, consistent with the repo's prior G-category builds.
- Playwright for tests (`@playwright/test`, pinned in `package.json`).
- No external APIs and no `ANTHROPIC_API_KEY` dependency — the core game is fully self-contained pedagogical content, evaluated with pure client-side logic.

## Data Structure
- `src/data.js` (global classic-script vars, no modules):
  - `FLAW_ORDER`: array of 10 flaw-type ids in fixed order.
  - `FLAW_TYPES`: object keyed by flaw id → `{ name, description }`.
  - `VIGNETTES`: array of 30 objects → `{ id, chapter (1-3), flaw (correct flaw id), text, options (array of 4 flaw ids, correct + 3 distractors, fixed order), explanation }`.
- `localStorage` keys (namespaced `confoundHunter_*`):
  - `confoundHunter_progress` → `{ "1": {passed, bestAccuracy}, "2": {...}, "3": {...} }`
  - `confoundHunter_mastery` → `{ "<flawId>": {correct, total}, ... }` for all 10 flaw ids
  - `confoundHunter_daily` → `{ date: "YYYY-MM-DD", vignetteIds: [..5 ids..], results: [bool x5] }` or `null` if not yet played today

## Folder Structure
```
builds/2026-07-15-confound-hunter/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── playwright.config.js
├── index.html
├── src/
│   ├── data.js       — flaw taxonomy + 30 vignettes
│   ├── app.js         — game engine, screen router, localStorage persistence
│   └── styles.css     — layout, dark-mode-first theme, mobile-responsive
└── tests/
    └── game.spec.js    — Playwright test suite
```

## Testing Strategy
- Playwright, driving the real `index.html` via a static file server (`file://` also works since there are no ES modules).
- Cover: data integrity (30 vignettes, valid flaw ids, exactly one correct option per vignette), practice-mode question flow (answer selection, correct/incorrect feedback rendering, streak tracking, chapter-end grade computation), chapter unlock gating (chapter 2/3 locked until the prior chapter is passed at ≥70%), daily-challenge determinism (same UTC date → same 5 vignette ids) and its one-play-per-day gate, share-string generation, mastery-dashboard persistence and accuracy math, localStorage round-tripping across reload, the reset control, and basic XSS-safety of vignette/explanation rendering (no `innerHTML` from anything resembling user input — there is none, but rendering must still use safe DOM APIs).
- Minimum 15 tests; target higher given three integrated features (practice, daily, mastery).
- Run with `npx playwright test`.

## Success Criteria
1. All 3 practice chapters (30 vignettes total) are playable end-to-end with correct/incorrect feedback and an accurate chapter-end grade; chapters 2 and 3 are locked until the previous chapter is passed at ≥70% accuracy.
2. The Daily Challenge selects the same 5 vignettes for the same UTC date (deterministic), blocks a second attempt on the same date, and produces a correct shareable emoji-result string.
3. The Mastery Dashboard accurately reflects per-flaw-type correct/total counts across both practice and daily play, persisted across a page reload.
4. All vignette/explanation content renders safely (no raw HTML injection risk) and the full test suite (≥15 tests) passes with zero failures.
5. Progress persists correctly in `localStorage` across reloads, and the Reset control fully clears it back to a fresh-install state.
