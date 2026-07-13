# PRD — GitHub Developer Activity Explorer

> **Build date:** 2026-06-26
> **Category:** F — Data Explorer
> **Complexity:** ambitious

---

## Goal

Fetch the authenticated user's full commit history from GitHub, analyze personal coding patterns, and render an interactive self-contained HTML dashboard that reveals when, where, and how they code — with an AI-generated developer profile written by Claude Haiku.

## User Story

As a solo developer who maintains multiple active repositories, I want to see a deep breakdown of my coding patterns across all my repos — hourly heatmap, day-of-week distribution, weekly volume trend, and repo focus map — so that I can understand my productivity rhythms and get a plain-English developer profile that GitHub's built-in graphs never provide.

## Scope

### In Scope
- Fetch all repos and commits for the authenticated GitHub user via GITHUB_TOKEN (up to 12 months, up to 50 repos)
- Hourly distribution chart: when during the day do I commit? (24-bar chart, converted to Eastern Time)
- Day-of-week distribution chart: which days am I most active?
- Weekly volume trend chart: how has my output changed over the past year? (52 weeks)
- Repository focus map: horizontal bar chart showing top 10 repos by commit count
- Streak analytics: current streak, longest streak, total active days
- Stats cards: total commits, most productive hour, current streak, commits per active day
- AI-generated developer profile: Claude Haiku analyzes all pattern data and writes 3 sentences describing the developer's coding style, peak time, and dominant focus area
- Self-contained HTML output: all data embedded as JSON, Chart.js from CDN, opens directly in browser
- Dark mode, mobile-responsive layout
- CLI with `--months` (default 12) and `--output` (default `dashboard.html`) flags

### Out of Scope
- Commit size / lines-of-code analysis (would require per-commit detail API calls)
- Collaboration metrics (PRs, reviews — this focuses on commits/personal output)
- Historical comparison across different accounts
- Live/auto-refreshing dashboard (static HTML output)
- GitHub Enterprise / non-github.com hosts

## Tech Stack

- **Language:** Python 3.9+
- **Framework:** None (stdlib HTTP + urllib)
- **Dependencies:** `anthropic>=0.52.0` (AI insights), `zoneinfo` (stdlib in 3.9+)
- **Runtime requirement:** `python src/main.py` (requires GITHUB_TOKEN and ANTHROPIC_API_KEY env vars)
- **Output:** self-contained HTML file, Chart.js 4.4.4 from CDN

## Data Structure

### Commit record (internal)
```
{
  "repo": "owner/repo-name",
  "sha": "abc1234",
  "timestamp": "2026-06-24T22:15:00Z",   # UTC ISO 8601
  "message": "fix: handle edge case in parser"
}
```

### Stats dict (passed to AI and renderer)
```
{
  "username": "gumfactor",
  "total_commits": 1247,
  "active_days": 93,
  "commits_per_active_day": 13.4,
  "most_productive_hour": 22,
  "most_productive_day": 1,            # 0=Mon, 6=Sun
  "current_streak": 7,
  "longest_streak": 31,
  "top_repo": "gumfactor/my-project",
  "top_repo_count": 423,
  "months": 12,
  "hourly_distribution": {0: 5, 1: 3, ..., 23: 88},
  "day_distribution": {0: 145, 1: 160, ..., 6: 55},
  "weekly_series": [{"week": "2025-W26", "count": 18}, ...],
  "repo_breakdown": [{"repo": "owner/repo", "count": 423}, ...]
}
```

## Folder Structure

```
builds/2026-06-26-github-activity-explorer/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── main.py          # CLI entry point
│   ├── fetcher.py       # GitHub API client (pagination, auth)
│   ├── analyzer.py      # Pattern analysis: hourly, weekly, streaks
│   ├── ai_insights.py   # Anthropic API: generate developer profile
│   └── renderer.py      # HTML generation with embedded Chart.js
└── tests/
    ├── test_analyzer.py  # 20 unit tests for all analysis functions
    └── test_renderer.py  # 5 tests verifying HTML output correctness
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_analyzer.py`, `tests/test_renderer.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - `hourly_distribution`: empty list, known timestamps, boundary hours
  - `day_of_week_distribution`: correct weekday mapping
  - `weekly_aggregation`: correct ISO week bucketing, missing weeks filled with 0
  - `compute_streak`: no commits, one commit, consecutive run, run with gap, today vs yesterday
  - `compute_stats`: empty input, known commits produce correct summary values
  - `repo_breakdown`: correct ranking, top-N truncation
  - `renderer.render_dashboard`: HTML contains data JSON, contains Chart.js script tag, contains all four chart canvas IDs, stat card values appear in output

## Success Criteria

1. All 25+ tests pass with zero failures
2. The script runs end-to-end with a real `GITHUB_TOKEN` and fetches at least 1 month of real commit data, producing a valid HTML file
3. The dashboard HTML renders all four charts (hourly, day-of-week, weekly, repos) and four stats cards in a browser without errors
4. The AI insights panel contains a non-empty paragraph describing the user's coding patterns (requires `ANTHROPIC_API_KEY`)
5. The HTML file is self-contained: no external file references beyond CDN-hosted Chart.js — it opens correctly when moved to any folder

---

## Scope Changes

<!-- Leave this section blank. If scope changes during the build,
     add a "Scope Changes" entry here explaining what was dropped and why. -->
