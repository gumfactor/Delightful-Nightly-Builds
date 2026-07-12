# Why This? — Research Question Forge

> **Date:** 2026-07-12

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 193 → `(193-1) % 9 = 3` → Category D (Creative / Generative). Checked the backlog synced from the most recent open build PR branch (`claude/cool-sagan-8r5sb5`, PR #36, 2026-07-11 Connectome): zero `pending` rows tagged Category D exist — the two most recent D-adjacent entries (#13 CanFile, #14 Course Concept Atlas) are both Category C, not D, and both are blocked pending Wikidata/Wikipedia access anyway. Per Step 2c, an empty filtered pool skips the lottery and goes straight to fresh idea generation.

## The Decision

Three fresh candidates were generated (see Alternatives). Research Question Forge was chosen because it directly targets a friction point PROFILE.md names explicitly — "grant writing" and "literature reviews" under *Things you do manually that you suspect could be automated or aided by a tool* — with a build that does real combinatorial generation and novelty scoring as its core logic, using Claude only as an optional polish layer on top of that logic rather than as the entire product. That structure was chosen deliberately in response to the lowest-rated Category D build to date: 2026-06-24's AI Lecture Builder scored 2/10 specifically because "a power user replicates this with one prompt in the Claude interface" — a single-shot AI-generated document in a viewer, no persistence, no differentiating computation. Tonight's build persists every generation into a growing, searchable local library and computes novelty algorithmically (Jaccard token overlap against prior saved questions), so repeat use compounds in value instead of resetting to zero each run — the same lesson 2026-07-11's Connectome (unrated but praised by the user as "fantastic," an Obsidian-like local knowledge graph) already validated: durable, indexable local libraries built from the user's own domain outperform single ephemeral AI outputs.

## Connection to User Context

PROFILE.md identifies the user as an Associate Professor running a forensic and affective neuroscience lab who writes grants and manuscripts and names empathy, psychopathy, and stress research explicitly as a rabbit-hole interest. The taxonomy seeded into this build (populations, constructs, methods, theoretical frames) is drawn directly from those named research areas rather than a generic academic template, so the generated question skeletons are immediately domain-relevant rather than requiring translation.

## Why Tonight

Category D's last two builds (2026-06-24 AI Lecture Builder, 2026-07-03 WeatherSong) bracket the failure and success modes for this category: single-shot AI document viewer (2/10) versus real-time algorithmic generation with a genuine computational core (WeatherSong, unrated but built on live-data synthesis, not just AI text). Tonight's build follows WeatherSong's pattern — real generative logic first, AI as an optional enrichment — applied to the user's actual day job instead of a sensory/ambient domain, since Creative/Generative doesn't have to mean art/music; a generator of well-formed, testable ideas is squarely in scope for the category and hasn't been tried yet.

## What I Hope the User Gets From This

1. A standing source of concrete, well-formed research question drafts to unstick a blank page when starting a new grant aim or manuscript introduction.
2. A growing personal library, specific to their own research domain, that gets more useful (and less repetitive, via the novelty scorer) the more it's used — not a one-off artifact.
3. A low-friction way to see combinations across population/construct/method/frame they might not have juxtaposed on their own.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Metaphor Machine — combinatorial neuroscience/psychology analogy generator for teaching and public-education talks, with a persistent rated library | D | Very similar shape to the winning idea (combinatorial generation + persistent library + optional AI polish) but serves a less concrete, less frequently-cited need than grant writing; appended to `builds/ideas.md` as a strong Category D backlog candidate for a future night. |
| Canada List Editorial Angle Generator — combinatorially generates blog post angles for The Canada List by crossing product category × consumer angle × seasonal hook | D | Weaker connection to real data — there is no accessible dataset of The Canada List's actual published categories/history in this build environment, so the taxonomy would have to be invented rather than drawn from the user's real content, which is exactly the "hollow/mock" failure pattern the preference prior warns against. Appended to `builds/ideas.md` for a future night when Canada List category data can be supplied. |
| Golf/Running Route Story Generator | D | No accessible live or historical GPS/route data source (Garmin is not in PROFILE.md's Data Sources for the build environment) — would have devolved into invented placeholder routes, the same "mock data" failure mode the preference prior flags most consistently. Discarded, not added to backlog. |
