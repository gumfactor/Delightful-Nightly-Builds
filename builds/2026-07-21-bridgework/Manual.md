# Manual — Bridgework

Bridgework generates and permanently accumulates analogies bridging your stress/empathy/psychopathy neuroscience research to everyday domains, for direct reuse in the "Stress and Coping" book and public empathy/AI talks.

## Setup

No installation required beyond Python 3 (standard library only). Optional: `pip install anthropic` is **not** needed — the AI polish call uses `urllib` directly. To enable it, set an environment variable before running:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

Without a key, every command still works fully — analogies are built from deterministic structural templates instead of AI-polished prose.

## Running commands

All commands are run from inside `builds/2026-07-21-bridgework/`:

```bash
python -m src.main <command> [options]
```

### `generate` — create new analogies

```bash
python -m src.main generate --count 5
python -m src.main generate --count 3 --concept allostatic_load
python -m src.main generate --count 1 --domain garden --audience book_chapter
python -m src.main generate --count 3 --no-ai        # skip the AI call even if a key is set
```

Bridgework always prioritizes (concept, domain, audience) combinations you haven't generated yet, so running `generate` repeatedly explores the library rather than repeating itself. Use `taxonomy` (below) to see valid `--concept`/`--domain` ids, and `--audience` accepts `undergrad_lecture`, `public_talk`, or `book_chapter`.

### `list` — browse the library from the terminal

```bash
python -m src.main list
python -m src.main list --concept empathy_fatigue
python -m src.main list --search "stadium"
python -m src.main list --limit 10
```

### `show` — full detail for one entry

```bash
python -m src.main show 12
```

### `export` — Markdown you can paste into the book or a slide deck

```bash
python -m src.main export --id 12
python -m src.main export --all --output all-analogies.md
```

### `render` — the browsable HTML library

```bash
python -m src.main render
```

Writes `data/bridgework.html` (created automatically). Open it directly in any browser — no server needed. Search, filter by subdomain/audience/source, click any card for the full analogy, and use "Copy as Markdown" to grab one for pasting elsewhere.

### `stats` — coverage at a glance

```bash
python -m src.main stats
```

Reports how many of the 291 valid (concept, domain, audience) combinations have been generated so far, broken down by subdomain and by source (template vs. AI).

### `taxonomy` — see every available concept and domain

```bash
python -m src.main taxonomy
```

## The library persists

Every `generate` call adds new rows to `data/bridgework.db` (created on first run) — nothing is ever overwritten, including regenerating the same combination. Run `generate` again another night and the library only grows; `render` and `list` always reflect everything you've ever generated.

## Running tests

```bash
python -m pytest tests/ -v
```
