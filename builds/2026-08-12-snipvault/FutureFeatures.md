# Future Features — Snipvault

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Global install location** — Add an `install.sh` that copies `main.py`/`src/` into `~/.snipvault/` and drops a `snipvault` shim on `PATH`, so the tool works from any project directory instead of only from inside tonight's dated build folder.
2. **`edit` command** — Currently editing a snippet means `remove` + re-`add` (deliberately out of scope tonight). A thin `edit <id> --code/--title/--tags/--description` wrapper that preserves the id and increments `updated_at` would close that gap in under an hour.
3. **`export`/`import` as JSON** — A one-command full-library dump/restore, useful before wiping a build folder or for backing up the SQLite file outside of `data/snippets.db`.

## Medium Effort (roughly one nightly build session)

4. **VS Code snippet export** — Generate a `.code-snippets` file from the library so saved snippets also appear in VS Code's native snippet autocomplete, closing the loop between "saved in Snipvault" and "usable while actually typing code" (PROFILE.md names VS Code as a daily tool).
5. **Language-aware syntax highlighting in `render`** — The current HTML dashboard shows code in a plain `<pre><code>` block. Swapping in a CDN-pinned, version-locked highlighter (e.g. highlight.js) with a graceful plain-text fallback when the CDN is blocked (this catalog's established pattern) would make the browsing view meaningfully more usable for longer snippets.

## Ambitious Extensions (multi-session effort)

6. **Real semantic search via local embeddings** — Tonight's AI-assisted search deliberately expands a natural-language query into keywords rather than using true similarity search, to stay deterministic and auditable. A follow-up build could add an optional local embedding index (e.g. a small sentence-transformer run once at index time, cached per snippet) for genuinely fuzzy "find me something like this" retrieval, while keeping the current keyword ranker as the always-available fallback.
7. **Editor/IDE extension surface** — A lightweight VS Code extension (or a filesystem-watcher Hook) that offers "Save selection to Snipvault" and "Insert from Snipvault" directly inside the editor, rather than requiring a Claude Code session or terminal round-trip.

---

## Possible Integration Points

- **Worklog** (2026-07-10) already correlates git/GitHub/AI-agent activity into workstreams; a snippet saved mid-session could be recorded as a Worklog event, giving "what did I build and what reusable pieces came out of it" a single combined timeline.
- **Voiceprint** (2026-07-28) audits prose for AI-tell patterns — no natural connection today, but if Snipvault ever stores prose snippets (not just code) alongside code, the same AI-tell heuristics could flag AI-sounding boilerplate before it's saved as a "reusable" pattern.
- Any future build that generates code (templates, scaffolds, boilerplate) could write its output straight into Snipvault via `main.py add` instead of only to disk, making it immediately searchable later.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The snippet database lives inside this dated build folder, so it isn't reachable from other projects without manually pointing `--db` at this path | Ship the install script from Quick Win #1 so the library has one stable, global location |
| No snippet versioning — saving a corrected version of a snippet creates a brand-new row rather than updating history | Add the `edit` command from Quick Win #2, or a lightweight version-chain like Panel Prep's per-project revision history |
| AI-assisted search quality depends entirely on Claude Haiku's query-expansion guess, with no feedback loop if the expansion misses | Log which keyword expansion led to a result the user then actually opened via `get`, and use that as a lightweight relevance signal over time |
| Tag extraction is frequency-based and can surface generic identifiers (e.g. `data`, `result`) for very short snippets | Weight tag candidates by TF-IDF-style rarity across the whole library (the same technique Connectome, 2026-07-11, already validated) instead of raw in-snippet frequency |
