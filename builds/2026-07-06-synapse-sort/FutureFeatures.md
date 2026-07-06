# Future Features — Synapse Sort

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Keyboard navigation for tiles** — Arrow-key movement between tiles plus Enter/Space to toggle selection, so the grid is fully playable without a mouse or touchscreen. The tiles are already `<button>` elements, so this is mostly wiring `keydown` handlers for arrow keys onto the grid container.
2. **"Copied!" toast confirmation is already there but silent on clipboard failure** — surface a visible error state (e.g. "Copy failed — select the text manually") when `navigator.clipboard` is unavailable (some older browsers or insecure contexts), instead of failing silently.
3. **Puzzle-of-the-day countdown** — a small "next puzzle in Xh Ym" timer on the already-played screen, computed from UTC midnight, so returning players know when to check back.
4. **Difficulty-tier legend** — a small always-visible key mapping color + label (Easy/Medium/Hard/Tricky) once at the top of the page, rather than only appearing after a category is solved.

## Medium Effort (roughly one nightly build session)

5. **Grow the puzzle bank past 30** — add another 20-30 hand-written puzzles (or a fresh batch generated with Claude once `ANTHROPIC_API_KEY` is available in the build environment, then hand-reviewed for quality) so the daily cycle takes longer to repeat. The `PUZZLES` array and `ANCHOR_EPOCH_DAY` logic in `src/puzzles.js` need no changes — just append entries.
6. **Per-category domain tagging** — add an optional `domain` field to each category (e.g. `"neuro"`, `"ai"`, `"investing"`, `"canada"`, `"fitness"`) to enable a future "practice by topic" filter in Archive mode, or a stats breakdown of which domains you're strongest/weakest in.
7. **Mistake-aware hint escalation** — after 2 mistakes, surface a soft hint (e.g. reveal one category's difficulty color without naming it) rather than only the existing "one away" signal, to make losses feel earned rather than abrupt for harder puzzles.

## Ambitious Extensions (multi-session effort)

8. **AI-authored puzzle packs, human-curated** — once `ANTHROPIC_API_KEY` is available, use Claude to draft candidate puzzles in bulk (with the same JSON shape this build already uses), then run them through an automated validator (uniqueness, difficulty balance) before a manual review pass keeps only the ones that are genuinely clever — turning puzzle-bank growth from a manual writing task into a curation task.
9. **Cross-build stats dashboard** — since this build and several others (Regex Dojo, Neurofact) all use `localStorage`-based daily/streak stats with a similar shape, a future build could be a small "game night" dashboard that reads all of them (if opened from a shared parent folder) and shows one combined streak/stats view across every browser game in the catalog.

---

## Possible Integration Points

- **Regex Dojo (2026-06-18)** and **Neurofact (2026-06-27)** share the same "vanilla HTML/JS browser game with Playwright tests and localStorage progress" pattern — a shared, reusable stats/streak micro-library across these builds would cut duplicated code if a future session revisits any of them.
- The **AI integration signal** noted in CLAUDE.md is deliberately unused at runtime here (no `ANTHROPIC_API_KEY` was available this session) but is the natural next step for puzzle-bank growth (see Quick Win 5 / Ambitious Extension 8) once that credential is present in a future build environment.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Puzzle bank repeats every 30 days | Grow the bank (see Medium Effort #5) |
| Daily puzzle resets at UTC midnight, not local time | Add a timezone-offset parameter to `getPuzzleIndexForDate`, sourced from `Intl.DateTimeFormat().resolvedOptions().timeZone` |
| No keyboard navigation between tiles | Add arrow-key handling (see Quick Win #1) |
| No way to un-complete a daily puzzle if played by mistake | Out of scope by design (matches the genre's one-attempt-per-day convention), but could add a "practice today's puzzle again" link that clearly labels it as non-scored |
