# Manual — GitHub Developer Analytics Dashboard

## What it does

Fetches your GitHub commit history and language data via the GitHub API, then generates a single self-contained HTML file with four interactive tabs:

- **Overview** — Hero metrics (total commits, active repos, most active project, top language) and a ranked bar chart of your top 8 repos by commit count
- **Timeline** — A project-activity heatmap: each row is one of your top 15 repos, each column is a month, cell colour shows commit intensity (dark green = many commits, dim = few)
- **Rhythm** — Two bar charts: commits by hour of day (UTC) and by day of week, revealing when you actually code
- **Languages** — A stacked horizontal bar showing byte-level language breakdown per repo (your top 10 repos, top 8 languages)

## Requirements

- Python 3.9+
- `requests` library: `pip install requests`
- `GITHUB_TOKEN` environment variable (read access to your repos)

## Run

```bash
cd builds/2026-06-30-github-developer-analytics
export GITHUB_TOKEN=your_token_here   # skip if already in env

python3 src/main.py
# → writes dashboard.html in the current directory

python3 src/main.py --output ~/Desktop/github-analytics.html
python3 src/main.py --months 6     # last 6 months only
python3 src/main.py --max-repos 30 # cap at 30 repos
```

Then open `dashboard.html` in any browser (Firefox, Chrome, Safari). No server needed.

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--output PATH` | `dashboard.html` | Output file path |
| `--months N` | `12` | Months of history to include |
| `--max-repos N` | `50` | Maximum repos to scan |

## Notes

- Commits are counted per author login. The script only counts commits authored by your GitHub username.
- Private repos require a token with `repo` scope. Without it, private repos are silently skipped and only public repos appear.
- Hour-of-day data is in UTC. Adjust mentally for your timezone (EST = UTC−5, EDT = UTC−4).
- The output file is fully self-contained: Chart.js loads from CDN (`cdn.jsdelivr.net`), so an internet connection is needed to render the charts in the browser.

## Run tests

```bash
cd builds/2026-06-30-github-developer-analytics
python3 -m pytest tests/ -v
# Expected: 61 passed, 0 failed
```
