# Why This? — CaseForge

> **Date:** 2026-09-04

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day-of-year 247 → index 3) is D — Creative/Generative. The backlog held exactly one pending Category D row (#17, Workshop Architect, unrated, 5 tickets by default). `R=0` numeric-rated pending rows, so `lottery_chance = min(75, 25 + 0*2) = 25%`. A random roll of `random.randint(1,100)` returned 44, which is above the 25% threshold, so the lottery missed and fresh ideas were generated instead.

## The Decision

Category D's existing catalog (WeatherSong, Bridgework, Vizstract, Panel Prep, Maple Press, and the poorly-rated 2026-06-24 AI Lecture Builder) splits into two failure/success patterns: AI Lecture Builder scored 2/10 specifically because "a power user replicates this with one prompt" — a thin AI-prose wrapper with no deterministic core. Every subsequent D build (Bridgework, Vizstract, Panel Prep, Maple Press) deliberately built a real deterministic engine underneath any AI layer. Three of those four (Research Question Forge's sibling pattern, Bridgework, Maple Press) share the same mechanism: a hand-authored taxonomy crossed through a compatibility rule engine. CaseForge deliberately breaks from that repeated mechanism — its rule engine's input isn't a hand-authored taxonomy, it's facts *dynamically extracted from real, live PubMed abstracts fetched at runtime*, which is a genuinely different generative substrate no prior Category D (or any prior) build uses.

## Connection to User Context

PROFILE.md names three specific courses the user currently teaches (Stress and Coping, Social Affective Neuroscience, AI Applications for Psychologists) and lists "Course material creation" verbatim under "Things you do manually that you suspect could be automated or aided by a tool." No prior build targets course-material generation from real literature: Curriculum Atlas (2026-08-16, Category C) indexes syllabi the user already wrote, it doesn't generate new material; PubMed Research Radar (2026-07-02) and Paper Lens (2026-06-23) are reading/discovery inboxes, not case-study generators; CircuitLab's (2026-07-13) 8 case vignettes are hand-authored and static. CaseForge is the first build to turn PROFILE.md's own named "Literature reviews" and "Course material creation" friction points into a single generative pipeline: real papers in, ready-to-teach cases out.

## Why Tonight

Category rotation put Category D up tonight. The two most recent Category D builds (Panel Prep, Maple Press) both explicitly noted in their own catalog entries that they were built to answer AI Lecture Builder's 2/10 failure mode with a deterministic core — CaseForge continues that corrective pattern one step further by grounding the deterministic core in live external data rather than a static taxonomy, which is also the differentiator that earned Portfolio Lab (2026-08-09) and Impact Ledger (2026-08-05) their strongest self-assessments in their own categories.

## What I Hope the User Gets From This

1. A working batch of real, citable discussion cases for an actual upcoming lecture or seminar, generated in minutes instead of an afternoon of literature searching and write-up
2. Confidence that the tool won't misrepresent a paper's findings — every discussion question and every numeric fact traces back to something the rule engine actually found in the real abstract, and the AI-polish path can't silently drop or invent a number
3. A reusable, growing local library of vetted teaching cases, tagged by course, that accumulates across semesters instead of living in scattered lecture-note files

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Devil's Advocate — an investment "pre-mortem" generator combining live yfinance fundamentals, SEC EDGAR financial statements, and Form 4 insider-transaction clustering into a structured bull-case/bear-case narrative per ticker | D | A genuinely new generative shape (multi-source real-data narrative synthesis) and zero prior Category D build touches investing, but investing/finance has already appeared twice in the last 10 builds (Trading Book 2026-08-23, EDGAR Lens 2026-08-28); CaseForge reaches a completely untouched PROFILE.md friction point ("Course material creation") with equally strong real-data grounding, so it was the stronger pick for topic diversity. Logged to `builds/ideas.md` as idea #42 for a future night. |
| Venue Noise Profile Card Generator — turn a JSON export of the user's own Earshot (2026-08-14) noise-logging sessions into a shareable, deterministically laid-out SVG "venue noise card" (similar rendering technique to Vizstract) | D | A real, named active project (Kwyeter) with zero prior Category D coverage, but its data source is a single prior build's local export rather than an independent live source, and the generative content itself (a small stat card) is a much thinner scope than a full case-generation pipeline — reads more like a feature bolted onto Earshot than a standalone ambitious build. Logged to `builds/ideas.md` as idea #43 for a future night. |
| A fourth taxonomy × compatibility-rule-engine generator (e.g., a "Stress and Coping" book-chapter outline generator, reusing Research Question Forge/Bridgework/Maple Press's proven architecture) | D | Would be the fourth build on an already-proven mechanism within the same category; CLAUDE.md's own topic-diversity guidance is about subject matter, but a fourth mechanism repeat back-to-back with Maple Press (the immediately preceding non-lottery D build) risked the same "recognizable formula" critique that this build is explicitly trying to avoid by using a dynamically-extracted-fact rule engine instead. |
