# Why This? — Earshot

> **Date:** 2026-08-14

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Category A's backlog held 3 pending rows after correcting a stale duplicate (#5, GitHub Repository Health Scorecard, a verbatim duplicate of the already-built 2026-06-21 build — marked `skipped` tonight). Remaining pool: #3 (rating 4) and #6 (unrated → 5 tickets). R = 1 rated idea, so `lottery_chance = min(75, 25 + 1*2) = 27%`. Rolled 84 (Python `random.randint(1,100)`) — 84 > 27, a miss, so the process moved to fresh idea generation.

## The Decision

Scanned the last 10 builds for topic saturation before generating candidates: investing/finance had appeared twice (Portfolio Lab 2026-08-09, Quarter Call 2026-08-11) — not yet "more than twice" per CLAUDE.md's threshold, but close enough that a third in a row felt like it would skew weight away from other named PROFILE.md domains, so investing-flavored candidates were deliberately not proposed. GitHub-API dashboards have also recurred heavily in Category A specifically (2026-06-21, 2026-06-30) and elsewhere (Landing Pattern, 2026-08-03) — another one would have added no differentiation.

Scanning PROFILE.md's named active projects against the full catalog turned up something concrete: **Kwyeter**, described verbatim as "a technology platform focused on environmental noise awareness and accessibility... calibrated sound measurements, venue-level noise information, and tools that support individuals with sensory sensitivities, tinnitus, or other hearing-related concerns," has zero prior builds anywhere in this catalog — the only one of the five explicitly named active personal projects with no coverage at all. That's a stronger signal than a generic "untouched topic" — it's a named product the user is actively building, and a working proof-of-concept of its core mechanic (measure real ambient noise, classify it, track exposure over time) is directly useful groundwork rather than a toy.

## Connection to User Context

PROFILE.md names Kwyeter explicitly under "Active personal projects" and separately lists "sensory sensitivities, tinnitus" support as its stated purpose. It also lists "Neuroimaging methods and forensic neuroscience" and general auditory/sensory-processing adjacency through the user's affective-neuroscience research, which makes real, honestly-labeled sound-level measurement (rather than a mocked demo) a genuinely relevant technical exercise, not just a product prototype.

## Why Tonight

Day-of-year rotation (day 226, `(226-1) % 9 = 0`) puts tonight in Category A — Dashboard/Visualizer, which the STANDARDS.md ambition floor requires to ship with a real visual/interactive interface, not a CLI. A live sound-level dashboard is a natural fit for that requirement: the "dashboard" is not just a display of pre-fetched data but a live instrument reading a real physical signal (the device microphone) in real time, which is a genuinely different data-source shape from every other Category A build so far (all of which have been GitHub/market/econ/citation API pulls).

## What I Hope the User Gets From This

1. A real, working first look at Kwyeter's core value proposition — "is this environment loud enough to matter" — running as an actual tool tonight, not a mockup or a pitch deck slide.
2. An honest, well-labeled instrument: it never claims calibrated-SPL accuracy it can't deliver from a laptop mic, and the exposure-dose math is the same standard NIOSH 3 dB-exchange-rate formula used by real occupational-safety tools, cross-checked against hand-computed values in tests.
3. A concrete technical foundation (live audio capture, A-weighting approximation, exposure dose accumulation, session history) that a future Kwyeter build or the product itself could extend directly, unlike a build whose logic doesn't transfer.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Canada List Coverage & Growth Dashboard | A | Real gap in Category A's coverage of The Canada List, but requires the user to manually supply a fresh directory export every run rather than the tool fetching or measuring anything live itself — a weaker "real data" story than an instrument reading an actual physical signal. Logged as backlog idea #26 for a future build where a real export can be arranged. |
| Sector Rotation Heatmap (yfinance sector-ETF momentum) | A | Technically strong and genuinely live-data-backed, but investing/finance had already appeared twice in the last 10 builds; a third in a row risked crowding out other named PROFILE.md domains this session correctly prioritized instead. Logged as backlog idea #27. |
| GitHub Contribution / Review-Load Dashboard | A | Category A already has two prior GitHub-API dashboards (2026-06-21, 2026-06-30) plus Landing Pattern (2026-08-03, Category H) and Waymark (2026-08-07, Category C) covering GitHub/git activity from multiple angles — a third Category A GitHub dashboard would add no real differentiation and risked reading as the "wrong layer automated" critique this catalog has flagged before. |
