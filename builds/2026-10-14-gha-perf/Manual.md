# gha-perf Manual

Analyses GitHub Actions runs across your repos and writes one self-contained HTML report (phone-readable, dark/light).

## Run

```bash
export GITHUB_TOKEN=ghp_...        # classic PAT with `repo`, or fine-grained with Actions: read
python main.py --days 30 -o report.html --json report.json
python main.py --repos me/canada-list,me/kwyeter --days 14
ANTHROPIC_API_KEY=... python main.py --ai       # adds a short Claude briefing
```

No install is needed (stdlib only). Open `report.html` in a browser; charts load Chart.js 4.4.4 from jsDelivr.

## Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--repos a/b,c/d` | all your non-fork, non-archived repos | limit scope |
| `--days N` | 30 | look-back window |
| `--max-runs N` | 300 | max runs per repo |
| `--jobs-per-workflow N` | 15 | runs per workflow to fetch job and step detail for (controls API calls) |
| `--include-forks` | off | include forks |
| `--ai` | off | Claude briefing; only aggregate metrics are sent |
| `-o`, `--json` | `gha-perf-report.html` | outputs |

## Reading the report

- **Billable min** is an estimate: job minutes rounded up per job, times 1 (Linux), 2 (Windows), 10 (macOS). Runs without job detail use their workflow's sampled average.
- **Wasted min** is billable time in failed, cancelled or timed-out runs.
- **Flaky** means the same commit failed and later passed, or passed only on a re-run attempt.
- **Findings** are rule-based (failure rate ≥30%, cancel rate ≥25%, p95 ≥3x p50, slow install steps, Windows/macOS spend).
- Click a table header to sort.

## Cost of a run

Roughly 1 call per 100 repos listed, 1+ per repo for runs, and up to `--jobs-per-workflow` calls per workflow. If the rate limit is hit, the report is produced from what was collected and the problem is listed on the page.

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```
