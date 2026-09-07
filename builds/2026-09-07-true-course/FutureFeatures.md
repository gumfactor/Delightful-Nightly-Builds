# Future Features — True Course

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Difficulty tiers** — Widen the generator's rejection-sampling bounds (e.g. Set & Drift's minimum correction angle, Right of Way's boundary margin) into named Easy/Medium/Hard presets, selectable before starting Practice Mode or a Voyage chapter.
2. **Keyboard input for Set & Drift** — Support arrow-key nudging of the numeric heading input, and Enter to submit, so the numeric puzzle type is as fast to answer as the choice-based ones.
3. **Persisted best daily streak** — Track consecutive-day Daily Challenge completions in `localStorage` (parallel to the existing per-type mastery stats) and surface it on the menu screen, matching the "streak" pattern several prior Category G builds (Synapse Sort, Lexicon, Quarter Call) already use.
4. **A "why" reveal for Right of Way** — After answering, currently the feedback text names the rule (head-on/crossing/overtaking) but doesn't show the computed relative bearings that produced it; surfacing `relBearingFromYou`/`relBearingFromOther` numerically would make the geometry fully auditable, matching how Set & Drift already shows SOG/ETA.

## Medium Effort (roughly one nightly build session)

5. **A fifth puzzle type: anchoring scope and swing radius** — Given water depth, tide range, and rode type (chain vs. rope), compute the minimum scope ratio and the resulting swing circle radius, then ask whether a given anchor spot leaves safe clearance from a charted obstruction or another anchored boat. Real, deterministic math (scope ratio tables, Pythagorean swing-radius geometry), a genuinely new engine, and a common real-world small-boat decision with zero prior coverage.
6. **Real chart-symbol recognition** — Extend the Buoyage engine into a broader "chart symbols" puzzle type covering a curated set of real NOAA/CHS chart symbols (rocks, wrecks, restricted areas, lights with real characteristic-flash notation like "Fl G 4s"), sourced from the publicly documented symbol standard rather than invented icons.
7. **Multi-leg voyage planning** — Chain several Set & Drift legs into a single route with a running fuel/time budget, surfacing cumulative ETA and a "will you make it before dark / before the tide turns" constraint that ties Set & Drift and Tide Window together into one combined puzzle.

## Ambitious Extensions (multi-session effort)

8. **Real regional tide-station data** — Swap the current cosine-model tide puzzles for actual harmonic constituent data from NOAA CO-OPS or Canadian Hydrographic Service tide-station APIs (both free/public), letting the player practice against a real Ontario/Great-Lakes or coastal station instead of a synthetic low/high pair — turning the trainer into something closer to a real trip-planning tool.
9. **A shared local "logbook" export** — Let a completed Voyage or Daily Challenge export a small JSON/CSV summary (puzzle type, params, player answer, correct answer, timestamp) that a future build (or a spreadsheet) could ingest to show long-run skill trends beyond what the in-app dashboard tracks.

---

## Possible Integration Points

- **Dockside** (2026-08-04) already computes real Open-Meteo Marine API boating-comfort scores and seasonal task readiness for the same "boating/cottage life" domain — a shared local data file recording which real-world conditions the user has actually sailed in could seed harder, more realistic True Course puzzle parameter ranges (e.g. drift/current ranges pulled from a real week's marine forecast rather than a uniform random draw).
- **TripKit** (2026-07-26) established the pattern of a packing/prep checklist keyed on trip parameters; a "Voyage Prep" mode combining a True Course Set & Drift leg with TripKit's packing logic for a specific real cottage-to-marina trip would be a natural cross-build extension once both are on `main`.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The tide model is a simplified cosine (harmonic) approximation between one low/high pair, not tide-table-grade precision (documented explicitly in the PRD as a scope cut) | Swap in real NOAA/CHS harmonic constituent data (see Ambitious Extensions #8) for stations the user actually boats near |
| COLREGS coverage is limited to power-driven-vessel Rules 13/14/15; sailing-vessel-specific Rule 12 (wind on different sides) is out of scope | Add a `vesselKind` parameter (power/sail) to `classifyEncounter` and a Rule 12 branch when both vessels are under sail |
| Right of Way and Buoyage puzzles are 2–3-option multiple choice rather than free-form; a player can narrow the answer by elimination rather than reasoning it through | Consider a "type the side/color" free-text mode as an optional harder difficulty once difficulty tiers (Quick Win #1) exist |
| The Voyage Mode chapter order (Buoyage → Right of Way → Tide Window → Set & Drift) is fixed | Let a completed Voyage be replayed in any unlocked order once all four chapters are unlocked, rather than only "Replay Chapter" on the current one |
