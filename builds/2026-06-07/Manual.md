# Manual — Git Standup Reporter

> **Version:** 1.0 (built 2026-06-07)
> **Complexity:** Focused Utility

---

## What This Is

Git Standup Reporter is a Python CLI that reads your git commit history and prints a clean standup-ready summary of what you worked on. Run it from any project directory (or point it at multiple repos) and it tells you exactly what was committed in the last N hours — grouped by repository, author-filtered, and formatted as either plain text or markdown.

It solves the problem of re-establishing context across sessions and writing standups when you're managing several concurrent projects. Unlike tools that require you to log entries manually, this one reads state that already exists: your git history.

---

## Quick Start

1. Navigate to any git repository (or stay anywhere and specify a path):
   ```bash
   cd ~/my-project
   python3 /path/to/builds/2026-06-07/main.py .
   ```

2. See what was committed in the last 24 hours by the current git user. That's it.

3. To scan multiple repos at once:
   ```bash
   python3 main.py ~/project-a ~/project-b ~/the-canada-list
   ```

---

## How to Use It

### Basic Usage

```bash
# Current directory, last 24 hours, current git user
python3 main.py .

# Specific repo path
python3 main.py /path/to/repo

# Multiple repos
python3 main.py /path/to/repo-a /path/to/repo-b

# Last 8 hours only
python3 main.py . --hours 8

# Last 7 days
python3 main.py . --hours 168
```

### Author Filtering

By default, standup reporter auto-detects your author name from `git config user.name` in the first valid repo path. You can override or disable this:

```bash
# Filter to a specific author
python3 main.py . --author "Shane"

# Show commits from all authors (team standup mode)
python3 main.py . --all-authors
```

### Output Formats

```bash
# Plain text (default) — clean, readable in terminal
python3 main.py .

# Markdown — suitable for pasting into Coda, Notion, or a PR description
python3 main.py . --format markdown
```

**Text output example:**
```
Standup — last 24 hours
========================================

[my-project]
  • Add login page  (abc12345)
  • Fix typo in README  (def67890)
```

**Markdown output example:**
```markdown
## Standup — last 24 hours

### my-project

- Add login page  `abc12345`
- Fix typo in README  `def67890`
```

### Graceful Failure

If a path is not a git repository, or has no commits in the window, it is silently treated as empty. If no repos have any commits, the output is:

```
Nothing committed in the last 24 hours.
```

No errors, no tracebacks.

---

## Configuration

No configuration files. All options are flags.

| Flag | Default | Description |
|------|---------|-------------|
| `paths` (positional) | `.` | One or more git repo paths to scan |
| `--hours N` | `24` | How many hours back to look |
| `--author NAME` | auto-detected | Filter commits by author name substring |
| `--all-authors` | off | Include commits from all authors |
| `--format text\|markdown` | `text` | Output format |

---

## Running the Tests

```bash
python3 -m pytest /path/to/builds/2026-06-07/tests/ -v
```

Expected output: **18 passed, 0 failed**

Tests cover:
- `test_standup.py` — formatter logic with mock commit data (8 tests, no git calls)
- `test_git_log.py` — real temp repo fixture; commit reading, author filtering, error handling (10 tests)

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Nothing committed in the last 24 hours` but you know you committed | Author filter mismatch | Run with `--all-authors` to bypass author filtering |
| Output shows someone else's commits | `git config user.name` is set to a shared name | Use `--author "Your Name"` explicitly |
| `fatal: not a git repository` is not shown but path seems wrong | Error is silently swallowed; path returns empty | Check that the path is a valid git repo with `git -C /path status` |
| Tests fail in CI with signing errors | Environment has global commit signing enabled | The fixture sets `commit.gpgsign = false` locally — ensure git 2.x is installed |

---

## Known Limitations

- If two different repos have the same top-level directory name, their commits will be merged under one name in the output dict. Use distinct repo names to avoid this.
- `--hours 0` is accepted and produces "Nothing committed in the last 0 hours." rather than an error. It is a valid edge case, not a useful input.
- The author auto-detection reads only the first valid path in the list. If repos have different configured authors, use `--author` explicitly.
