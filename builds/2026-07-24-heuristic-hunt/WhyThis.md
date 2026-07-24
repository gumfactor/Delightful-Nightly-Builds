# Why This? — Heuristic Hunt

> **Date:** 2026-07-24

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category rotation (day of year 205, `(205-1) % 9 = 6`) lands on **G — Game/Puzzle**. Two `pending` backlog ideas matched category G: #11 "Market Cap Higher or Lower" and #12 "Stock Chart Direction Quiz," both blank-rated (5 tickets each), giving a lottery pool of R=0 numeric-rated entries and a `lottery_chance` of `min(75, 25 + 0*2) = 25%`. A random roll of 89 exceeded the 25% threshold, so the process moved to fresh idea generation per Step 2d rather than drawing from the backlog.

## The Decision

Scanned the last 10 builds in `builds/index.md` (2026-07-13 through 2026-07-22) for topic saturation: neuroscience circuits, research funding, research-methods literacy, agent-instruction linting, academic deadlines, Canadian macroeconomics, IRB/ethics protocols, Canadian ownership lookup, research analogy generation, and Bayesian inference. No domain repeats more than twice, and investment/finance topics are absent from that window entirely, so no saturation flag applies. Within category G specifically, four prior builds exist (Regex Dojo, Neurofact, Synapse Sort, Confound Hunter) — none address cognitive-bias identification, so this is genuinely new ground even within the category's own history.

## Connection to User Context

PROFILE.md names "Human motivation and decision making" as a specific rabbit-hole interest and "Quantitative investing and market structure" as an active hobby and learning goal. Cognitive biases (anchoring, loss aversion, overconfidence, sunk cost, base rate neglect, etc.) sit at the exact intersection of behavioral psychology — the user's own research domain — and the systematic errors that undermine quantitative investing discipline. The vignette pool intentionally draws scenarios from research/lab settings, investing/portfolio decisions, and everyday life (running, golf, boating) to hit multiple named interests in one build rather than one.

## Why Tonight

This is the fifth Game/Puzzle build in the catalog. The prior four (Regex Dojo: syntax skill; Neurofact: true/false fact-checking; Synapse Sort: category-sorting/Connections-style; Confound Hunter: methodological-flaw identification) established a proven architecture — chaptered campaigns with an accuracy-gated unlock, a date-seeded Daily Challenge with a shareable emoji-grid result, and a persistent per-topic Mastery Dashboard. Confound Hunter in particular (2026-07-15, methodological literacy) is the closest structural sibling, so this build reuses that proven shape and applies it to a different taxonomy and a different set of named interests, the same "reuse a working architecture on new content" move that Bridgework (2026-07-21) used deliberately to sidestep the "one Claude prompt replicates this" critique that scored AI Lecture Builder a 2/10.

## What I Hope the User Gets From This

1. A genuinely reusable drilling tool for a skill with cross-domain payoff — recognizing cognitive biases sharpens both research judgment (interpreting data, reviewing manuscripts) and investing decisions (recognizing sunk cost, recency bias, overconfidence in one's own trades).
2. A quick, low-commitment daily habit (the 5-question Daily Challenge) that fits the "things I'll actually use daily or weekly" ranking the user placed second in PROFILE.md's build-value ranking.
3. Something genuinely fun and replayable — multiple-choice vignette games with immediate explanatory feedback are effective at teaching pattern recognition, not just testing it.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Coping Compass — stress/coping-strategy classification game tied to the user's "Book on Stress and Coping" project | G | Strong PROFILE.md tie, but the underlying taxonomy (problem-focused vs. emotion-focused coping, etc.) is thinner than the 12-bias cognitive-bias taxonomy and would produce a shallower vignette pool at ambitious scope. Worth building later with more taxonomy development time. |
| Boardroom Bluff — startup strategic-decision game (pick the strategically sound option among plausible alternatives) | G | Ties to "Startup strategy" interest, but grading "strategically sound" is inherently more subjective/debatable than grading "which cognitive bias is this," which weakens the game's core promise of a defensible right answer. |
| Market Cap Higher or Lower / Stock Chart Direction Quiz (backlog #11/#12) | G | These were in the lottery pool and lost the draw (roll 89 > 25% chance). Left pending in the backlog for a future night; both would need baked-in Yahoo Finance snapshot data, which is a heavier build-time data-prep step than tonight's scope needed. |
