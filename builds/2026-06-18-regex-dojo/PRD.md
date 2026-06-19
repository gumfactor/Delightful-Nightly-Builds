# PRD — Regex Dojo

## Goal

A browser-based puzzle game with 20 progressive levels where the player writes regular expressions to match a set of target strings while rejecting a set of forbidden strings — teaching practical regex fluency through puzzle-solving.

---

## User Story

As a developer who uses regex regularly but reaches for a reference every time, I want a fun, self-paced puzzle game that forces me to recall and apply regex syntax under light pressure, so that the patterns become intuitive rather than something I have to look up.

---

## Scope

### In scope
- 20 puzzle levels, one per core regex concept (literals → lookaheads)
- Each level has 3–5 strings to MATCH and 3–5 strings to REJECT
- Real-time feedback as the player types: each string shows ✓ or ✗ immediately
- Submit button enabled only when all conditions are satisfied
- Hint button per level (reveals the concept being tested, not the answer)
- Level select screen showing locked/unlocked/complete status
- Progress persisted in `localStorage`
- Dark terminal aesthetic (monospace, green/red, dark panels)
- Single-file delivery — all CSS and JS inline in `index.html`
- No external dependencies or CDN calls

### Out of scope
- User accounts / leaderboard
- Custom level editor
- Timed mode / speedrun
- Backend or server
- External API calls
- Multiplayer

---

## Tech Stack

- Vanilla HTML5 / CSS3 / ES6 — all inline in `index.html`
- `localStorage` for progress persistence
- `@playwright/test` (v1.56.1) for tests
- No build step, no dependencies to install for the game itself

---

## Data Structure

### Level object (embedded in game JS)
```javascript
{
  id: 1,                    // 1-indexed, used in UI
  title: "string",          // short puzzle name
  concept: "string",        // regex feature being taught
  description: "string",    // puzzle instructions
  hint: "string",           // conceptual hint (no answer)
  match: ["string", ...],   // strings the regex must match (3–5)
  reject: ["string", ...]   // strings the regex must NOT match (3–5)
}
```

### State object (persisted to localStorage key `regex-dojo-state`)
```javascript
{
  completed: [1, 3, 5],     // array of completed level IDs (1-indexed)
  lastLevel: 2              // last level the player was on
}
```

---

## Folder Structure

```
builds/2026-06-18-regex-dojo/
├── PRD.md                    ← this file
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html                ← entire game (HTML + CSS + JS inline)
├── playwright.config.js      ← Playwright config
└── tests/
    └── game.spec.js          ← all 20+ Playwright tests
```

---

## Testing Strategy

Tests use Playwright with `file://` URLs (no server required). Each test calls `page.addInitScript(() => localStorage.clear())` before loading, ensuring a fully clean initial state.

**Coverage plan:**
- Page load and initial render (title, level select view visible)
- Level select: 20 levels shown, first level unlocked, others locked initially
- Entering a correct regex: all match strings show ✓, all reject strings show ✗
- Submit button gating: disabled with empty/wrong regex, enabled with correct regex
- Level completion: submitting advances state, progress counter updates
- Hint button: reveals hint text on click
- Invalid regex: does not crash, shows error indicator
- Level navigation: clicking level in level select opens game view for that level
- Multi-level flow: completing level 1 unlocks level 2, completion marker appears in level select
- Regex specifics: correct patterns for levels 1 and 2 verified end-to-end

---

## Success Criteria

1. **All 20 levels load and display correctly** — each level shows its title, description, match/reject strings, and hint button.
2. **Real-time feedback works** — typing a regex immediately updates ✓/✗ indicators on every string without requiring a page action.
3. **Submit gating is correct** — the submit button is disabled unless every match string matches and every reject string doesn't match.
4. **Progress persists** — completing a level and reloading the page shows that level as complete in the level select.
5. **All tests pass** — `npx playwright test` runs with zero failures (minimum 20 tests).
