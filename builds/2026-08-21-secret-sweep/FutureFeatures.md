# Future Features — Secret Sweep

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Custom pattern config file** — let `src/patterns.py`'s `NAMED_PATTERNS` list be extended
   via a user-supplied JSON/YAML file (`--patterns-file config.json`) so org-specific or
   less-common credential formats (internal service tokens, a specific SaaS vendor's key shape)
   can be added without editing the source.
2. **`--exclude` glob flag** — skip specific paths (e.g. `tests/fixtures/**`) from working-tree
   and history scans, for repos that intentionally keep fake-but-secret-shaped values in test
   fixtures (this build's own `tests/` directory is a good example of exactly that case).
3. **Exit code gating for CI** — a `--fail-on critical` flag that returns a non-zero exit code
   when unacknowledged critical findings exist, so `scan` can be dropped into a pre-push hook
   or CI job the same way `dep-check --exit-on-outdated` (2026-06-19) already does.

## Medium Effort (roughly one nightly build session)

4. **Pre-commit hook installer** — a `secretsweep install-hook` command that writes a
   `.git/hooks/pre-commit` script running `scan` on staged files only. Deliberately scoped out
   of tonight's build (see PRD Out of Scope) because it crosses the "never modifies the repo it
   scans" line this build otherwise holds to — worth a dedicated review of exactly what that
   hook does and how a user opts in/out per repo.
5. **Staged-files-only mode** — `scan --staged` restricting the working-tree scan to
   `git diff --cached --name-only`, for a genuinely fast pre-commit check on large repos where
   scanning every tracked file is unnecessarily slow.
6. **Cross-repo dashboard** — the `report` command already aggregates multiple `--repo` flags,
   but a `sweep-all` command that discovers every git repo under a root directory (e.g. `~/dev`)
   and scans them all in one pass would remove the need to remember and list every repo path by
   hand — directly matching how this build's design brief imagines it being used across The
   Canada List, Kwyeter, and lab infrastructure repos simultaneously.

## Ambitious Extensions (multi-session effort)

7. **Verified-live credential checking** — for a subset of providers with a safe, side-effect-free
   validity check (e.g. a GitHub PAT's rate-limit endpoint, which just reports token scope and
   doesn't mutate anything), optionally confirm whether a flagged credential is still active
   before recommending rotation — turning "this looks like a real credential" into "this
   credential is confirmed still valid, rotate today," which is a meaningfully stronger signal.
8. **Trend view** — since findings already persist with `first_seen`/`last_seen` timestamps in
   SQLite, a `history-report` command showing new-findings-per-week across all scanned repos
   would turn one-off audits into an ongoing hygiene metric, similar to how Voiceprint
   (2026-07-28) tracks a Human Voice Score trend over repeated runs on the same file.

---

## Possible Integration Points

- **BugTrace (2026-07-25)** already mines this exact user's commit history for bug-fix patterns
  via the same "walk local repos, classify with a rule engine + optional AI second opinion"
  architecture — a shared `git_ops.py`-style module could be extracted if a future build wants
  to consolidate the two tools' git-history-walking code.
- **Ingest Gate (2026-08-10)** already establishes the "aggregate-only data sent to the optional
  AI call, architecturally guaranteed privacy-safe" pattern this build follows for its own
  `ai_review` module — worth keeping consistent as more builds add optional AI layers over
  sensitive local data.
- **Landing Pattern (2026-08-03)** reads this very repo's own 50+ open PR backlog — a future
  build could combine the two: flag any PR whose diff introduces a Secret Sweep finding before
  it gets merged, closing the loop between detection and this repo's own review process.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| No CI-friendly exit-code gate yet | Add `--fail-on critical\|high` (see Quick Win #3) |
| Every scan re-walks the full file list / full history from scratch — no incremental mode | Cache the last-scanned commit SHA per repo in SQLite and only walk new commits on repeat `history` runs, the same incremental pattern Waymark (2026-08-07) already uses for its own git-history indexing |
| Generic entropy detector's false-positive rate is not empirically measured | Run it against a larger corpus of real (non-secret) code and tune `MIN_ENTROPY_BITS_PER_CHAR` / the allowlist against actual results, rather than the single hand-picked threshold shipped tonight |
