# Manual — Connectome: Personal Knowledge Graph Builder

> **Version:** 1.1 (built 2026-07-11; `backlinks` command added same day)
> **Complexity:** Ambitious

---

## What This Is

Connectome turns a folder of your own notes (Markdown or plain text) into a searchable, cross-linked local knowledge base. It reads every note, extracts the concepts each one is actually about, and — crucially — figures out which notes are related to each other based on shared ideas, even when they live in completely different files or were written months apart. The result is a browsable HTML page: search your notes, browse by topic, and see (via a concept graph and a "related notes" list) connections you'd otherwise have to remember existed on your own. Everything runs locally — no external service is required for the core feature.

`index`, `search`, `related`, `stats`, and `build` only ever read the files you point them at. The one exception is the optional `backlinks` command, which can write `[[wiki-link]]` "See also" blocks directly into your note files — off by default (dry-run), and gated behind a git safety check when you turn it on. See "Writing backlinks into your own notes" below.

---

## Quick Start

1. `cd` into this build folder.
2. `python3 src/main.py index --notes-dir sample_notes` (or point `--notes-dir` at your own folder of `.md`/`.txt` files).
3. `python3 src/main.py build`
4. Open `output/index.html` in any browser (double-click it, or `file://` the path directly — no server needed).
5. Search, click a tag, click a note, or click a node in the concept graph.

---

## How to Use It

### Indexing your notes

```
python3 src/main.py index --notes-dir /path/to/your/notes
```

Only `.md` and `.txt` files are read. Re-running `index` is safe and fast — unchanged files are skipped (detected by content hash), changed files are re-extracted, and deleted files are removed from the knowledge base along with their links. Run this any time your notes change; there's no background watcher.

Add `--ai` to refine concept extraction with Claude Haiku (only if `ANTHROPIC_API_KEY` is set in your environment):

```
python3 src/main.py --db connectome.db index --notes-dir /path/to/your/notes --ai
```

Without a key, or if the API call fails for any reason, extraction falls back automatically to the built-in deterministic method — nothing breaks either way.

### Searching

```
python3 src/main.py search "some topic"
```

Matches note titles, bodies, and extracted concepts (case-insensitive).

### Finding related notes

```
python3 src/main.py related "Note Title"
```

Shows the notes most related to a given one, ranked by shared-concept score, with the specific shared concepts listed so you can see *why* they're related, not just that they are.

### Corpus stats

```
python3 src/main.py stats
```

Note/concept/link counts and the most-connected "hub" notes in your corpus.

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

`--top` controls how many related notes appear per block (default 5).

### Building the browsable knowledge base

```
python3 src/main.py build
```

Writes a single self-contained `output/index.html`. Open it directly in a browser — no server, no build step, no internet connection required. It includes:
- A search box that live-filters your notes
- A tag cloud of the most common concepts across your corpus (click to filter)
- A note detail view showing the full note text plus its related notes
- A concept graph (click any node to jump to that note and highlight its connections)

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db PATH` | `connectome.db` in the build folder | SQLite database location |
| `--notes-dir DIR` (index only) | `sample_notes` | Folder of `.md`/`.txt` files to index |
| `--ai` (index only) | off | Use `ANTHROPIC_API_KEY` (if set) to refine concept extraction via Claude Haiku |
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

---

## Known Limitations

- Concept extraction is single-word only — multi-word ideas get split into separate tokens rather than recognized as one phrase.
- Renaming a note file is indistinguishable from deleting the old one and adding a new one; the note's link history isn't preserved across a rename.
- Only `.md` and `.txt` files are supported — no PDF, Word, or other formats yet.
- The `--ai` enrichment path could not be exercised against a live Claude API key during this build session (none was available in the build sandbox); it is fully covered by mocked tests and degrades safely, but has not been manually verified against a real API response.
- `index`/`search`/`related`/`stats`/`build` never touch your note files — only `backlinks --write` does, and only under the guardrails described above.
- `backlinks` always appends its block at the end of the file; it doesn't yet know about YAML frontmatter or an existing "Related" section you may have written yourself.
- Renaming a note after running `backlinks --write` leaves stale `[[old-name]]` links in any note that referenced it until you run `backlinks --write` again (same underlying limitation as the no-rename-detection issue above).
