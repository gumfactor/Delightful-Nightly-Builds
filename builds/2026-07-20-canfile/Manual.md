# Manual — CanFile: Canadian Ownership Knowledge Cards

> **Version:** 1.0 (built 2026-07-20)
> **Complexity:** Ambitious Project

---

## What This Is

CanFile is a local research tool for the exact question The Canada List asks about every business it considers listing: is this company actually Canadian-owned? Give it a company name and it queries Wikidata for structured ownership facts (country of registration, headquarters, parent organization, owned-by relationships), pulls a Wikipedia summary, and applies a transparent rule engine to produce a confidence-rated verdict — Canadian-owned, foreign-owned, uncertain, or insufficient data — with every source cited. Every lookup is saved as a new, timestamped version of that company's knowledge card, so you can see how an assessment (or the underlying Wikidata data) has changed since the last time you checked. An optional Claude pass turns the same facts into a better-written paragraph, but the tool is fully functional with zero API keys.

---

## Quick Start

1. `cd builds/2026-07-20-canfile`
2. (Optional) `pip install -r requirements.txt` — only needed for `pytest` or the optional Claude enrichment; core functionality is stdlib-only.
3. `python3 src/main.py add "Tim Hortons"` — looks up the company and prints its new knowledge card.
4. `python3 src/main.py export-html` — writes `canfile_report.html`; open it in any browser.
5. `python3 src/main.py list` / `show "Tim Hortons"` / `search canada` to browse what you've collected.

---

## How to Use It

### `add <company>` — look up and store a new card version

```
python3 src/main.py add "Tim Hortons"
```

Searches Wikidata, fetches ownership-related claims, resolves one hop of parent/owner country, fetches a Wikipedia summary, and stores a new version of the card. If `ANTHROPIC_API_KEY` is set in your shell (or passed via `--api-key`), the printed assessment is a Claude-written paragraph over the same facts; otherwise you get the deterministic rule-engine text. Running `add` again for the same company **adds a new version** rather than overwriting — useful for re-checking a company months later.

### `show <company>` — full version history

```
python3 src/main.py show "Tim Hortons"
```

Prints every stored version for that company, oldest first.

### `list` — latest card per company

```
python3 src/main.py list
```

### `search <term>` — search by name or assessment text

```
python3 src/main.py search "foreign"
```

### `export-html [output.html]` — searchable/filterable report

```
python3 src/main.py export-html
```

Writes a self-contained dark-mode HTML file (default `canfile_report.html`) with a search box, a verdict filter dropdown, confidence badges, cited sources, and an expandable version-history panel per card. No server or build step needed — just open the file in a browser.

### Custom database location

All commands accept `--db path/to/file.db` (before the subcommand) if you want to keep separate CanFile databases for different projects. Default is `canfile.db` in the current directory.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ANTHROPIC_API_KEY` (env var) | unset | If set, `add` uses Claude Haiku to write a richer plain-English assessment of the same rule-engine facts. Fully optional. |
| `--api-key` (CLI flag on `add`) | none | Overrides the `ANTHROPIC_API_KEY` env var for a single call. |
| `--db` (CLI flag, before subcommand) | `canfile.db` | Path to the SQLite database file. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: Wikidata request failed: ...403 Forbidden...` | You're running inside a restricted network (e.g. a CI/build sandbox) that blocks `wikidata.org` | Run CanFile on a normal machine with unrestricted internet access — Wikidata and Wikipedia are free, public, no-auth APIs and work from any regular connection. |
| `No Wikidata entity found for "..."` | The company has no Wikidata page, or the name doesn't match closely enough | Try the company's more formal/legal name, or the name of its Wikipedia article if you know it. |
| Assessment says `insufficient-data` / `low` confidence | Wikidata has no country or ownership claims recorded for that entity | This is an honest signal, not a bug — treat it as "needs manual research," not "foreign" or "Canadian." |
| Claude enrichment doesn't seem to be running | `ANTHROPIC_API_KEY` isn't set, or the API call failed silently | Check `echo $ANTHROPIC_API_KEY`; a failed/missing key always falls back to the deterministic text rather than erroring, by design. |

---

## Known Limitations

- Resolves only one hop of parent/owner ownership (a Canadian brand owned by a foreign-owned holding company that is itself owned by a Canadian parent would currently be flagged foreign-owned at the first hop). See `FutureFeatures.md`.
- Relies on Wikidata's `country` (P17) property, which reflects legal/incorporation jurisdiction — this can differ from genuine beneficial ownership in edge cases (shell companies, dual-listed entities).
- No disambiguation prompt when a company name matches multiple Wikidata entities; the top search result is used.
- Requires the company to have a Wikidata entry; very small or private Canadian businesses often won't.
