# Manual — Dockside: Cottage & Boat Season Readiness Dashboard

> **Version:** 1.0 (built 2026-08-04)
> **Complexity:** Ambitious Project

---

## What This Is

Dockside tracks the recurring seasonal maintenance tasks that come with owning a cottage or a boat — dock installation, dock removal, winterizing, engine service — and tells you, using real live weather and marine forecast data for your actual location, which of them are ready to do this week and which are blocked and why. It also shows a general "boating outlook" for the next 7 days, independent of any specific chore. Everything runs locally: one SQLite file, no server, no account.

---

## Quick Start

1. `python3 src/main.py add-site "Cottage Dock" --location "Muskoka, Ontario"` (or `--lat`/`--lon` if you'd rather skip geocoding)
2. `python3 src/main.py add-task "Install Dock" --site "Cottage Dock" --category dock --window-start-month 4 --window-end-month 5 --max-wind 25 --min-water-temp 8`
3. `python3 src/main.py sync` — fetches live forecast + marine data and scores every task
4. `python3 src/main.py render --site "Cottage Dock"` — writes a standalone HTML dashboard; open it in any browser
5. (Optional) `export ANTHROPIC_API_KEY=sk-...` then `python3 src/main.py brief --site "Cottage Dock"` for an AI-written season briefing

All commands run from the build folder root (`builds/2026-08-04-dockside/`).

---

## How to Use It

### Sites

A site is a location — your cottage, a marina slip, wherever the tasks and weather apply. `add-site NAME --location "City, Region"` geocodes via the free Open-Meteo Geocoding API. If you'd rather not geocode, pass `--lat` and `--lon` directly. `list-sites` shows every configured site and whether marine data (wave height, water temperature) is available there — this is only known after the first `sync`, since it depends on whether Open-Meteo's marine model covers that location (many inland lakes aren't covered; that's normal, not a bug).

### Tasks

A task belongs to a site and has:
- `--category` — one of `dock`, `boat`, `water_system`, `structure`, `other`
- `--window-start-month` / `--window-end-month` — the months (1–12) this task is normally done in, e.g. `4 5` for April–May
- Optional weather constraints, any combination:
  - `--max-wind N` — maximum acceptable wind speed in km/h
  - `--min-water-temp N` — minimum acceptable water temperature in °C (requires marine data)
  - `--dry-days N` — requires N consecutive dry days (under 1mm precipitation) ending on the candidate day
  - `--frost-free` — requires the day's low temperature to stay above 0°C

`list-tasks [--site NAME]` shows everything configured.

### Sync

`sync [--site NAME]` fetches a 7-day forecast (and, best-effort, marine data) for every site (or just the one named), stores it, and prints a readiness line for every active task: `[id] Task Name: status (best day: YYYY-MM-DD)`. Re-running `sync` on the same day never creates duplicate rows — it just refreshes the numbers.

### Task statuses

| Status | Meaning |
|--------|---------|
| `ready_now` | Today satisfies every constraint the task specifies |
| `ready_soon` | Not today, but a day within the next 7 satisfies everything |
| `not_ready` | Currently in-window, but no day this week satisfies every constraint |
| `overdue` | The task's window has passed for this year and it was never marked complete |
| `off_season` | The task's window hasn't started yet this year |
| `done_this_season` | Already marked complete for the current calendar year |

### Completing a task

`complete TASK_ID [--date YYYY-MM-DD]` (defaults to today) records the task as done for that year and prints when next season's window is expected to open. You'll see it again automatically once next year's window arrives.

### Dashboard

`render --site NAME [--output PATH]` writes a self-contained dark-mode HTML file (default name `dockside-<site-name>.html`) with:
- **This Week's Boating Outlook** — a 0–100 comfort score per day combining wind, precipitation, temperature, and wave height (when available)
- **Weather Trend** — 7-day max/min temperature and wind chart
- **Season Task Readiness** — one card per active task with its status badge, best available day, and a pass/fail/unknown breakdown of every constraint it uses
- **Season Briefing** — the most recent output of `brief`, if you've run it

If Chart.js's CDN is unreachable, both charts automatically fall back to a plain data table — nothing breaks, you just get numbers instead of a picture.

### AI Briefing

`brief --site NAME` asks Claude Haiku for a short, practical summary of the week ("pull the dock Saturday, wind's calm; hold off on winterizing until Thursday's frost passes"). It reads `ANTHROPIC_API_KEY` from your environment. **With no key set, it makes zero network calls** and instead prints a short deterministic summary counting ready vs. blocked tasks — the tool is fully useful without ever calling the Anthropic API.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `dockside.db` | Path to the SQLite database file (global flag, before the subcommand) |
| `ANTHROPIC_API_KEY` (env var) | unset | Enables the AI briefing; falls back to a deterministic template when absent |

No configuration file is required — everything above is a CLI flag or environment variable.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `list-sites` shows `marine_data=unknown` | You haven't run `sync` yet | Run `sync` once; the flag is set on the first successful fetch attempt |
| A task never shows `ready_now` even in calm weather | `--min-water-temp` set on a site with no marine coverage | Check `list-sites` — if `marine_data=no`, drop the water-temp constraint for that site's tasks; inland lakes are often outside Open-Meteo's marine model grid |
| `add-site --location "..."` fails with "No geocoding match" | The place name is too vague or unrecognized | Try a more specific name (e.g. add the province/state), or pass `--lat`/`--lon` directly |
| Charts don't render in the HTML dashboard | Chart.js CDN blocked or offline | Expected fallback: a plain data table appears instead automatically — no action needed |

---

## Known Limitations

- Season windows that wrap the calendar year boundary (e.g. a Nov–Feb winterizing window) are correctly evaluated while "in window," but Dockside doesn't compute an `overdue` state for them — the ambiguity of "overdue relative to which year's window" wasn't worth the complexity for a first release. Non-wrapping windows (the common case: spring/fall tasks) have full `overdue` support.
- Marine data (wave height, water temperature) depends entirely on Open-Meteo's marine model coverage for your exact coordinates. Many inland lakes and small bays aren't covered; Dockside detects this per-site and shows the affected constraints as "data unavailable" rather than guessing.
- The dashboard is a static snapshot — completing a task or adding a new one requires the CLI; there's no "mark complete" button in the HTML itself.
- Boating comfort score is a simple, transparent weighted average, not a calibrated model — treat it as a quick read, not a forecast guarantee.
