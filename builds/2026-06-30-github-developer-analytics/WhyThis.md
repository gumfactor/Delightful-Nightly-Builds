# WhyThis — GitHub Developer Analytics Dashboard

## Category Decision
Tonight is day 181 of 2026. category_index = (181 - 1) % 9 = 0 → **Category A: Dashboard / Visualizer**.

## Lottery
- Pending Category A ideas in backlog: ID 3 (Lab Research Project Tracker, rating 4), ID 5 (GitHub Repository Health Scorecard, already built 2026-06-21), ID 6 (Open-Meteo Activity Planner, rating blank)
- Effective pool after excluding already-built: ID 3, ID 6
- R = 1 (one numeric rating)
- lottery_chance = min(75, 25 + 1×2) = 27%
- Roll: 81 (derived from day_of_year mod 100 = 181 mod 100 = 81)
- 81 > 27 → **fresh ideas**

## Topic Diversity Check (Last 10 Builds)
Domains in the last 10 builds: regex/game, developer tools (dep-check), fitness (run planner), GitHub (repo health), productivity (morning briefing), academic research (Paper Lens), education/AI (lecture builder), survey research (Qualtrics), investment (thesis journal), investment (watchlist dashboard).

Finance/investment appears twice (builds 9 and 10) — borderline but treated as saturated for tonight.
GitHub appeared once (Health Scorecard, 2026-06-21). A second GitHub-based dashboard is acceptable because the data angle is completely different.

## Why This Idea Over Others

Three fresh ideas were considered:

1. **GitHub Developer Analytics Dashboard** ← SELECTED
   - Uses live GitHub API (GITHUB_TOKEN always available)
   - Shows patterns GitHub's own UI doesn't surface: cross-repo activity timeline, hour-of-day coding heatmap, language evolution
   - Directly relevant to a developer managing many simultaneous projects
   - Distinct from the 2026-06-21 Health Scorecard (that = repo health scores; this = personal time-allocation patterns)

2. **Kwyeter Noise Profile Visualizer** → added to ideas.md
   - Would visualize noise level data to support the Kwyeter project
   - No suitable live noise API accessible through the proxy; would require manual data entry

3. **Canada List Category Intelligence Dashboard** → added to ideas.md
   - Statistics Canada open data could show which categories are underrepresented by Canadian businesses
   - Statistics Canada API is blocked by the network policy proxy; data would need to be pre-downloaded

## Why Not Others
- Backlog ID 3 (Lab Research Project Tracker): User explicitly noted "No need — already use Teamwork.com" in rating notes
- Backlog ID 6 (Open-Meteo Activity Planner): Open-Meteo API blocked by network policy proxy; similar weather data already appeared in the Run Planner (2026-06-20) and Morning Briefing (2026-06-22)

## Environmental Notes
- `ANTHROPIC_API_KEY` is not available in this scheduled routine environment (no API key in env). AI synthesis layer omitted; noted in BUILD_LOG.
- External APIs (OpenAlex, arXiv, Statistics Canada, Open-Meteo) are blocked by the network egress proxy. GitHub API is accessible.
- Build designed around what IS available: live GitHub data via GITHUB_TOKEN.

## Calibration Check
Previous A-category builds that scored poorly used mock data or had no visual output. This build:
- Uses real live data (GitHub API) ✓
- Has a visual interactive dashboard (4 tabs, Chart.js charts, CSS heatmap) ✓
- Offers insights GitHub doesn't surface natively ✓
- Is relevant to a solo founder managing many projects simultaneously ✓
