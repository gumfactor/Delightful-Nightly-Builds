# Future Features — Fleet Drift

Enhancements to a working, valuable tool — not features required for tonight's build to be genuinely useful as shipped.

1. **More manifest formats.** Add `pyproject.toml` (PEP 621 `[project.dependencies]` and Poetry's `[tool.poetry.dependencies]`), `Pipfile`, and `pubspec.yaml` (Dart/Flutter, PROFILE.md's #3 preferred stack) so the drift matrix covers every ecosystem the user actually ships in, not just Python/`requirements.txt` and JS/`package.json`.

2. **Vulnerability overlay.** Cross-reference each tracked dependency against a free vulnerability feed (e.g. OSV.dev's API, which is free and no-auth) once one is added to PROFILE.md's Data Sources, so the dashboard can flag "drifted AND one of the pinned versions has a known CVE" as the highest-priority row rather than relying on staleness alone as a proxy for risk.

3. **Drift trend chart.** `history` currently prints one dependency's version-over-time as text/JSON; a `render --trend <dependency>` mode could plot the accumulated multi-day snapshot history (already persisted) as a real line chart showing when a repo's pin diverged from the fleet, not just where things stand today.

4. **One-command fix suggestion (still read-only).** For a `patch`-severity drift where every pinned version is a subset of one repo's already-latest pin, generate the exact `pip install package==X.Y.Z` / `npm install package@X.Y.Z` commands needed to converge every repo on the newest already-adopted version — still never executes them, matching this catalog's established read-only convention for GitHub-reading tools, but removes the last manual step of looking up what to actually type.

5. **Private/internal registry support.** Accept a configurable registry base URL (for a self-hosted PyPI mirror or npm-compatible internal registry) so the drift/staleness computation still works for organizations that don't publish everything to the public registries.

6. **Slack/email digest mode.** A `--notify` flag that posts the hero-stats summary (not the full matrix) to a webhook after `sync`, turning this from a pull tool the user has to remember to run into something closer to a Routine that surfaces drift automatically — a natural fit given CLAUDE.md's own guidance that recurring checks are usually a better fit as a Routine than a standalone script.

7. **Archived/forked-repo exclusion.** `list_owned_repos` currently returns every owned repo; a `--skip-archived` flag (the GitHub API already returns an `archived` boolean per repo) would keep old, no-longer-maintained repos from diluting the drift matrix with dependencies nobody is actually going to update.
