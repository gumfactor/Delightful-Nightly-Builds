# Future Features — Burnrate

1. Incremental SQLite cache keyed by file mtime so scans of years of transcripts take milliseconds.
2. Adapters for Codex and Copilot transcript formats behind the existing `Turn` model.
3. Budget alerts: a Claude Code Routine that runs weekly and flags projects exceeding a monthly dollar threshold.
4. Optional Claude Haiku pass (runtime `ANTHROPIC_API_KEY`) that summarizes what each expensive session was trying to do.
5. Per-session drill-down page: context growth curve and a timeline of tool errors.
6. Cost per merged PR by joining sessions to git branches via `gitBranch` and the GitHub API.
7. Inline Chart.js fallback so charts work fully offline.
