# Future Features — Heuristic Hunt

> Ideas for extending this build. The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Timed mode** — an optional 10-second-per-question timer in Practice and Daily Challenge modes, tracking average response time alongside accuracy. Rewards fast, confident recognition rather than slow deliberation.
2. **Explanation-first review screen** — a "Review Missed Questions" button after any completed session that re-lists only the vignettes the player got wrong, with their explanations, for quick spaced-repetition-style re-reading.
3. **Keyboard shortcuts** — number keys 1-4 to select an answer and Enter/Space to advance, so a desktop user can play a full chapter without touching the mouse.
4. **Streak milestone toasts** — a small celebratory message at 5/10/25-correct-answer streak milestones, reusing the existing `currentStreak`/`bestStreak` state that's already tracked but currently only shown as plain text on the menu.

## Medium Effort (roughly one nightly build session)

5. **Investment-specific chapter** — a fourth, opt-in chapter built entirely from portfolio/trading-decision vignettes (the "Market Cap Higher or Lower" and "Stock Chart Direction Quiz" backlog ideas could feed distractor-quality content here), directly extending the quantitative-investing tie without diluting the general-purpose taxonomy in Chapters 1-3.
6. **AI-generated vignette mode** — an optional Anthropic API key (session-only, browser-supplied, matching the pattern used by CircuitLab and Bayes Lab) that generates fresh, on-the-fly vignettes for a chosen bias, checked against the deterministic taxonomy so grading stays defensible (the AI writes the scenario; the app still owns the ground-truth answer).
7. **Two-bias "trap" questions** — a harder difficulty tier where a vignette plausibly involves two overlapping biases and the player must pick the more central one, with the explanation addressing why the second bias is present but secondary. This is a natural extension of Chapter 3's existing "requires nuance" design intent.

## Ambitious Extensions (multi-session effort)

8. **Cross-build bias library** — expose `HH.BIASES` and `HH.VIGNETTES` as a small importable data module that a future Learning Aid or Data Explorer build (e.g., a "spot the bias in this paper's discussion section" tool) could reuse, turning this taxonomy into shared infrastructure rather than a one-off game asset. Would need copying, not cross-folder importing, per the "never import from another build's folder" hard standard.

---

## Possible Integration Points

Confound Hunter (2026-07-15) proved the exact chapter/unlock/Daily-Challenge/Mastery-Dashboard architecture this build reuses — a future build could generalize that shared shell into a small reusable "vignette game engine" template that both builds (and future ones) could be re-authored against, reducing duplicated app.js logic across the catalog's growing family of vignette-quiz games (Neurofact, Synapse Sort, Confound Hunter, Heuristic Hunt).

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| All 30 vignettes are fixed at build time; the pool never grows without a code change | Ship a small "community vignette" JSON file the user could hand-edit locally to add their own scenarios, loaded as an optional overlay on top of the built-in set |
| Practice mode's shuffle uses `Math.random`, so replaying "All Biases" gives a different order each time with no way to resume a partially-completed practice set | Persist an in-progress practice session to localStorage so a page reload mid-practice doesn't lose position |
| No visual distinction between "this bias I've never tried" and "this bias I got 0% on" beyond the Mastery Dashboard's gray-vs-red bar color, which a colorblind user could find hard to tell apart at a glance | Add a text label (e.g. "Not attempted" is already textual, but add matching iconography/pattern-fill, not just color, to the bar itself for colorblind-safe redundancy) |
