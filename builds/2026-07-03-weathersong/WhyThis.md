# Why This? — WeatherSong

> **Date:** 2026-07-03

---

## How This Idea Was Selected

**Selection method:** Fresh generation

Tonight's category (day of year 184, `(184-1) % 9 = 3` → **D — Creative/Generative**) has zero `pending` rows in `builds/ideas.md` (checked via a filter on `Category = D`; none exist in the backlog at all). Per Step 2c, an empty filtered pool skips the lottery entirely and moves straight to Step 2d (fresh generation) — no roll was needed.

## The Decision

Three fresh ideas were generated for category D (see Alternatives Considered). The category's last outing — 2026-06-24, AI Lecture Builder — scored 2/10 with the explicit critique: *"a tabbed HTML viewer adds overhead without adding capability the user can't get from a single Claude prompt... a power user replicates this with one prompt."* That is the failure mode to design away from tonight: any AI-text-wrapper-in-a-viewer shape is disqualified before it's built. WeatherSong's differentiating layer is a native Web Audio synthesis engine driven by live data — something no single LLM prompt produces — which sidesteps that exact criticism.

The topic-diversity check on the last 10 builds also mattered: GitHub-based tooling (Developer Activity Explorer, ci-pulse, Developer Analytics Dashboard) and neuroscience/research tooling (Neurofact, BIDS Validator, PubMed Radar, Paper Lens) each appear 3+ times recently. WeatherSong uses Open-Meteo, which has appeared exactly once (Run Planner, 2026-06-20) as a secondary data source — a clear underused, free, no-auth API rather than a repeat of a saturated domain.

## Connection to User Context

PROFILE.md lists boating, cottage life, and distance running among personal interests, and the "Creative pursuits" section explicitly cites "building software products" as itself a creative outlet. WeatherSong is designed as something ambient to run in the background — the kind of thing that turns a weather check before a run or a day on the water into something a little more textured than a forecast number.

## Why Tonight

Tonight is a straightforward category-rotation slot for D — Creative/Generative, the 9-day rotation's fourth position, landing on 2026-07-03 exactly 9 days after the last D-category build (2026-06-24). No idea brief was linked (fresh generation, no backlog match), so there was no brief to consult per Step 2e.

## What I Hope the User Gets From This

1. Something genuinely surprising to open — weather rendered as sound and generative color rather than another dashboard, matching the category's purpose
2. A small, low-stakes way to notice weather more attentively (the mapping is legible enough that a windy day audibly sounds windier)
3. A Weather Journal that becomes more interesting the longer it's used — a personal, ambient record of what different days actually felt like

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Market Mood Chronicle — a generative daily poem + abstract SVG mood board derived from live yfinance portfolio movement | D | Investment/finance builds have consistently scored low-to-mid (1, 2, 3, 4, 5, 6 across the catalog) and the poem angle risks feeling gimmicky rather than genuinely useful — weaker fit than a fully interactive audiovisual instrument |
| Canada Badge Forge — a procedural SVG badge/crest generator for The Canada List's product categories and provinces | D | Speculative: nothing in PROFILE.md or builds/ideas.md indicates The Canada List currently needs branded visual assets: this would be inventing a requirement rather than serving a stated one |
| AI Workshop Deck Builder — Claude-generated workshop outline/slides/discussion prompts for the "empathy and AI" public education work, with a persistent library | D | Too structurally similar to the low-scoring 2026-06-24 AI Lecture Builder (same "AI drafts a document, viewer displays it" shape) — repeating a build the user already rated 2/10 without a fundamentally different mechanism |
