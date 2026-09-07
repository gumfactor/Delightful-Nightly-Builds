# PRD — True Course

> **Build date:** 2026-09-07
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project
> **Day of week:** Monday

---

## Goal

A browser navigation-puzzle game that teaches real small-boat seamanship — set-and-drift course correction, tide-window timing, COLREGS right-of-way, and IALA buoyage — through procedurally generated puzzles whose answers are always computed live from real navigational math, never hand-authored or hardcoded.

## User Story

As a boat owner and cottage-life enthusiast who has never had a nightly build touch boating in 90+ prior builds, I want to practice the actual math and rules real boaters use (correcting a heading for current, judging a safe tide window, knowing who gives way, reading a buoy), so that I build genuine intuition for seamanship instead of playing a generic trivia quiz wearing a nautical skin.

## Scope

### In Scope
- **Four independent puzzle engines**, each real navigational math/rules, not flavor text:
  1. **Set & Drift** — given a desired track bearing, distance, boat speed through water, and a current's set/drift, compute the course to steer, resulting speed over ground, and ETA (vector-triangle navigation, closed-form solution, numerically cross-checked by reconstructing the resultant vector).
  2. **Tide Window** — given a low tide and the next high tide (time + height), a charted depth, a boat's draft, and a safety margin, compute the exact time the rising tide first provides safe depth, using a cosine (harmonic) interpolation model between the two known extremes.
  3. **Right of Way** — given two vessels' headings and the bearing between them, classify the encounter as head-on, overtaking, or crossing per COLREGS Rules 13/14/15 and identify the give-way vessel, using a real geometric rule engine (22.5°-abaft-the-beam overtaking threshold, reciprocal-course head-on window, starboard-side crossing rule).
  4. **Buoyage** — given IALA System B rules ("red right returning," used in Canada/US), identify which side to pass a buoy on, its shape (can/nun), and its expected color from its number's parity.
- **Voyage Mode** — 4 chapters (Buoyage → Right of Way → Tide Window → Set & Drift), each chapter's rounds freshly generated every playthrough (never a fixed bank), 70%-accuracy gate to unlock the next chapter.
- **Practice Mode** — unlimited generated rounds, pick any single puzzle type.
- **Daily Challenge** — UTC-date-seeded, deterministic 5-round mix (same puzzles for everyone on a given day), one attempt per UTC day, shareable ⚓/🌊 emoji-grid result.
- **Mastery Dashboard** — per-type attempt/accuracy tracking and chapter-unlock state, persisted in `localStorage`.
- **Canvas 2D visuals** — compass-rose vector diagram (Set & Drift), two-vessel relative-bearing diagram (Right of Way), tide-height curve (Tide Window) — hand-drawn, no charting library.
- **Optional "First Mate's Log"** — after completing a voyage or the daily challenge, an optional direct-browser call to the Anthropic API (session-only key, aggregate score/type breakdown only, never sent per-answer data) returns a short nautical-flavored commentary; unconditional deterministic-template fallback with zero network calls when no key is supplied.

### Out of Scope
- Real chart/GPS data or live weather/tide feeds (Open-Meteo has no tide data; this is a self-contained math trainer, not a live tide predictor — the cosine model is a documented simplified approximation, not tide-table-grade precision)
- IALA System A (used outside North America) — System B only, matching the user's Canadian/US boating context
- Sailing-vessel-specific COLREGS rules (Rule 12, wind-on-different-sides) — power-driven-vessel rules only (13/14/15), documented as a scope cut
- Multiplayer or server-side leaderboards

## Tech Stack

- **Language:** Vanilla HTML/CSS/JS (classic `<script>` tags, no ES modules, opens directly via `file://`)
- **Framework:** None
- **Dependencies:** `@playwright/test` 1.56.1 (dev/test only); Anthropic API (optional, direct browser call, user-supplied session-only key)
- **Runtime requirement:** Open `index.html` directly in a browser — no build step, no server

## Data Structure

All game state is client-side only:
- **Engine functions** (`src/engine.js`) are pure — take numeric inputs, return computed results, no I/O.
- **Puzzle generators** (`src/generator.js`) produce plain-object puzzle instances: `{type, params, correctAnswer, distractors?}`, using a seeded PRNG (mulberry32) — date-seeded for Daily Challenge, `Math.random()`-seeded otherwise — with rejection sampling to guarantee unambiguous (non-boundary) scenarios.
- **Persisted state** (`localStorage`, key `trueCourseState_v1`): per-type `{attempts, correct}`, chapter unlock booleans, `dailyChallenge: {date, completed, score}`.
- No file I/O, no external data files, no server.

## Folder Structure

```
builds/2026-09-07-true-course/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── playwright.config.js
├── index.html
├── styles/
│   └── main.css
├── src/
│   ├── engine.js
│   ├── generator.js
│   ├── render.js
│   └── app.js
└── tests/
    ├── engine.spec.js
    ├── generator.spec.js
    ├── ui.spec.js
    └── security.spec.js
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test` 1.56.1)
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Set & Drift: closed-form course-to-steer matches an independently reconstructed vector sum (resultant direction equals desired track within floating-point tolerance); an unsolvable case (current faster than boat's cross-track capability) is detected and reported, not NaN.
  - Tide Window: cosine model correctly reproduces the given low/high boundary values at their exact times; computed crossing time correctly satisfies `height(t) == requiredHeight`; an "always passable" case (charted depth already exceeds draft+margin) short-circuits to the full window.
  - Right of Way: head-on, overtaking, and crossing scenarios are each correctly classified from a hand-worked reference case; the give-way vessel determination is symmetric (swapping "you"/"other" swaps the answer correctly).
  - Buoyage: red/green + inbound/outbound → correct side; color → correct shape; number parity → correct expected color.
  - Puzzle generators: 200 generated instances of each type never produce a boundary/ambiguous scenario (rejection sampling holds) and every generated instance's stored `correctAnswer` matches a fresh call to the engine on the same params (no drift between generation and validation).
  - Daily Challenge determinism: two independent seedings with the same UTC date produce an identical 5-round puzzle set; a different date produces a different set.
  - UI happy path: Voyage Mode chapter 1 playable end-to-end, correct/incorrect answers update the mastery dashboard, chapter unlocks at 70% accuracy.
  - Security: a `<script>`/`<img onerror>` payload typed into the optional API-key-gated AI note path never executes (mocked Anthropic response), verified via zero `dialog`/`pageerror` events.
  - Edge cases: 0-knot current (drift has zero effect), current exactly on the beam (β=90°), tide range of zero (flat tide, no window math needed).

## Success Criteria

1. All tests pass (zero failures)
2. Every puzzle's correct answer is computed live from the same engine used to validate the player's input — no puzzle instance in Voyage, Practice, or Daily Challenge mode has a hardcoded or hand-authored answer
3. Voyage Mode is playable end-to-end through all 4 chapters with the 70%-accuracy unlock gate working correctly
4. Daily Challenge produces an identical puzzle set for all players on the same UTC date (deterministic seeding verified by test) and gates to one attempt per day
5. No user-controlled or AI-response text ever reaches `innerHTML` — verified live in headless Chromium against injected payloads with zero dialogs/console errors

---

## Scope Changes

(none — filled in during/after build if scope changes)
