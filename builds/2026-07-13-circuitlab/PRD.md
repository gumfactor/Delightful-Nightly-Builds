# PRD — CircuitLab: Affective & Forensic Neuroscience Circuit Trainer

> **Build date:** 2026-07-13
> **Category:** E — Learning Aid
> **Complexity:** Ambitious Project
> **Day of week:** Monday

---

## Goal

An interactive browser-based trainer that teaches the brain regions and functional circuits central to affective and forensic neuroscience (empathy, psychopathy, stress) through a clickable labeled brain diagram, three quiz modes, mastery tracking, and AI-generated case vignettes.

## User Story

As a neuroscience professor who teaches Social Affective Neuroscience and runs a forensic/affective neuroscience lab, I want to drill myself (or hand students) an interactive tool that tests region identification, region function, and multi-region circuit sequencing for the exact constructs my research and courses cover, so that review sessions build genuine recall instead of passive re-reading of slides.

## Scope

### In Scope
- Two clickable SVG brain diagrams: a lateral (surface) view and a medial/subcortical cutaway view, together covering 13 curated regions relevant to empathy, psychopathy, and stress research
- A structured content record per region: name, abbreviation, one-line function, a research-relevance note tied to empathy/psychopathy/stress literature, and its circuit memberships
- Three practice modes:
  1. **Label Mode** — a region is highlighted on the diagram; pick its name from 4 choices
  2. **Function Match Mode** — a function description is shown; click the correct region directly on the diagram
  3. **Circuit Trace Mode** — a named process (e.g. "Fear conditioning & extinction") is shown; click the involved regions on the diagram in the correct order
- 6 curated circuits, each a 3–4 region ordered sequence drawn from the 13 regions
- Local mastery tracking per region (0–3 levels: New → Learning → Reviewing → Mastered) persisted in `localStorage`, with the diagram itself color-coded by mastery level and a stats panel showing per-region and overall progress
- A **Case Vignette Mode**: a short clinical/research scenario is shown and the user identifies the implicated region or circuit from a multiple-choice list, with an explanation on submission
  - Ships with a curated fallback bank of 8 hand-written vignettes (always available, no key required)
  - Optional **AI-generated vignette**: if the user pastes an Anthropic API key into a session-only (never persisted) field, a "Generate New Vignette" button calls Claude Haiku directly from the browser (`anthropic-dangerous-direct-browser-access` header) to produce a fresh vignette + target region + explanation as structured JSON; grading stays local/deterministic against the returned target region
- Reset-progress control and a session summary screen
- Mobile-responsive layout, dark mode, keyboard-accessible controls, `alt`/`aria-label` coverage on interactive SVG regions

### Out of Scope
- Anatomically precise, textbook-grade brain rendering (the diagrams are clean, labeled schematic representations sufficient for teaching purposes, not medical imaging)
- Server-side or multi-user accounts — all state is local to the browser via `localStorage`
- Editing/adding custom regions or circuits through the UI (content is curated and fixed for this build)
- True date-based spaced repetition scheduling (mastery levels are session-driven, not calendar-driven — see FutureFeatures.md)

## Tech Stack

- **Language:** HTML/CSS/JS (vanilla, classic `<script>` tags — no ES modules, no bundler, so it opens directly via `file://`)
- **Framework:** None
- **Dependencies:** `@playwright/test` (dev-only, for tests)
- **Runtime requirement:** Open `index.html` directly in a browser. No install needed to use the tool. `npm install && npx playwright test` to run tests.

## Data Structure

All content lives in `src/data.js` as plain JS objects/arrays loaded before the app script:

```js
REGIONS = {
  amygdala: {
    id: 'amygdala', name: 'Amygdala', abbr: 'Amyg',
    view: 'medial', shape: 'medial-amygdala', // SVG element id
    function: 'Rapid threat/salience detection and fear conditioning.',
    relevance: 'Blunted amygdala reactivity to fearful expressions is one of the most replicated findings in psychopathy research.',
    circuits: ['fear-conditioning', 'hpa-stress'],
  },
  // ... 13 regions total
}

CIRCUITS = {
  'fear-conditioning': {
    id: 'fear-conditioning', name: 'Fear conditioning & extinction',
    sequence: ['amygdala', 'hippocampus', 'vmpfc'],
    description: '...'
  },
  // ... 6 circuits total
}

VIGNETTES = [
  { id: 1, text: '...', targetRegion: 'amygdala', targetCircuit: null, explanation: '...' },
  // ... 8 curated vignettes
]
```

Mastery state persisted in `localStorage` under key `circuitlab_mastery_v1`:
```json
{ "amygdala": 2, "hippocampus": 0, "...": "..." }
```
(0 = New, 1 = Learning, 2 = Reviewing, 3 = Mastered)

Session summary state (last run's score) persisted under `circuitlab_last_session_v1`. No personal data, no credentials, no vignette-answer content is ever persisted or sent anywhere except the direct-to-Anthropic call the user explicitly triggers with their own key.

## Folder Structure

```
builds/2026-07-13-circuitlab/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── index.html
├── package.json
├── package-lock.json
├── playwright.config.js
├── .gitignore
├── src/
│   ├── styles.css
│   ├── data.js
│   ├── mastery-store.js
│   ├── brain-diagram.js
│   ├── quiz-engine.js
│   ├── ai-vignette.js
│   └── app.js
└── tests/
    ├── diagram.spec.js
    ├── quiz-modes.spec.js
    ├── mastery.spec.js
    └── vignette.spec.js
```

## Testing Strategy

- **Framework:** Playwright (`@playwright/test`)
- **Test file location:** `tests/*.spec.js`
- **Run command:** `npx playwright test`
- **What will be tested:**
  - Both diagrams render with all 13 regions clickable and labeled
  - Switching between lateral/medial views and between the three quiz modes plus vignette mode
  - Label Mode: correct answer increases mastery and advances to next question; incorrect answer resets mastery to 0 and shows the correct region
  - Function Match Mode: clicking the right SVG region on the diagram registers correct; clicking the wrong one registers incorrect
  - Circuit Trace Mode: clicking regions out of order is rejected; correct in-order sequence completes the circuit
  - Mastery persists across a page reload via `localStorage` and the diagram color-codes regions accordingly
  - Reset Progress clears `localStorage` and resets all regions to New
  - Vignette Mode without an API key uses only the curated 8-vignette bank and never attempts a network call
  - Vignette Mode "Generate New Vignette" button is disabled/hidden until a key is entered, and the outbound `fetch` call is intercepted/mocked in tests (no live Anthropic API calls in tests)
  - Malformed/empty API key input is handled without a crash
  - Session summary screen shows correct counts after a full run
  - Keyboard navigation (Tab/Enter) reaches and activates at least one region and one answer choice
  - No `console.error` during a full happy-path run through every mode

## Success Criteria

1. All tests pass (zero failures)
2. All 13 regions across both views are clickable, labeled, and show correct function/relevance content on selection
3. All three quiz modes (Label, Function Match, Circuit Trace) function correctly with accurate scoring and mastery updates
4. Mastery state persists across reloads and is visually reflected on the diagram
5. Case Vignette Mode works fully offline with the curated bank, and the optional AI generation path is properly gated behind a user-supplied key with all live calls mocked in tests

---

## Scope Changes

None — full scope as specified above was completed as planned.
