# PRD — Agent Relay

> **Build date:** 2026-09-25
> **Category:** G — Game / Puzzle
> **Complexity:** Ambitious
> **Day of week:** Friday

---

## Goal

A browser puzzle game where the player assigns a dependency graph of tasks onto a limited number of parallel "agent" lanes to finish as fast as possible, scored against a from-scratch exact scheduling solver's provably optimal makespan.

## User Story

As a builder of AI agent workflows who is actively trying to master agent orchestration (PROFILE.md: "Master AI agent workflows and orchestration"), I want to practice the intuition for how task dependencies and limited parallelism interact by directly playing with a scheduling puzzle, so that I build a felt sense for why some tasks can run in parallel and others can't, without reading another article about it.

## Scope

### In Scope
- A deterministic scheduling engine: given a task DAG (id, name, duration, dependency ids) and a lane count, compute start/finish times for any valid placement sequence (a "ready task → lane" assignment built one placement at a time).
- A from-scratch exact solver (branch-and-bound over the same ready-queue formulation, with lower-bound pruning, lane-symmetry pruning, and a greedy initial upper bound) that finds the true minimum possible makespan for a given task DAG + lane count.
- 6 hand-authored "Campaign" levels of increasing size/complexity (3 to 9 tasks, 2 to 3 lanes), themed as a coding-agent's session tasks (clone repo, write code, run tests, review, ship).
- A procedurally generated **Daily Challenge**: a UTC-date-seeded random valid DAG (deterministic per date), one attempt per day, with a shareable emoji-grid result string.
- A **Tutorial** mode: a guided walkthrough of the simplest campaign level explaining the ready-task/lane mechanic step by step.
- **Practice mode**: unlimited replays of any unlocked campaign level.
- Click-to-place interaction: select a ready task, then click a lane to append it to that lane's queue. No native HTML5 drag-and-drop (avoids flakiness; more testable and touch-friendly).
- A live Canvas-rendered dependency graph (layered layout, arrows) showing the full task DAG with ready/placed/locked states color-coded.
- Per-lane timeline view showing placed tasks as duration-proportional blocks with start/finish labels.
- Scoring: Gold (matches optimal exactly), Silver (within `max(2, round(0.15 * optimal))` minutes of optimal), Bronze (any complete valid schedule).
- `localStorage` persistence: best (lowest) makespan/grade per campaign level, Daily Challenge streak + last-played date + today's result, viewable on a Dashboard screen.
- Optional "Mission Debrief" AI panel: on the result screen, if the user supplies their own Anthropic API key, a direct-browser call to Claude Haiku produces a short coaching note built strictly from the computed numbers (task names/durations/times only — no personal data). Unconditional deterministic fallback note with zero network calls when no key is set or the call fails.
- Mobile-responsive layout (lanes stack vertically under ~600px), dark mode by default with light-mode support via `prefers-color-scheme`.
- Security hardening: all DOM built via `createElement`/`textContent`, never `innerHTML`; AI responses and any user-visible strings rendered as inert text even if hostile.

### Out of Scope
- Native drag-and-drop reordering of already-placed tasks (placement order within a lane is final once placed; Reset clears the whole level instead of fine-grained undo).
- Multiplayer or server-synced leaderboards (single-player, local only).
- Editing/creating custom levels in the UI.
- A general-purpose RCPSP solver for arbitrary large instances (solver is tuned and tested for the puzzle's small task counts, ≤10).

## Tech Stack

- **Language:** Vanilla HTML/CSS/JS (classic `<script>` tags, no ES modules — opens directly via `file://`)
- **Framework:** None
- **Dependencies:** None at runtime. `@playwright/test` as a dev/test-only dependency.
- **Runtime requirement:** Open `index.html` directly in a browser, or serve statically. No build step, no install needed to play.

## Data Structure

```js
// A task in a level's DAG
Task = {
  id: string,        // unique within the level, e.g. "A"
  name: string,       // display name, e.g. "Write Unit Tests"
  duration: number,   // minutes, integer > 0
  deps: string[]      // ids of tasks that must finish first
}

// A level
Level = {
  id: string,
  title: string,
  flavor: string,     // one-line scenario blurb
  numLanes: number,
  tasks: Task[]
}

// Placement state during play (in-memory, not persisted mid-level)
PlacementState = {
  placed: { [taskId]: { lane: number, start: number, finish: number } },
  laneFreeAt: number[]   // length numLanes, next-free time per lane
}
```

`localStorage` key `agent-relay-progress-v1`:
```js
{
  campaign: { [levelId]: { bestMakespan: number, bestGrade: "gold"|"silver"|"bronze" } },
  daily: { lastPlayedDate: "YYYY-MM-DD", streak: number, history: { [date]: { grade, makespan, optimal } } }
}
```

## Folder Structure

```
builds/2026-09-25-agent-relay/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── .gitignore
├── package.json
├── package-lock.json
├── playwright.config.js
├── index.html
├── src/
│   ├── styles.css
│   ├── engine.js       (RNG, scheduling simulation, exact solver, grading, daily generator)
│   ├── levels.js        (hand-authored campaign level data + task name pool)
│   ├── graph.js          (Canvas dependency-graph renderer)
│   ├── ai.js              (optional Claude Haiku "Mission Debrief" panel + fallback)
│   └── game.js             (UI state machine, screens, event wiring, localStorage)
└── tests/
    ├── engine.spec.js       (Node-level: require src/engine.js directly)
    ├── game.spec.js          (Playwright: UI interaction, scoring end-to-end)
    └── security.spec.js       (Playwright: hostile-payload / XSS hardening)
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`); `engine.js`/`levels.js` are written to also `require()` directly from Node for fast, browser-free logic tests (same dual-export pattern as the 2026-09-16 Marginal Gains build's `engine.js`).
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Scheduling simulation: lane-free-time waiting, cross-lane dependency waiting, hand-computed fixture DAGs (diamond, chain, fully parallel).
  - Exact solver cross-verified against independent brute-force enumeration on randomized small DAGs (N≤6), plus known-closed-form cases (fully serial chain → sum of durations; fully parallel with lanes ≥ tasks → max single duration).
  - Daily Challenge generator: deterministic per UTC date, varies across dates, always acyclic, never degenerate (always has ≥2 root tasks and ≥⌈N/2⌉ edges when N≥4).
  - Grading boundaries (gold/silver/bronze) at exact threshold values.
  - AI panel: prompt contains only computed numbers/names (no personal data), zero network calls with no API key, deterministic fallback content, safe rendering of a mocked hostile API response.
  - UI: task placement via click-select-then-click-lane, Reset, Submit gating (only enabled once every task is placed), result screen shows the correct grade for a deterministically-reproduced known-optimal play-through, Dashboard best-score persistence (only improves, never regresses), Daily Challenge one-per-day gating, mobile viewport layout, zero console/page errors across a full playthrough, hostile-payload rendering safety.

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests, run via `npx playwright test`.
2. The exact solver's optimal makespan matches independent brute-force enumeration on every randomized cross-check fixture.
3. A full campaign playthrough (select level → place every task → submit) reaches the result screen with a grade computed from the documented gold/silver/bronze thresholds, verified against a hand-known deterministic play sequence.
4. The Daily Challenge is deterministic per UTC date (same date always yields the same puzzle) and gates to one attempt per day via `localStorage`.
5. The build has zero `innerHTML` usage and passes hostile-payload rendering tests with zero dialogs, zero page errors, and zero injected DOM nodes.

---

## Scope Changes

None — full scope as planned was completed.
