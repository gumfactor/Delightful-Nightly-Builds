# Manual — Grant Vault

> **Version:** 1.0 (built 2026-08-25)
> **Complexity:** Ambitious Project

---

## What This Is

Grant Vault is a personal, local knowledge base built from your own past grant documents. Point it at a folder of old grant drafts (plain text or Markdown) and it splits them into paragraphs, tags each one with a grant section (Specific Aims, Significance, Innovation, Approach, Broader Impacts, Data Management Plan, Budget Justification), and scores how safely reusable that paragraph is in a *different* future proposal. The next time you start a new grant, search your own library instead of starting from a blank page.

---

## Quick Start

1. Install the one test dependency: `pip install -r requirements.txt`
2. Ingest a folder of your past grant text files: `python3 main.py ingest /path/to/your/grants`
3. Search for reusable language: `python3 main.py search "broader impacts"`
4. Generate a browsable dashboard: `python3 main.py render`
5. Open `grant_vault_dashboard.html` directly in your browser (double-click it, or `open grant_vault_dashboard.html` on macOS)

---

## How to Use It

### `ingest <path>` — build or update your library

Point `ingest` at a single `.txt`/`.md` file or a folder containing several. Each file becomes a "document"; each paragraph within it becomes a "chunk." Re-running `ingest` on the same path is safe and fast — files whose content hasn't changed are skipped automatically, and a changed file's old chunks are replaced with freshly-scored ones.

```
python3 main.py ingest ~/Documents/past-grants
```

Add `--ai` to also generate a one-sentence AI summary and AI-suggested tags per chunk via the Anthropic API (see **AI Enrichment** below). Without `--ai`, everything is fully deterministic and offline.

### `search [query]` — find reusable language

```
python3 main.py search "data management"
python3 main.py search "broader impact" --section "Broader Impacts"
python3 main.py search "" --min-reuse 7
python3 main.py search "translational" --tag stress
```

Results are ranked by how well they match your query, then printed with their section, reusability tier/score, source file, a preview, and tags. Run with no query (`python3 main.py search ""`) to browse everything, sorted by reusability score.

### `stats` — see what's in your library

```
python3 main.py stats
```

Prints document/chunk counts, a breakdown by section and by reusability tier, and your top 10 most common tags.

### `render [--output PATH]` — the visual dashboard

```
python3 main.py render --output grant_vault_dashboard.html
```

Produces a single self-contained HTML file (no server needed — open it directly) with section tabs, a live search box, clickable tag filters, color-coded reusability badges, and a one-click Copy button on every chunk.

### AI Enrichment (optional)

Set `ANTHROPIC_API_KEY` in your environment and pass `--ai` to `ingest` to get an AI-generated one-sentence summary and AI-suggested tags per chunk (via Claude Haiku), in addition to the deterministic section/score/tags every chunk always gets. **Only the chunk text itself — your own already-written grant prose — is sent to the Anthropic API, and only when you explicitly pass `--ai`.** Every other command, and `ingest` without `--ai`, makes zero network calls. If `--ai` is passed without an API key set, Grant Vault prints a warning and continues with deterministic tags only — it never fails the whole run.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `grantvault.db` | SQLite database path (global flag, goes before the subcommand: `python3 main.py --db mydb.db search ...`) |
| `--ai` | off | `ingest`-only flag; enables optional Anthropic API enrichment |
| `--output` | `grant_vault_dashboard.html` | `render`-only flag; where the HTML dashboard is written |
| `--section` | none | `search`-only filter by exact section name |
| `--tag` | none | `search`-only filter by tag (case-insensitive) |
| `--min-reuse` | none | `search`-only filter: minimum reusability score (0–10) |
| `ANTHROPIC_API_KEY` (env var) | not set | Required only when using `--ai` |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: Path not found: ...` | The path passed to `ingest` doesn't exist | Double-check the path; both files and folders are accepted |
| Every chunk classified as "Other" | Your source documents don't use recognizable section headings or keyword language | This is expected for non-grant text; for real grant drafts, adding a heading line (e.g. "Significance") as the first line of a section improves classification accuracy |
| `--ai` warning printed even though you set the key | The key isn't actually exported in the shell running the command | Confirm with `echo $ANTHROPIC_API_KEY`; environment variables set in one terminal session don't carry to another |
| `python -m pytest` reports "No module named pytest" | Some Python environments separate the `pytest` executable from the `python -m` invocation | Run the `pytest` command directly instead: `pytest tests/ -v` (after `pip install -r requirements.txt`) |
| Dashboard opens but looks unstyled | Rare — some very old browsers don't support CSS custom properties | Use a current version of Chrome, Firefox, Safari, or Edge |

---

## Known Limitations

- Only plain text (`.txt`) and Markdown (`.md`) files are ingested — PDF and Word documents need to be exported/copy-pasted to text first
- Section classification and reusability scoring are rule-based heuristics, not a trained model — they work well on grant-style prose but can misjudge unusual writing styles
- Search ranking is simple keyword-overlap, not semantic similarity — searching "funding gap" won't necessarily surface a chunk that only says "unmet need" without sharing a word
- Each chunk is a whole document's own once — there's no cross-document merging of near-identical paragraphs yet (see `FutureFeatures.md`)
