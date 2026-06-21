# Future Features — GitHub Repository Health Scorecard

---

## 1. Commit Frequency Trend
Show a sparkline bar chart per repo for the last 8 weeks of commit activity using the GitHub `GET /repos/{owner}/{repo}/stats/commit_activity` endpoint. A repo with 30 commits/week dropping to 2 signals declining momentum better than a single "pushed 2 days ago" timestamp.

## 2. Contributor Count Column
Fetch `GET /repos/{owner}/{repo}/contributors?per_page=1&anon=false` for each repo. A single-contributor repo with many open issues and a failing CI is a different risk profile from a multi-contributor one. Add a Contributors column to the table and factor it into the health score.

## 3. Schedule as a Nightly Claude Code Routine
Package `main.py` as a scheduled Routine definition (`.claude/routines/github-health.md`) that runs each morning, generates the HTML, and sends a PushNotification summary. Turns a manual tool into an automatic daily briefing without the user having to remember to run it.

## 4. CI Failure Drill-Down
When a repo has CI failures, link to the failing run in GitHub Actions and include the name of the failing workflow. Currently the scorecard shows "Failing" with no drill-down path. A link to the exact failing run saves the step of navigating through the GitHub UI.

## 5. Repository Size and Language Filtering
Add filters for repository language (Python, Dart, JavaScript…) and size tiers. The user works in multiple languages across multiple project types; being able to quickly see "show me all Python repos with open issues" would save time during triaging sessions.

## 6. Watchlist Mode
Accept a `--repos owner/repo1 owner/repo2 ...` argument to restrict the scorecard to a curated list of high-priority repos rather than all repos. Useful for focusing the morning briefing on the 5-10 repos that actually matter right now.

## 7. Open PR Count as Separate Column
Currently open PRs are bundled into GitHub's `open_issues_count`. A separate PR count column (using `GET /repos/{owner}/{repo}/pulls?state=open`) distinguishes "stale PRs waiting for review" from "actual open bug reports" — a meaningful distinction for triage.
