# Why This? — Renewal Radar

> **Date:** 2026-08-22

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 234 → `category_index = (234-1) % 9 = 8` → Category I — Life Admin Helper. `builds/ideas.md` (synced from the most recent open PR branch, `claude/cool-sagan-w0k5dx`, build #77) held zero `pending` rows tagged Category I, so the lottery step was skipped entirely per Step 2c/2d and fresh ideas were generated directly.

## The Decision

Category I already has five prior builds: Ledger Lens (spending/budget), Deadline Guardian (academic administrative deadlines), TripKit (weather-aware trip packing), Dockside (boat/cottage seasonal maintenance), and Macro Kitchen (meal/macro planning). CLAUDE.md's own named Category I examples are "budget tracker, meal planner, habit log, checklist" — budget and meal planner are both already built, and a plain habit log or checklist would either duplicate Teamwork.com/Coda (already flagged as unwanted in `builds/ideas.md` idea #3: "No need — already use Teamwork.com for project tracking") or read as a toy with no real data behind it (the exact 4/10-and-below failure pattern named in CLAUDE.md's calibration note: mock/manual data instead of live integration). Renewal Radar was chosen instead because it has a genuinely live, no-auth, no-credential data source that no prior build has touched — RDAP domain-expiration lookups and direct TLS certificate-expiration handshakes — combined with a real, named administrative-overhead friction point that has nothing to do with academic deadlines (Deadline Guardian's territory) or the Canada List's ingestion pipeline (Ingest Gate's territory).

## Connection to User Context

PROFILE.md names "administrative overhead" and "keeping multiple data systems synchronized" as recurring friction points for someone running two live platforms — The Canada List and Kwyeter — on top of a full academic role. Both platforms depend on domains staying registered and certificates staying valid; a lapsed domain or an expired cert on a public-facing site is a silent, high-consequence failure that a spreadsheet or memory won't reliably catch. This build gives that specific, named risk a live, automated check rather than another manual-entry list.

## Why Tonight

Category I comes up once per 9-day rotation; today is that night. No other Category I idea in the backlog was pending, so this was the natural point to fill the "genuinely live-data, non-duplicate Life Admin build" gap the category has been missing since Dockside (2026-08-04) introduced live Open-Meteo Marine data — Renewal Radar does the same thing (a real network check replacing a manual log) for a different, previously-untouched domain.

## What I Hope the User Gets From This

1. A single command (`sync` + `render`) that tells them, using real live data, whether any domain behind The Canada List or Kwyeter is close to a registration or certificate lapse — something they currently have no automated way to know.
2. A place to put the non-technical admin renewals (business license, insurance, professional memberships) that otherwise live only in memory or scattered emails, with correct recurrence math so a completed renewal reappears at the right future date without re-entering it.
3. A dashboard they can open on their phone (per PROFILE.md's stated mobile-readability preference) that surfaces what needs attention this week without them having to check three different registrar/CA dashboards manually.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Habit Log (cross-domain habit tracker, e.g. running/golf/strength/writing streaks) | I | Would be localStorage/manual-entry only with no live data source behind it — the exact pattern CLAUDE.md's calibration note flags as the top driver of low ratings. Garmin Connect data is only available as a CSV export the user has to manually download (as Macro Kitchen already uses), which doesn't solve the "no real automated signal" problem for a daily habit log. |
| Generic Checklist / Recurring Chore Tracker | I | Directly overlaps with Teamwork.com and Coda, which `builds/ideas.md` idea #3's rating notes already explicitly rejected for project/task tracking ("No need — already use Teamwork.com for project tracking"). No differentiating live-data angle. |
| Subscription Cost Tracker (manually-entered recurring software/service costs, spending trend over time) | I | Real friction point, but functionally a narrower re-run of Ledger Lens's (2026-07-08) already-built recurring-charge detection from bank CSV exports — not enough differentiation to justify a second build on the same problem. |
