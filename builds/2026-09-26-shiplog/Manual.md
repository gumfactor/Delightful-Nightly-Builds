# Manual — Shiplog

> **Version:** 1.0 (built 2026-09-26)
> **Complexity:** Ambitious

---

## What This Is

Shiplog turns a local git repository's raw commit history into a categorized, human-readable changelog: Breaking Changes, Features, Fixes, and Maintenance, with revert/re-revert pairs automatically cancelled out as noise and a suggested semver bump (`major`/`minor`/`patch`/`none`). It works on any git repo — conventional-commit-formatted or not, since it falls back to keyword-based classification for ordinary commit messages. It's for the moment before a release or a status update, when re-reading raw `git log` output by hand is the alternative.

---

## Quick Start

1. `cd` into this build folder (or reference its full path).
2. Run: `python3 src/shiplog.py generate /path/to/your/repo`
3. Look in the current directory for `CHANGELOG_<range>.md` and `report_<range>.html`.
4. Open the `.html` file in a browser for the visual version, or paste the `.md` file into your project's `CHANGELOG.md`.

No installation is required beyond Python 3.11+ and `git` itself — the core CLI is stdlib-only.

---

## How to Use It

### Choosing a range

By default, Shiplog covers everything since the latest git tag reachable from `HEAD` (or the entire history if the repo has no tags). To narrow or widen the range:

```bash
python3 src/shiplog.py generate /path/to/repo --since v1.2.0 --until HEAD
python3 src/shiplog.py generate /path/to/repo --since 2026-09-01   # a date instead of a ref
```

`--since`/`--until` accept any git ref (tag, branch name, commit SHA). `--since` alone can also be a date string, in which case Shiplog uses `git log --since=<date>` semantics.

### Output format

```bash
python3 src/shiplog.py generate /path/to/repo --format md      # Markdown only
python3 src/shiplog.py generate /path/to/repo --format html     # HTML report only
python3 src/shiplog.py generate /path/to/repo --format both      # both (default)
python3 src/shiplog.py generate /path/to/repo --out ./release-notes
```

### GitHub PR enrichment (optional)

If the target repo's PRs are merged via "Merge pull request #N from ..." commits, pass `--repo owner/name` with `GITHUB_TOKEN` set in the environment to replace the unhelpful merge-commit subject with the actual PR title, and to refine classification using PR labels (`bug` → Fixes, `enhancement`/`feature` → Features, `breaking`/`breaking-change` → Breaking Changes, `documentation` → Maintenance, etc.). Without `--repo` or without `GITHUB_TOKEN` set, this step is skipped entirely — zero network calls are made.

```bash
GITHUB_TOKEN=ghp_xxx python3 src/shiplog.py generate /path/to/repo --repo yourname/yourrepo
```

### AI-polished prose (optional)

```bash
ANTHROPIC_API_KEY=sk-ant-xxx python3 src/shiplog.py generate /path/to/repo --ai-polish
```

With `--ai-polish` and a key set, each non-empty section gets a short (2-4 sentence) prose summary written by Claude Haiku, built only from the already-classified commit type/scope/subject/breaking-flag structure — never from diffs, file contents, or file paths. Without a key, or if the API call fails for any reason, each section falls back to a clean deterministic bulleted list of commit subjects. The tool never partially fails: you always get complete output either way.

### As a Claude Code Skill

A companion skill ships in `skill/SKILL.md`. Copy or symlink it into your project's `.claude/skills/` (or reference it directly) to invoke Shiplog conversationally — e.g. "generate a changelog for this repo since the last tag."

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--since` | latest tag reachable from `--until` (or full history) | Lower bound: a git ref or a date string |
| `--until` | `HEAD` | Upper bound: a git ref |
| `--format` | `both` | `md`, `html`, or `both` |
| `--out` | current directory | Where output files are written |
| `--ai-polish` | off | Reads `ANTHROPIC_API_KEY` from the environment when set |
| `--repo` | none | `owner/name` — reads `GITHUB_TOKEN` from the environment when set |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `error: '<path>' is not a git repository` | The given path (or its parents) has no `.git` directory | Point `--repo-path` at an actual git working tree |
| `error: '<ref>' is not a valid git ref` | `--until` (or a ref-like `--since`) doesn't exist in that repo | Check `git tag`/`git branch` in the target repo for the correct name |
| Everything lands in "Uncategorized" | Commit messages are unusually generic (e.g. "wip", "misc") | Adopt conventional-commit prefixes (`feat:`, `fix:`, etc.) going forward, or accept the keyword classifier's best guess — it still groups commits correctly, just without a specific type |
| `--repo` set but titles didn't change | `GITHUB_TOKEN` not set, or the commit isn't a "Merge pull request #N" style merge commit | Confirm `GITHUB_TOKEN` is exported; squash-merged PRs without that exact merge-commit format aren't detected as PRs |
| `--ai-polish` produced bullet lists instead of prose | `ANTHROPIC_API_KEY` not set, or the API call failed | Export the key; check `stderr` isn't showing an unrelated error — this is a deliberate fallback, not a bug |

---

## Known Limitations

- Only single-level revert/re-revert pairs are cancelled (a revert commit matched against the exact original commit it reverts). A revert-of-a-revert chain is not specially handled beyond that.
- GitHub PR enrichment only recognizes GitHub's default "Merge pull request #N from ..." merge-commit format — squash-merge commits that don't reference a PR number by that exact phrasing are classified from their own commit message instead.
- `--since` as a date string uses `git log --since=<date>`, which is git's own date parser (accepts things like `"2 weeks ago"` or `"2026-09-01"`) — it is not validated as a ref first, so a genuinely invalid ref that also happens to fail as a date will silently produce an empty range rather than an error.
