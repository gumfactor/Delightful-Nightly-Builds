# Why This? — Marginal Gains

> **Date:** 2026-09-16

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day of year 259, `(259-1) % 9 = 6`) is **G — Game / Puzzle**. `builds/ideas.md` held 6 pending Category G rows (#11, #12, #23, #32, #47, #48), all unrated (blank = 5 tickets each, R=0). `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled `random.randint(1,100)` → **55**. 55 > 25, so the lottery was missed and fresh ideas were generated per Step 2d.

## The Decision

None of the 6 pending backlog rows offered a mechanic genuinely distinct from what Category G has already built. Two (#11 Market Cap Higher/Lower, #12 Stock Chart Direction Quiz) are thin investing guess-games from the earliest backlog entries, already implicitly superseded by the stronger investing-flavored Quarter Call build. #23 (Circuit Six) is a hand-curated concept graph — its own rating notes flag that "hand-curated-content model... sits closer in spirit to Synapse Sort's hand-curated puzzle bank than to something requiring real computed game logic." #32 (Pace Strategy Simulator) was explicitly deferred twice as "too close to Fairway Physics" (a from-scratch physics simulation, same shape). #47 (Data Detective) and #48 (Diagnosis Duel) both sit in the same "spot the methodological flaw" / diagnostic-elimination territory already covered twice (Confound Hunter, Heuristic Hunt) and once adjacently (CircuitLab in Category E). Generating fresh gave more room to find an untouched mechanic.

## Connection to User Context

PROFILE.md names, verbatim, under "Recurring friction points": *"Managing many simultaneous projects"* and *"Administrative overhead."* It also names running a neuroscience lab, The Canada List, Kwyeter, a book project, and teaching as genuinely simultaneous demands on a fixed weekly hour budget — a real allocation problem the user lives with, not a hypothetical one. Marginal Gains turns that lived problem into a puzzle: allocate a limited weekly hour budget across a realistic mix of academic and entrepreneurial project types, each with its own diminishing-returns curve, and see exactly how close the allocation came to the mathematically optimal one.

## Why Tonight

Category rotation put tonight at G — Game/Puzzle, the ninth night in the 9-day cycle. This is the 11th Category G build in the catalog; the prior 10 span regex-writing, real-vs-fake trivia, category sorting, two flavors of vignette flaw-spotting, Wordle-style word-guessing, investing trivia, from-scratch physics simulation, CSP logic-grid deduction, and closed-form navigation math. A resource-allocation optimization puzzle (separable-value knapsack solved by dynamic programming) is a mechanic none of those 10 use, keeping Category G's pattern of "a real, verifiable computed engine under every puzzle" intact rather than repeating an existing shape under a new skin.

## What I Hope the User Gets From This

1. A few minutes of genuinely fun puzzle-solving that also sharpens real prioritization instinct — the same "front-load several things a little rather than max out one" intuition that applies to an actual overloaded week.
2. A concrete, honest look at how far human intuition drifts from the mathematically optimal allocation once diminishing returns and startup costs are in play — something no spreadsheet or to-do app shows directly.
3. A Daily Challenge habit loop (UTC-seeded, one attempt per day, shareable result) in the same spirit as the catalog's other daily-challenge games.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Course Correction — a timed "spot and fix the bug" debugging puzzle over small buggy Python/JS snippets across a 12-category root-cause taxonomy (reusing BugTrace's, 2026-07-25, classification scheme but as an interactive game rather than a commit-history miner) | G | Genuinely untouched mechanic and ties to PROFILE.md's "Become substantially stronger as a Python developer" learning goal, but real-time interactive code execution/validation in-browser (safely, without `eval()` on arbitrary player-edited code) added meaningful scope risk for one session; Marginal Gains's DP solver is equally novel with a cleaner, fully deterministic correctness story. |
| Calibration Arena — a cross-domain trivia game where the player states a confidence percentage alongside each answer, scored with a proper scoring rule (Brier/log score) to teach probabilistic self-calibration | G | Ties well to PROFILE.md's Bayesian-statistics learning goal and "decision making" interest, but the core interaction (answer + confidence slider on a trivia question) reads too close to the catalog's existing quiz-shaped builds (Neurofact, Heuristic Hunt, Confound Hunter) even with a different scoring rule underneath. |
| Circuit Six, rebuilt with a live Wikidata-derived concept graph instead of hand-authored edges (the exact fix its own 2026-08-20/08-29 rating notes called for) | G | A legitimate path forward, but it would depend on live network access at play time (or a build-time scouting pass this session didn't budget for) for a graph the game's correctness can't independently verify the way a closed-form or DP-solved mechanic can; left pending in the backlog for a future night with room to survey the Wikidata query first. |
