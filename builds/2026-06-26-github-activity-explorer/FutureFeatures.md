# FutureFeatures — GitHub Developer Activity Explorer

## 1. Commit message sentiment and complexity analysis (AI)
Pass recent commit messages to Claude Haiku and classify them: bug fixes vs. features vs. refactors vs. docs updates. A stacked bar chart over time would show whether the developer spends more time shipping features or maintaining code — a genuine signal GitHub doesn't surface.

## 2. Language/technology breakdown over time
Use the GitHub API to detect which languages appear in each repo's commits, then show a time-stacked area chart: which languages have you been writing more or less of over the past year? Useful for tracking skill drift and project focus.

## 3. Pull request cycle time analysis
Extend the data fetch to include PRs (opened, reviewed, merged). Chart PR-open-to-merge times by repo, identify outliers (PRs open for months), and compute a personal "review turnaround" metric. Shows collaboration patterns GitHub's own PR page doesn't aggregate.

## 4. Interactive repo filter
Add a dropdown or checkbox list to the dashboard that lets the user toggle individual repos on/off and see all charts update in real time. Useful for excluding bots or experimental repos from the personal productivity view.

## 5. Weekly email digest as a Claude Code Routine
Package the script as a weekly Routine that runs every Monday morning, generates the dashboard, and writes a markdown summary of the past week's activity — streak status, total commits, most active repo, and a one-sentence AI trend note. Turns the one-shot report into a recurring check-in.

## 6. Side-by-side period comparison
Add a `--compare` flag that fetches two different date ranges and renders them in a split dashboard — "this month vs. last month" or "this year vs. last year". The delta column would show which habits have changed.

## 7. Collaboration graph
Identify co-authors from commit metadata (`Co-authored-by` trailer lines) and build a mini collaboration graph showing which contributors you work with most. Useful for visualizing team dynamics or acknowledging regular collaborators.
