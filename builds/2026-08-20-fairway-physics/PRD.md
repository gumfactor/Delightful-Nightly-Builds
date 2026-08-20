# PRD — Fairway Physics

> **Build date:** 2026-08-20
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious Project
> **Day of week:** Thursday

---

## Goal

A browser golf game where every shot is resolved by a real, hand-built physics model (club distance, wind, elevation, shot-shape curve, roll, and lie) rather than a quiz, sort, or word mechanic — the first Category G build built around a simulation engine instead of trivia/vignette/word content.

## User Story

As a psychology professor and indie builder who lists golf as a personal interest but has never had a nightly build engage it, I want to play a physically-grounded golf round in my browser — picking clubs, shaping shots, and reading wind — so that I get a genuinely different kind of game night than the six quiz/sort/word-guess Category G builds already in the catalog.

## Scope

### In Scope
- A from-scratch, dependency-free physics engine (pure functions, no DOM) covering: per-club carry distance vs. power, headwind/tailwind and crosswind effects (with lateral drift), elevation change effects, draw/fade/straight shot-shape curve, post-landing roll (varies by lie), lie classification (fairway/rough/bunker/water/OB/green), stroke-and-distance water/OB penalty, and a separate on-green putting model (power, aim/break, capture radius)
- 9 hand-authored holes (mix of par 3/4/5, real yardages, dogleg corridors, bunkers, water hazards, OB, elevation change) rendered top-down on an HTML5 Canvas, with the ball's flight path animated per shot
- Two modes: **Daily Round** (UTC-date-seeded wind per hole, one completion per UTC day, shareable ⛳ emoji scorecard) and **Practice** (play any single hole repeatedly, optional wind shuffle, no daily gate)
- Full 9-hole scorecard (strokes vs. par per hole, running total, standard golf score names: Eagle/Birdie/Par/Bogey/Double Bogey+)
- Persistent `localStorage` stats: rounds completed, best round score, per-hole average, practice attempts
- Optional "Ask the Caddie" AI tip: sends only hole geometry/wind/lie numbers (no personal data) to Claude Haiku via a direct browser call using a session-only, user-entered API key; unconditional deterministic rule-based fallback tip when no key is set or the call fails/errors
- Mobile-responsive layout; keyboard- and touch-usable controls

### Out of Scope
- True 3D rendering or realistic ball-flight arcs (top-down 2D with an animated flight-path line stands in for a real trajectory)
- Polygon-shaped hazards/fairways (rectangular/circular zone geometry only — sufficient for dogleg corridors and hazard placement, not photorealistic course shapes)
- Club fitting, equipment customization, or multiplayer
- Persisting the Anthropic API key (it is held in memory for the session only, matching the pattern used by prior direct-browser-call builds)
- Wind/weather sourced from a live weather API (would require networked "current conditions" that don't meaningfully improve a golf **simulation** game — the daily seed already gives fair, repeatable variety)

## Tech Stack

- **Language:** Vanilla HTML/CSS/JS (classic `<script>` tags, no ES modules, no bundler — opens directly via `file://`)
- **Framework:** None
- **Dependencies:** None (native Canvas 2D); Anthropic API called directly from the browser, optional, runtime-only key
- **Runtime requirement:** Open `index.html` directly in a browser, or serve statically. No install, no build step.

## Data Structure

- `src/course-data.js` defines `window.COURSE` = an array of 9 hole objects:
  `{ id, name, par, yardage, tee: {x,y}, pin: {x,y}, elevationChangeFt, greenRadius, zones: [{type: 'fairway'|'rough'|'bunker'|'water'|'ob', xMin, xMax, yMin, yMax}] }`
  — coordinates are in yards on a per-hole (X = lateral offset from centerline, Y = downrange distance from tee) plane; the canvas renderer scales this to pixels per hole.
- `src/engine.js` defines `window.FairwayEngine`, a set of pure functions operating on plain numbers/objects — no DOM access, so they are directly callable from both `app.js` and Playwright's `page.evaluate`.
- Game/session state lives in `app.js` module-scope variables (current hole, current position, stroke count, mode) — never persisted mid-round; only completed-round summaries and aggregate stats are written to `localStorage` under `fairwayphysics_*` keys.
- `localStorage` shape: `fairwayphysics_stats` = `{ roundsCompleted, bestRoundScore, totalStrokesByHole: [9 arrays of numbers], practiceAttempts }`; `fairwayphysics_daily_<YYYY-MM-DD>` = `{ completed: true, scorecard: [...] }` once that day's round is finished.

## Folder Structure

```
builds/2026-08-20-fairway-physics/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── playwright.config.js
├── src/
│   ├── engine.js         (pure physics/scoring/lie/putting functions)
│   ├── course-data.js    (9 hole definitions)
│   ├── app.js            (UI wiring, canvas rendering, modes, persistence, AI caddie)
│   └── styles.css
└── tests/
    └── game.spec.js
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/game.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Physics engine pure functions (`window.FairwayEngine.*`) called via `page.evaluate` and checked against hand-computed reference values: carry distance scaling by power/club, headwind reduces / tailwind increases distance, crosswind produces correctly-signed lateral drift, uphill reduces / downhill increases effective distance, draw/fade curve direction
  - Lie classification against hand-built zone fixtures (fairway/rough/bunker/water/OB/green boundaries, including an off-course point)
  - Roll behavior (zero in bunker/water, reduced in rough, full on fairway/green)
  - Water/OB penalty adds exactly one stroke and resets position to the pre-shot spot
  - Putting: a putt landing within the capture radius holes out; one outside it repositions the ball on the green without holing
  - A full deterministic shot sequence on one hole produces the expected stroke count and score name (e.g. Par, Birdie)
  - Daily Round: same UTC date yields the same per-hole wind seed across two page loads; a second daily attempt on the same UTC date is gated after completion
  - Practice mode allows replaying a hole with no gate and does not affect the daily-completion flag
  - Stats persistence: completing a round updates `roundsCompleted`/`bestRoundScore` in `localStorage` and survives a reload
  - Course data integrity: all 9 holes have valid tee/pin/zone coordinates and required fields
  - XSS/injection safety: an injected `</script><script>` + `<img onerror>` payload in a hole name and an AI caddie tip renders as inert text with zero dialogs and zero extra script/img elements
  - AI caddie tip: a mocked successful API response renders safely; the deterministic fallback fires (zero network calls) when no key is set
  - Full 9-hole round completion renders a scorecard with all 9 holes, strokes, and a total relative-to-par score
  - Mobile viewport (375px) renders the canvas and controls without layout breakage

## Success Criteria

1. All tests pass (zero failures, minimum 15 tests)
2. The physics engine's core functions (carry distance, wind, elevation, shot-shape curve, roll, lie classification, putting) match hand-computed reference values in tests
3. A full 9-hole Daily Round can be completed end-to-end in the browser with deterministic per-hole wind seeded from the UTC date, gated to one completion per UTC day, ending in a scorecard with strokes vs. par per hole and a total score
4. Practice mode allows unlimited replay of any single hole independent of the Daily Round gate and stats
5. No XSS vulnerability: all dynamic text is rendered via `textContent`/escaping, verified by an injection-payload test producing zero dialogs and zero injected DOM elements

---

## Scope Changes

None recorded yet — will be updated here if scope changes during the build.
