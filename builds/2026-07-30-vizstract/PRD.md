# PRD — Vizstract: Visual Abstract Generator

## Goal
Turn a study's structured findings into a publication-ready, downloadable visual-abstract graphic (SVG/PNG) in minutes, with no design software required.

## User Story
As a researcher who regularly writes grants and manuscripts, many of which now require or benefit from a graphical/visual abstract, I want to enter my study's key details and get a clean, professional visual abstract I can drop into a submission, a slide, or a social post — without opening a design tool or hiring a designer.

## Scope

### In Scope
- A form for structured study metadata: title, study-design type (5 templates: Comparison of Groups, Correlational/Relationship, Process/Timeline/Intervention, Survey/Cross-Sectional, Before-After/Pre-Post), population/sample description, IV/predictor label, DV/outcome label, sample size (n), headline finding sentence, effect direction (increase / decrease / no change / mixed), optional stat detail string (e.g. "p < .05", "r = .42").
- A deterministic SVG layout engine that picks a template by design type and arranges a title bar, icon boxes, arrow/connector elements, and a finding callout into fixed, non-overlapping regions.
- A text-fitting algorithm: any user string that would overflow its box is wrapped across multiple lines first, then font-size-reduced, then ellipsis-truncated as a last resort — deterministic, no external layout library.
- A hand-authored inline SVG icon library (~20 icons: person, group, brain, arrows in 4 directions, bar chart, line chart, clock, clipboard, magnifier, scale, heart, lightbulb, database, branch/split, checkmark, x-mark, plus/minus, calendar) — no external icon CDN, so the file stays fully self-contained.
- 5 accessible, colorblind-safe color themes, switchable live.
- A live preview that re-renders on every keystroke/selection change.
- Export: download the current visual abstract as a standalone `.svg` file and as a `.png` file (rasterized client-side via Canvas 2D — no server, no external service).
- A local library (localStorage): save a generated abstract under a name, list saved abstracts, reload one into the editor, delete one. Persists across reloads.
- A "New / Clear Form" action that resets the editor to a blank entry, so one session can create and independently save multiple visual abstracts without reloading the page.
- Optional AI assist: paste a full free-text study abstract and extract the structured fields (design type, population, IV/DV, n, headline finding, direction) via a direct browser call to the Anthropic API using a user-supplied, session-only key (kept in memory only, never written to localStorage or disk). When no key is supplied, a deterministic keyword/regex extractor attempts the same extraction with zero network calls, as a best-effort fallback that is always available.
- Ships as a single self-contained `index.html` + classic (non-module) scripts, so it opens directly via `file://` with no build step and no dev server.

### Out of Scope
- Cloud storage, sync, accounts, or sharing links — local-browser-only by design.
- User-uploaded custom icon images — only the built-in icon library, to keep the SVG output simple and safe.
- PDF export (SVG/PNG cover the realistic submission/sharing formats).
- Collaborative/multi-user editing.

## Tech Stack
Vanilla HTML/CSS/JS, classic `<script>` tags (no ES modules, no bundler), native SVG for layout/rendering, native Canvas 2D for PNG rasterization. Optional direct-from-browser call to the Anthropic Messages API (user-supplied key, session-only). Playwright (`@playwright/test` 1.56.1, pinned) for end-to-end tests.

No CDN dependencies are required for the core app (icons and layout are hand-authored and native), so the tool works fully offline except for the opt-in AI extraction call.

## Data Structure

```js
// One saved visual abstract
{
  id: string,            // crypto.randomUUID()
  name: string,           // library display name, user-chosen
  title: string,
  designType: "compare" | "correlate" | "process" | "survey" | "prepost",
  population: string,
  ivLabel: string,
  dvLabel: string,
  sampleSize: string,     // free text so "N = 48" style entries are allowed
  headlineFinding: string,
  effectDirection: "increase" | "decrease" | "none" | "mixed",
  statDetail: string,
  theme: "indigo" | "teal" | "amber" | "crimson" | "slate",
  createdAt: string,      // ISO timestamp, stamped at save time
  updatedAt: string
}
```

