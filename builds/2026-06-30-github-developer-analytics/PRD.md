# PRD — GitHub Developer Analytics Dashboard

## Goal

Generate a self-contained HTML dashboard that reveals personal GitHub coding patterns — when you code, which projects consumed your attention, and how your tech stack has evolved — using live data from the GitHub API.

## User Story

As a developer managing many simultaneous projects, I want to open a single dashboard and immediately see:
- Which projects I was actively working on each month
- What time of day and day of week I code most
- How my language/technology mix has shifted over the past year
- Which repos received the most commits

So I can make better decisions about where to focus and understand my own working patterns.

## Scope

### In Scope
- Fetch all repos owned by the authenticated GitHub user (up to 50 most recently pushed)
- Fetch commits authored by the user in the last 12 months for each repo
- Fetch language byte counts per repo
- **Tab 1 — Overview**: Hero metrics (total commits, active repos, most active repo, top language), plus top 5 repos ranked by commits with mini bars
- **Tab 2 — Timeline**: CSS grid heatmap — rows = repos (top 15 by total commits), columns = months (12 months), cell colour intensity = commit count
- **Tab 3 — Rhythm**: Two Chart.js bar charts — commits by hour of day (0–23, UTC) and commits by day of week (Mon–Sun)
- **Tab 4 — Languages**: Chart.js stacked horizontal bar chart of language bytes per repo (top 10 repos, top 8 languages)
- Dark mode HTML output; mobile-responsive; self-contained single file
- CLI: `python3 src/main.py --output dashboard.html [--months N] [--max-repos N]`
- GitHub API authenticated via `GITHUB_TOKEN` environment variable

### Out of Scope
- PR and issue analysis
- Collaboration / team analysis
- AI-generated insights (Anthropic API unavailable in this environment)
- Real-time / auto-refresh
- Multi-user comparison

## Tech Stack

- **Language**: Python 3.11
- **HTTP**: `requests` library (stdlib + requests 2.33.1)
- **HTML rendering**: Python f-string template with embedded JSON data
- **Charts**: Chart.js 4.4.4 via CDN (loaded in browser, not in Python)
- **Timeline heatmap**: CSS grid with JS colour interpolation (no plugin needed)
- **Testing**: pytest 9.1.1
- **External APIs**: GitHub REST API v3 (`api.github.com`), authenticated via `GITHUB_TOKEN`

## Data Structures

```python
# Commit record stored per repo
{
    "sha": str,
    "date_utc": str,          # ISO 8601, e.g. "2026-06-30T14:23:45Z"
    "hour": int,               # 0-23 UTC
    "weekday": int,            # 0=Mon, 6=Sun
    "year_month": str          # "2026-06"
}

# Analytics payload embedded in HTML as JSON
{
    "generated_at": str,       # ISO 8601
    "total_commits": int,
    "active_repos": int,
    "months": [str],           # ["2025-07", ..., "2026-06"] — 12 items
    "timeline": {
        "repos": [str],        # top 15 repo names
        "data": [[int]],       # data[repo_idx][month_idx] = commit count
        "max_val": int         # for colour scaling
    },
    "hour_counts": [int],      # 24 items (hour 0-23)
    "weekday_counts": [int],   # 7 items (Mon=0 to Sun=6)
    "top_repos": [{"name": str, "commits": int}],   # top 10
    "languages": {
        "repos": [str],        # top 10 repos with any language data
        "langs": [str],        # top 8 languages
        "data": [[int]]        # data[repo_idx][lang_idx] = byte count
    }
}
```

## Folder Structure

```
builds/2026-06-30-github-developer-analytics/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── github_client.py    # GitHub API wrapper
│   ├── analytics.py        # Data aggregation logic
│   ├── renderer.py         # HTML template + generation
│   └── main.py             # CLI entry point
└── tests/
    ├── test_github_client.py
    ├── test_analytics.py
    └── test_renderer.py
```

## Testing Strategy

All logic is in pure-Python modules (no UI framework to stub). Tests use `unittest.mock.patch` to mock HTTP calls in `github_client.py` and test the aggregation/rendering logic directly.

| Layer | What is tested |
|-------|---------------|
| `github_client.py` | URL construction, pagination handling, timestamp parsing, empty-list handling, error recovery |
| `analytics.py` | Timeline matrix construction, hour/weekday bucketing, top-repos ranking, language aggregation, edge cases (zero commits, single repo, all commits in one month) |
| `renderer.py` | Output file created, HTML contains Chart.js script tag, analytics JSON embedded correctly, valid HTML structure, graceful empty-data rendering |

## Success Criteria

1. **Live data**: Running `python3 src/main.py` with `GITHUB_TOKEN` set fetches real repos and commits and produces a non-empty HTML file without errors.
2. **Timeline heatmap**: The generated HTML contains a visible grid with at least one non-zero cell coloured by commit intensity.
3. **All four tabs render correctly**: Overview, Timeline, Rhythm, Languages tabs each contain their respective chart or grid.
4. **Edge-case safety**: Script completes without crash when a repo returns zero commits in the time window.
5. **Tests pass**: All 20+ pytest tests pass with zero failures.
