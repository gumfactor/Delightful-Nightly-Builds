# Manual — Citation Vault

> **Version:** 1.0 (built 2026-07-29)
> **Complexity:** Ambitious Project

---

## What This Is

Citation Vault is a local, single-user research reading tracker. Add any paper you encounter — by DOI (looked up via the free Crossref API), by search, or by hand — and it tracks your progress through it (to-read → reading → read → cited), holds your personal notes and tags, nudges you to revisit old reading that's newly relevant, and produces a clean BibTeX bibliography whenever a manuscript or grant needs one. Unlike a topic-scoped discovery feed (Paper Lens, PubMed Research Radar), this is a running personal library of everything you've actually decided to read, across every project at once.

---

## Quick Start

1. `cd builds/2026-07-29-citation-vault/src`
2. Add a paper by DOI: `python3 main.py add 10.1038/s41586-021-03819-2`
3. Or add one by hand: `python3 main.py add --manual --title "My Paper" --authors "Jane Doe"`
4. Move it along: `python3 main.py status 1 reading`
5. See everything: `python3 main.py render --out dashboard.html` and open `dashboard.html` in any browser

---

## How to Use It

### Adding papers

- **By DOI:** `python3 main.py add <doi>` — fetches title, authors, year, journal, and abstract from Crossref.
- **By search:** `python3 main.py add --search "cortisol reactivity forensic"` lists up to 5 candidates; re-run with `--pick N` to add one: `python3 main.py add --search "..." --pick 2`.
- **Manually (no DOI):** `python3 main.py add --manual --title "..." --authors "A, B" --year 2022 --journal "..."` — for book chapters, preprints, or internal reports.

### Tracking status and notes

- `python3 main.py status <id> <to-read|reading|read|cited>`
- `python3 main.py note <id> "your note text"` — appends a timestamped note; a paper can have any number of notes.
- `python3 main.py show <id>` — full detail view including every note.

### Tagging

- `python3 main.py tag <id> tag1,tag2` — sets manual tags (replaces the existing tag set).
- `python3 main.py tag <id> --ai-tag` — adds AI-suggested concept tags from the title/abstract. Uses Claude Haiku if `ANTHROPIC_API_KEY` is set in your environment; otherwise falls back to a deterministic keyword-frequency tagger with zero network calls. Combine both: `python3 main.py tag <id> mytag --ai-tag`.

### Listing and filtering

- `python3 main.py list` — everything, newest first.
- `python3 main.py list --status reading --tag stress --search cortisol` — combine any filters.

### Resurfacing old reading

- `python3 main.py resurface [--days 60]` — lists papers marked `read`/`cited` at least N days ago (default 60) that share a tag with something currently `to-read`/`reading`. Add `--ai` for a one-sentence AI-generated rationale (Claude Haiku, or a deterministic template with no key).

### Exporting a bibliography

- `python3 main.py export bibtex` — prints BibTeX to stdout.
- `python3 main.py export bibtex --status cited --out references.bib` — filter by status/tag and write to a file.

### The dashboard

- `python3 main.py render --out dashboard.html` then open `dashboard.html` in any browser. No server, no build step, no CDN dependency — it's a single static file.
- Four columns (To Read / Reading / Read / Cited), a live search box, a clickable tag cloud/filter, and a click-through detail panel per paper with its full note history and a "Copy BibTeX" button.
- Re-run `render` any time to refresh the dashboard after adding/updating papers — it is not live-updating on its own.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db` | `citation_vault.db` (current directory) | Path to the SQLite database. Pass a different path to keep separate libraries for separate projects. |
| `ANTHROPIC_API_KEY` (env var) | not set | Enables Claude Haiku for `--ai-tag` and `resurface --ai`. Never required — both features work fully offline without it. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `add <doi>` fails with a Crossref error | No network access, or the DOI doesn't exist in Crossref | Verify the DOI resolves at `https://doi.org/<doi>` in a browser; use `add --manual` as a fallback |
| `add --search` returns "No Crossref results" | Query too narrow/specific, or a network block | Try a broader query, or add the paper with `--manual` |
| `tag --ai-tag` doesn't look "smarter" than plain keywords | `ANTHROPIC_API_KEY` isn't set | This is expected — the deterministic fallback is intentionally simple. Set the env var to enable the Claude Haiku pass. |
| `resurface` never shows anything | No settled (`read`/`cited`) paper is both old enough and tag-overlapping with an active one | Lower `--days`, or make sure your `read`/`cited` and `to-read`/`reading` papers actually share a tag |
| BibTeX entry has an odd citation key like `anon2020` | The paper has no listed authors | Add authors via `tag`/manual re-entry, or edit the `.bib` file by hand after export |

---

## Known Limitations

- No PDF ingestion or full-text search — only metadata and your own notes are searchable.
- No import from Zotero/Mendeley/EndNote yet — see FutureFeatures.md.
- `export bibtex` only produces the `@article` entry type; book chapters and conference papers are exported the same way (a minor citation-style inaccuracy, not a data-loss issue).
- The HTML dashboard is a snapshot, not live — re-run `render` after making changes to see them reflected.
- Crossref's free API occasionally lacks an abstract for older or non-open papers; `abstract` will simply be blank in that case, which is expected Crossref behavior, not a bug.
