# Future Features — Zebra Lab

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Pencil-marks elimination grid** — A secondary grid (rows = studies, columns = every possible value across all categories) where clicking a cell toggles a small "eliminated" mark, mirroring how people actually solve logic-grid puzzles on paper. This was the one feature deliberately cut from tonight's scope (see PRD.md Scope Changes) to keep the core loop tight; it's a pure front-end addition — the solver and clue data already support it, since nothing about elimination-tracking touches the CSP logic.
2. **Print/export a puzzle** — A "Print This Puzzle" button that renders the clue list and a blank grid as a clean printable page, for solving away from a screen.
3. **Difficulty indicator per puzzle** — Show the generated clue count next to a puzzle's title (fewer clues = harder), since it's already computed by the generator and currently discarded.

## Medium Effort (roughly one nightly build session)

4. **A fourth "Custom" chapter** — Let the player choose category count, grid size (up to 5), and which clue types are allowed, then generate on demand. The generator and solver already support arbitrary chapter configs (`data.js`'s `ZL_CHAPTERS` array is the only place difficulty is defined); this is mostly a settings UI plus input validation.
5. **Puzzle history / replay** — Persist the last N generated puzzles (not just aggregate stats) so a player can revisit or share a specific practice puzzle's seed with someone else, the same way the Daily Challenge is already shareable by date.
6. **A second taxonomy pack** — Swap in a different category set (e.g. statistical-test selection: test type, IV levels, DV scale, assumption violated) as an alternate "track," reusing the exact same solver/generator/UI — the architecture was built category-agnostic specifically so this drops in without touching `logic.js`.

## Ambitious Extensions (multi-session effort)

7. **A real solving-technique tutor** — After a player gets stuck, offer a "What can I deduce right now?" button that runs one step of the actual `zlPropagateToFixpoint` propagation used by the generator and narrates the specific inference in plain English (e.g. "Since the Clinical Sample study can only be Study #2 or #4, and Study #4 already uses Correlational Study which we know pairs with Community Sample, Clinical Sample must be Study #2"). This would turn the existing solver from a puzzle-generation tool into a teaching tool.
8. **Multiplayer daily-challenge leaderboard** — Given the deterministic daily seed already guarantees everyone gets the same puzzle, a lightweight shared backend (out of scope for a self-contained nightly build, but a natural next step) could rank same-day check/hint counts across multiple people, turning today's single-player share string into a real competitive leaderboard.

---

## Possible Integration Points

- **Confound Hunter** (2026-07-15) and **Heuristic Hunt** (2026-07-24) cover the same research-methods domain via a vignette-judgment mechanic; Zebra Lab is the deduction-mechanic sibling. A shared "Research Methods Arcade" landing page linking all three (plus any future methods games) would give the growing methods-game cluster a real home instead of three disconnected builds.
- The AI-explainer's snippet-composition pattern (`zlComposeExplanation` in `logic.js`, `ZL_METHOD_SNIPPETS`/`ZL_THREAT_SNIPPETS`/`ZL_METHOD_ADDRESSES` in `data.js`) is a reusable technique for any future build that needs a genuinely accurate, deterministic explanation with an optional AI-polish layer on top — the same shape used by Fairway Physics' caddie advice and Quarter Call's historical-context note.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No pencil-marks / elimination-tracking UI — players must track working hypotheses mentally or on paper | Build Quick Win #1 above |
| Practice mode has no difficulty signal beyond the chapter name | Build Quick Win #3 above |
| The AI explainer only ever covers the Confound-Control/Threat-to-Validity pairing from Study #1 of the solved puzzle, never any other study's pairing | Randomize which study's pairing gets explained, or offer a dropdown to pick any solved study |
| Hint reveals an entire study's row at once — a player who only wants one category's value has no lighter-weight option | Add a "Reveal one cell" hint tier alongside the existing "reveal one study" tier |
