# Build Log — True Course

> **Date:** 2026-09-07
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [00:05 UTC] Session Start

- Step 0: checked the most recent dated build folder. Local `main` only carries build folders through 2026-06-18 (regex-dojo); per CLAUDE.md's Step 1 guidance, resynced from the most recent open PR branch (`claude/cool-sagan-lfa9fy`, PR #91, 2026-09-06 Almanac) to get the current `builds/index.md`/`builds/ideas.md`. That build's own `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed. Working branch `claude/cool-sagan-703xh7` was identical to `origin/main` (no divergent commits), so no reset was needed; `builds/index.md` and `builds/ideas.md` were overwritten from the PR branch's copies.
- Read PROFILE.md, builds/index.md (full catalog, 92 prior builds), STANDARDS.md in full.
- Day of year 2026-09-07 = 250 → `(250-1) % 9 = 6` → Category G (Game/Puzzle).
- Category G backlog: 5 pending ideas, all unrated (R=0) → lottery gate = 25%. Rolled 60/100 → above threshold → fresh ideas generated (Step 2d).
- Topic diversity check (last 10 builds, Aug 27–Sep 6): E, F, G, H, A, B, C, D, E, F — investment/finance appears once (EDGAR Lens) in that window, not saturated.
- Category G mechanic diversity check (all 9 prior G builds): CSP logic grid (Zebra Lab), physics simulation (Fairway Physics), chart-direction guessing (Quarter Call), vignette-quiz (Confound Hunter, Heuristic Hunt — same mechanic twice), category-sort (Synapse Sort), letter-guess (Lexicon), regex-writing (Regex Dojo), true/false trivia (Neurofact). No prior build uses a procedurally-generated math/geometry-engine mechanic, and no prior build (any category, 92 total) touches boating.
- Decided to build: **True Course** — a nautical navigation puzzle game with four real, from-scratch deterministic engines (set-and-drift vector navigation, cosine-model tide windows, COLREGS right-of-way classification, IALA System B buoyage rules), directly answering backlog idea #33's own rating notes ("worth developing further into a concrete mechanic, e.g. a real tide/current calculation engine, not a trivia quiz").
- Build folder created: `builds/2026-09-07-true-course/`

### [00:20 UTC] PRD Written

- Goal: procedurally generated navigation puzzles across 4 real engines, Voyage/Practice/Daily Challenge modes, localStorage mastery tracking, optional AI flavor commentary.
- Full navigation math worked out before any code: course-to-steer via the current-triangle closed-form correction-angle formula (cross-checked by reconstructing the resultant vector), cosine-interpolation tide model between a known low/high pair, a COLREGS classifier using the real 22.5°-abaft-the-beam overtaking threshold and starboard-side crossing rule, and IALA System B "red right returning" buoyage.
- Scope Changes: none yet.

### [00:35 UTC] Build Phase — Engine

- `src/engine.js`: pure functions only, no DOM. `courseToSteer` implements the current-triangle correction-angle formula (perpendicular-component cancellation, closed-form `asin`), returning `solvable:false` (never NaN) when the current's cross-track push exceeds the boat's own speed. `tideHeight`/`tideWindowStart` implement the cosine-interpolation model between a known low and high tide, with closed-form inversion (`acos`) for the crossing time. `classifyEncounter` implements COLREGS Rules 13/14/15 with the real 112.5°-abaft-the-beam overtaking threshold; `encounterBoundaryMargin` supports the generator's rejection sampling. `buoyage` implements IALA System B ("red right returning").
- `src/generator.js`: mulberry32 seeded PRNG (`Math.random()`-seeded for Voyage/Practice, UTC-date-hash-seeded for Daily Challenge). Each of the four generators calls straight into `engine.js` for its `correctAnswer` — never a hand-authored value — and rejects/redraws scenarios too close to a rule boundary (right-of-way: <6° margin; tide-window: within 0.15 m of the low/high boundary; set-drift: correction angle <3° or >45°).
- `src/render.js`: Canvas 2D helpers (compass rose + vector arrows for Set & Drift, a two-vessel relative-bearing diagram for Right of Way, a tide-height curve with shaded safe window for Tide Window, a can/nun buoy icon for Buoyage). No charting library.
- `src/app.js`: menu, Voyage Mode (4 chapters, 70%-accuracy unlock gate, resumes at the furthest unlocked chapter), Practice Mode (per-type infinite rounds), Daily Challenge (UTC-date-seeded 5-round mix, one attempt/day, shareable ✅/❌ grid), Mastery Dashboard (localStorage-persisted per-type attempts/accuracy + chapter-unlock badges), and an optional "First Mate's Log" direct-browser Anthropic API call (session-only key, aggregate score only, deterministic-template fallback with zero network calls when no key is set). All dynamic text goes through `textContent`/`createElement`, never `innerHTML`.

### [01:10 UTC] Tests Written and Run

- 41 Playwright tests across 4 files: `engine.spec.js` (17 — closed-form math cross-checked by independent vector reconstruction, hand-worked COLREGS/tide/buoyage cases, a symmetry test for right-of-way, an unsolvable-current edge case), `generator.spec.js` (7 — 200-300 generated instances per type verified against a fresh engine call with zero drift, plus daily-seed and PRNG determinism), `ui.spec.js` (13 — full happy-path play through Voyage/Practice/Daily Challenge, the 70%-accuracy chapter-unlock gate both passing and failing, the one-play-per-day gate, dashboard state), `security.spec.js` (4 — a live `<img onerror>` + `</script><script>` payload injected into a mocked Anthropic API response, verified to render as inert text with zero dialogs/page errors/injected script tags; zero network calls with no API key; graceful fallback on a failed request; the API key never appears on the debug hook).
- First run: **41 passed, 0 failed** — no fix-up needed on the first pass; the only mid-write correction was one test's hand-picked overtaking scenario, where the geometry actually implied the *other* vessel was overtaking *you* rather than the reverse — rewritten with a case that unambiguously makes you the overtaking vessel and re-verified against the engine's own output.
- Tests: 41 passed, 0 failed.

### [01:20 UTC] Manual Verification

- Ran a headless-Chromium smoke pass (separate from the Playwright suite) driving Voyage Mode chapter 1 (all 6 rounds), Practice Mode for all four puzzle types, the Mastery Dashboard, and the Daily Challenge's first round, capturing screenshots at each step and asserting zero `console.error`/`pageerror` events. Zero errors. Visually confirmed: the compass-rose vector diagram correctly draws the track (cyan), current (orange), and player-guessed heading (yellow) arrows; the tide curve correctly shows the sigmoid rise with the required-height dashed line; the two-vessel diagram correctly places "OTHER" along the given bearing line with its own heading arrow; the buoy icon correctly renders a green can / red nun by color; the dashboard badges correctly reflect chapter-unlock state.
- Security checklist (STANDARDS.md) grepped clean: no `innerHTML`, `eval`/`exec`, hardcoded credentials, `.env` files, or `os.system`/`subprocess` calls (N/A — pure browser build, no file I/O).

### [01:25 UTC] Verify — Step 7

PRD success criteria:
1. All tests pass (zero failures) — 41/41 passing.
2. Every puzzle's correct answer is computed live — verified by `generator.spec.js`'s 750+ generated-instance cross-checks against fresh engine calls; no hand-authored answer key exists anywhere in the codebase.
3. Voyage Mode playable end-to-end through all 4 chapters with the 70%-accuracy gate — verified by `ui.spec.js`'s perfect-run (unlocks) and zero-score-run (does not unlock) tests, and manually through chapter 1→2 in the smoke pass.
4. Daily Challenge is deterministic per UTC date and gates to one attempt/day — verified by both a pure-generator determinism test and a full-UI one-play-per-day test.
5. No user/AI-response text ever reaches `innerHTML` — verified live against an actual `<img onerror>`/`<script>` injection payload in a mocked AI response, zero dialogs/errors/injected nodes.

Build complete. Success criteria reviewed. All tests passing.
