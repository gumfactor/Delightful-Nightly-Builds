# Manual — Maple Press

> **Version:** 1.0 (built 2026-08-17)
> **Complexity:** Ambitious Project

---

## What This Is

Maple Press turns a CSV of Canadian businesses into ready-to-publish editorial copy for The Canada List — a business spotlight, a category gift guide, a "buy Canadian instead" swap piece, or a regional roundup. Every piece is assembled from a deterministic content-structure engine (real eligibility rules, real headline selection, real fact-grounded body text pulled straight from your CSV), so it's fully useful with zero setup. An optional AI polish pass can smooth the prose further if you set `ANTHROPIC_API_KEY`. It reads the same `verdict`/`confidence`/`evidence` columns Provenance and CanFile produce, so their output CSVs work as Maple Press input without any reformatting.

---

## Quick Start

1. `cd builds/2026-08-17-maple-press`
2. Point it at a business CSV (see **CSV Format** below) — the bundled `fixtures/businesses_valid.csv` works for a first try:
   ```bash
   python3 src/main.py generate --csv fixtures/businesses_valid.csv \
     --type gift_guide --category Skincare --tone consumer
   ```
3. The piece prints to the terminal and is saved. List everything you've generated:
   ```bash
   python3 src/main.py list
   ```
4. Browse the whole library visually:
   ```bash
   python3 src/main.py render --out library.html
   ```
   Open `library.html` directly in a browser — no server needed.

---

## How to Use It

### CSV Format

Required columns: `name`, `category`. Optional: `description`, `city`, `province`, `website`. Also optional, and Provenance/CanFile-compatible: `verdict` (`canadian`/`foreign`/`uncertain`), `confidence` (0–1), `evidence` (free text — feeds the "why it's Canadian" line on each business card).

If your CSV has no `verdict` column at all, every business is included and every card carries an "unverified — confirm before publishing" disclaimer. If it does have a `verdict` column, only `verdict == canadian` rows are used by default.

### Piece Types

| Type | Requires | Notes |
|---|---|---|
| `spotlight` | `--business "<exact name>"` | One business, full feature. |
| `gift_guide` | `--category "<name>"`, ≥3 matching businesses | Category roundup. |
| `swap_it` | `--category "<name>"`, ≥2 matching businesses | "Try this instead" framing. |
| `local_spotlight` | `--province "<name>"`, ≥2 matching businesses | Regional feature. |

### Tones and Occasions

Tones: `consumer` (friendly, second-person), `editorial` (journalistic), `social` (short-form, hashtags). `social` is only valid for `spotlight` and `gift_guide` — `swap_it` and `local_spotlight` need the longer forms and will be rejected with a clear error if you try `social` on them.

Occasions (`--occasion`, default `general`): `holiday`, `canada-day`, `back-to-school` swap in occasion-specific headlines and closing lines. This is an explicit flag, not auto-detected from today's date — the tool never behaves differently depending on when you happen to run it.

### Including Unverified Businesses

By default, only `verdict == canadian` businesses are used. Add `--include-unverified` to include everything the category/province selector matches — every unverified business then carries an explicit disclaimer in the generated copy rather than a silent claim of Canadian ownership.

### AI Polish

Add `--ai-polish` with `ANTHROPIC_API_KEY` set in your environment to get a smoother prose rewrite of the deterministic draft (Claude Haiku). Only the assembled draft text is sent — never raw CSV rows or personal data. With no key set, `--ai-polish` is silently ignored (zero network calls) and you still get the complete deterministic draft.

### Managing Your Library

- `list [--type TYPE] [--tone TONE]` — list all generated pieces, or filter.
- `show <id>` — print a stored piece in full.
- `export <id> --format markdown --out piece.md` — write a ready-to-publish Markdown file.
- `export <id> --format html --out piece.html` — write a single-piece HTML file.
- `render --out library.html` — the full searchable/filterable library dashboard.

Every `generate` call creates a new, permanently versioned piece — nothing is ever overwritten, even if you generate the same category twice. The headline picker actively avoids repeating a near-duplicate of a prior draft in the same category.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `maple_press.db` | SQLite database path (created if missing). |
| `ANTHROPIC_API_KEY` (env var) | unset | Required for `--ai-polish`; the tool works fully without it. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `Error: 'gift_guide' requires at least 3 business(es) in the same category; found 2.` | Not enough matching businesses after verdict filtering. | Add more businesses to the CSV, try a different category, or add `--include-unverified` if some were filtered out. |
| `Error: 'social' tone is not valid for 'swap_it'` | `social` is only valid for `spotlight`/`gift_guide`. | Use `--tone consumer` or `--tone editorial` for `swap_it`/`local_spotlight`. |
| `--ai-polish` doesn't seem to do anything | `ANTHROPIC_API_KEY` isn't set. | Export the key in your shell before running, or accept the deterministic draft — it's complete either way. |
| A business is missing from a generated piece | It didn't pass verdict filtering, or its category/province spelling doesn't exactly match your `--category`/`--province` argument (matching is case-insensitive but not fuzzy). | Check the `verdict` column, or `--include-unverified`; check for typos/extra whitespace in the CSV's category/province values. |

---

## Known Limitations

- Headline variety within one (piece type, occasion) pair is bounded by a hand-authored formula bank — see `FutureFeatures.md` for the expansion plan.
- Category/province matching is exact-string (case-insensitive), not fuzzy — "BC" and "British Columbia" are treated as different provinces.
- No image handling — this is a text-copy generator only.