Persisted as a JSON array under localStorage key `vizstract.library.v1`.

Template definitions (`src/templates.js`) are declarative JS objects per `designType`: an array of regions (`{x, y, w, h, kind, icon?, textKey?}`) plus arrow connectors between regions. The render engine (`src/render.js`) is generic over any template — it does not special-case a design type by name once the template object is built.

## Folder Structure

```
builds/2026-07-30-vizstract/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── package.json
├── playwright.config.js
├── src/
│   ├── styles.css       — page chrome, form, theme swatches, library list
│   ├── icons.js          — inline SVG path library, keyed by icon name
│   ├── templates.js      — 5 design-type layout templates (regions + connectors)
│   ├── render.js         — SVG generation, text-fitting/wrapping engine
│   ├── extract.js        — deterministic regex/keyword extractor + Anthropic API call
│   ├── library.js        — localStorage CRUD for saved abstracts
│   ├── export.js         — SVG string → downloadable .svg; SVG → Canvas → .png
│   └── app.js            — form wiring, state, live preview updates, event handlers
└── tests/
    └── vizstract.spec.js — Playwright end-to-end suite
```

## Testing Strategy

Playwright drives the real UI in headless Chromium against the built `index.html` (served via a static file server, since Playwright's route-mocking for the AI-extraction test needs `http://` rather than `file://`). Minimum 18 tests, covering:

1. Page loads with all core UI regions present (form, preview, library panel).
2. Editing the title field updates the live SVG preview's title text.
3. Switching design type swaps the rendered template (different region/icon layout).
4. Switching theme changes the SVG's fill colors.
5. A very long title wraps/truncates and never overflows its bounding box (measured via SVG geometry, not a screenshot diff).
6. Sample size and stat detail render correctly formatted inside the finding callout.
7. Each effect direction (increase/decrease/none/mixed) selects the matching directional icon.
8. Saving to the library persists a named entry to localStorage, and it appears in the on-screen library list.
9. Loading a saved library entry restores every form field and re-renders the matching preview.
10. Deleting a library entry removes it from both localStorage and the visible list.
11. SVG download produces well-formed, script-free SVG markup with the expected filename.
12. PNG export produces a non-empty PNG data URL/blob.
13. With no API key supplied, "Extract from abstract" uses the deterministic fallback and makes zero network requests.
14. With a key supplied and the Anthropic endpoint mocked via Playwright route interception, exactly one POST is made and a mocked structured response correctly populates the form fields.
15. A title/finding field containing `<script>...</script>` or raw `&`/`<` renders as inert, escaped text in the preview — never executed, no dialogs, no injected DOM nodes.
16. A reloaded library entry containing the same injection payload also renders inert (persistence path is escaped too, not just the live-typing path).
17. Blank required fields (title) show a validation message and block SVG download until fixed.
18. Two independently saved library entries do not bleed state into each other when loaded back to back.
19. A fresh page load (nothing in localStorage yet) shows sane defaults, not an error.

Run with: `npx playwright test` (from the build folder, after `npm install`).

## Success Criteria

1. All 5 design-type templates render a complete, non-overlapping SVG layout, correctly text-fitted for both minimal and maximal realistic input lengths.
2. A generated visual abstract downloads as both a valid standalone `.svg` and a valid `.png`, each of which opens correctly outside the browser.
3. The local library persists across a full page reload — a saved abstract can be closed out of and reloaded intact, edited, and deleted.
4. AI-assisted field extraction from a pasted abstract works when a key is supplied (verified against a mocked API response) and the deterministic fallback still produces a usable partial result with zero network calls when no key is supplied.
5. All Playwright tests (19) pass with zero failures, including the two script-injection safety tests.

## Idea Brief Traceability
Not applicable — this idea was freshly generated tonight (Category D backlog held zero pending rows). See `WhyThis.md` for the candidate ideas considered and the reasoning for this pick.
