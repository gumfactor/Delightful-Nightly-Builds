# Manual — Secret Sweep

> **Version:** 1.0 (built 2026-08-21)
> **Complexity:** Ambitious

---

## What This Is

Secret Sweep scans your own local git repositories — both the current working tree and the
full commit history — for accidentally committed secrets and credentials: API keys, tokens,
private keys, and passwords. It's the automated version of the "no hardcoded credentials"
check every nightly build in this repo already does by hand, applied to any repo you point it
at. It never modifies the repos it scans, and it never stores or transmits the raw secret
values it finds — every report is redacted by construction.

---

## Quick Start

1. `cd` into this build folder (`builds/2026-08-21-secret-sweep/`).
2. `python3 secretsweep.py scan /path/to/your/repo` — fast, working-tree-only check.
3. `python3 secretsweep.py history /path/to/your/repo` — slower, full-history audit (does
   everything `scan` does, plus every past commit).
4. `python3 secretsweep.py report --format html --output report.html` — build a browsable
   dashboard from everything found so far, across every repo you've scanned.
5. Open `report.html` in a browser.

No install step beyond a Python 3.11+ interpreter and `git` on your `PATH`. No dependencies
to install for normal use (pytest is only needed to run the test suite).

---

## How to Use It

### `scan` — working-tree check (fast)

```bash
python3 secretsweep.py scan [repo ...] [--ai-review]
```

Scans the current tracked + untracked-but-not-ignored files of one or more repos (defaults to
the current directory if none given). Every finding is `critical` severity, since it's live in
the working tree right now. Add `--ai-review` to get a Claude Haiku second opinion on each
finding (requires `ANTHROPIC_API_KEY` in your environment; falls back to the deterministic
classification with zero network calls if it's not set).

### `history` — full commit-history audit (slower)

```bash
python3 secretsweep.py history [repo ...] [--ai-review] [--max-commits N]
```

Walks every commit on the current branch via `git log -p` and flags any line that ever
introduced something secret-shaped — even if it was later deleted. A finding is `critical` if
the exact value is still present at `HEAD`, or `high` if it only exists in a past commit
(removed from HEAD, but permanently present in any clone that already pulled it). Use
`--max-commits` to cap the walk on a very large repo.

### `list` — quick terminal view of what's already been found

```bash
python3 secretsweep.py list [--repo PATH ...] [--severity critical|high|all] [--status new|acknowledged|all]
```

Prints stored findings without regenerating a file — the fastest way to check "anything new?"

### `report` — JSON or HTML output

```bash
python3 secretsweep.py report [--repo PATH ...] --format json|html [--output PATH]
```

Renders everything currently stored (optionally filtered to specific repos) as a JSON export
or a self-contained dark-mode HTML dashboard with search/filter and one-click-copy remediation
snippets. Omit `--output` to print to stdout (useful for `--format json` piped elsewhere).

### `ack` — acknowledge a confirmed false positive

```bash
python3 secretsweep.py ack FINDING_ID
```

Marks a finding `acknowledged` so it stops counting as "new" on future scans, without deleting
it from the audit trail — it still shows up in the full report, just visually de-emphasized.

### Claude Code Skill

`skill/SKILL.md` wraps the fast `scan` path for use mid-coding-session (e.g. "scan this repo
for secrets before I commit"). Copy it into `.claude/skills/secret-scan/` in any repo where you
want that available on demand. It deliberately does not run `history` automatically — that's a
slower, occasional-audit action, not a per-commit check.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `~/.secretsweep/findings.db` | SQLite database path — override to keep separate findings per project, or point at a shared location |
| `--api-key` | `$ANTHROPIC_API_KEY` | Anthropic API key for `--ai-review`; omit both to always use the deterministic fallback |
| `--max-commits` (history only) | unlimited | Cap the number of commits walked, for very large repos |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `warning: '...' is not a git repository — skipping` | The path isn't a git repo, or `git` isn't on `PATH` | Confirm the path and that `git --version` works |
| `history` takes a long time | Very large repo with a long commit history | Re-run with `--max-commits 500` (or similar) to cap the walk |
| No findings on a repo you know has a leaked key | The value is in a binary file, exceeds the 2MB per-file size cap, or doesn't match any of the 12+ named patterns or the generic entropy heuristic | Check `src/patterns.py` — patterns are easy to extend; open an issue-style note for a new format |
| `--ai-review` output always says "No AI review available" | `ANTHROPIC_API_KEY` isn't set (or wasn't passed via `--api-key`) | This is the correct, safe fallback behavior, not a bug — set the environment variable to enable it |

---

## Known Limitations

- Text files only — binary files (compiled artifacts, images) are never scanned, since secrets
  are practically always committed as text.
- Detection is pattern + entropy based, not a live validity check against each provider's API —
  a `critical` finding means "this looks like a real credential," not "this credential is
  confirmed still active." Always verify and rotate rather than assuming a finding is stale.
- `history` walks `--no-merges` commits only, to avoid double-counting the same change through
  a merge commit's combined diff.
- The generic high-entropy detector can still false-positive on genuinely random-looking
  non-secret strings (UUIDs, hashes used as public identifiers) that happen to be assigned to a
  variable name containing "key" or "id"-adjacent words — use `--ai-review` or `ack` to manage
  the noise on a specific repo.
