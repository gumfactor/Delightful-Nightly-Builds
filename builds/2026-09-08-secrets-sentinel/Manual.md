# Manual — Secrets Sentinel

A local CLI that walks the full git commit history of your own repositories looking for credentials that were ever committed — including ones already deleted from the current tree but still recoverable from history.

## Requirements
- Python 3.10+ (stdlib only for the core engine)
- `git` on your `PATH`
- Optional: `anthropic` package + `ANTHROPIC_API_KEY` environment variable, for the AI triage pass that reduces false positives on ambiguous findings

## Install
```bash
cd builds/2026-09-08-secrets-sentinel
pip install -r requirements.txt   # only needed if you want the AI triage pass
```

## Run it
Scan one repo:
```bash
python -m src.main /path/to/your/repo
```

Scan every repo under a directory (auto-discovers `.git` folders, skips `node_modules`/`.venv`/etc.):
```bash
python -m src.main ~/code
```

Scan several repos at once:
```bash
python -m src.main ~/code/canada-list ~/code/kwyeter ~/code/lab-tools
```

## Options
| Flag | Effect |
|------|--------|
| `--current-branch-only` | Scan only the checked-out branch instead of every local branch (`git log --all` is the default) |
| `--max-commits N` | Cap how many commits are scanned per repo — useful for a first pass on a very large/old repo |
| `--no-ai` | Skip the AI triage pass even if `ANTHROPIC_API_KEY` is set |
| `--html-out report.html` | Write a self-contained dark-mode HTML report |
| `--json-out report.json` | Write findings as JSON (for scripting or diffing runs over time) |
| `--fail-on-high` | Exit with status 1 if any high-confidence finding exists — for wiring into a pre-push hook or CI gate |

## Reading the output
Every finding gets a **tier**:
- **high** — matched a named vendor pattern (AWS key, GitHub token, Slack token, Stripe key, Google/Firebase key, a PEM private key block, a JWT). Unambiguous — these skip AI triage entirely.
- **medium** — a long random-looking string sitting next to a secret-sounding variable name (`api_key`, `token`, `secret`, `password`, `credential`).
- **low** — a long random-looking string with no other signal. Often a hash, UUID, or test fixture — this is where the AI triage pass earns its keep.

Every finding also shows whether the secret is **still in HEAD** or **history only**. History-only findings are easy to miss — the file looks clean today — but the secret is still sitting in every clone of the repo's `.git` folder until it's rotated and the history itself is rewritten (e.g. with `git filter-repo`). Deleting the line from the current file is not enough.

## AI triage
If `ANTHROPIC_API_KEY` is set and `--no-ai` isn't passed, every medium/low finding gets one extra classification call to Claude Haiku: `likely_real_secret`, `likely_test_fixture_or_hash`, or `uncertain`. **The actual secret value is never sent** — only a redacted context window (the pattern name and the surrounding line with the secret replaced by a `[REDACTED:Nchars]` placeholder). High-tier findings never go through AI triage; a named vendor pattern match needs no second opinion. With no API key, medium/low findings are tagged `unreviewed` and the deterministic tier stands as-is.

## Run the tests
```bash
cd builds/2026-09-08-secrets-sentinel
python -m pytest tests/ -v
```

## What this tool does not do
It reports; it does not act. Rotating a leaked credential and rewriting git history to purge it are always manual steps you take afterward — this tool is not going to force-push your repository for you.
