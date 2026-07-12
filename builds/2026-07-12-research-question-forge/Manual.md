# Manual — Research Question Forge

> **Version:** 1.0 (built 2026-07-12)
> **Complexity:** Ambitious Project

---

## What This Is

A tool that generates candidate research-question and hypothesis skeletons for forensic/affective neuroscience research by combinatorially crossing a curated taxonomy of populations, constructs, outcomes, methods, and theoretical frames drawn from your own named research areas (empathy, psychopathy, stress). Every generated question is checked against compatibility rules so you never get a nonsensical pairing (like an fMRI study proposed on a construct with no plausible neural outcome), scored for novelty against everything you've generated before, optionally polished into grant-ready prose by Claude, and saved into a growing, searchable local library you browse in a dark-mode HTML viewer. Use it when starting a new grant aim, manuscript introduction, or study idea and you want a concrete starting point instead of a blank page.

---

## Quick Start

1. `cd builds/2026-07-12-research-question-forge`
2. `python3 src/main.py generate --count 10` — generates 10 new questions and saves them to `output/forge.db`
3. `python3 src/main.py render` — builds `output/forge.html`
4. Open `output/forge.html` directly in your browser (double-click it, or `file://` the path) — search, filter, and click any row for detail
5. Star the ones worth keeping: `python3 src/main.py star <id>`, then `render` again to see the update reflected

---

## How to Use It

### Generating questions

```
python3 src/main.py generate --count 10
```

Generates up to 10 new, compatibility-valid, non-duplicate question skeletons and saves them to the library. If you request more than the taxonomy can produce without repeating, you'll get however many valid combinations remain.

Add `--seed 42` for reproducible output (same seed + same existing library state = same batch — useful for testing or demoing).

Add `--polish` to send each generated skeleton to Claude for a grant-ready paragraph:

```
ANTHROPIC_API_KEY=sk-ant-... python3 src/main.py generate --count 5 --polish
```

Without an API key (or if the call fails for any reason), `--polish` silently falls back to a clean deterministic template — the tool always produces a usable result.

### Browsing the library

```
python3 src/main.py render
```

Rebuilds `output/forge.html` from everything currently saved. Open it in any browser via `file://` — no server needed. Use the search box to full-text filter by question text, rationale, or tag; use the two dropdowns to filter by testability tag or starred state. Click any row to open the detail panel, which shows the full rationale, novelty score, AI polish (or template fallback) text, and a **Copy as Markdown** button for pasting straight into a grant draft.

### Managing questions

```
python3 src/main.py list                        # print every saved question
python3 src/main.py star 3                       # star question #3
python3 src/main.py star 3 --unstar              # remove the star
python3 src/main.py tag 3 "R01-empathy-aim2"     # attach a project/grant label
python3 src/main.py use 3                        # mark a question as actually used somewhere
python3 src/main.py search cortisol              # full-text search across skeleton/rationale/tag/polish
```

After any of these, run `render` again to refresh the HTML view.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `output/forge.db` | Path to the SQLite library file (global flag, before the subcommand) |
| `--output` (on `render`) | `output/forge.html` | Where the HTML viewer is written |
| `ANTHROPIC_API_KEY` (env var) | unset | When set and `--polish` is passed to `generate`, enables the Claude enrichment pass. Fully optional. |

No other configuration required.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `generate` prints "No new compatible combinations could be generated" | You've already saved every valid combination the taxonomy can produce for the current seed/history | Run without `--seed`, or edit `src/taxonomy.json` to add more populations/constructs/outcomes/methods/frames |
| `forge.html` opens but shows "0 questions" | You ran `render` before ever running `generate`, or pointed `--db`/`--output` at different files across commands | Run `generate` first, then `render` using the same `--db` path each time |
| `--polish` questions still show `ai_source: template` | `ANTHROPIC_API_KEY` isn't set, or the Anthropic API call failed (network, invalid key, rate limit) | Confirm the env var is exported in the shell that runs the command; the tool always falls back cleanly rather than erroring, by design |
| Search box in the HTML viewer returns nothing for a term you know is there | The term only appears in a field the search doesn't index by design | Search covers skeleton text, rationale, tag, and AI polish text — not raw taxonomy IDs |

---

## Known Limitations

- The taxonomy is fixed content (10 populations, 10 constructs, 10 outcomes, 7 methods, 7 frames) authored once at build time — see `FutureFeatures.md` for a planned in-app editor.
- Novelty scoring is a transparent word-overlap heuristic, not semantic similarity — two very differently-worded questions about the same idea won't be flagged as near-duplicates.
- `--polish` makes one Anthropic API call per question in the batch (no batching), so a large `--count --polish` run will be slower and use more API calls than an unpolished one.
