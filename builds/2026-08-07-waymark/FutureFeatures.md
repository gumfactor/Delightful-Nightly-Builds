# Future Features — Waymark

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--json` output on `search`** — add a flag to `waymark search` that prints newline-delimited JSON instead of the plain-text table, so results can be piped into `jq` or another tool without re-parsing formatted text.
2. **`waymark index --all-branches` toggle** — `read_commits` already passes `--all` to `git log`, which includes every local branch's history; add a `--current-branch-only` flag for repos where the user only wants `HEAD`'s ancestry, since some monorepos have dozens of stale branches that add noise.
3. **Configurable score threshold on `render`** — currently the dashboard's min-score dropdown is hardcoded to 0/3/5/7; expose a `--min-score` CLI flag on `render` that pre-filters before rendering, useful for very large multi-repo databases where the full JSON payload gets large.
4. **`waymark index --remove-repo <label>`** — a way to drop a repo's commits from the shared database (e.g. after a project is archived), currently requires manual SQLite surgery.

## Medium Effort (roughly one nightly build session)

5. **GitHub PR correlation** — when `GITHUB_TOKEN` (or a user-configured PAT) is available, cross-reference each indexed commit's hash against the GitHub API to attach the PR title/description/review discussion that merged it, giving the decision summary richer context than the commit message alone. This was explicitly scoped out of tonight's build to keep it to a single, well-tested data source (local git).
6. **Manual annotation** — let the user attach a free-text note to any commit (`waymark annotate <hash> "we reverted this in March because..."`), stored in a new `annotations` table. Tonight's build deliberately shipped zero manual entry to fix the exact failure mode that sank the 2026-06-06 AI Session Context Bridge build, but a *retroactive*, optional annotation layer wouldn't reintroduce that dependency — the tool is still useful with zero notes.
7. **Semantic search** — replace (or augment) the `LIKE`-based keyword search with local embeddings (e.g. a small sentence-transformer run entirely offline) so "why did we change the auth flow" can match a commit whose message never uses those exact words.

## Ambitious Extensions (multi-session effort)

8. **Claude Code Skill wrapper** — package `waymark search` as a `/waymark` skill so a live Claude Code session can query project decision history mid-conversation ("what did we decide about the database schema last month?") without the user leaving the terminal. This is the natural evolution given PROFILE.md's stated interest in tools that "preserve context across sessions."
9. **Scheduled cross-repo digest Routine** — a weekly Claude Code Routine that runs `waymark index` across all of the user's active repos, then uses Claude to write a one-paragraph "what changed and why, across every project" digest — effectively a decision-focused sibling to the existing Git Standup Reporter build.

---

## Possible Integration Points

- **Git Standup Reporter** (2026-06-07): that build summarizes *recent* commits for a daily standup. Waymark is the long-horizon complement — it's for searching *any* commit, months later, not just today's. The two could share a git-parsing layer in a future refactor, though each is fully self-contained today per the no-cross-import rule.
- **AI Session Context Bridge** (2026-06-06, 3/10): Waymark is the direct fix for that build's core critique. A future build could go further and have Waymark ingest that tool's saved handoff docs (if any exist) as an additional evidence source alongside git history.
- **Connectome** (2026-07-11): both are local knowledge-graph-style tools with zero required external APIs. A future "personal knowledge hub" build could present Connectome's note graph and Waymark's decision timeline side by side as two views of the same underlying idea — externalized project memory.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The decision scorer is a hand-tuned heuristic, not learned from feedback — it will over- or under-score some commit styles (e.g. a team that never uses conventional-commit prefixes gets no type-based signal) | Let the deterministic score serve as a prior, and let `enrich` (when a key is present) also emit a confidence-adjusted score, not just a rewritten summary |
| `search`'s ranking is `decision_score` then recency, not true relevance ranking against the query | Add a simple TF-IDF-style rank blended with decision_score once the corpus is large enough to make plain recency ordering feel stale |
| No way to re-score existing commits after a scorer.py change without re-indexing from scratch (incremental indexing skips already-seen hashes, including their old score) | Add a `waymark rescore` command that recomputes `decision_score`/`tags`/`summary` for already-indexed commits without re-walking git history |
| The HTML dashboard loads its entire dataset as one embedded JSON blob, which will get slow to parse past a few thousand commits | Paginate the embedded data or switch to lazy-loading pages of results once a single user's aggregate database grows that large |
| `enrich` processes commits one HTTP request at a time with no concurrency | Batch requests with a small thread pool once daily commit volume across all indexed repos is high enough to make sequential calls noticeably slow |
