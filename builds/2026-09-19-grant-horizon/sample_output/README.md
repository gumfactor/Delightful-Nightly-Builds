# Sample Output

`dashboard.html` and `projects_export.csv` in this folder were generated from a
**synthetic fixture**, not a live NIH RePORTER sync.

## Why

This build container's egress proxy blocks direct connectivity to
`api.reporter.nih.gov` (confirmed with a direct connectivity check before any
code was written tonight — the request was denied outright by the sandbox's
network policy, the same build-container constraint documented in
`PROFILE.md` and hit by prior builds such as Dominion Index (2026-09-10)
against Wikidata and Preprint Pulse (2026-09-13) against arXiv). The tool
itself calls the real, public, no-auth NIH RePORTER API — `sync` will fetch
genuine live data once you run it outside this build environment.

## How the sample was generated

`normalize_project()` and the rest of the pipeline (storage, aggregation,
rendering) were run unmodified against 47 hand-generated fixture records
(`random.seed(19)`) shaped exactly like a real NIH RePORTER v2 response —
5 topics (matching `config.json`'s defaults), realistic institution names,
PI names, fiscal years 2020–2026, and award amounts in a realistic
$150k–$750k range. The AI briefing panels use the deterministic fallback
template (no `ANTHROPIC_API_KEY` in this build environment), which is the
same code path the shipped tool falls back to whenever a user runs
`report` without `--ai` or without the key set.

## What was verified against this sample (beyond pytest)

Using the pre-installed headless Chromium via Playwright:
- Dashboard loads with zero console errors other than the Chart.js CDN
  request being genuinely blocked by this container's own network policy,
  and the DOM-table fallback renders correctly in its place (29 fallback
  trend rows, top-institutions fallback table populated)
- Hero stats matched the fixture's true totals exactly
  ($17,878,546.71 across 47 projects, 5 topics)
- Search ("psychopathy" -> 11 matching rows) and column-sort (click
  "Award" -> highest award first) both work
- A dedicated hostile-payload run (`</script><script>...` and
  `<img onerror=...>` injected into a project title, institution name, PI
  name, and AI briefing text) confirmed: zero dialogs, zero page errors,
  zero injected `window.__xss*` globals, exactly the page's own 3
  `<script>` tags present, zero injected `<img>` nodes, and the hostile
  title rendered back as literal inert text in the project table
- Zero horizontal overflow at a 375px mobile viewport

## Running it for real

```bash
cd builds/2026-09-19-grant-horizon
python3 src/main.py sync
python3 src/main.py report            # deterministic briefing
# or, with a key exported:
ANTHROPIC_API_KEY=sk-... python3 src/main.py report --ai
open output/dashboard.html            # or just double-click it
```
