# Future Features — Landing Pattern

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--repo-file repos.txt` batch mode** — read a list of `owner/name` repos from a file and run `sync` + `report` across all of them in one command, with a combined summary table (repo, batch1 count, blocked count) at the top. Removes the "run it once per repo" limitation noted in Manual.md.
2. **`--stale-days N` flag on `report`** — highlight (or separately list) any Blocked PR older than N days, since an old PR stuck in the same state across several `sync` runs is the one most worth manually intervening on.
3. **Colorized terminal output** — ANSI color codes on the text report (green for Batch 1, yellow for Batch 2, red for Blocked labels) using only `\033[...]` escape codes — no new dependency, matches the pattern several other builds in this catalog already use for terminal reports.

## Medium Effort (roughly one nightly build session)

4. **Semantic overlap detection beyond file paths** — the current file-overlap graph only catches PRs touching the *same file*. A meaningful upgrade: parse unified diffs (via the GitHub API's diff endpoint) and flag PRs that touch overlapping *line ranges* within a shared file, which is a much sharper conflict signal than "both touched `builds/index.md`" when a file is large and most edits are additive/non-overlapping.
5. **A `merge` subcommand with `--dry-run` and `--execute`** — given the recommended order, actually perform the GitHub merges via the API (squash or merge commit, user's choice), stopping and re-syncing if any merge in the batch fails partway through. This is the natural "close the loop" feature — Landing Pattern currently only recommends; this would let it (optionally, behind an explicit confirmation flag) act.
6. **Slack/email digest mode** — `report --notify` posts the Batch 1 / Blocked summary to a webhook, so a recurring Claude Code Routine could run `sync` + `report --notify` on a schedule and surface a fresh backlog summary without the user having to remember to check.

## Ambitious Extensions (multi-session effort)

7. **Cross-repo merge-order awareness** — for repos where PRs on repo A depend on a corresponding PR on repo B (e.g. a shared library and its consumer), track cross-repo file/dependency links and factor them into the merge order recommendation — currently every repo is analyzed in isolation.
8. **A GitHub Action / status check integration** — post the readiness label and any file-overlap warnings as a PR comment or a check-run status directly on GitHub, so the signal is visible in the PR view itself rather than requiring a separate `report` run.

---

## Possible Integration Points

- **Pipeline Pulse** (2026-07-09) already answers "which nightly builds are stuck in an open PR and for how long" by diffing this repo's `builds/index.md` catalog against git history. Landing Pattern is a natural second stage for that exact same repo: Pipeline Pulse tells you a backlog exists; Landing Pattern tells you how to clear it safely. A future build could have Pipeline Pulse invoke Landing Pattern's `sync`/`report` directly and merge the two into a single "backlog health" dashboard.
- **Worklog: Cross-Agent Project Activity Workstreams** (2026-07-10) already correlates git/GitHub/AI-agent activity into workstreams — Landing Pattern's per-PR readiness data would be a clean additional signal for Worklog's standup/resume views ("workstream X has a PR ready to merge, workstream Y is blocked on CI").
- Given the deployment-model guidance in CLAUDE.md, Landing Pattern's `sync` + `report` pair is a strong candidate for a Claude Code Routine that runs weekly and surfaces a "your PR backlog" briefing without the user remembering to run it manually.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| File-overlap detection is path-based only, not line-range-based | See Medium Effort item #4 above — parse diffs for line-level overlap |
| No cross-repo awareness | See Ambitious Extension #7 |
| CI state treats "no CI configured" the same as "CI passed" | Add a distinct `ci_state: "not_configured"` label (detectable when both the combined-status and check-runs endpoints return zero total) so a repo with no CI doesn't look artificially "ready" |
| One repo per `sync`/`report` invocation | See Quick Win #1 — batch mode |
