# Manual — Provenance

Batch Canadian-ownership classifier for The Canada List's business submission pipeline.

## Quick Start

```bash
cd builds/2026-08-15-provenance
python3 -m pytest tests/ -v                 # optional: confirm the suite passes on your machine
python3 -m src.cli classify businesses.csv --out enriched.csv
```

Your CSV needs one required column, `name`. Optional `website` and any other columns pass through untouched to the output. See `tests/fixtures/sample_businesses.csv` for the minimal shape.

Requires a real internet connection to `www.wikidata.org` — this build's own container blocks that host, which is expected (see `PRD.md`'s "Success Criteria"); run it from your own machine or CI environment where Wikidata is reachable.

## Commands

### `classify <input.csv>`

Resolves every business in the CSV against Wikidata, classifies it, and writes an enriched CSV.

| Flag | Default | Meaning |
|---|---|---|
| `--out PATH` | `<input>.enriched.csv` | Output CSV path |
| `--db PATH` | `provenance.db` | SQLite cache/history file (created if missing) |
| `--refresh` | off | Ignore the cache and re-resolve every row from Wikidata |
| `--ai-enrich` | off | Add a one-sentence Claude Haiku note to `uncertain` rows (requires `ANTHROPIC_API_KEY`) |
| `--render PATH` | — | Also write a self-contained dark-mode HTML batch report |

Output columns: every input column, plus `verdict` (`canadian`/`foreign`/`uncertain`), `confidence` (0–1), `evidence` (plain-English rationale), `wikidata_qid`, and `ai_note`.

Re-running `classify` on the same CSV is fast and free of duplicate Wikidata traffic — already-resolved businesses are served from the local cache. Pass `--refresh` when you want a genuine re-check (e.g. after a company's Wikidata entry has plausibly changed).

### `history <business name>`

Prints every resolution version ever recorded for a business, oldest first — useful for seeing how (or whether) a verdict has changed over repeated runs.

```bash
python3 -m src.cli history "Shopify Inc."
```

## Using the AI enrichment layer

Set `ANTHROPIC_API_KEY` in your shell before running with `--ai-enrich`:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python3 -m src.cli classify businesses.csv --ai-enrich --render report.html
```

Without a key, `--ai-enrich` is a no-op — every `ai_note` column is left blank and zero calls are made to the Anthropic API. The AI layer never changes a verdict; it only adds a plain-English sentence explaining an `uncertain` classification, generated from the same evidence the deterministic rule engine already computed.

## How the rule engine works

For each business, the tool resolves (via free, no-auth Wikidata lookups):

1. The business's own registered country (property `P17`)
2. Its headquarters location's country (`P159`, one hop)
3. Its parent organization's country (`P749`, one hop)
4. Its owning entity's country (`P127`, one hop)

A direct `P17` match to Canada is the highest-confidence signal (0.95). Falling back to headquarters, then parent, then owner drops confidence at each tier, since each is one inferential hop further from a direct ownership claim. Any conflict between two resolved signals (e.g. Canadian `P17` but a foreign parent organization) always lands as `uncertain` rather than picking a side — the tool is deliberately conservative about calling something definitively Canadian or foreign when the evidence disagrees with itself.

A business Wikidata has never heard of, or one with no resolvable claims at all, comes back `uncertain` with confidence `0.0` — an honest "we don't know," not a guess.

## Companion Skill

`skill/SKILL.md` wraps this CLI as a Claude Code Skill. Copy the `skill/` folder's contents into `.claude/skills/provenance/` in a repo where you're working on Canada List content, and a session can invoke it on a CSV you've just produced ("classify this batch of businesses for Canadian ownership") without leaving the coding session.

## Troubleshooting

- **Every row comes back `uncertain` with confidence `0.0`:** most likely Wikidata is unreachable from wherever you're running the tool (firewall, proxy, or — if you're running this inside a build/CI container — an egress policy blocking `wikidata.org`). The tool degrades honestly rather than crashing or fabricating a verdict; check connectivity and re-run with `--refresh`.
- **A business you know is on Wikidata still comes back `uncertain`:** Wikidata's entity search is name-matching, not fuzzy — try the business's exact legal or common name as it appears on its Wikidata page.
- **`classify` says "Input CSV must have a 'name' column":** the header row's first matching column must be literally `name` (case-sensitive); rename your CSV's business-name column.

## Running Tests

```bash
python3 -m pytest tests/ -v
```

51 tests, all mocking any Wikidata/Anthropic network call — the suite makes zero live network requests and runs the same with or without an internet connection.
