# Future Features — BugTrace

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--exclude-category` / `--min-count` filters on `report`** — let the terminal/JSON output skip noise categories (e.g. `other`) or categories below a count threshold, so a large history doesn't drown the signal.
2. **CSV export** — a `--format csv` alongside the existing text/json/html, for pasting straight into a spreadsheet or Google Sheets for the user's own manual trend tracking.
3. **`--author` filter on `sync`** — restrict to commits by a specific git author email, useful once BugTrace is pointed at a shared repo where only the user's own fixes should count.
4. **Colorized terminal output** — the current text report is plain; ANSI color-coding the top category (matching the pattern used by `dep-check`) would make `bugtrace report --format text` more scannable at a glance.

## Medium Effort (roughly one nightly build session)

5. **Trend delta in the coaching paragraph** — compare the current run's category distribution against the same window from the previous `sync` (stored as a snapshot), so the AI/template coaching can say "your null-handling fixes dropped 40% since last month" instead of only a point-in-time snapshot. This is the single highest-value addition: it turns BugTrace from a mirror into a measurable improvement tracker, which is the whole premise of the build.
6. **Per-file hotspot view** — aggregate fix commits by the files they touched (already captured via `changed_files` from the GitHub API path; local git path would need a small addition), surfacing "this file has been the target of 6 fixes across 3 categories" as its own dashboard panel.
7. **Claude Code Skill wrapper** — ship a `/bugtrace-sync` skill definition (documented in this build's Manual.md for the user to copy into their own `~/.claude/skills/`) so a sync + report refresh can be triggered with a single slash command from within any Claude Code session, rather than remembering the CLI invocation.

## Ambitious Extensions (multi-session effort)

8. **Cross-repo "developer growth" report as a Routine** — schedule a monthly `sync --all` + `report` run (per CLAUDE.md's Routine deployment guidance) that emails or files a standing markdown summary of category trend deltas, turning this from an on-demand tool into a genuine passive feedback loop.
9. **Language-aware diff parsing** — right now the classifier works on raw diff text for any language. A Python-specific (and later JS/TS) AST-diff layer could catch more precise signals (e.g. distinguishing "added a None check" from "added a try/except" at the syntax level rather than by keyword), reducing the `other` bucket that currently absorbs anything the keyword rules don't recognize.

---

## Possible Integration Points

- **Worklog** (2026-07-10) already correlates git/GitHub activity into workstreams with decision rationale; BugTrace's fix-commit classification could feed into Worklog's `why` decision-search as an additional signal type ("this workstream's fixes cluster around config/env issues").
- **Protocol Forge** (2026-07-19) and **AgentLint** (2026-07-16) both established the "deterministic-rule-first, optional-AI-second-opinion, always-functional-without-a-key" pattern this build reused — a future build could extract that shared fallback architecture into documented conventions rather than re-deriving it each time.
- **ci-pulse** (2026-06-28) already tracks CI failure rates per workflow; a shared dashboard combining "how often CI fails" with "what kind of bug caused the fix" would be a genuinely richer picture than either alone.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Keyword classification is heuristic and can misfile ambiguous commits (e.g. a message mentioning both "config" and "async") into whichever category's rule happens to be checked first | Add a confidence score alongside the category, and route only high-ambiguity cases through the optional AI classifier automatically even without `--ai` set globally |
| The classification taxonomy is fixed at 12 categories and cannot be customized per-project | Support a user-supplied taxonomy file so teams/projects with different failure-mode vocabularies (e.g. a Flutter project's categories differ from a Python backend's) can tailor it |
| Diff excerpts are truncated to 4000 characters, so very large fix commits lose context for classification | Summarize oversized diffs (via a cheap deterministic diff-stat + hunk-header extraction) instead of naively truncating, preserving signal from the parts of a large diff that actually matter |
| `--since-months` on the GitHub path approximates months as 30.4375 days rather than calendar months | Switch to proper calendar-month arithmetic if precise month boundaries ever matter for the trend view |
