# Future Features — dep-check

## 1. `pyproject.toml` Support

Python 3.11+ has `tomllib` in stdlib. Add a `parse_pyproject_toml()` function that reads the `[project].dependencies` and `[project.optional-dependencies]` tables. Gracefully skip on Python < 3.11 with a warning rather than a crash.

## 2. CVE / Security Advisory Integration

Query the [OSV API](https://osv.dev/docs/) (free, no auth) for known vulnerabilities in each pinned version. OSV covers PyPI, Go, npm, and Rust packages. Add a `VULN` column to the report table with CVE counts and links. This transforms dep-check from a "version drift" tool into a genuine security scanner.

## 3. Transitive Dependency Walk

When a `requirements.txt` is scanned, also check the dependencies of each listed package (fetched from PyPI `requires_dist`). Surface second- and third-level dependencies that are yanked or critically outdated. This catches the failure mode where your direct dependencies are current but pull in old vulnerable transits.

## 4. Claude Code Skill Packaging (`/dep-check`)

Package dep-check as a Claude Code Skill so it can be invoked with `/dep-check` in any coding session. The skill would scan the current project's requirements files, produce a summary, and optionally open the HTML report. This turns the tool from a separate script into an always-available context layer during development.

## 5. GitHub Actions Integration

Add a `--github-summary` flag that writes Markdown-formatted output to `$GITHUB_STEP_SUMMARY`. This makes dep-check a drop-in CI step: one line in a workflow YAML adds a formatted dependency health card to every PR's Actions summary tab — visible without downloading any artifact.

## 6. Historical Drift Tracking

On each run, append a JSON snapshot (`~/.dep-check-history/{project-hash}.jsonl`) with a timestamp and per-package version data. Add a `dep-check history` subcommand that shows how long each package has been outdated. This turns dep-check from a point-in-time check into a longitudinal metric: "requests has been 2 major versions behind for 180 days."
