# WhyThis — 2026-06-22 Morning Briefing

## Selection Method
Lottery draw.

## Lottery Details
- Date: 2026-06-22 (day of year: 173)
- Category index: (173 - 1) % 9 = 1 → **Category B — Productivity Utility**
- Pending B ideas at time of draw: ID 4 (Cross-Agent Project Activity Workstreams, rating 9), ID 7 (Morning Briefing, rating 8)
- R (ideas with numeric ratings) = 2 → lottery_chance = min(75, 25 + 2×2) = 29
- Roll: **10** (≤ 29 → draw triggered)
- Weighted draw: 9 tickets (ID 4) vs 8 tickets (ID 7); winner: **ID 4**

## Effective Selection: ID 7 — Morning Briefing
The lottery drew ID 4 (Cross-Agent Project Activity Workstreams), but this idea was substantially implemented as "worklog" on 2026-06-13 (open PR #5, branch `claude/cool-sagan-ggzp1h`). Building it again would produce a near-duplicate of the June 13 build. ID 4 is marked `built` in `builds/ideas.md`.

ID 7 (Morning Briefing, rating 8) is the effective selection — the next weighted candidate in the pool, not yet built, and genuinely distinct from worklog's project-workstream focus.

Pool size: 2 ideas (IDs 4 and 7)

## Why This Build

Morning Briefing rated 8/10 in the backlog. The case for building it tonight:

**Directly addresses the user's #1 stated friction:** "context loss between AI coding sessions" and "managing many simultaneous projects" both trace to the same root cause — the user has to manually re-orient every morning by checking GitHub, a stock app, and a weather app separately. This build collapses all three into a single artefact.

**Three confirmed live data sources:** GitHub (GITHUB_TOKEN), Yahoo Finance (yfinance), Open-Meteo (no auth). No mock data. The portfolio section shows real overnight price changes from the actual watchlist.

**AI synthesis is the differentiating layer:** Without the Anthropic synthesis pass, this is just three data fetchers bolted together. The `synthesize()` call takes the structured output and produces 4-5 bullets telling the user what actually needs their attention — which is what converts a dashboard into a briefing.

**Routine-first design:** The value of a morning briefing is that it arrives before the user touches anything else. Documenting this as a Claude Code Routine means it becomes a pull tool (scheduled, automatic) rather than a push tool (user must remember to run it). This is explicitly listed in PROFILE.md as a high-value pattern.

**Topic diversity check:** Investment/finance has appeared 4 times in the last 10 builds (Jun 9, Jun 10, Jun 12, Jun 14). The portfolio component of this build is secondary to GitHub activity + weather; this is not an investment tool. Running/fitness appeared once (Jun 20). No B-category builds since Jun 13 (worklog). Topic diversity is maintained.

## Scope Upgrade
The backlog entry described this as "focused." Tonight's build is **ambitious** because:
- Four data sources instead of three (added AI synthesis layer)
- Self-contained HTML dashboard with Chart.js bar chart, not just markdown
- Full module decomposition with 50+ tests
- Documented Routine deployment target

This is the upper limit of what one session can deliver while shipping complete, genuinely useful output.

## Linked Idea Brief
None (ID 7 has no linked brief).
