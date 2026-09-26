---
name: shiplog
description: Generate a categorized changelog (with a suggested semver bump) from a local git repo's commit history. Invoke when the user wants release notes, a changelog, or a summary of what shipped since the last tag in the current or a named repo.
---

# Shiplog

Use this skill when the user asks things like "generate a changelog", "what shipped since the last release", "write release notes for this repo", or "summarize recent commits into a changelog".

## Running it

```bash
python3 <path-to-this-build>/src/shiplog.py generate <repo-path> \
  [--since REF] [--until REF] [--format md|html|both] [--out DIR] \
  [--ai-polish] [--repo OWNER/NAME]
```

- `<repo-path>` — defaults to the current project if the user doesn't name one.
- `--since`/`--until` — any git ref (tag, branch, SHA) or, for `--since`, a date string. Omit both to cover everything since the latest tag (or full history if there is no tag).
- `--repo OWNER/NAME` — set this to enrich merge-commit entries with the actual PR title and labels via `GITHUB_TOKEN` (must already be set in the environment). Skip it entirely if the repo isn't on GitHub or the token isn't available — the tool falls back to commit-message-only classification with zero network calls.
- `--ai-polish` — set this to have Claude write short prose per section using `ANTHROPIC_API_KEY` from the environment. Without a key set, output is a clean deterministic bullet list — never a partial or broken result.
- `--out DIR` — where to write `CHANGELOG_<range>.md` / `report_<range>.html`. Defaults to the current directory; never writes inside the target repo unless explicitly pointed there.

## What it does NOT do

- Never commits, tags, or pushes anything to the target repo — read-only `git log` only.
- Never sends diffs, file contents, or file paths to any external service — only commit type/scope/subject/breaking-flag ever leave the machine, and only when `--ai-polish` or `--repo` is explicitly requested.

## After running

Report the suggested version bump and where the files were written. If `--format both` (the default), mention both the Markdown file (for pasting into `CHANGELOG.md`) and the HTML file (for a quick visual read).
