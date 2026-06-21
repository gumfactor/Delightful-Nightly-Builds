# PRD — GitHub Repository Health Scorecard

> **Build date:** 2026-06-21
> **Category:** A — Dashboard / Visualizer
> **Complexity:** ambitious
> **Selected via:** Lottery draw (roll 9 ≤ 27%, pool 3 ideas, ID 5 won)

---

## Goal

Fetch all of the authenticated user's GitHub repositories, compute a composite health score per repo (recency, CI/Actions status, open issues), and produce a self-contained HTML dashboard the user can open in their browser as a morning briefing.

## User Story

As a researcher and indie developer managing 20+ simultaneous GitHub projects, I want to open a single HTML file each morning that shows me exactly which repos have gone stale, which have CI failures, and which need attention — so I can triage my project portfolio in under two minutes without clicking through each repo individually.

## Scope

### In Scope
- Fetch all user repos via authenticated GitHub API (`GITHUB_TOKEN`)
- For each non-archived repo: fetch latest GitHub Actions workflow run status
- Compute composite health score (0–100) from recency + CI status + open issues
- Generate self-contained HTML dashboard with:
  - Summary stats row (counts by health label)
  - AI-generated morning briefing (via Anthropic API, graceful fallback if unavailable)
  - Health distribution doughnut chart (Chart.js 4.4.4 via CDN)
  - Sortable, client-side-filterable repo table
  - Color-coded health badges (Healthy / Good / Fair / Needs Attention / Stale)
  - Dark-mode design, mobile-responsive
- CLI: `python3 src/main.py [--output FILE] [--no-ai]`
- Paginate GitHub API (handles >100 repos)

### Out of Scope
- Contributor count per repo (would require N extra API calls; deferred)
- Commit frequency sparklines (data requires separate commits API calls; deferred)
- Caching or incremental refresh (fresh fetch on each run)
- Deployment or scheduling (run manually as needed)
- Private repo filtering toggle (shows all repos by default)

## Tech Stack

- **Language:** Python 3.8+
- **Framework:** None
- **Dependencies:** stdlib only at runtime (`urllib.request`, `json`, `html`, `argparse`, `pathlib`, `datetime`, `os`) — no pip install required
- **AI integration:** Anthropic Messages API via direct HTTPS (`ANTHROPIC_API_KEY` env var)
- **HTML dependencies:** Chart.js 4.4.4 via CDN (pinned)
- **Testing:** pytest
- **Runtime requirement:** `python3 src/main.py` — outputs a standalone HTML file

## Data Structure

### Repo record (internal dict, embedded as JSON in HTML output)
```json
{
  "name": "repo-name",
  "full_name": "owner/repo-name",
  "language": "Python",
  "health_score": 75,
  "health_label": "Good",
  "health_css": "good",
  "pushed_at": "2026-06-19T10:00:00Z",
  "days_since_push": 2,
  "open_issues": 3,
  "ci_status": "passing",
  "archived": false,
  "private": false,
  "description": "A short description"
}
```

### Health score formula (0–100 total)

| Component     | Max | Scoring rule |
|---------------|-----|-------------|
| Recency       | 30  | ≤1 day: 30 / ≤7 days: 25 / ≤30 days: 15 / ≤90 days: 5 / older: 0 |
| CI status     | 40  | passing: 40 / running: 30 / no-ci: 20 / failing: 10 |
| Open issues   | 30  | 0: 30 / 1–5: 20 / 6–20: 10 / >20: 0 |

### Health label thresholds

| Score | Label |
|-------|-------|
| 80–100 | Healthy |
| 60–79 | Good |
| 40–59 | Fair |
| 20–39 | Needs Attention |
| 0–19 | Stale |

## Folder Structure

```
builds/2026-06-21-github-health-scorecard/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── main.py           # CLI entry point — orchestrates fetch, score, report
│   ├── github_client.py  # GitHub REST API client (paginated repos + CI runs)
│   ├── scorer.py         # Health score computation and labeling
│   ├── report.py         # Self-contained HTML generator
│   └── ai_summary.py     # Anthropic API integration (graceful fallback)
└── tests/
    ├── test_scorer.py         # 19 tests: scoring logic, labels
    ├── test_github_client.py  # 5 tests: response parsing
    ├── test_report.py         # 6 tests: HTML structure and XSS safety
    └── test_ai_summary.py     # 3 tests: insights generation, fallback
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Recency scoring: boundary values (today, 7d, 30d, 90d, 6 months)
  - CI scoring: all four states (passing, failing, running, no-ci)
  - Issues scoring: boundary values (0, 5, 20, 21)
  - Composite score: healthy repo, stale-failing repo
  - Health labels: all five thresholds
  - GitHub client: parsing repo list, filtering archived, parsing CI success/failure/no-runs
  - HTML report: DOCTYPE, Chart.js CDN ref, repo name inclusion, score in output, dark-mode CSS, XSS safety for description field
  - AI summary: returns text with mock, returns empty string without key, returns empty string on API error

## Success Criteria

1. All tests pass (zero failures, minimum 15 tests)
2. `python3 src/main.py --no-ai --output report.html` completes without error and produces a valid HTML file containing the authenticated user's repos
3. The generated HTML file opens in a browser and renders a sortable repo table with correct health labels
4. Repos with CI failures show "failing" status and receive a health score ≤ 50 when issues > 5 and push is > 30 days ago
5. The AI insights panel renders when `ANTHROPIC_API_KEY` is set and is gracefully absent when not set

---

## Scope Changes

<!-- Leave blank; update if scope changes mid-build -->
