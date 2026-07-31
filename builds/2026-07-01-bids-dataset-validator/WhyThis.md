# Why This Build

## Category & Lottery

Today is 2026-07-01 (day of year 182). `category_index = (182 - 1) % 9 = 1` → **B —
Productivity Utility**.

Read `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-9fcncu`,
2026-06-30 build) rather than the local copy, since prior sessions have noted the
local `main`-derived copy lags behind unmerged PR branches. It matched the local copy
for category B (no new entries added on 06-30, those were both category A).

Category B pending pool: idea #4 (Cross-Agent Project Activity Workstreams, rating 9)
and idea #7 (Morning Briefing, rating 8). Both have numeric ratings, so `R = 2`.
`lottery_chance = min(75, 25 + 2*2) = 29%`. Rolled a random integer 1–100: **88** — above
29, so **fresh ideas**, not a lottery draw.

(Note: idea #7, "Morning Briefing," is still marked `pending` in the backlog even
though a build with that exact name and description already shipped 2026-06-22 and is
rated 5/10 in the catalog — an earlier session's oversight in not flipping its status.
It should not be drawn again regardless of the roll; today's roll made that moot.)

## Fresh Idea Generation

**Topic diversity check** (last 10 catalog rows, 06-20 through 06-30): GitHub-derived
dev-analytics tools appear four times (06-21 Repo Health Scorecard, 06-26 Dev Activity
Explorer, 06-28 ci-pulse, 06-30 Dev Analytics Dashboard) — that domain is saturated.
Investment/finance hasn't appeared since 06-14 and isn't a fit for category B tonight
anyway. Academic/research-workflow tools (06-23 Paper Lens) have appeared once and
scored well (6/10) on the "AI as a differentiating layer" pattern.

**Candidates considered:**

1. **BIDS Dataset Organizer & Validator** (winner) — batch-validates a neuroimaging
   dataset folder against core BIDS naming rules, reports every violation, and safely
   auto-fixes zero-padding mismatches. Directly answers the profile's "managing lab
   computing infrastructure" friction point and the highest-rated build to date
   (Qualtrics Survey Data Inspector, 9/10) followed the same shape: a real, specific,
   research-workflow QA tool with no external API dependency, plus an optional Claude
   layer that turns raw findings into a prioritized action list.
2. Manuscript/Grant AI Consistency Checker — batch-scans draft manuscript/grant files
   for terminology drift, undefined acronyms, and missing citation placeholders via
   Claude. Solid, but weaker differentiation from "ask Claude to proofread this" than
   the BIDS tool's deterministic rule engine.
3. Research Ethics/IRB Protocol Batch Assembler — assembles a first-draft REB/IRB
   submission from reusable boilerplate + a study config. Appealing but leans more
   generative/templating than "workflow tool / batch processor," and the assembled
   draft would still need substantial human editing, diluting the "ships complete"
   requirement.

Candidate 1 was the clear winner: it is a genuine batch processor (the category's own
definition), it is testable end-to-end with synthetic fixtures (no real scan data
needed or touched), it needs no paid/auth API beyond the always-available Anthropic
key for an optional layer, and it targets a documented, specific pain point
("managing lab computing infrastructure") rather than a generic productivity pattern
already covered by existing tools (Coda, Teamwork.com).

Candidates 2 and 3 were appended to `builds/ideas.md` as new pending rows (IDs 15 and
16) for a future night.

## Idea Brief

No linked Idea Brief — this is a freshly generated idea, not drawn from a backlog row
with a brief.
