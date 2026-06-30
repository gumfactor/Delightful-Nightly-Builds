# Future Features — GitHub Developer Analytics Dashboard

## 1. Personal Access Token Support with Full Private Repo Access
The current build uses whatever token is in `GITHUB_TOKEN`, which may be scoped to public repos only. Adding explicit PAT support (prompting for a token with `repo` scope if the current token fails) would unlock the full picture — especially valuable for users where private repos contain most of their actual work.

## 2. PR and Issue Activity Layer
Commit count is an imperfect proxy for work done. Adding PR opens/merges and issue closes per repo per month would create a richer "effort per project" view — especially useful for repos where much of the work happens in PR reviews and issue triage rather than direct commits.

## 3. Timezone-Aware Rhythm Charts
Currently the hour-of-day chart shows UTC hours. Adding a `--timezone` CLI flag (e.g. `--timezone America/Toronto`) would convert commit timestamps to local time before plotting, making the "when do I actually code" insight accurate.

## 4. Weekly Email Digest as Claude Code Routine
Package this as a scheduled Claude Code Routine that re-generates the dashboard weekly and emails it to the user. This turns a one-shot script into a recurring intelligence delivery — the user gets their coding pattern summary in their inbox every Monday without remembering to run the script.

## 5. Commit Message Topic Clustering
Feed commit messages through a keyword analysis (or Claude API when available) to identify dominant work themes per month. For example, a month heavy with "fix", "bug", "patch" messages signals maintenance mode vs. a month of "feature", "add", "implement" messages signalling active development. Surface this as a "mode indicator" per repo per month on the timeline.

## 6. Repo Focus Score
Derive a single "focus score" per week: high score = few repos with many commits each (deep focus), low score = many repos with few commits each (scattered context-switching). Plot this over time as a line chart on the Overview tab — gives an at-a-glance view of focus vs. fragmentation over the year.

## 7. GitHub Actions CI Health Overlay
Cross-reference the timeline heatmap with workflow run failure rates (from the GitHub Actions API) per repo per month. Cells with high commit counts + high failure rates would be highlighted in amber — indicating periods of churning code that keeps breaking CI, which are more useful to examine than periods of smooth delivery.
