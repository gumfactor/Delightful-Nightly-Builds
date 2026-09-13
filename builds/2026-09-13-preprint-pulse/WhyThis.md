# Why This? — Preprint Pulse

> **Date:** 2026-09-13

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Category D (Creative / Generative) has 3 pending backlog rows tonight — #17 (Workshop Architect), #42 (Devil's Advocate: Investment Pre-Mortem Generator), #43 (Venue Noise Profile Card Generator) — all unrated (blank = 5 tickets each), so `R = 0` and `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 39 (>25) → the lottery missed and the night moved to fresh idea generation. No re-roll.

## The Decision

Generated three fresh Category D candidates: (1) **Preprint Pulse**, an arXiv-grounded trend-detection + fact-extraction engine that drafts a research-digest article; (2) a **Psychology Experiment Design Idea Generator** (IV × DV × population × paradigm taxonomy engine); (3) a **Boating/Cottage Weather-Window Trip Story Generator** (Open-Meteo-driven narrative). Preprint Pulse won: it hits a real PROFILE.md friction point head-on ("Blog writing and editing"), pulls from a live, free, no-auth API with a genuine deterministic analysis core (linear-regression trend slope, keyword-shift detection, regex fact extraction), and produces a content shape — a publish-ready article draft — that nothing else in the catalog does. Candidate (2) was rejected for mechanism fatigue: it would be the 4th catalog build reusing the exact taxonomy-compatibility-engine shape (after Research Question Forge, Bridgework, Maple Press), and CLAUDE.md's guidance says a 4th should only win if genuinely the strongest candidate — it wasn't, next to a live-data-grounded alternative. Candidate (3) was rejected for topic/mechanism overlap: WeatherSong (2026-07-03) already built the weather-driven creative-output mechanic, and Open-Meteo comfort-window scoring is already used by three prior builds (Run Planner, Morning Briefing, TripKit).

## Connection to User Context

PROFILE.md names "Blog writing and editing" directly under "Things you do manually that you suspect could be automated or aided by a tool," and separately lists "writing academic papers and public-facing articles" under Creative Pursuits and "Public education initiatives around empathy and AI — workshops, talks, podcasts, and educational content" under Active Personal Projects. Preprint Pulse targets the specific gap between "I should write something about this research trend" and an actual draft: it does the literature-scanning and fact-gathering work (which the user would otherwise do by hand) and hands back a structured starting point, not a finished-and-final piece — matching the stated preference for tools that "reduce friction" and "free up time for higher-level thinking," not tools that pretend to replace judgment.

## Why Tonight

Today is day 256 of the year → `(256-1) % 9 = 3` → Category D. This is the 9th Category D build in the catalog. The most recent Category D build, AI Lecture Builder (2026-06-24), scored 2/10 with the explicitly documented failure reason "no deterministic core of comparable weight to the AI call" — a thin AI wrapper. Preprint Pulse is designed specifically against that failure mode: the trend engine, keyword-shift detector, and fact extractor are all real, independently testable algorithms that produce a complete, useful, readable draft on their own (the "template" fallback path), with the AI layer purely additive and constrained to the facts the deterministic layer already extracted.

## What I Hope the User Gets From This

1. A working first draft the next time a research trend is worth writing about publicly — minutes instead of an afternoon of manual scanning.
2. A concrete, numeric answer to "is this topic actually heating up right now?" (trend slope + rising keywords), not a vibe.
3. A reusable pattern (deterministic extraction + fact-constrained AI drafting) that is honest about which parts are "real" (traced to a specific paper) and which parts are AI-assembled prose — useful in a domain where the user has explicitly said writing that "sounds obviously AI-generated" is unwelcome.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Psychology Experiment Design Idea Generator | D | 4th reuse of the taxonomy × compatibility-rule-engine mechanism already used by Research Question Forge, Bridgework, and Maple Press; a live-data-grounded alternative was clearly stronger on the same night. Logged as idea #57. |
| Boating/Cottage Weather-Window Trip Story Generator | D | Weather-driven generative narrative overlaps WeatherSong's already-built mechanic, and Open-Meteo comfort-window scoring is already used by three prior builds. Logged as idea #58. |
| Devil's Advocate: Investment Pre-Mortem Generator (backlog #42) | D | Present in tonight's Category D lottery pool but the lottery missed (rolled 39 > 25% chance); investing/finance was also flagged in that idea's own prior note as needing "more room to breathe." Left pending for a future night. |
