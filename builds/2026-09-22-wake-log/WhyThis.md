# Why This? — Wake Log

> **Date:** 2026-09-22

---

## How This Idea Was Selected

**Selection method:** Lottery draw from `builds/ideas.md`.

Day of year 265 → `category_index = (265-1) % 9 = 3` → **Category D — Creative / Generative**.

`builds/index.md` was resynced from the most recent open PR branch (`claude/cool-sagan-aaw3ax`, PR #105, 2026-09-21) before anything else, since local `main` was stale (last local build was 2026-06-24; the real catalog has 98 builds through 2026-09-21). Filtering `builds/ideas.md` to pending Category D rows produced exactly two: #57 (Psychology Experiment Design Idea Generator) and #58 (Boating/Cottage Weather-Window Trip Story Generator). Neither has a numeric rating, so `R = 0` matching rows with a rating → `lottery_chance = min(75, 25 + 0*2) = 25%`.

Rolled a random integer 1–100: **25**. `25 ≤ 25` → draw triggered.

Both pending ideas are unrated (blank = 5 tickets each, 10 tickets total). Weighted draw rolled **8 of 10** → landed on idea **#58, Boating/Cottage Weather-Window Trip Story Generator**, which was then marked `built` in `builds/ideas.md`.

## The Decision

Idea #58's own rating notes (written the night it was passed over, 2026-09-13) explicitly warned that a weather-driven generative narrative "sits too close to WeatherSong's (2026-07-03) already-built weather→creative-output mechanic" and that Open-Meteo comfort-window scoring is already used by Run Planner, Morning Briefing, and TripKit — with the explicit condition "worth building only with a mechanism clearly distinct from WeatherSong." I took that condition seriously: WeatherSong's differentiator is real-time Web Audio synthesis + Canvas visuals from weather data; Run Planner's differentiator is a generic multi-activity comfort score with no narrative output at all. Wake Log's mechanism is neither — it is a deterministic **Beaufort-scale wind classifier** feeding a **weighted boating-comfort scoring engine** (wind/gust/precip/temp/daylight, boating-specific thresholds, not reused from Run Planner's code or weights) that drives a **novelty-scored, mad-libs-style narrative template bank** (the same proven "deterministic draft + Jaccard novelty check against a persisted history" architecture used successfully by Maple Press and Research Question Forge, applied to a genuinely new domain and output shape: a written trip log entry, not audio/visuals). The lottery drew this idea; the job was to execute it with the differentiation its own notes demanded, not to overrule the draw.

## Connection to User Context

PROFILE.md names "boating" and "cottage life" explicitly under Personal Interests & Hobbies, and lists "boating, cottage life" among the domains where a personal tool would add value. No prior build (98 to date) has produced anything for this specific hobby except as a side-effect of Run Planner's generic activity-comfort scoring. This build gives the user a genuine planning tool — "which day this week should I actually take the boat out" — backed by real math (Beaufort scale is an actual maritime standard), plus a small creative payoff: a written log entry for the trip, grounded in the real forecast that justified picking that day.

## Why Tonight

Category D was up per the fixed 9-day rotation, and the lottery selected this specific idea from the backlog rather than requiring fresh generation. The 9-day rotation last put Category D up on 2026-09-13 (Preprint Pulse), so tonight is the first Category D night since this idea was logged.

## What I Hope the User Gets From This

1. A fast, real answer to "is this weekend good for the boat" backed by an actual meteorological classification (Beaufort scale) instead of a vague forecast glance.
2. A running personal log of boating/cottage days — a lightweight, zero-manual-entry-to-start journal that can be flipped through later (`render` produces a browsable HTML journal).
3. A small, genuine piece of writing per outing — not generic AI prose, but text whose specific numbers (wind speed, Beaufort description, temperature) are always traceable to the real forecast that produced it, deterministically by default and optionally AI-polished.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| #57 — Psychology Experiment Design Idea Generator | D | Lost the weighted draw (2/10 tickets vs. #58's 8/10). Also would have been the 4th build reusing the taxonomy × compatibility-rule-engine architecture (after Research Question Forge, Bridgework, Maple Press) — a real mechanic-repeat risk noted in its own backlog row. |
| Fresh idea: a second Category D generation path | D | Not reached — the lottery drew before fresh generation was needed (roll 25 ≤ 25% chance gate). |
