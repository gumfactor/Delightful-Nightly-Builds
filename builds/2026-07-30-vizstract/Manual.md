# Manual — Vizstract

## What it is
A browser tool that turns a study's key details into a downloadable visual-abstract graphic (SVG and PNG) — the kind of figure many journals and grant funders now expect alongside a manuscript or proposal. No design software, no account, no server.

## Running it
Open `index.html` directly in any modern browser (double-click it, or `file:///path/to/builds/2026-07-30-vizstract/index.html`). No build step, no dev server, no internet connection required for the core tool.

## Basic workflow
1. Fill in **Study Details** on the left: title, study design (5 options), population/sample, predictor/manipulation, outcome measured, sample size, effect direction, headline finding, and an optional stat detail (e.g. `p < .05`).
2. Watch the **Preview** update live on the right as you type.
3. Pick a color theme from the swatches under the preview.
4. Click **Download SVG** or **Download PNG** to save the graphic. Both require a title first (validation blocks empty-title exports).
5. Click **Save to Library** to keep the current entry in this browser for later (name it first, or it defaults to the title). Saved entries persist across page reloads.
6. Click **New / Clear Form** to start a fresh entry without losing what's already saved.

## The 5 study-design templates
- **Comparison of Groups** — two groups + what was measured, connected by a comparison icon.
- **Correlational / Relationship** — two variables connected by a directional icon showing the relationship's shape.
- **Process / Timeline / Intervention** — baseline → intervention → outcome, in sequence.
- **Survey / Cross-Sectional** — a central sample linked to a predictor and an outcome.
- **Before-After / Pre-Post** — a large directional arrow between a "before" and "after" state.

Every template is built from the same fields (title, population, predictor, outcome, N, finding, effect direction, stat) — switching templates re-arranges the same data into a different layout, so you can try a few and see which best represents your study.

## Extracting fields from a pasted abstract (optional)
Paste a full study abstract into the **Extract From a Pasted Abstract** box.
- **With an Anthropic API key** (paste it into the key field — it is kept in memory only for this browser tab and is never written to disk or localStorage): Claude Haiku extracts the structured fields and fills the form.
- **Without a key**: a deterministic keyword/regex extractor does its best (looks for patterns like `N = 84`, `effect of X on Y`, `p < .05`, and phrases like "found that" / "results indicated") — no network call is made either way in this path.

Either path only fills fields it's confident about; review and adjust before exporting.

## Your saved library
Everything you save lives in this browser's `localStorage` under the key `vizstract.library.v1` — it does not sync anywhere and is not sent to any server. Clearing your browser's site data for this file will remove it. Use **Load** to bring a saved entry back into the editor, **Delete** to remove it permanently.

## Running the tests
From this folder:
```
npm install
npx playwright test
```
This starts a small local static file server (`test-server.js`, used only for tests — you never need it to use the app) and runs 19 end-to-end tests in headless Chromium.

## Notes
- The generated graphic itself is always on a white/light background, even if your system is in dark mode — that's deliberate, since the graphic is meant to be embedded in a paper, grant PDF, or slide, where a dark background would look wrong. The surrounding page (form, buttons) does follow your system's light/dark preference.
- The icon set is intentionally small (~22 hand-drawn icons) and fixed — there is no image upload, by design, to keep the exported file simple and safe.
