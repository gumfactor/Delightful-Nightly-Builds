# WhyThis.md — Run Planner

## Selection Method

**Fresh generation** — no lottery. The Category I (Life Admin Helper) backlog had zero pending ideas, so the lottery was skipped entirely and ideas were generated fresh.

## Lottery Details

- Pool size: 0 pending Category I ideas
- Roll: N/A (lottery skipped)
- Idea Brief: none (fresh idea)

## Category Determination

- Today: 2026-06-20 UTC
- Day of year: 171
- category_index = (171 - 1) % 9 = 170 % 9 = **8 → Category I — Life Admin Helper**

## Fresh Idea Generation

Three candidates generated:

**Candidate 1 (SELECTED): Run Planner — Running Training Log & Weather Planner**
Logs running workouts in local JSON, fetches Open-Meteo 7-day forecast for Toronto, scores hourly windows for running comfort (temperature, wind, precipitation), and generates an HTML dashboard with mileage charts and ranked training windows.

**Candidate 2 (added to ideas.md): Weekly Project Dashboard / Context Switcher**
A browser-based tool (HTML/JS, localStorage) to set weekly priorities across active projects (lab, Canada List, investments, personal), mark items complete, and export a weekly review summary. Directly addresses the "managing many simultaneous projects" friction.

**Candidate 3 (added to ideas.md): Student Supervision Log**
A Python CLI + HTML report to log grad student / RA supervision sessions — meeting date, agenda, action items, next check-in — with a weekly "who do I need to follow up with?" summary. Designed for a lab director managing 3–6 students simultaneously.

## Why Run Planner Wins

1. **Real data source available**: Open-Meteo is in PROFILE.md's no-auth sources. The weather integration makes this tool meaningfully better than a spreadsheet.
2. **Directly serves the user**: PROFILE.md lists distance running as an active physical hobby. The user already tracks fitness via Garmin Connect and MyFitnessPal — a local log + planning tool is additive, not redundant.
3. **Saves real time**: The top-ranked value is "things that save real time." Checking weather, opening Garmin, estimating pace — a single `python src/main.py plan` replaces 3 context switches.
4. **Novel domain**: Fitness/running has appeared zero times in the 10-build catalog. Investment/finance dominates — this adds genuine diversity.
5. **Firmly Category I**: Habit log + personal planner. Not a developer tool, not a data explorer — this is personal life administration.
6. **Testable logic**: Weather scoring functions, pace calculation, streak counting, and duration parsing all have clear inputs/outputs and meaningful edge cases.

## Domain Saturation Check (last 10 builds)

- Investment/finance: 5+ times (A×3 + C×1 + H×0) — heavily saturated, avoiding
- Developer tooling: 2 times (H×2)
- Data/research: 2 times (F×2)
- Games: 1 time (G×1)
- Fitness/health: 0 times → **new territory**
