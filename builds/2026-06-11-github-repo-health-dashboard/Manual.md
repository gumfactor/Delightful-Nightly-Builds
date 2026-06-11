# Manual — GitHub Repository Health Dashboard

## What This Is

A Python CLI that fetches your GitHub repositories and displays a health dashboard in the terminal. Runs in seconds; no browser needed. Tells you at a glance which repos are active, which have accumulated open issues, and which have quietly gone stale.

## Requirements

- Python 3.10 or later
- `GITHUB_TOKEN` environment variable set to a GitHub Personal Access Token with `repo` scope (or a fine-grained token with repository read access)
- In GitHub Actions, `GITHUB_TOKEN` is provided automatically

## Setup

```bash
# Set your token (once, or add to your shell profile)
export GITHUB_TOKEN=ghp_yourtoken

# Install test dependency (for running tests only)
pip install pytest
```

## Usage

```bash
# From the build folder
python3 main.py
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | 30 | Maximum repos to display |
| `--include-archived` | off | Show archived repos (hidden by default) |
| `--format json` | table | Output JSON instead of a table |
| `--org ORG` | (none) | Show repos for a GitHub organisation |

### Examples

```bash
# Your top 30 repos by most recent push
python3 main.py

# Fewer repos, focused view
python3 main.py --limit 10

# Include archived repos
python3 main.py --include-archived

# JSON output — pipe to jq, save to file, or feed a script
python3 main.py --format json | jq '.[] | select(.health == "stale")'

# Organisation repos
python3 main.py --org my-github-org --limit 50

# Combine flags
python3 main.py --limit 20 --include-archived --format json
```

## Output Format

### Table (default)

```
Repository                                    Language        ★  Issues   Days  Health
────────────────────────────────────────────────────────────────────────────────────────
gumfactor/delightful-nightly-builds           Python          3       2      2  ● active
gumfactor/canada-list                         JavaScript     12       8     20  ● active
gumfactor/kwyeter                             Dart            1       0     45  ◐ quiet
gumfactor/old-experiment                      Python          0       3    200  ○ stale
gumfactor/archived-thing                      —               0       0    400  ▪ archived

Health: ● active (<30d)  ◐ quiet (30–90d)  ○ stale (>90d)  ▪ archived
Note: Issues column includes open PRs (GitHub conflates issues and PRs in this count).
```

### Health Statuses

| Symbol | Label | Meaning |
|--------|-------|---------|
| ● | active | Pushed within the last 30 days |
| ◐ | quiet | Pushed 30–90 days ago |
| ○ | stale | Not pushed in over 90 days |
| ▪ | archived | Repository is archived on GitHub |

### Issues Column Note

GitHub's API returns `open_issues_count`, which includes **both open issues and open pull requests**. The Issues column reflects this combined count. A repo showing "3 issues" may have 1 issue and 2 open PRs, or 3 issues and 0 PRs. A future enhancement could break these into separate columns using per-repo PR API calls.

### JSON Output

```json
[
  {
    "name": "delightful-nightly-builds",
    "full_name": "gumfactor/delightful-nightly-builds",
    "language": "Python",
    "stars": 3,
    "open_issues": 2,
    "days_since_push": 2,
    "health": "active",
    "archived": false,
    "private": false,
    "url": "https://github.com/gumfactor/delightful-nightly-builds"
  }
]
```

## Running Tests

```bash
# From the build folder
python -m pytest tests/ -v
```

Expected output: 35 tests, 0 failures. Tests cover all logic functions — parsing, staleness calculation, health scoring, filtering, and both output formats. No network access is required; tests use fixed data and a fixed timestamp.

## Error Messages

| Error | Cause | Fix |
|-------|-------|-----|
| `GITHUB_TOKEN environment variable is not set.` | Token missing | `export GITHUB_TOKEN=ghp_...` |
| `GitHub API error 401:` | Token invalid or expired | Regenerate token at github.com/settings/tokens |
| `GitHub API error 404:` | Organisation not found | Check `--org` spelling; confirm access |
| `Network error:` | No internet / DNS failure | Check network connectivity |
