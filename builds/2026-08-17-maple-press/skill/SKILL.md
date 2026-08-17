---
name: maple-press
description: Turn a CSV of Canadian businesses (optionally verdict/confidence/evidence-tagged, e.g. from Provenance/CanFile) into a ready-to-publish editorial piece for The Canada List — a business spotlight, category gift guide, "Canadian swap" piece, or local roundup. Use when the user asks to draft, write, or generate a gift guide, business spotlight, or similar editorial copy for The Canada List, or says something like "turn this business list into an article" or "draft a Canadian gift guide for these businesses."
---

# Maple Press — Canada List Editorial Copy Generator

Wraps the `maple_press` CLI (from `builds/2026-08-17-maple-press/` in the Delightful-Nightly-Builds repo) so a coding session can draft Canada List editorial content without leaving the session.

## When to use this

The user has a CSV of businesses (at minimum `name` and `category` columns; ideally also `description`, `city`, `province`, and Provenance-style `verdict`/`confidence`/`evidence` columns) and wants a structured, factually-grounded first draft of an article rather than a blank page.

## How to run it

1. Confirm the input CSV has at least `name` and `category` columns.
2. From the `builds/2026-08-17-maple-press/` directory, pick the right piece type for what the user wants:
   - One business → `--type spotlight --business "<exact name>"`
   - A category roundup (≥3 businesses in one category) → `--type gift_guide --category "<category>"`
   - A "buy Canadian instead" piece (≥2 businesses in one category) → `--type swap_it --category "<category>"`
   - A regional feature (≥2 businesses in one province) → `--type local_spotlight --province "<province>"`

   ```bash
   python3 src/main.py generate --csv <input.csv> --type gift_guide --category "Skincare" \
     --tone consumer --occasion holiday
   ```

3. Add `--ai-polish` if `ANTHROPIC_API_KEY` is set in the environment and the user wants smoother prose (the deterministic draft is still complete and publishable without it).
4. Every `generate` call is saved permanently — list past drafts with `python3 src/main.py list`, view one with `show <id>`, or export it with `export <id> --format markdown --out piece.md`.
5. To browse the whole library visually, run `python3 src/main.py render --out library.html` and open `library.html` — a single self-contained file, safe to open via `file://`.

## Notes

- `social` tone is only valid for `spotlight` and `gift_guide` — `swap_it` and `local_spotlight` need the longer `consumer`/`editorial` forms. The CLI rejects an invalid combination with a clear error rather than producing a broken piece.
- If the CSV has a `verdict` column, only `verdict == canadian` businesses are used by default. Pass `--include-unverified` to include the rest — every unverified business then carries an explicit "confirm before publishing" disclaimer in the generated copy, never a silent claim.
- Re-running `generate` on the same category never overwrites anything — every call inserts a new, permanently versioned piece, and headline selection actively avoids repeating a near-duplicate of a prior draft in the same category.
