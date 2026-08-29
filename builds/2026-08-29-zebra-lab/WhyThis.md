# Why This? — Zebra Lab

> **Date:** 2026-08-29

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Category G (Game/Puzzle) has 4 matching pending backlog rows tonight (`builds/ideas.md` IDs 11, 12, 22, 23), none with a numeric rating, so `R = 0` → `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 50 (1–100), which is above the 25% gate, so the lottery did not draw and fresh ideas were generated instead.

## The Decision

Backlog idea #22 ("Research Design Deduction," added 2026-08-20) had already been passed over twice with an explicit note that it was "worth building on a future Category G night" — a hand-authored, provably-unique logic-grid deduction puzzle over experimental-design attributes. Tonight's fresh-generation pass used that direction as the strongest of three candidates (see Alternatives below) because it is the first Category G build driven by a real constraint-satisfaction solver rather than a quiz, sort, word-guess, chart-guess, or physics-simulation mechanic — the prior 8 builds cover all of those shapes but none do real step-by-step logical deduction. It is also fully self-contained (no external API dependency), which sidesteps the build-container network restrictions entirely.

## Connection to User Context

PROFILE.md names "Research Design Deduction"-style methodological literacy directly: the user runs a forensic/affective neuroscience lab, teaches "Stress and Coping" and "AI Applications for Psychologists," and has already invested in two other research-methods games (Confound Hunter's flaw-spotting, Heuristic Hunt's bias-spotting). Zebra Lab covers the same domain expertise from a different angle — population, study design, confound control, and threats to validity — through active deduction rather than passive judgment, which is a genuinely different skill for the same subject-matter interest.

## Why Tonight

Day 241 of 2026 → `category_index = (241-1) % 9 = 6` → Category G (Game/Puzzle), per the fixed 9-day rotation. The category has 8 prior builds; the last was Fairway Physics (2026-08-20), a physics-simulation golf game, so tonight deliberately picks a mechanic with no overlap to that or any earlier G build.

## What I Hope the User Gets From This

1. A puzzle mechanic that genuinely differs from every other build in the catalog — real logical deduction with a provably-unique solution, not another vignette quiz
2. A daily 5-minute deduction habit (Daily Challenge, one per UTC day) that reinforces methodological vocabulary the user already teaches
3. A worked, testable example of building a minimal, provably-correct puzzle generator (backtracking CSP + minimality pruning) that could be reused as a technique in future puzzle builds

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|-----------------|
| Circuit Six (backlog idea #23) — six-degrees graph-traversal game over a hand-curated concept graph | G | Hand-authored graph edges sit closer in spirit to Synapse Sort's (2026-07-06) hand-curated content model than to a build with real computed game logic; also a weaker tie to an untouched PROFILE.md interest than the deduction angle. Left pending in the backlog for a future night, ideally paired with a way to derive edges from real data instead of hand-authoring them. |
| Pace Strategy Simulator — allocate effort across race segments (elevation/weather-driven fatigue model) for distance running, an untouched PROFILE.md hobby | G | A real simulation engine is exactly what Fairway Physics (2026-08-20, the immediately preceding G build) already delivered; building a second physics/simulation game back-to-back would read as a mechanic repeat rather than genuine diversity, even though the topic (running vs. golf) would differ. |
| Market Cap Higher/Lower (backlog idea #11) and Stock Chart Direction Quiz (backlog idea #12) | G | Both are guessing-game mechanics over investing data; Quarter Call (2026-08-11) already delivered a market chart-reading game in this category, and a second investing-only game would both repeat that mechanic shape and over-index Category G on one PROFILE.md domain. |

Backlog idea #22 is marked `skipped` in `builds/ideas.md` tonight (with a note pointing to this build) so a future lottery draw does not propose a duplicate; idea #23 stays `pending` since it remains a distinct, viable direction for a future night.
