# Manual — Waymark

> **Version:** 1.0 (built 2026-08-07)
> **Complexity:** Ambitious Project

---

## What This Is

Waymark automatically mines your git commit history into a searchable knowledge base of *decisions* — the "why" behind changes, not just the "what." Point it at any local git repo you work in, and it builds a cross-project, browsable timeline of the commits that mattered: breaking changes, bug-fix root causes, refactor rationale, reverts. There is nothing to write down — the git history already exists and is never wrong. Months later, instead of re-reading diffs or trying to remember which repo a decision happened in, search across everything you've indexed.

---

## Quick Start

1. `cd` into the Waymark build folder (or reference `main.py` by full path)
2. Index a repo you work in: `python3 main.py index /path/to/some/repo --label myproject`
3. Search it: `python3 main.py search "database migration"`
4. Build the browsable dashboard: `python3 main.py render`
5. Open the printed HTML path in a browser

Repeat step 2 for every repo you want in your cross-project index — they all share one database by default, so `search` and `render` cover everything you've indexed so far.

---

## How to Use It

### Indexing a repo

```
python3 main.py index /path/to/repo --label myproject
```

Walks the repo's full commit history (all local branches), scores every commit's decision-worthiness, and stores it. Safe to re-run any time — already-indexed commits (by hash) are skipped, so re-indexing only picks up new commits since the last run. Waymark never writes to, or otherwise modifies, the repo it indexes — it only reads `git log` output.

### Searching

```
python3 main.py search "auth" --repo myproject --min-score 5
```

- Positional argument is free-text, matched against the summary, commit message, and tags.
- `--repo <label>` restricts to one indexed repo.
- `--tag <tag>` restricts to commits carrying a specific tag (conventional-commit type, or a matched decision keyword like `revert`, `workaround`, `breaking`).
- `--since <ISO date>` restricts to commits on/after that date.
- `--min-score <0-10>` filters out low-signal commits (default 0, i.e. no filter).
- Omit the query entirely to browse everything matching your filters.

### Rendering the dashboard

```
python3 main.py render --output ~/waymark-dashboard.html
```

Builds a single self-contained HTML file — no server, no external network calls when viewing it. Open it in any browser. It has a search box, repo/tag filters, a minimum-score dropdown, and click-to-expand detail per commit (full message, file/line stats). Defaults to `~/.waymark/dashboard.html` if `--output` is omitted.

### AI enrichment (optional)

```
export ANTHROPIC_API_KEY=sk-...
python3 main.py enrich --limit 20
```

If `ANTHROPIC_API_KEY` is set, this rewrites the summary for your highest-scoring not-yet-enriched commits into a clearer plain-English sentence using Claude Haiku. Without a key set, this command does nothing and makes zero network calls — every commit already has a usable deterministic summary from indexing, so enrichment is a quality upgrade, never a requirement. Only sends the commit subject, body, and file/line-count stats to the API — never full diff content.

### Listing indexed repos

```
python3 main.py list-repos
```

Shows every repo you've indexed, its commit count, how many were decision-worthy (score ≥ 5), and when it was last indexed.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db <path>` | `~/.waymark/waymark.db` | SQLite database location. Shared across all repos by default so search/render cover everything; override to keep a repo's index separate. |
| `ANTHROPIC_API_KEY` | unset | Enables the optional `enrich` command. Never required for `index`/`search`/`render`. |

No configuration file — every option is a CLI flag.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `index` fails with "is not a git repository" | The path isn't a git repo, or is a bare repo/submodule without the expected structure | Confirm `git -C <path> status` works before running Waymark against it |
| `index` reports 0 new commits every time | Already fully indexed — this is expected on a re-run with no new commits | Make new commits, or point at a different repo/branch |
| `enrich` prints "ANTHROPIC_API_KEY is not set; nothing to enrich" | No key in the environment | This is not an error — deterministic summaries are already stored. Set the key if you want AI-refined summaries. |
| Dashboard shows fewer commits than `list-repos` reports | The `render` command shows everything in the database with no filtering by default — check you're opening the most recently rendered file, not a stale one | Re-run `render` after indexing |

---

## Known Limitations

- The decision-worthiness score is a deterministic heuristic (commit type, keywords, diff size), not a learned model — it will occasionally over- or under-score an unusual commit style.
- No manual annotation layer yet — everything comes from git history alone (see `FutureFeatures.md` for why this was deliberate).
- `search` ranks by decision score then recency, not full-text relevance ranking.
- The AI-enriched summary, when present, replaces the deterministic one in search/render output, but the deterministic summary is always retained in storage as the permanent fallback.
