# Why This? — Maple Press

> **Date:** 2026-08-17

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Category D's backlog (`builds/ideas.md`) held zero pending Category D rows, so the lottery step was skipped entirely and fresh ideas were generated directly, per Step 2d.

## The Decision

Day-of-year 229 → `(229-1) % 9 = 3` → Category D — Creative / Generative. The four prior Category D builds (Research Question Forge, Bridgework, Vizstract, Panel Prep) all proved out a reliable architecture — taxonomy × compatibility rules × novelty-scored persistent library, deterministic core with an optional AI polish layer — applied to a different topic each time. None of them, or any of the 101 other builds in the catalog, generate editorial content for The Canada List, despite it being a named, actively-developed project whose profile explicitly calls out "editorial content" and "public education" as core parts of the platform. Three prior builds (CanFile, Ingest Gate, Provenance) built the *verification and data-quality* side of that pipeline; nothing turns verified data into something publishable. Maple Press closes that loop directly — it can consume Provenance's own output CSV (`verdict`/`confidence`/`evidence` columns) as input.

## Connection to User Context

PROFILE.md names The Canada List as "a substantial technology platform" combining "data engineering, AI-assisted classification, editorial content, and public education" and lists "Blog writing and editing" among the friction points the user does manually. Maple Press targets both directly: it is the first build to generate Canada List editorial output rather than validate or classify Canada List data.

## Why Tonight

Category D was due tonight by the fixed 9-day rotation. The backlog held no pending Category D ideas (the two most recent fresh-idea sessions in Categories B and C both found stale/duplicate backlog rows and generated fresh instead, but D's backlog was simply empty — no ideas had ever been logged against it), so tonight's build is a fresh idea rather than a lottery draw.

## What I Hope the User Gets From This

1. A genuine head start on Canada List editorial work — a structurally complete, fact-grounded first draft in minutes instead of a blank page
2. A tool that plugs directly into the pipeline the last two Category B/C builds already built (Provenance's enriched CSV output), rather than one more standalone script
3. Confidence that the tool won't publish an unverified claim: any business without a `canadian` verdict is explicitly flagged in the generated copy, never silently treated as confirmed

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Workshop Architect — combinatorial generator for talk/workshop session plans (format × audience × topic module × activity type) targeting the named "developing educational workshops" and "Public education initiatives around empathy and AI" friction points | D | Genuinely viable and reuses the same proven architecture, but Maple Press has a stronger real-data hook (chains directly off Provenance's actual output) and targets a named project with a fuller supporting pipeline already built around it. Logged to `builds/ideas.md` for a future session. |
| Investment thesis narrative generator — turn portfolio holdings + fundamentals into a draft investment memo | D | Investing/finance already appeared twice in the last 10 builds (Portfolio Lab, Quarter Call); not yet "saturated" per the >2 threshold, but a third generative-content build in the same window risked topic imbalance versus the clearly under-served Canada List editorial gap. |
| Course Material Batch Formatter (backlog idea #13, Category B, already rated as a weak pattern) | B — not D | Wrong category for tonight, and already flagged in its own backlog notes as sharing AI Lecture Builder's 2/10 failure mode (no deterministic layer of comparable weight to the AI call). Ruled out on both counts. |
