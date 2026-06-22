# Manual — Morning Briefing

## Overview
Morning Briefing is a Python CLI that generates a dated HTML dashboard and markdown summary combining GitHub repository activity, investment portfolio moves, and Toronto weather windows — with an AI-synthesized briefing of what needs attention today.

## Requirements
- Python 3.8+
- `yfinance` (install: `pip install yfinance==1.4.1`)
- Environment variables:
  - `GITHUB_TOKEN` — GitHub personal access token with repo read access
  - `ANTHROPIC_API_KEY` — Anthropic API key for the AI synthesis section
- Both are optional: the tool degrades gracefully when either is absent

## Quick Start

```bash
cd builds/2026-06-22-morning-briefing
pip install yfinance==1.4.1
python src/main.py
# ✓ output/2026-06-22.html
# ✓ output/2026-06-22.md
```

Open `output/YYYY-MM-DD.html` in any browser. No server required — the file is fully self-contained.

## Configuration

Edit `config.json` in the build root:

```json
{
  "watchlist": ["NVDA", "AAPL", "MSFT", "SPY", "BRK-B", "SHOP.TO"],
  "weather_location": {
    "lat": 43.651070,
    "lon": -79.347015,
    "name": "Toronto"
  },
  "stale_days": 7,
  "activity_lookback_hours": 24
}
```

| Key | Description | Default |
|-----|-------------|---------|
| `watchlist` | List of Yahoo Finance ticker symbols | 6 US/CA stocks |
| `weather_location.lat` / `.lon` | Decimal coordinates for weather forecast | Toronto (43.65, -79.35) |
| `stale_days` | Days without a push before a repo is marked stale | 7 |
| `activity_lookback_hours` | Lookback window for "recent push" detection | 24 |

## CLI Arguments

```
python src/main.py [options]

--config PATH       Config file path (default: config.json)
--output-dir DIR    Output directory (default: output/)
--date YYYY-MM-DD   Override report date (default: today UTC)
--no-ai             Skip Anthropic AI synthesis
--stdout            Print markdown to stdout instead of writing files
```

## Output Files

| File | Description |
|------|-------------|
| `output/YYYY-MM-DD.html` | Self-contained dark-mode HTML dashboard with Chart.js portfolio bar chart |
| `output/YYYY-MM-DD.md` | Markdown briefing suitable for pasting into notes or a Coda doc |

## Sections

**Today's Priorities (AI)** — Claude Haiku synthesizes the other three sections into 4–5 actionable bullet points. Skipped gracefully when `ANTHROPIC_API_KEY` is absent.

**GitHub Activity** — repositories with pushes in the last 24h, repositories that haven't been touched in 7+ days (stale), and open PRs across active repos. Requires `GITHUB_TOKEN`.

**Portfolio Pulse** — today's price change for each ticker in the watchlist, classified as up/down/flat (±1% threshold), with a Chart.js bar chart. Requires yfinance network access.

**Weather Windows** — hourly running, golf, and boating comfort scores for today using Open-Meteo's free forecast API. Filters to daylight hours (6am–9pm). No auth required.

## Activity Scoring

| Score | Rating |
|-------|--------|
| 80–100 | Excellent |
| 60–79 | Good |
| 40–59 | Moderate |
| 0–39 | Poor |

**Running**: optimized for 10–20°C, low wind (<15 kph), no precipitation.
**Golf**: optimized for 15–25°C, very low wind (<12 kph), dry conditions.
**Boating**: optimized for 20–28°C, moderate wind (5–20 kph), minimal rain.

## Running as a Claude Code Routine

To schedule this as a daily morning briefing that runs automatically, create a file at `.claude/routines/morning-briefing.md` in your repo:

```markdown
---
schedule: "0 11 * * 1-5"   # 7am ET Mon–Fri (11:00 UTC)
description: Generate daily morning briefing
---

Run the morning briefing and send the summary as a push notification:

1. `cd builds/2026-06-22-morning-briefing && python src/main.py --stdout`
2. Extract the "Today's Priorities" section from the output
3. Send as a push notification summarizing what needs attention today
```

The Routine runs `python src/main.py`, generates the HTML and markdown, and can push a notification summary via the `PushNotification` tool.

## Running Tests

```bash
cd builds/2026-06-22-morning-briefing
pytest tests/ -v
# 109 passed, 0 failed
```

All tests mock external APIs — no network required for the test suite.
