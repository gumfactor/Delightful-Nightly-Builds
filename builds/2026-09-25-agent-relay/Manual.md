# Manual — Agent Relay

## Opening it

Open `index.html` directly in any modern browser (double-click it, or `file:///path/to/builds/2026-09-25-agent-relay/index.html`). No build step, no server, no install required to play. Works offline.

## How to play

Each level is a small dependency graph of tasks (shown as the graph diagram at the top of the play screen) plus a fixed number of parallel "agent" lanes. Some tasks can't start until others finish — that's what the arrows mean.

1. The **Ready** tray shows every task whose dependencies are already placed. Click one to select it (it highlights).
2. Click a **lane** to place the selected task at the end of that lane's queue. The task's start/finish time is computed automatically: it starts as soon as both its lane is free *and* every dependency has finished, whichever is later.
3. Placing a task may unlock new tasks into Ready. Keep going until every task is placed.
4. Click **Submit**. You're graded against the true optimal schedule for that exact task graph and lane count, computed by an exact solver (not a guess or a heuristic — the shipped code brute-force-searches every valid placement, pruned for speed):
   - **Gold** — you matched the optimal exactly.
   - **Silver** — within `max(2, round(0.15 × optimal))` minutes of optimal.
   - **Bronze** — any complete, valid schedule outside that margin.
5. **Reset** clears the current level's placements and starts it over. **Exit** leaves without saving.

## Modes

- **Tutorial** — a guided 3-task walkthrough of the mechanic. Doesn't affect your saved progress.
- **Campaign** — 6 hand-built levels (3 to 9 tasks, 2-3 lanes) of increasing size. Levels unlock in order as you complete the one before it. Replay any unlocked level any time; your best (lowest) makespan per level is kept.
- **Daily Challenge** — a new puzzle every day (UTC), generated deterministically from the date, so everyone playing on the same day gets the same puzzle. One attempt per day; a completed streak counter tracks consecutive UTC days played. Clicking "Daily Challenge" again after you've played today re-shows today's result instead of letting you retry.
- **Dashboard** — your campaign best scores and your Daily Challenge streak, all read from this browser's `localStorage`.

## Mission Debrief (optional AI coaching)

On the result screen, you can paste your own Anthropic API key into the "Mission Debrief" box and click **Get Debrief** for a short plain-English coaching note from Claude Haiku about your run. The key is only ever used for a single direct browser call to `api.anthropic.com` — it is never stored, never sent anywhere else, and the page makes zero network calls at all if you leave the box empty. Without a key (or if the call fails), you still get a note — a deterministic, locally-computed one.

## Progress storage

Everything (campaign best scores, Daily Challenge streak/history) lives in this browser's `localStorage` under the key `agent-relay-progress-v1`, on this device only. Clearing site data resets it. Nothing is ever sent to a server.

## Running the tests

```
npm install
npx playwright test
```

48 tests across three files:
- `tests/engine.spec.js` — the scheduling engine, exact solver (cross-verified against independent brute-force search), grading, and the Daily Challenge generator, run directly under Node via `require()`.
- `tests/game.spec.js` — full browser UI interaction: placement, tutorial, campaign unlocking, Dashboard persistence, Daily Challenge gating, mobile layout, the AI panel.
- `tests/security.spec.js` — hostile-payload / XSS hardening checks.
