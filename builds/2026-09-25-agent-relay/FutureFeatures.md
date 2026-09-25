# Future Features — Agent Relay

1. **Theme-aware dependency graph.** `src/graph.js` uses a fixed dark-leaning palette for node fills/strokes regardless of `prefers-color-scheme`. In light mode the locked/ready/placed node colors still read fine (verified visually), but they'd look more native if `renderGraph` picked up the page's CSS custom properties instead of a hardcoded `STATE_COLORS` object.

2. **Undo last placement.** Right now Reset clears the whole level. A single "undo" that pops the most recent entry off `state.order` and recomputes the placement state from scratch (replaying all but the last placement) would let players correct one mistake without starting over — useful on the 8-9 task levels.

3. **A second Daily Challenge difficulty.** The daily generator is fixed at 5-7 tasks / 2-3 lanes. A "Daily Hard" variant (8-9 tasks, occasionally 2 lanes only) would give returning players more to chase once the campaign is fully cleared.

4. **Per-level leaderboard of your own attempt history**, not just the best score — a small local log of every completed attempt (timestamp, makespan, grade) per level, so a player can see whether they're actually getting faster over repeated plays, not just their single best.

5. **Export/import progress.** `localStorage` progress is single-device only. A "copy my progress as text" / "paste to restore" pair (just the JSON blob, base64'd) would let a player carry their streak and campaign scores to a different browser or after clearing site data.

6. **A "watch the optimal" replay.** After a non-gold result, animate the solver's actual optimal `assignment` (already computed and available in `solveOptimal`'s return value) onto the lane view step by step, instead of only stating the number — would make the gap between the player's schedule and the true optimum concretely visible rather than abstract.

7. **Custom level import.** A small JSON schema for a task list (id/name/duration/deps) that a player could paste in to build and solve their own dependency graphs — turns the game into a lightweight what-if tool for a real small project, not just fixed puzzles.
