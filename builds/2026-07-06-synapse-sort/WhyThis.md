# Why This? — Synapse Sort

> **Date:** 2026-07-06

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day of year 187, index `(187-1) % 9 = 6` → **G — Game/Puzzle**) had two pending backlog entries: #11 "Market Cap Higher or Lower" and #12 "Stock Chart Direction Quiz" (both blank rating → 5 tickets each, R=0 numeric-rated entries). Lottery chance = `min(75, 25 + 0*2) = 25%`. Rolled 88/100 (`python3 -c "import random; print(random.randint(1,100))"`) → above threshold → fresh-idea path.

## The Decision

I generated three fresh candidates in category G (below) and picked "Synapse Sort," a Connections-style daily category-sorting puzzle with a hand-curated, personally-themed puzzle bank. The two backlog finance ideas were available but not chosen even in the fresh-generation path, because they're a narrower single-mechanic game ("guess which of two things is bigger") versus the ambition ceiling this category allows, and the finance-trivia idea would have depended on baking static Yahoo Finance snapshots that go stale — Synapse Sort's content ages fine because it isn't about live facts. The last G build (Regex Dojo, 06-18) taught mechanics through play; the one before that in spirit, Neurofact (06-27), was a binary real-vs-fake trivia format. Synapse Sort uses a genuinely different mechanic (set-partitioning under ambiguity) not yet used in this repo.

## Connection to User Context

PROFILE.md lists neuroscience, AI agent workflows, investing, entrepreneurship, and running/golf/boating as core interests, and explicitly flags "things that are fun or delightful to use" as a ranked (if lower-priority) build outcome. Rather than a generic trivia game, the puzzle content is written directly from the user's own five worlds — lab/psychology terminology, LLM and agent concepts, market/investing jargon, Canadian business, and endurance-sport/outdoor vocabulary — so solving it draws on knowledge the user actually has, which is what makes a personalized puzzle bank a better fit than a public Connections clone.

## Why Tonight

Straightforward category-rotation slot (index 6 = G). No G-category idea brief exists in `builds/idea-briefs/`. This is the third G-category build in the catalog (after Regex Dojo and Neurofact), so the bar was to find a mechanic distinct from both a code-teaching puzzle and a binary trivia quiz — the set-partitioning "find the connection" mechanic satisfies that.

## What I Hope the User Gets From This

1. A genuinely replayable two-minute daily habit (30 days of puzzles before repeats) rather than a one-off toy.
2. A puzzle that occasionally makes them smile at a specific in-joke from their own fields (an LLM term hidden next to a neuroscience term as an intentional red herring, a Canadian-business category, etc.) — the "delightful" outcome the profile calls out.
3. A concrete, correct reference implementation of the difficulty-tiered category-sort mechanic, in case a future build wants to extend it (new puzzle packs, a shareable-link mode, etc.).

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Confound Hunter — timed game where the player clicks the specific flawed element in a simplified real study design | G | Research-methods framing has already appeared three times in the last 10 builds (Neurofact 06-27, Power Lab 07-04, TrialScope 07-05); topic risk of a fourth back-to-back research/stats build outweighed the mechanic's novelty. Recorded for a future night when that topic has more headroom. |
| Lab Bench Escape — neuroscience-lab-themed escape-room mini-game with chained logic puzzles | G | Single-playthrough content has low replay value versus a 30-puzzle daily bank, and getting a chain of interlocking escape-room puzzles internally consistent and fairly solvable in one session is high content-risk for the payoff. Recorded as a future idea. |
| Market Cap Higher or Lower (backlog #11) / Stock Chart Direction Quiz (backlog #12) | G | Both are single-mechanic comparison games dependent on a static financial-data snapshot that ages; lower ambition ceiling than a full category-sort game with a 30-puzzle curated bank, and investing is already a well-covered topic domain in the catalog (06-06 through 06-14). Left pending in the backlog rather than re-added. |
