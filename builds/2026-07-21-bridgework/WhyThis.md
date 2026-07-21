# Why This Build — Bridgework

## Category rotation

`day_of_year` for 2026-07-21 = 202. `category_index = (202 - 1) % 9 = 3` → **Category D — Creative / Generative**.

## Lottery

Pending backlog entries matching Category D: 2 (#15 "Metaphor Machine", #16 "Canada List Editorial Angle Generator"). Neither has a numeric `Your Rating`, so `R = 0`. `lottery_chance = min(75, 25 + 0*2) = 25%`.

Rolled a random integer 1–100: **46**. `46 > 25`, so the lottery does not draw — proceeding to fresh idea generation (Step 2d). Pool size at time of roll: 2 pending Category D ideas.

## Topic diversity check (last 10 builds, 2026-07-10 → 2026-07-20)

Worklog (project correlation), Connectome (personal knowledge graph), Research Question Forge (grant-adjacent generative), CircuitLab (neuroanatomy learning), GrantScope (NIH funding data explorer), Confound Hunter (research-methods game), AgentLint (dev tooling), Deadline Guardian (admin), CanEcon Pulse (Canadian macroeconomics), Protocol Forge (IRB/ethics generative). No investment/finance build in the last 10 (none of Investment Research Platform/Thesis Journal have recurred recently). Academic-research tooling is heavily represented (6 of 10), and GitHub/dev-activity data has been used in five prior builds across the full catalog — both ruled out as source material for tonight's idea. The Canada List has exactly two builds (CanEcon Pulse, CanFile) in the last 10, both from *external* data sources; nothing yet exploits the user's own long-running academic writing projects.

## Fresh ideas considered

1. **Bridgework (winner)** — A combinatorial analogy/metaphor generator that crosses a hand-curated taxonomy of stress/empathy/psychopathy neuroscience concepts against everyday-domain analogs (sports, weather, kitchen, driving, gardening, music, etc.) through a structural-mapping compatibility rule engine, scores novelty against everything previously generated in a persistent local library, and optionally polishes the strongest combination into publication-ready prose via Claude Haiku (deterministic template fallback with no key). Every analogy is saved as a new library entry, browsable/searchable/exportable-as-Markdown in a self-contained dark-mode HTML viewer, so the tool becomes more valuable with every session rather than being a one-shot generator.

   This directly targets two named, zero-prior-build items in PROFILE.md: **"A book on Stress and Coping"** (Active personal projects) and **"Public education initiatives around empathy and AI"** (Active personal projects) — both explicitly named, neither previously built for. It reuses the taxonomy × compatibility-rules × novelty-scoring × optional-AI-polish architecture that Research Question Forge (2026-07-12) proved out structurally, applied to a genuinely different, high-value topic area, which sidesteps the "one Claude prompt replicates this" critique that sank AI Lecture Builder (2/10) — the persistent, growing, deduplicated library is the differentiating layer, not the AI call itself.

   This is close in spirit to backlog idea #15 ("Metaphor Machine"), which was logged as "Strong Category D candidate for a future night." Rather than propose a near-duplicate as a *new* backlog row, idea #15 is marked `built` below with a note pointing to tonight's build, matching the precedent set for idea #13 → CanFile.

2. **Course Case Vignette Forge** — Generates novel clinical-adjacent case vignettes (empathy/stress/psychopathy topics) for course discussion via a rule engine plus AI polish. Rejected: overlaps heavily with CircuitLab's (2026-07-13) existing Case Vignette mode, and risks the same concern that shelved the "Forensic Assessment Reasoning Trainer" backlog idea — fabricated clinical-adjacent scenarios in a forensic-assessment-adjacent domain need more careful, possibly multi-session grounding than one night allows.

3. **Public Talk Opener Generator** — Generates hooks (stat + story premise + audience angle) for empathy/AI public talks. Rejected: the "real stat" half would need a live, well-scoped data source to avoid being fabricated, and without one it reduces to the same "one Claude prompt" pattern AI Lecture Builder was penalized for.

Ideas 2 and 3 are appended to `builds/ideas.md` as new pending rows (IDs 34–35, today's date, Category D, complexity `ambitious`).

## Idea Brief

No linked Idea Brief — this idea originated fresh tonight, not from a backlog row with a brief.
