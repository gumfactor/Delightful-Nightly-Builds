# Manual — ci-pulse

## What it does

ci-pulse fetches all completed GitHub Actions workflow runs from your repos over the last 30 days and generates a self-contained dark-mode HTML dashboard with:

- 4 stat cards: total runs, failure rate, CI minutes burned, repos with CI
- Horizontal bar chart: top 10 workflows by average duration
- Horizontal bar chart: failure rate per workflow
- Line chart: 30-day trend (weekly avg duration and failure rate)
- Sortable table: all workflows with avg/p95 duration, failure rate, and run counts
- AI Insights panel: 4–5 Claude-generated bottleneck suggestions (requires `ANTHROPIC_API_KEY`)

## Requirements

- Python 3.8+
- `GITHUB_TOKEN` environment variable set (required)
- `ANTHROPIC_API_KEY` environment variable set (optional — enables AI insights)

Install optional dependencies:

```bash
pip install anthropic
```

## Usage

```bash
# Basic — generates ci-pulse-YYYY-MM-DD.html in the current directory
python src/main.py

# With verbose progress output
python src/main.py --verbose

# Custom lookback window (default: 30)
python src/main.py --days 60

# Custom output path
python src/main.py --output /tmp/my-ci-report.html

# Skip AI insights (faster; works without ANTHROPIC_API_KEY)
python src/main.py --no-ai

# Open the report immediately (macOS / Linux)
python src/main.py && open ci-pulse-$(date +%Y-%m-%d).html
python src/main.py && xdg-open ci-pulse-$(date +%Y-%m-%d).html
```

## CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--days N` | `30` | Lookback window in days |
| `--output PATH` | `ci-pulse-YYYY-MM-DD.html` | Output file path |
| `--no-ai` | off | Skip Anthropic API call |
| `--verbose` / `-v` | off | Print per-repo progress |

## What each metric means

| Metric | Meaning |
|--------|---------|
| Avg Duration | Mean wall-clock time for completed runs |
| p95 Duration | 95th-percentile duration — what most runs actually take at worst |
| Failure rate | Proportion of completed runs with conclusion `failure` or `timed_out` |
| CI minutes | Sum of (avg_duration × run_count) / 60 across all workflows |

## Failure rate badge colors

| Color | Failure rate |
|-------|-------------|
| Green | < 5% |
| Amber | 5%–20% |
| Red | > 20% |

## Running tests

```bash
/root/.local/bin/pytest tests/ -v
# or, if pytest is on PATH:
pytest tests/ -v
```

Expected: 50 tests, 0 failures.

## Notes

- Archived repos are excluded automatically.
- Repos with no completed workflow runs in the window are silently skipped.
- Rate-limited repos (403) are skipped with a warning but don't abort the run.
- The tool uses only the run-level timestamps (`run_started_at` / `updated_at`) for duration — no per-job API calls. This keeps API usage to ~2 requests per active repo.
- The generated HTML is self-contained and requires no server. Open it with `file://` in any browser.
