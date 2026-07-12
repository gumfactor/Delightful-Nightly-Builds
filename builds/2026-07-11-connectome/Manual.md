# Manual — Connectome: Personal Knowledge Graph Builder

> **Version:** 1.2 (built 2026-07-11; `backlinks` command and multi-category graph added same day)
> **Complexity:** Ambitious

---

## What This Is

Connectome turns a folder of your own notes (Markdown or plain text) into a searchable, cross-linked local knowledge base. It reads every note, extracts the concepts each one is actually about, and — crucially — figures out which notes are related to each other based on shared ideas, even when they live in completely different files or were written months apart. The result is a browsable HTML page: search your notes, browse by topic, and see (via a concept graph and a "related notes" list) connections you'd otherwise have to remember existed on your own. Everything runs locally — no external service is required for the core feature.

As of the 2026-07-11 follow-up, "notes" doesn't have to mean just notes: every item belongs to a **category** (Notes, Academic Papers, News Articles, or any label you choose), and the graph spans all of them at once — a note, a paper, and a news article about the same underlying idea link to each other regardless of category. Every item also gets a **subcategory**: a named cluster of related items (e.g. "Session / Context / Agent") computed from the same links, independent of category, so you can see thematic groupings that cut across the Notes/Papers/News split.

`index`, `search`, `related`, `stats`, and `build` only ever read the files you point them at. The one exception is the optional `backlinks` command, which can write `[[wiki-link]]` "See also" blocks directly into your note files — off by default (dry-run), and gated behind a git safety check when you turn it on. See "Writing backlinks into your own notes" below.

---

## Quick Start

1. `cd` into this build folder.
2. `python3 src/main.py index --notes-dir sample_notes` (or point `--notes-dir` at your own folder of `.md`/`.txt` files).
3. `python3 src/main.py build`
4. Open `output/index.html` in any browser (double-click it, or `file://` the path directly — no server needed).
5. Search, click a tag, click a note, or click a node in the concept graph.

To see the multi-category graph with all three bundled demo categories connected:

```
python3 src/main.py index --notes-dir sample_notes --category "Notes"
python3 src/main.py index --notes-dir sample_papers --category "Academic Papers"
python3 src/main.py index --notes-dir sample_news --category "News Articles"
python3 src/main.py build
```

Open `output/index.html` and click the category chips, or a note like "Semiconductor Capex Thesis" — its related list will include a paper and a news article on the same topic.

---

## How to Use It

### Indexing your notes

```
python3 src/main.py index --notes-dir /path/to/your/notes
```

Only `.md` and `.txt` files are read. Re-running `index` is safe and fast — unchanged files are skipped (detected by content hash), changed files are re-extracted, and deleted files are removed from the knowledge base along with their links. Run this any time your notes change; there's no background watcher.

Add `--ai` to refine concept extraction with Claude Haiku (only if `ANTHROPIC_API_KEY` is set in your environment) — this also enables the optional subcategory-relabeling pass (see "Categories and subcategories" below):

```
python3 src/main.py --db connectome.db index --notes-dir /path/to/your/notes --ai
```

Without a key, or if the API call fails for any reason, extraction falls back automatically to the built-in deterministic method — nothing breaks either way.

### Categories and subcategories

Every item indexed belongs to a **category** — pass `--category` to `index` (defaults to `"Notes"`):

```
python3 src/main.py index --notes-dir /path/to/your/papers --category "Academic Papers"
```

Run `index` once per category/folder. Indexing one category never touches or deletes another category's items — but links, doc frequencies, and **subcategories** are always recomputed across your *entire* database, so items in different categories can link to each other.

Subcategories are computed automatically on every `index` run — no flag needed. They're a deterministic clustering of strongly-linked items (regardless of category), named from each cluster's own top concepts (e.g. "Session / Context / Agent"). Pass `--ai` (with `ANTHROPIC_API_KEY` set) to additionally ask Claude for a cleaner human-readable name per cluster; any cluster it doesn't confidently name keeps its deterministic name instead of losing one.

### Searching

```
python3 src/main.py search "some topic"
python3 src/main.py search "some topic" --category "Academic Papers"
```

