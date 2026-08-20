# Future Features — Fairway Physics

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Aim assist readout** — Show the predicted landing X-offset (from aim + shot shape + wind) as a live number next to the aim slider before the shot is taken, so the player can reason about compensation instead of trial-and-error.
2. **Club recommendation badge** — A small "suggested club" hint next to the club selector, computed deterministically from `distanceToPin / club.baseCarry` closest to 1.0 — pure UI sugar on top of the existing engine, no new physics.
3. **Keyboard shortcuts** — Arrow keys to nudge aim, `Enter` to take the shot — meaningful for the presumably desktop-heavy Practice-mode grinding session.

## Medium Effort (roughly one nightly build session)

4. **18-hole "Full Course" mode** — Double the course to a real front-nine/back-nine 18, reusing the same engine and zone system; would also let the scorecard compute a proper 18-hole handicap-style differential.
5. **Shot shape visual preview** — Before committing to a shot, draw a faint dotted preview arc on the canvas showing the predicted flight path given the current club/power/aim/shape/wind inputs (the math already exists in `resolveShot`; this just calls it speculatively and renders without mutating state).
6. **Leaderboard-style "Course Record" tracking per hole** — Currently `totalStrokesByHole` only stores an average; storing and surfacing the single best strokes-count per hole (with the date it happened) would give a concrete target to beat.

## Ambitious Extensions (multi-session effort)

7. **Real terrain elevation via a heightmap** — Replace the single hole-level `elevationChangeFt` scalar with a small per-hole heightmap (e.g. a coarse grid of elevation samples) so approach shots from different lateral positions on the same hole experience genuinely different elevation effects, and greens could have actual slope-dependent putting reads computed from the same heightmap instead of a single `greenBreakYd` constant.
8. **Club bag customization / equipment fitting** — Let the player adjust individual club base-carry and roll-factor values within a realistic range (representing different skill levels or equipment), persisted per player profile, turning the engine into a lightweight club-fitting sandbox in addition to a game.

---

## Possible Integration Points

None identified yet — this is the first Category G build to use a simulation/physics engine rather than curated text/quiz content, and the first build overall to touch golf, so there is no existing catalog entry to connect it to. A future Learning Aid (Category E) build on ballistics/projectile-motion fundamentals could reuse `engine.js`'s wind/elevation model as a teaching example, if that ever becomes a build topic.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Hazard/fairway/rough zones are axis-aligned rectangles, not true polygons, so a dogleg is approximated by two adjacent rectangles rather than a smoothly curving corridor | Extend `classifyLie`/rendering to support polygon zones (point-in-polygon test) for more natural-looking, more accurately-shaped holes |
| Elevation is a single hole-level constant applied identically to every shot on that hole, rather than the actual remaining elevation change from the ball's current position to the pin | Store elevation as a function of downrange position (or a coarse per-segment table) and compute the relevant delta for each shot's actual start/end range |
| Wind is constant for an entire hole (Daily Round) or the whole practice session (Practice mode, until shuffled) rather than varying shot-to-shot the way real wind gusts do | Add a small per-shot wind-speed jitter (still seeded deterministically from `(date, holeIndex, strokeNumber)` for Daily Round, to keep it fair and repeatable) |
| No sand/rough lie penalty to shot accuracy (only to distance/roll) — a bunker lie should realistically also reduce aim precision, not just distance | Add a lie-dependent aim-error term to `resolveShot` inputs, small for fairway, larger for rough/bunker |
