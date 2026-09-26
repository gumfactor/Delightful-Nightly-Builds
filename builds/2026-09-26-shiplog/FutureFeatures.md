# Future Features — Shiplog

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--append-to <file>`** — instead of writing a standalone `CHANGELOG_<range>.md`, prepend the new section directly under the `# Changelog` heading of an existing `CHANGELOG.md`, so repeated runs build one running file instead of one file per range.
2. **`--json` output format** — emit the `ChangelogResult` as raw JSON (sections, cancelled pairs, suggested bump) so the result can be piped into another script or CI step without parsing Markdown or HTML.
3. **Author breakdown** — `git log` already returns author info for free (the format string can add `%an`); add a small "by author" count table to the HTML report's banner.

## Medium Effort (roughly one nightly build session)

4. **Squash-merge PR detection** — GitHub's squash-merge commits don't say "Merge pull request #N"; they typically end the subject with `(#123)`. Add a second PR-number extraction pattern and route those through the same `github_enrich` enrichment path, since right now they're silently classified from the commit message alone.
5. **Multi-repo mode** — accept a list of repo paths (or a directory containing several repos) and produce one combined report grouped by repo, for a "what shipped across all my projects this week" view — a natural pairing with the 2026-07-10 Worklog build's cross-repo activity correlation.

## Ambitious Extensions (multi-session effort)

6. **Routine wrapper** — a weekly Claude Code Routine that runs Shiplog against a configured list of repos every Sunday night and drops the Markdown output somewhere the user reviews on Monday, turning this from a pull tool into a genuine pull-tool-that-comes-to-you per PROFILE.md's stated preference.
7. **Learned classification** — log every commit the keyword classifier routes to "Uncategorized" to a local file across runs; once enough examples accumulate, surface a periodic prompt suggesting new keyword rules (or, with `--ai-polish`, ask Claude to propose them) rather than leaving the same phrasing "Uncategorized" forever.

---

## Possible Integration Points

- **2026-07-10 Worklog (Cross-Agent Project Activity Workstreams)** — Worklog already correlates git/GitHub/agent activity into workstreams; Shiplog's classified-commit structure would slot in as a ready-made "what shipped" section for Worklog's generated handoff documents instead of Worklog re-deriving that from raw commits itself.
- **2026-06-28 ci-pulse / 2026-08-03 Landing Pattern** — both already parse GitHub PR/Actions data via `GITHUB_TOKEN`; the `github_enrich.py` module here is intentionally small and dependency-free enough to lift into either build if PR-title enrichment there ever becomes useful.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Squash-merge commits with `(#123)` suffix aren't recognized as PRs | Add a second regex to `classify.extract_pr_number` for the `(#N)` suffix pattern (see Quick Win #4 above) |
| No caching of GitHub PR lookups across runs | Add a small local JSON cache keyed by `owner/name#pr_number` so re-running the same range twice doesn't re-fetch identical PRs |
| Revert cancellation is single-level only | Extend `cancel_reverts` to walk a chain (revert-of-a-revert re-adds the original change) if this ever shows up in practice |
