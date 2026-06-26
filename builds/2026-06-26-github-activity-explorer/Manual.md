# Manual — GitHub Developer Activity Explorer

## What it does

Fetches your full GitHub commit history across all your repos for the past N months, analyzes your personal coding patterns, and renders a self-contained dark-mode HTML dashboard with:

- **Hourly heatmap** — which hours of the day do you commit most? (Eastern Time)
- **Day-of-week distribution** — which days are your most productive?
- **Weekly volume trend** — 52-week line chart showing your output over time
- **Repository focus map** — top 10 repos ranked by commit count
- **Stats cards** — total commits, peak hour, current streak, top repo
- **AI developer profile** — Claude Haiku analyzes your patterns and writes a plain-English summary (requires `ANTHROPIC_API_KEY`)

## Requirements

- Python 3.9+
- `GITHUB_TOKEN` environment variable (requires `repo` and `read:user` scopes)
- `ANTHROPIC_API_KEY` environment variable (optional — for AI insights)

Install dependencies:
```bash
pip install anthropic
```

## Usage

```bash
# Basic — 12 months of history, output to dashboard.html
python -m src.main

# Specify months and output path
python -m src.main --months 6 --output ~/Desktop/my-activity.html

# Skip AI insights (faster, no API key needed)
python -m src.main --no-ai

# Verbose output (shows which repos are being fetched)
python -m src.main --verbose
```

Run from inside the build folder:
```bash
cd builds/2026-06-26-github-activity-explorer
python -m src.main --verbose
```

Or from the repo root:
```bash
python -m builds.2026-06-26-github-activity-explorer.src.main --verbose
```

## Output

A single self-contained `dashboard.html` file — open it in any browser. No server required.
The file can be moved to any folder; it has no local dependencies beyond the CDN-hosted Chart.js.

## Running tests

```bash
python -m pytest builds/2026-06-26-github-activity-explorer/tests/ -v
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--months N` | 12 | Months of history to fetch |
| `--output PATH` | `dashboard.html` | Output file path |
| `--no-ai` | off | Skip Anthropic API call |
| `--verbose` | off | Print repo-by-repo progress |

## Notes

- Commits are capped at 300 per repo (3 pages × 100) to stay within GitHub rate limits
- Up to 50 repos are checked; repos with no activity in the date range are skipped
- Timestamps are converted from UTC to Eastern Time (America/Toronto) for the hourly and day-of-week charts
- Duplicate commits (same SHA appearing in a fork and source) are deduplicated
- If `ANTHROPIC_API_KEY` is not set, the AI insights panel shows a fallback message; run with the key set to generate the profile
