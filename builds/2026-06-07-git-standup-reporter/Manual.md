# Manual — Git Standup Reporter

> **Version:** 2.0 (extended 2026-06-08)
> **Complexity:** Focused Utility (original) + Solid Feature extension

---

## What This Is

Git Standup Reporter is a Python script that runs daily and produces a morning digest of everything you committed in the last 24 hours — across all your GitHub repos and any uncommitted local work in `C:\Dev`. It runs automatically via Windows Task Scheduler and appends output to a markdown file you open each morning.

It covers two sources:
- **GitHub API** — all commits pushed to any of your repos, from any machine or agent
- **Local git scan** — commits in your local `C:\Dev` repos that haven't been pushed yet

Commits that exist in both (pushed local commits) are deduplicated by SHA so they appear only once.

---

## Setup (One-Time)

See `SETUP_WINDOWS.md` for the full setup walkthrough. Summary:

1. **Create a GitHub token** at github.com → Settings → Developer Settings → Personal Access Tokens (Classic) with `repo` scope
2. **Set the environment variable** permanently in PowerShell:
   ```powershell
   [System.Environment]::SetEnvironmentVariable("GITHUB_TOKEN", "your-token-here", "User")
   ```
3. **Configure `standup.toml`** — copy `standup.toml.example` to `standup.toml` and fill in your values:
   ```toml
   [standup]
   github_username = "gumfactor"
   hours = 24
   format = "markdown"
   journal_path = "C:/Users/100505118/OneDrive/Dev/Dev-management/Git-Standup/standup_journal.jsonl"
   local_roots = ["C:/Dev"]
   exclude_repos = []
   ```
4. **Schedule the task** via Windows Task Scheduler (see `SETUP_WINDOWS.md`)

---

## Running Manually

```powershell
cd C:\Users\100505118\Dev\Delightful-nightly-builds\builds\2026-06-07
python main.py
```

Prints the standup report to the terminal and appends a JSON entry to the journal file.

---

## Output Format

### Text (format = "text")

```
Standup — last 24 hours
========================================

[my-project]
  • Add login page  (abc12345)
  • Fix bug in parser  (def67890) (local)

[canada-list]
  • Update CSV validator  (aaa11111)
```

### Markdown (format = "markdown")

```markdown
## Standup — last 24 hours

### my-project

- Add login page  `abc12345`
- Fix bug in parser  `def67890` *(local)*

### canada-list

- Update CSV validator  `aaa11111`
```

Commits tagged `(local)` or `*(local)*` are unpushed — they exist in your local `C:\Dev` repos but haven't been pushed to GitHub yet.

---

## Configuration Reference

All settings live in `standup.toml` in the build folder. The `GITHUB_TOKEN` environment variable must be set separately — never put it in the config file.

| Key | Default | Description |
|-----|---------|-------------|
| `github_username` | `""` | Your GitHub username |
| `hours` | `24` | How many hours back to look |
| `format` | `"text"` | Output format: `"text"` or `"markdown"` |
| `journal_path` | `~/.standup_journal.jsonl` | Path to the JSONL history file |
| `local_roots` | `[]` | Parent directories to scan for local git repos |
| `exclude_repos` | `[]` | Repo names to skip (e.g. `["archived-thing"]`) |

---

## Output Files

- **`standup_today.md`** (or wherever Task Scheduler appends) — human-readable markdown, the file you open each morning
- **`standup_journal.jsonl`** — machine-readable JSONL history, one line per run; structured for future querying

---

## Running the Tests

```powershell
python -m pytest tests/ -v
```

Expected: **46 passed, 0 failed**

Test files:
- `test_standup.py` — formatter logic (11 tests)
- `test_git_log.py` — original local git reader tests (10 tests, kept for historical record)
- `test_local_git.py` — unpushed commit scanner (5 tests)
- `test_github_api.py` — GitHub API client with mocked responses (5 tests)
- `test_dedup.py` — SHA deduplication logic (5 tests)
- `test_journal.py` — JSONL journal writer (5 tests)
- `test_config.py` — TOML config loading (5 tests)

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Warning: GITHUB_TOKEN not set` | Environment variable not visible to this terminal | Reopen PowerShell/VS Code after setting the variable; VS Code requires a full restart |
| `Nothing committed in the last 24 hours` but you know you committed | GitHub API not returning results, or local repos not found | Verify `github_username` in standup.toml; check `local_roots` paths exist |
| TOML parse error with backslashes | Windows paths use `\` which TOML treats as escape sequences | Use forward slashes in standup.toml: `C:/Dev` not `C:\Dev` |
| Task runs but file not created | Output path doesn't exist yet | Create the parent folder manually first, or let the journal auto-create on first run |
| GitHub API returns partial results | Token lacks `repo` scope | Regenerate token with `repo` scope checked |

---

## Known Limitations

- `local_roots` scans only one level deep — repos nested inside subdirectories of `C:\Dev` won't be found. Add the intermediate directory to `local_roots` if needed.
- If two different repos share the same directory name, their commits may appear merged under one name. Use distinct repo names.
- Agent-created commits (e.g. from Claude Code Routines) are captured via the GitHub API, not the local scan. They'll appear without the `(local)` tag since they go straight to GitHub.