Matches item titles, bodies, and extracted concepts (case-insensitive). Add `--category` to restrict results to one category; omit it to search everything.

### Finding related notes

```
python3 src/main.py related "Note Title"
```

Shows the items most related to a given one, ranked by shared-concept score, with the specific shared concepts listed so you can see *why* they're related, not just that they are — and each result shows its category, so a related item from a different category (e.g. a paper related to a note) is clearly labeled, not mistaken for another note.

### Corpus stats

```
python3 src/main.py stats
python3 src/main.py stats --category "News Articles"
```

Item/concept/link counts and the most-connected "hub" items. Without `--category`, also prints a per-category breakdown when more than one category is present. With `--category`, all counts (including links and hubs) are scoped to that category alone.

### Writing backlinks into your own notes

```
python3 src/main.py backlinks --notes-dir /path/to/your/notes
```

Generates a **"See also"** block for each note listing its top related notes as `[[wiki-links]]` (Obsidian-style — link targets are filenames, with the note's title shown as a display alias). By default this is a **dry run**: it prints a unified diff of what would change and writes nothing.

To actually write the changes:

```
python3 src/main.py backlinks --notes-dir /path/to/your/notes --write
```

`--write` requires `--notes-dir` to be a **git repository with a committed, clean working tree**. If it isn't, the command refuses and tells you why (not a git repo / no commits yet / uncommitted changes already present) rather than editing files with no way to review or undo the change. Once you've committed, run `--write` and use `git diff` to review exactly what was inserted, or `git checkout -- .` to revert it. If you understand the risk and want to bypass this (e.g. a scratch folder you don't care about), pass `--skip-git-check`.

Re-running `backlinks --write` is safe and idempotent: each note gets exactly one delimited block (`<!-- connectome:links:start -->` … `<!-- connectome:links:end -->`), which is replaced in place on each run rather than duplicated, and removed automatically if a note no longer has any related notes. If you edit a note directly after indexing it but before running `backlinks --write`, that note is skipped (with a warning) rather than having your edit silently overwritten — re-run `index` first to pick it up.

```
python3 src/main.py backlinks --notes-dir /path/to/your/notes --top 3 --write
```

`--top` controls how many related notes appear per block (default 5). Add `--category` if you're writing backlinks for a category other than the default `"Notes"` — it must match the category that `--notes-dir` was last indexed under. A related item from a *different* category still resolves correctly in the written `[[link]]` (it's looked up across your whole database), even though only the category being written to actually gets its files touched.

### Building the browsable knowledge base

```
python3 src/main.py build
```

Writes a single self-contained `output/index.html`. Open it directly in a browser — no server, no build step, no internet connection required. It includes:
- A search box that live-filters your notes
- A category panel (only shown when more than one category is indexed) — click a category to filter the list to just that one; click again to clear
- A tag cloud of the most common concepts across your corpus (click to filter)
- A note detail view showing the full note text, its category and subcategory, plus its related notes (each labeled with its own category)
- A concept graph (click any node to jump to that note and highlight its connections) — nodes are colored by category, with a legend when more than one category is present

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db PATH` | `connectome.db` in the build folder | SQLite database location |
| `--notes-dir DIR` (index, backlinks) | `sample_notes` | Folder of `.md`/`.txt` files to index / write into |
| `--category NAME` (index, backlinks) | `Notes` | Category to file these items under. `search`/`stats` also accept `--category` but default to unscoped (all categories) |
| `--ai` (index only) | off | Use `ANTHROPIC_API_KEY` (if set) to refine concept extraction and propose cleaner subcategory names via Claude Haiku |
| `--output-dir DIR` (build only) | `output/` in the build folder | Where `index.html` is written |
| `--write` (backlinks only) | off | Actually modify note files (default is dry-run: prints a diff, touches nothing) |
| `--top N` (backlinks only) | 5 | Max related notes listed per See Also block |
| `--skip-git-check` (backlinks only) | off | Allow `--write` even without a clean, committed git baseline (not recommended) |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `build` produces a page with no connections in the graph | Your notes don't share enough vocabulary yet, or `--notes-dir` points at very few/short files | Index more notes, or write a sentence or two connecting related ideas explicitly — shared vocabulary is what drives linking |
| `--ai` flag seems to have no effect | `ANTHROPIC_API_KEY` isn't set, or the API call failed | This is expected, safe behavior — it silently falls back to deterministic extraction. Set the env var to enable it |
| `related` says a note has no related notes | It genuinely doesn't share enough vocabulary with anything else yet | Not a bug — add more notes on similar topics, or rerun after editing the note to include shared terms |
| Re-indexing an unchanged folder still says notes were "removed" | You deleted or renamed a file since the last index | Expected — renamed files are treated as delete + add, since there's no rename detection (see Known Limitations) |
| `backlinks --write` refuses with a git-related error | `--notes-dir` isn't a git repo, has no commits yet, or has uncommitted changes | Run `git init && git add -A && git commit` in your notes folder first, so the backlink edit lands as a clean, revertible commit-sized diff |
| `backlinks --write` says a note was "skipped" | That note's file changed on disk after the last `index` run | Run `index` again, then `backlinks --write`, so the note being written matches what's actually on disk |
| Indexing a second category seems to make my first category's notes disappear from `search`/`stats` | You probably passed the wrong `--category` on the second `index` call, or ran `stats --category X` and are looking at scoped output | Run `stats` with no `--category` to see the full per-category breakdown; `index` scopes its "removed" detection strictly to the category you pass, so a correctly-tagged second `index` run cannot delete the first category's items |
| No cross-category links appear even with multiple categories indexed | The categories genuinely don't share enough vocabulary yet | Not a bug — linking is still driven by shared concepts regardless of category; add a sentence or two using the same terms across items if you expect them to connect |

---

## Known Limitations

- Concept extraction recognizes single words and two-word phrases (e.g. "canada list", "semiconductor capex") — it does not yet form three-word-or-longer phrases, so a run like "research design outline" produces two overlapping two-word phrases rather than one three-word one.
- Renaming a note file is indistinguishable from deleting the old one and adding a new one; the note's link history isn't preserved across a rename.
- Only `.md` and `.txt` files are supported — no PDF, Word, or other formats yet.
- The `--ai` enrichment path could not be exercised against a live Claude API key during this build session (none was available in the build sandbox); it is fully covered by mocked tests and degrades safely, but has not been manually verified against a real API response.
- `index`/`search`/`related`/`stats`/`build` never touch your note files — only `backlinks --write` does, and only under the guardrails described above.
- `backlinks` always appends its block at the end of the file; it doesn't yet know about YAML frontmatter or an existing "Related" section you may have written yourself.
- Renaming a note after running `backlinks --write` leaves stale `[[old-name]]` links in any note that referenced it until you run `backlinks --write` again (same underlying limitation as the no-rename-detection issue above).
- The HTML category filter is single-select, like the existing tag-cloud filter (click one category at a time; click again to clear) — no way to view exactly two of three categories together without also matching the tag/search filters.
- `related`/`export`-style path lookups that don't specify a category (e.g. `backlinks`'s "related item" resolution) pick an arbitrary match if the same relative filename exists in more than one category — a known ambiguity, not a crash.
- Real ingestion for Academic Papers and News Articles (PDF parsing, a live arXiv/PubMed/news feed) wasn't built tonight — `sample_papers/`/`sample_news/` are synthetic demo content you replace with your own `.md`/`.txt` files, same as `sample_notes/`.
- True semantic (embedding-based) linking was investigated and explicitly deferred, not silently skipped: PyPI is reachable in this build environment (confirmed by installing `onnxruntime`), but HuggingFace Hub — the standard source for pretrained embedding model weights — returns 403 here, so there's no way to source real model weights without either committing ~50-100MB of binary weights into this repo permanently or falling back to a much weaker hash-based substitute that wouldn't actually deliver "catches related items with no shared vocabulary." Revisit if a future session has different network access, or if a genuinely self-contained small-embedding PyPI package (weights bundled in the wheel, not fetched separately) turns up.
