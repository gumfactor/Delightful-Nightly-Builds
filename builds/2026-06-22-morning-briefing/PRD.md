# PRD — Morning Briefing

> **Build date:** 2026-06-22
> **Category:** B — Productivity Utility
> **Complexity:** ambitious

---

## Goal

Generate a unified daily digest combining GitHub repository activity, investment portfolio moves, and Toronto weather windows — AI-synthesized into a morning briefing — that runs as a Claude Code Routine and outputs a self-contained HTML dashboard plus dated markdown file.

## User Story

As a researcher and founder managing 20+ active GitHub repositories and a personal investment watchlist, I want to open a single morning report that tells me what happened in my repos yesterday, how my watchlist moved overnight, and whether conditions support a run or round of golf today — so I can orient in under 2 minutes without clicking through six separate tools.

## Scope

### In scope
- **GitHub activity section**: repos with recent pushes (last 24h), stale repos (7+ days quiet), open PRs across active repos
- **Portfolio pulse section**: yfinance price data for a configurable watchlist with day change %, mover classification, and a Chart.js bar chart
- **Weather windows section**: Open-Meteo hourly forecast for Toronto, scored per hour for running, golf, and boating comfort; best 3 windows per activity shown
- **AI synthesis section**: Claude Haiku 4-point summary of what needs attention today (graceful fallback to empty if key absent or API fails)
- **Output**: console confirmation + dated `.md` in `output/` + self-contained `.html` in `output/`
- **Config**: `config.json` in build root with watchlist tickers, location coordinates, and stale threshold
- **Routine-ready**: documented in `Manual.md` with the exact Claude Code Routine definition to enable daily scheduled runs

### Out of scope
- Push notifications (Routine context handles delivery)
- Historical trend charts (future feature)
- Commit-level detail per repo
- Any auth-required API not confirmed in PROFILE.md

## Tech Stack
- Python 3.8+
- `yfinance` — real stock data, no auth required
- `pytest` — test framework
- Stdlib: `urllib.request`, `json`, `html`, `argparse`, `pathlib`, `datetime`, `os`, `sys`
- HTML output: Chart.js 4.4.4 via CDN (pinned)

## Data Sources
- **GitHub REST API** — authenticated via `GITHUB_TOKEN` env var; endpoints: `/user/repos`, `/repos/{owner}/{repo}/pulls`
- **Yahoo Finance** — via `yfinance 1.4.1`; daily price data (current + previous close); no auth required
- **Open-Meteo** — `api.open-meteo.com/v1/forecast`; hourly apparent temperature, wind speed, precipitation probability; no auth required
- **Anthropic Messages API** — `claude-haiku-4-5-20251001` via `ANTHROPIC_API_KEY` env var; graceful degradation when key absent

## Data Structure

### config.json
```json
{
  "watchlist": ["NVDA", "AAPL", "MSFT", "SPY", "BRK-B", "SHOP.TO"],
  "weather_location": {"lat": 43.651070, "lon": -79.347015, "name": "Toronto"},
  "stale_days": 7,
  "activity_lookback_hours": 24
}
```

### Output files
```
output/
  2026-06-22.md    — dated markdown summary
  2026-06-22.html  — self-contained HTML dashboard (opens in any browser)
```

## Folder Structure
```
builds/2026-06-22-morning-briefing/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── config.json
├── src/
│   ├── __init__.py
│   ├── main.py              ← entry point; run as: python src/main.py
│   ├── github_fetcher.py    ← GitHub API client + data transformation
│   ├── market_fetcher.py    ← yfinance wrapper + price change logic
│   ├── weather_fetcher.py   ← Open-Meteo client + hourly scoring
│   ├── ai_synthesizer.py    ← Anthropic API integration + prompt builder
│   └── report.py            ← markdown + HTML renderer
├── tests/
│   ├── __init__.py
│   ├── test_github_fetcher.py
│   ├── test_market_fetcher.py
│   ├── test_weather_fetcher.py
│   ├── test_ai_synthesizer.py
│   └── test_report.py
└── output/                  ← generated at runtime; gitignored
```

## Testing Strategy
All external APIs mocked via `unittest.mock.patch`. No network calls in tests.

- **github_fetcher tests**: repo health classification (active/recent/stale), date-based filtering, archived repo exclusion, error handling when token missing or API fails
- **market_fetcher tests**: `calculate_change_pct` accuracy, `classify_move` thresholds, `format_price` formatting, `fetch_ticker_data` with mocked yfinance responses including error path
- **weather_fetcher tests**: `score_hour` returns expected scores for ideal/extreme/rainy conditions, non-negativity guarantee, `get_best_windows` returns top N sorted, filters nighttime hours, `parse_forecast_response` filters by date and handles None values
- **ai_synthesizer tests**: `format_prompt` includes all three sections, `synthesize` returns empty string on missing API key and on API error
- **report tests**: HTML structure (DOCTYPE, Chart.js CDN), AI section present/absent logic, XSS escaping in repo names and chart data, all section headings present, markdown output structure

## Success Criteria
1. Running `python src/main.py` from the build folder produces `output/YYYY-MM-DD.md` and `output/YYYY-MM-DD.html` containing all four sections (GitHub, portfolio, weather, AI brief)
2. The HTML dashboard renders all sections in a browser with correct Chart.js bar chart for portfolio changes and no console errors
3. The tool degrades gracefully when any single data source is unavailable — other sections still render rather than the whole script crashing
4. All 50+ tests pass with zero failures; every test corresponds to a real failure mode in the production data path
5. Portfolio section shows real live price data (not mock/hardcoded) when run with network access — verified by comparing output to known market prices
