# Manual — Project Pulse

## Overview

Project Pulse is a command-line context manager for people who juggle many simultaneous projects. Define your projects once, let it track GitHub activity automatically, and get AI-generated context briefs when you switch between projects.

## Prerequisites

- Python 3.8+
- `GITHUB_TOKEN` env var (for GitHub commit sync)
- `ANTHROPIC_API_KEY` env var (for AI context briefs; optional — falls back to text summary)

## Quick Start

```bash
# Add your active projects
python src/main.py add "Canada List" --desc "Canadian business directory" --type business --repos owner/canada-list

python src/main.py add "Neuroscience Lab" --desc "Forensic and affective neuroscience" --type lab

python src/main.py add "Kwyeter" --desc "Environmental noise awareness platform" --type code --repos owner/kwyeter-app

# Pull GitHub commits for all code projects
python src/main.py sync

# Get an AI context brief when switching to a project
python src/main.py brief canada-list

# Generate an HTML dashboard showing all project activity
python src/main.py dashboard
open dashboard.html
```

## Commands

### `add` — Register a project

```
python src/main.py add NAME [--desc TEXT] [--type TYPE] [--repos OWNER/REPO ...]
```

| Argument | Description |
|----------|-------------|
| `NAME` | Project display name (must be unique) |
| `--desc` | Short description (shown in dashboard) |
| `--type` | `lab`, `code`, `writing`, `business`, or `personal` |
| `--repos` | Space-separated list of GitHub repos to track |

The slug (URL-safe name) is derived automatically: `"Canada List"` → `canada-list`.

### `list` — Show all projects

```
python src/main.py list [--status STATUS]
```

Status options: `active` (default), `paused`, `archived`, `all`.

### `log` — Record a manual activity note

```
python src/main.py log SLUG "Note text"
```

Use this for non-code activity: submitted ethics application, reviewed submissions, attended meeting, finished writing section.

Duplicate notes are silently skipped (idempotent).

### `sync` — Pull GitHub commits

```
python src/main.py sync [SLUG]
```

Fetches commits from the last 30 days for all configured GitHub repos. Omit `SLUG` to sync all active projects. Requires `GITHUB_TOKEN`.

New commits are stored in the local database. Re-running sync is safe — duplicates are skipped.

### `brief` — Generate a context brief

```
python src/main.py brief SLUG
```

Prints a 3-5 sentence summary of recent activity and next steps. Uses the Anthropic API when `ANTHROPIC_API_KEY` is set; falls back to a text summary otherwise.

### `dashboard` — Generate HTML dashboard

```
python src/main.py dashboard [--output PATH]
```

Produces a self-contained dark-mode HTML file (default: `dashboard.html` in the build root). Open in any browser — no server required.

The dashboard shows:
- **Activity timeline** — 30-day stacked bar chart per project
- **Project cards** — staleness badge, activity count, recent activity list
- **Type filter** — narrow to Lab / Code / Writing / Business / Personal

## Staleness Badges

| Badge | Meaning |
|-------|---------|
| 🟢 Green (0-2d) | Active — touched in the last 2 days |
| 🟡 Yellow (3-7d) | Quiet — no activity this week |
| 🟠 Orange (8-14d) | Cooling — more than a week idle |
| 🔴 Red (15d+) | Stale — consider checking in |
| ⬜ Grey | No activity logged yet |

## Database

Projects and activity are stored in `data/projects.db` (SQLite). The `data/` folder is created automatically. Back up this file to preserve your history.

Default path: `builds/2026-06-29-project-pulse/data/projects.db`

Use `--db PATH` on any command to point to a custom database location.

## Running Tests

```bash
pytest tests/ -v
```

66 tests, all must pass.

## Packaging as a Claude Code Skill

Add to `.claude/skills/project-brief.md`:
```
---
name: project-brief
description: Get a context brief for a project before switching to it
---
Run: python /path/to/builds/2026-06-29-project-pulse/src/main.py brief $ARGS
```

Then invoke with `/project-brief canada-list` in any Claude Code session.
