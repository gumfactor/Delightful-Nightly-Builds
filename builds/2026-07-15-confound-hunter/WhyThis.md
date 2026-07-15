# Why This — Confound Hunter

## Selection path
Fresh-idea generation, not a lottery draw. Tonight's category (G — Game/Puzzle) had two pending
backlog rows (#11 Market Cap Higher/Lower, #12 Stock Chart Direction Quiz), both unrated (5 tickets
each, R=0 rated ideas → lottery_chance = 25%). Rolled 1–100 via `python3 -c "import random;
print(random.randint(1,100))"` → **35**, which is above the 25% threshold, so the fresh-idea path was
taken instead of drawing from the backlog.

## Why not the backlog ideas
Both pending G-category ideas are investment-themed quiz games. Investment/finance builds have a
mixed-to-weak track record in `builds/index.md` (several discarded outright — Jun 8 Quick Data
Profiler tangent, Jun 9/12 investment dashboards — and the surviving ones cluster in the 3-6/10
range). A third investment game felt like the safer-but-less-interesting choice versus generating
something tied more directly to the user's actual day job.

## Why Confound Hunter over the other two fresh candidates
Generated three G/ambitious candidates (see `BUILD_LOG.md` for full descriptions): Confound Hunter
(study-design-flaw diagnosis game), P-Hack Detective (questionable-research-practice judgment game),
and Grant Triage (timed grant-pitch ranking game). Picked Confound Hunter because:
- It ties directly to a concrete, named part of the user's actual job — Associate Professor teaching
  research-methods-adjacent courses (Stress and Coping, Social Affective Neuroscience) and supervising
  graduate students on study design — rather than a generic trivia theme.
- It's mechanically distinct from every prior Game/Puzzle build: Regex Dojo (write-a-pattern),
  Neurofact (binary real-vs-fake trivia), and Synapse Sort (Connections-style category grouping).
  Confound Hunter is a diagnostic multiple-choice format built around a genuine taxonomy, not a
  reskin of an existing mechanic.
- Grant Triage was set aside specifically because it would have repeated GrantScope's subject matter
  (grant funding) one night after GrantScope shipped (2026-07-14, Category F) — a different category
  and mechanic, but likely to feel repetitive back-to-back.
- P-Hack Detective is a reasonable idea but a weaker mechanic (binary yes/no judgment per item rather
  than a genuine four-way diagnosis), and overlaps thematically with Confound Hunter's research-
  integrity focus; kept as a distinct backlog idea rather than folded in, since it would dilute both.
- No external API or `ANTHROPIC_API_KEY` dependency is needed or wanted here: the 30 vignettes are
  intentionally hand-authored pedagogical scenarios (fictional but methodologically realistic), which
  is the correct call for training content — fabricating "real" study data to back a training game
  would be worse than curated fiction, and there is no live data source that would make this more
  authentic (unlike, say, a market-data quiz).

## Idea Brief
None — this was fresh generation, not a backlog draw with a linked brief. Per Step 2d, the two
non-winning fresh candidates (P-Hack Detective, Grant Triage) were appended to `builds/ideas.md` as
new pending rows for potential future nights.

## Ambition floor check
Category G requires a genuinely playable browser interface (STANDARDS.md Completeness). Confound
Hunter ships three integrated, interactive views (chapter-based practice with gating, a dated daily
challenge, and a persistent mastery dashboard) rather than a single flat quiz loop, matching the
"ambitious" complexity bar the last several G builds have set.
