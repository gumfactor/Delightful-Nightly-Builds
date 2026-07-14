# Manual — GrantScope

> **Version:** 1.0 (built 2026-07-14)
> **Complexity:** Ambitious Project

---

## What This Is

GrantScope pulls currently and recently funded NIH grants in your own research domain — empathy, psychopathy, stress/coping, forensic neuroscience, and affective neuroscience — from the free, public NIH RePORTER database, and turns them into a browsable local dashboard: who's funding this work, through what mechanisms (R01 vs. R21 vs. K-series), at what Institutes/Centers, and roughly what scale of award. It's meant to shortcut the manual research you'd otherwise do by hand on the NIH RePORTER website before writing a grant, and it keeps a searchable local history you can revisit and re-sync over time.

---

## Quick Start

1. `cd builds/2026-07-14-grantscope`
2. `python3 src/main.py sync` — fetches projects for all 5 default topics from NIH RePORTER (requires internet access; no API key needed)
3. `python3 src/main.py build` — renders `output/dashboard.html` from the synced data
4. Open `output/dashboard.html` directly in any browser (no server required)
5. (Optional) `export ANTHROPIC_API_KEY=sk-...` before step 3 to get an AI-generated landscape briefing instead of the deterministic template summary

---

## How to Use It

### Syncing data

```
python3 src/main.py sync                              # all 5 default topics, last 5 fiscal years
python3 src/main.py sync --topics empathy psychopathy  # only specific topics
python3 src/main.py sync --years 2022 2023 2024        # specific fiscal years
python3 src/main.py sync --max-results 200             # more results per topic (default 100)
```

Re-running `sync` is safe — projects are deduplicated by NIH's core project number, so re-syncing updates existing records (refreshing `last_seen`) instead of creating duplicates.

### Building the dashboard

```
python3 src/main.py build                  # renders output/dashboard.html
python3 src/main.py build --refresh-briefing  # force-regenerate AI briefings even if cached
python3 src/main.py build --no-ai           # skip AI calls entirely, use template briefings
```

The dashboard has an **Overview** tab (aggregated across all topics) plus one tab per topic, each with:
- A funding-by-fiscal-year line chart
- A top-funding-Institutes/Centers bar chart
- A funding-mechanism (R01/R21/K01/etc.) doughnut chart
- A searchable, sortable table of every stored project
- A one-paragraph landscape briefing (AI-generated if `ANTHROPIC_API_KEY` is set, otherwise a deterministic summary)

If your browser can't reach the Chart.js CDN (offline use), each chart card automatically falls back to a plain-text summary of the same numbers — the dashboard never breaks, it just loses the visual charts.

### Terminal summary

```
python3 src/main.py stats                    # summary across all topics
python3 src/main.py stats --topic empathy     # summary for one topic
```

### Searching

```
python3 src/main.py search "risk assessment"
```

Matches against project title, abstract, organization name, and PI name.

### Listing topics

```
python3 src/main.py list-topics
```

### Refreshing just the AI briefing

```
python3 src/main.py briefing                  # all topics
python3 src/main.py briefing --topic stress_coping
```

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db` | `output/grantscope.db` | SQLite database path (global flag, before the subcommand) |
| `ANTHROPIC_API_KEY` (env var) | unset | When set, `build` and `briefing` call Claude Haiku for an AI-generated landscape briefing. Unset → deterministic template summary. Never required. |
| `--years` (sync) | last 5 fiscal years | Which NIH fiscal years to query |
| `--max-results` (sync) | 100 | Max projects fetched per topic per sync |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `sync` fails with "Could not reach NIH RePORTER API" | No internet access, or the API is temporarily down | Check your connection and retry; the NIH RePORTER API is free and requires no account, so a persistent failure is almost always network-side |
| `build` produces an empty-looking dashboard | No `sync` has been run yet, or it synced zero results for every topic | Run `python3 src/main.py sync` first, or check `python3 src/main.py stats` to confirm data is stored |
| Charts don't render but the page loads | The Chart.js CDN (`cdn.jsdelivr.net`) is unreachable — likely a restrictive network | Expected fallback: text summaries replace the charts automatically; the table and briefing are unaffected |
| Briefing always says "(Deterministic summary...)" | `ANTHROPIC_API_KEY` isn't set in your shell | `export ANTHROPIC_API_KEY=sk-...` before running `build` or `briefing` |

---

## Known Limitations

- Only NIH RePORTER is queried — NSF, DoD, and private-foundation funding are not included (see FutureFeatures.md)
- The five default topics are fixed in `src/topics.py`; there's no CLI command yet to add or edit topics without editing that file
- PI names come directly from NIH RePORTER as free text and aren't deduplicated across name variants (e.g. "Jane A Smith" vs. "Jane Smith") — treat the PI field as approximate
- `sync` always re-fetches the full requested fiscal-year window rather than doing a true incremental sync
