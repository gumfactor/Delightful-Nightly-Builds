# Manual — GitHub Repository Health Scorecard

## Requirements

- Python 3.8 or later (no additional packages required)
- `GITHUB_TOKEN` environment variable — a GitHub personal access token with `repo` scope (or a fine-grained token with Repository Read access)
- Optional: `ANTHROPIC_API_KEY` for the AI briefing section

## Running

```bash
# From the build folder
python3 src/main.py

# Specify output file name
python3 src/main.py --output ~/Desktop/github_health.html

# Skip AI insights (faster; still generates the full dashboard)
python3 src/main.py --no-ai

# Open the generated file
open github_health_report.html       # macOS
xdg-open github_health_report.html  # Linux
start github_health_report.html      # Windows
```

## Setting GITHUB_TOKEN

```bash
# Temporary (current shell session only)
export GITHUB_TOKEN=ghp_yourtokenhere

# Permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export GITHUB_TOKEN=ghp_yourtokenhere' >> ~/.zshrc
```

Generate a token at: github.com/settings/tokens — needs `repo` scope to see private repos.

## Dashboard Overview

| Section | Description |
|---------|-------------|
| **Stats row** | Counts of repos by health label at a glance |
| **AI Briefing** | 3-4 natural-language bullet points from Claude Haiku (if `ANTHROPIC_API_KEY` is set) |
| **Health Distribution** | Doughnut chart showing the breakdown across health labels |
| **Repo Table** | Full repo list, sortable by any column, filterable by label or search |

## Health Score Calculation (0–100)

| Component | Max | Rules |
|-----------|-----|-------|
| Recency | 30 | ≤1 day: 30 / ≤7 days: 25 / ≤30 days: 15 / ≤90 days: 5 / older: 0 |
| CI Status | 40 | Passing: 40 / Running: 30 / No CI: 20 / Failing: 10 |
| Open Issues | 30 | 0: 30 / 1–5: 20 / 6–20: 10 / >20: 0 |

## Health Labels

| Score | Label | Color |
|-------|-------|-------|
| 80–100 | Healthy | Green |
| 60–79 | Good | Blue |
| 40–59 | Fair | Yellow |
| 20–39 | Needs Attention | Orange |
| 0–19 | Stale | Red |

## CI Status Values

| Label | Meaning |
|-------|---------|
| **Passing** | Latest workflow run concluded successfully |
| **Failing** | Latest workflow run failed or timed out |
| **Running** | A workflow run is currently in progress |
| **No CI** | No GitHub Actions workflow runs found |

## Filtering and Sorting

- **Search box** — filters by repo name, language, or description (live, client-side)
- **Filter buttons** — shows only repos with a specific health label
- **Column headers** — click any sortable column to sort; click again to reverse

## Running Tests

```bash
python3 -m pytest tests/ -v
```

54 tests across scorer, GitHub client, report generator, and AI summary modules.
