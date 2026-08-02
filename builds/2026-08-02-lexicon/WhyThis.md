# Why This? — Lexicon

> **Date:** 2026-08-02

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 214 → `category_index = (214-1) % 9 = 6` → Category G — Game / Puzzle. `builds/ideas.md` had 2 pending Category G rows (#11 "Market Cap Higher or Lower", #12 "Stock Chart Direction Quiz"), both unrated (blank = 5 tickets each), so `R = 0` numeric ratings and `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 32 (1–100) — above the 25% threshold, so the fresh-idea path was taken instead of a draw. Pool size for the (unused) draw would have been 2.

## The Decision

Both pending backlog rows were investment-data guessing games, and the last 10 builds already include one investing-heavy build this window (SiliconWatch, 2026-07-27), so a second investing game tonight would have leaned on an already-recently-touched domain without adding a new mechanic. The catalog's four prior Category G builds (Regex Dojo, Neurofact, Synapse Sort, Confound Hunter, Heuristic Hunt) cover three mechanics — regex-writing, trivia quiz, category-sorting — and two of them (Confound Hunter, Heuristic Hunt) already use the identical "vignette + chaptered unlock + daily challenge" shape. A fourth build reusing either the vignette-quiz or the finance-guessing shape would have been a weaker pick than a genuinely new mechanic, so I generated fresh ideas targeting a mechanic never used in this catalog: a letter-guessing word puzzle (Wordle-style feedback), built from real technical vocabulary spanning the user's own domains rather than generic dictionary words.

## Connection to User Context

PROFILE.md names neuroscience research, AI/agentic workflows, and quantitative investing as core, parallel interests, and explicitly values "things that are fun or delightful to use" and "things that help me learn something." A vocabulary game built from the exact terms the user works with daily (AMYGDALA, GRADIENT, POSTERIOR, ARBITRAGE) is a two-minute daily habit that reinforces precise recall across all of those domains at once, rather than a single-topic quiz.

## Why Tonight

Category G is tonight's slot in the fixed 9-day rotation. Scanning the last 10 builds for topic saturation: investing/finance appeared once (SiliconWatch) — not saturated on its own, but both pending G-backlog ideas were investing-only, so building one tonight would have made investing the dominant topic across two of the last ~11 builds while ignoring three other named profile domains (neuroscience, stats, AI) that a cross-domain word bank could cover in a single build instead.

## What I Hope the User Gets From This

1. A genuinely fast (2–3 minute), replayable daily habit — the kind of "small polished thing that just works" PROFILE.md ranks highly
2. Passive reinforcement of precise domain vocabulary across neuroscience, statistics, AI, and investing in one sitting, rather than four single-topic builds
3. A new game mechanic in the catalog, so future Category G nights aren't limited to reskinning the existing three shapes

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Circuit Breaker — a spatial neural-signal wiring puzzle (drag connections to route excitatory/inhibitory signal flow through a level) | G | Genuinely novel mechanic, but level design and win-condition logic for a satisfying wiring puzzle needs more per-level hand-authoring and playtesting than one session reliably delivers to a polished, bug-free standard; parking it for a future session with more design lead time. |
| Estimate! — a Fermi-estimation numeric-guessing game using real facts (population figures, funding amounts, physical constants) with a closeness-scored slider | G | Solid mechanic but weaker connection to the user's own named domains than a vocabulary game built from their actual working terminology; also closer in shape to the existing Bayes Lab / Power Lab "guess the number" interactions already in the catalog under Category E. |
| Rebuild backlog #11/#12 (finance-guessing games) via a forced fresh pick | G | Both are investing-only; building either would push investing/finance topic weight higher this window than any other Category G idea, and neither introduces a mechanic the catalog doesn't already have in a different category (SiliconWatch already delivers rich live investing data). Left pending in the backlog rather than discarded — still viable for a future night with less domain overlap. |
