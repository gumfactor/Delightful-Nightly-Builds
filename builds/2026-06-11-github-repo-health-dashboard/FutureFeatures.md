# Future Features — GitHub Repository Health Dashboard

## Quick Wins

### 1. Separate PR and Issue Counts
Currently `open_issues_count` from the GitHub API conflates open issues and open PRs. A separate `GET /repos/{owner}/{repo}/pulls?state=open` call (with caching or rate-limit awareness) could break these into distinct columns — "Issues" and "PRs" — making the dashboard more actionable.

### 2. Configurable Staleness Thresholds
Add a `--stale-days N` flag (default 90) and `--quiet-days N` flag (default 30) so the user can tune what counts as "stale" vs "quiet" for their workflow. Some repos are legitimately slow-moving (completed libraries) and shouldn't be flagged stale.

### 3. Filter by Language
`--language python` would filter output to repos in a specific language — useful when managing multi-language projects and wanting to focus on one stack's repos.

### 4. Minimum-Stars Filter
`--min-stars N` to hide low-star repos from the output — reduces noise when personal repos include many small experiments. Pairs well with `--limit` for a clean "active projects" view.

### 5. Watchlist Mode
A `--watchlist repos.txt` flag that reads a newline-separated file of `owner/repo` strings and shows those specific repos regardless of who owns them. Useful for monitoring external repos (dependencies, competitor projects, upstream libraries).

## Medium Complexity

### 6. CI Status Column
Add a "CI" column showing the latest workflow run status (✓ passing, ✗ failing, ⟳ running) per repo. Requires one additional API call per repo (`GET /repos/{owner}/{repo}/actions/runs?per_page=1`) but delivers significant value — a failing CI alongside open issues is a much stronger signal than issues alone.

### 7. Claude Code Skill Packaging
Ship this as a `/repo-health` Claude Code Skill so it can be invoked directly from within a Claude Code session with `claude /repo-health`. The skill wrapper would handle token lookup, call the existing Python module, and present the output in the conversation. No new logic needed — just the skill wrapper.

### 8. Caching Layer
Add a simple JSON cache (`~/.cache/gh-repo-health/repos.json`) with a configurable TTL (default 5 minutes) so running the command multiple times in a session doesn't hit the API repeatedly. Particularly valuable when using `--format json` to feed downstream scripts.

## Ambitious

### 9. HTML Dashboard Export
A `--format html` flag that generates a self-contained `dashboard.html` file with sortable columns, click-to-open-repo links, and color-coded health badges. Could be opened in a browser or served locally for a richer view. Builds on the same enriched data structure with no new API calls.

### 10. Weekly Digest Email / Markdown Report
A scheduled mode (`--report weekly`) that generates a Markdown or plain-text digest of repos that changed health status since last run (newly stale, newly active after a quiet period, new issues opened). Persists last-run state in a small JSON file. Designed to be run as a Claude Code Routine on a weekly schedule, emailing results or appending to a log.
