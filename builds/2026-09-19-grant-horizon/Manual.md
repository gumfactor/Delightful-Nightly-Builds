# Manual — Grant Horizon

> **Version:** 1.0 (built 2026-09-19)
> **Complexity:** Ambitious

---

## What This Is

Grant Horizon is a competitive-intelligence tool for grant writing: it syncs live, public NIH RePORTER funding-award data for a configurable set of research topics into a local database, then renders a dashboard showing who else is funded, for how much, and where the money is trending — so you can write a sharper "gap in the funding landscape" argument and identify comparable funded projects before you submit.

---

## Quick Start

1. `cd builds/2026-09-19-grant-horizon`
2. `python3 src/main.py sync` — fetches and stores the latest data for the topics in `config.json` (default: psychopathy, affective neuroscience, empathy neuroscience, stress cortisol, forensic neuroscience; fiscal years 2020–2026)
3. `python3 src/main.py report` — renders `output/dashboard.html` and `output/projects_export.csv`
4. Open `output/dashboard.html` directly in a browser (no server needed)
5. Re-run `sync` + `report` before your next submission cycle to refresh the data — it upserts, so nothing is duplicated

Optional: `python3 src/main.py report --ai` with `ANTHROPIC_API_KEY` exported adds a one-paragraph AI-written funding-landscape briefing per topic. **What's sent to Anthropic when you use `--ai`:** the topic string itself (exactly as configured in `config.json` or passed to `--topics`), plus aggregate numbers computed from NIH's own public data (fiscal-year totals, institution names, project counts) and up to 8 project titles. PI names and abstracts are never sent (excluded by construction, not redaction — see `src/briefing.py`). Because the topic string is free text you control, avoid putting anything confidential in a custom `--topics` value if you don't want it sent to a third party; the 5 default topics are just plain research-area names.

Haven't looked at real output yet? Open `sample_output/dashboard.html` first — it's built from a realistic synthetic fixture (see `sample_output/README.md` for why) and shows exactly what a live sync would produce.

---

## How to Use It

### Configuring topics and fiscal years

Edit `config.json`:
```json
{
  "topics": ["psychopathy", "affective neuroscience", "..."],
  "fiscal_year_start": 2020,
  "fiscal_year_end": 2026
}
```
Or override per-run without editing the file:
```bash
python3 src/main.py sync --topics "oxytocin,antisocial behavior" --fy-start 2018 --fy-end 2026
python3 src/main.py report --topics "oxytocin,antisocial behavior" --fy-start 2018 --fy-end 2026
```
(Pass the same `--topics`/`--fy-start`/`--fy-end` to both `sync` and `report`, or set them once in `config.json`, so `report` reads the data `sync` actually fetched.)

### The dashboard

- **Hero stats** — total tracked funding, total projects, topic count, fiscal-year range
- **Funding by fiscal year, per topic** — a line chart (falls back to a plain table if the Chart.js CDN is unreachable)
- **Top funded institutions** — a bar chart of the 10 most-funded institutions across all tracked topics
- **Agency / IC breakdown** — which NIH institutes/centers are funding this work
- **Per-topic summary** — total funding and project count per topic, plus the AI briefing paragraph if `--ai` was used
- **Tracked projects table** — every synced project; type in the search box to filter by title, institution, or PI name, and click any column header to sort

### CSV export

`output/projects_export.csv` contains every tracked project with full detail (PI names, institution, agency, award amount, dates) for pasting into a grant's own literature/landscape section or a spreadsheet. Any cell that would otherwise be interpreted as a spreadsheet formula (starting with `=`, `+`, `-`, or `@`) is automatically prefixed so it opens as plain text instead.

---

## Running the Tests

Two independent suites:

```bash
python -m pytest tests/ -v          # core logic: RePORTER client, storage, aggregation, briefing, CSV/HTML rendering
npm install                         # one-time, installs @playwright/test
npx playwright test                 # the rendered dashboard's actual browser behavior (search, sort, XSS safety)
```

The Playwright suite regenerates its own HTML fixtures from the real `render.py` before every run (see `tests/global-setup.js`), so it always tests the same template the CLI ships, never a stale copy.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `topics` (config.json) | 5 topics matching this lab's research areas | Search terms sent to NIH RePORTER's full-text search across project title, terms, and abstract |
| `fiscal_year_start` / `fiscal_year_end` (config.json) | 2020 / 2026 | Fiscal-year range to sync |
| `ANTHROPIC_API_KEY` (environment variable) | unset | Enables `report --ai`; without it, `--ai` still works but uses the deterministic template |
| `--db` (CLI flag) | `output/grant_horizon.db` | SQLite database path |
| `--output-dir` (CLI flag, `report` only) | `output/` | Where `dashboard.html` and `projects_export.csv` are written |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `sync` fails with a `ReporterAPIError` about a failed request | No internet access, or NIH RePORTER is temporarily down | Check your connection and retry; RePORTER has no published rate limit for reasonable use but is a public government service that occasionally has downtime |
| Dashboard shows a plain table instead of charts | The Chart.js CDN (`cdn.jsdelivr.net`) couldn't load — no internet when the dashboard was opened, or a restrictive network | The table has the same numbers; reconnect and reload to get the chart view |
| `report --ai` briefings read like a plain data summary, not prose | No `ANTHROPIC_API_KEY` set, or the Anthropic API call failed | Export `ANTHROPIC_API_KEY` in your shell before running `report --ai`; the deterministic fallback is intentional and always complete, never broken |
| `report` shows 0 projects for a topic | You haven't run `sync` for that topic yet, or the topic string matched nothing in RePORTER | Run `sync` first; try a broader search term if a very specific phrase returns nothing |

---

## Known Limitations

- NIH RePORTER only covers NIH-funded projects — it does not include CIHR, NSERC, SSHRC, or other non-US funders. It's used here as competitive intelligence (the standard practice of citing the funded landscape in a "no one has yet funded X" argument), not as a claim that it's the complete funding picture.
- A project with multiple co-PIs has its full award amount credited to *each* named PI in the "Top PIs" ranking (RePORTER doesn't expose a per-PI budget split) — this is documented in `src/aggregate.py`, and means PI-ranking totals should be read as "involved with this much funding," not "personally received."
- No automatic re-sync scheduling is included — re-run `sync` manually before each grant-writing cycle (see `FutureFeatures.md` for a Routine-based version).
