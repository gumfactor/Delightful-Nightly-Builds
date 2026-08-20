# Why This? — Fairway Physics

> **Date:** 2026-08-20

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Category G's backlog held two pending, unrated ideas (#11 "Market Cap Higher or Lower" and #12 "Stock Chart Direction Quiz"), both investing-guessing games. R (rated ideas among the matching pool) = 0, so `lottery_chance = min(75, 25 + 0*2) = 25%`. A bash `$RANDOM`-based roll of 79 exceeded that 25% threshold, so the lottery missed and fresh idea generation followed.

## The Decision

Every one of the 7 existing Category G builds (Regex Dojo, Neurofact, Synapse Sort, Confound Hunter, Heuristic Hunt, Lexicon, Quarter Call) is built on a quiz, sort, word-guess, or chart-reading-guess mechanic — text or chart content presented for the player to classify or guess against. None is a simulation with a real physics/scoring engine underneath it. Missing the lottery (and PROFILE.md naming golf as an untouched hobby) pointed toward building something mechanically different rather than a fifth investing-guessing variant, which is also what the two backlog ideas would have been.

## Connection to User Context

PROFILE.md lists "golf" explicitly under both "Physical activities" and "Personal interests and hobbies." Across 76 prior build sessions, no build has touched it. The Complexity preference section ("start with a simple, reliable foundation and extend it incrementally... reliability beats cleverness") also argued for a deterministic, hand-verifiable physics model over anything relying on chance or opaque heuristics — every shot outcome here is a pure function of explicit inputs, checkable by hand.

## Why Tonight

Day-of-year 232 → `(232-1) % 9 = 6` → Category G, on schedule with the 9-day rotation (G last appeared 2026-08-11, Quarter Call, exactly 9 nights ago). The lottery missing sent this to fresh generation rather than another investing game, which was the deciding factor in reaching for a genuinely new mechanic instead of extending an existing one.

## What I Hope the User Gets From This

1. A different kind of game night — pick a club, shape a shot, read the wind, putt it out — rather than another trivia/quiz session.
2. A concrete, hand-verifiable model of how club selection, wind, elevation, and shot shape interact, in case the underlying math itself is of interest.
3. A low-stakes way to unwind for a few minutes between lab work and Canada List operations, in a mode (Daily Round) that naturally caps how much time it can eat per day.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Research Design Deduction — a Zebra-puzzle-style logic-grid game about experimental-design attributes (IV/DV/confound control/sample type) with a uniqueness-verified clue generator | G | Genuinely novel mechanic (deduction vs. quiz/sort/word/guess), but a text-only puzzle would have read as a cousin of the vignette-quiz shape already used twice (Confound Hunter, Heuristic Hunt); the golf physics engine offered a cleaner mechanical break and a completely untouched PROFILE.md hobby. |
| Circuit Six — a "six degrees" shortest-path connection game over a hand-curated neuroscience/psych/AI concept graph | G | Interesting graph-traversal mechanic, but the curated-content model (hand-authored graph edges) is closer in spirit to Synapse Sort's hand-curated puzzle bank than to something requiring real computed logic; also weaker tie to an unaddressed PROFILE.md interest than golf. |
| Market Cap Higher or Lower / Stock Chart Direction Quiz (backlog ideas #11/#12) | G | Both lost the 25%-chance lottery draw; both would have been the third and fourth investing-flavored Category G builds after Quarter Call, adding little mechanical or topical novelty. |
