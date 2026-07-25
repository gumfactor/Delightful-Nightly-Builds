# Manual — BugTrace

> **Version:** 1.0 (built 2026-07-25)
> **Complexity:** Ambitious Project

---

## What This Is

BugTrace mines your own git commit history — one repo, several repos, or everything you own on GitHub — for bug-fix commits, and classifies each one into a root-cause category (null handling, off-by-one, race condition, type mismatch, missing error handling, and eight others) using deterministic keyword rules, with an optional Claude Haiku second opinion. Every classified fix accumulates in a local SQLite database, so over weeks and months you get an evidence-based answer to "what kind of mistakes do I actually make most often" — not a guess, and not something any linter or GitHub analytics view currently shows you.

---

## Quick Start

1. `cd builds/2026-07-25-bugtrace`
2. Point it at any local git repo, no credentials needed:
   `python3 main.py sync --repo-path /path/to/your/repo`
3. Generate the dashboard:
   `python3 main.py report --format html --out report.html`
4. Open `report.html` in a browser.
5. Re-run `sync` any time — already-classified commits are never re-processed or double-counted, so it's safe to run daily/weekly as a cron job or Routine.

---

## How to Use It

### `sync` — fetch and classify new fix commits

```
python3 main.py sync --repo-path /path/to/repo1,/path/to/repo2
python3 main.py sync --repos yourname/repo1,yourname/repo2 --db bugtrace.db
python3 main.py sync --all --since-months 6 --ai
```

- `--repo-path` — one or more comma-separated local git repos. No token required; uses `git log`/`git show` directly.
- `--repos` — one or more comma-separated `owner/repo` GitHub targets. Requires `GITHUB_TOKEN` in the environment.
- `--all` — fetch every repo you own via the GitHub API (requires `GITHUB_TOKEN`).
- `--since-months N` — only consider commits from the last N months (default 12).
- `--limit-per-repo N` — cap how many commits are scanned per repo (default 500).
- `--ai` — send new fix commits (message + redacted diff excerpt) to Claude Haiku for classification instead of relying purely on keyword rules. Requires `ANTHROPIC_API_KEY` in the environment. Any failure (no key, network error, malformed response) silently falls back to the keyword classifier for the affected commit — the tool never breaks because the AI call failed.
- `--ai-limit N` — cap how many new commits per run are sent to the AI (default 40), to bound API cost.
- `--db PATH` — SQLite database file (default `bugtrace.db` in the current directory).

A commit is only ever fetched and classified once — a second `sync` run over the same repo reports "0 new fix commits" and does not re-touch existing rows.

### `report` — render the accumulated data

```
python3 main.py report --format text
python3 main.py report --format json --out report.json
python3 main.py report --format html --out report.html --ai
```

- `--format text` — terminal summary, category breakdown with percentages, per-repo counts.
- `--format json` — structured export (`counts`, `monthly`, `repos`, `fixes`) to a file (`--out path`) or stdout (`--out -`).
- `--format html` — a self-contained dark-mode dashboard: a category-frequency bar chart, a monthly trend line, a searchable/filterable list of every fix commit grouped by category and linked to GitHub, and a coaching paragraph on your top recurring pattern. Works fully offline (degrades to a plain table if the Chart.js CDN is unreachable). Pass `--ai` to have Claude Haiku write the coaching paragraph instead of the deterministic template (requires `ANTHROPIC_API_KEY`).

### `show <category>` — list the raw commits behind one category

```
python3 main.py show null_none_handling
```

Valid categories: `test_only_fix`, `config_env_credentials`, `dependency_version`, `async_race_condition`, `off_by_one_index`, `null_none_handling`, `type_mismatch`, `logic_operator_error`, `error_handling_missing`, `api_integration_misuse`, `typo_naming`, `other`.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `GITHUB_TOKEN` (env var) | none | Required only for `--repos`/`--all`; not needed for `--repo-path`. |
| `ANTHROPIC_API_KEY` (env var) | none | Required only for `--ai`; the tool is fully functional without it. |
| `--db` | `bugtrace.db` | SQLite database path; safe to keep one shared file across every project you sync. |
| `--since-months` | `12` | Lookback window for `sync` (GitHub path uses this as an ISO timestamp filter; local path passes it to `git log --since`). |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Skipping owner/repo: GITHUB_TOKEN not set.` | You passed `--repos`/`--all` without a token in the environment | `export GITHUB_TOKEN=...` or use `--repo-path` instead for local-only repos |
| `report` shows "No fix commits recorded yet" | You ran `report` before `sync`, or `sync` found zero fix-like commits in the window | Run `sync` first; widen `--since-months` or check that your commit messages actually contain fix-shaped language (fix/bug/patch/resolve/crash/etc.) |
| Charts don't render in the HTML report | The Chart.js CDN is unreachable from your network | This is expected and handled: the report automatically falls back to a plain data table with identical numbers — no data is lost |
| `Not a git repository (no .git found)` | `--repo-path` points at a directory without a `.git` folder | Point it at the repo root, not a subdirectory |

---

## Known Limitations

- Keyword classification is heuristic — ambiguous commit messages can land in a less-than-perfect category. Use `--ai` for a more nuanced (though still imperfect) read.
- The 12-category taxonomy is fixed and not currently user-customizable per project.
- Diff excerpts sent for classification are truncated to 4000 characters, so extremely large fix commits lose some context.
- Local-repo `--since-months` and GitHub-repo `--since-months` use slightly different underlying mechanisms (`git log --since` vs. an ISO timestamp API filter) and may not produce byte-identical windows at the edges.
