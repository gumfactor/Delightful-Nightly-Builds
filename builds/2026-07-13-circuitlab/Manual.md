# Manual — CircuitLab

> **Version:** 1.0 (built 2026-07-13)
> **Complexity:** Ambitious Project

---

## What This Is

CircuitLab is a self-contained browser trainer for the brain regions and circuits central to affective and forensic neuroscience — the exact constructs behind empathy, psychopathy, and stress research. It combines a clickable, labeled brain diagram (lateral surface + medial subcortical cutaway) with three quiz modes, local mastery tracking, and a case-vignette mode that ties abstract regions to concrete clinical/research scenarios. It's built for review sessions before a lecture, a grant deadline, or just to keep the material sharp.

---

## Quick Start

1. Open `index.html` directly in any modern browser (double-click it, or `file://` path — no server or install needed).
2. Click **Explore** (the default tab) and click around the two brain diagrams to read what each region does.
3. Click **Label Quiz**, **Function Match**, or **Circuit Trace** to start drilling. Click **Case Vignettes** for applied scenarios.
4. Progress is saved automatically in your browser. Click **Reset Progress** any time to start over.

---

## How to Use It

### Explore Mode

Use the **Lateral (Surface) View** / **Medial / Subcortical View** tabs to switch diagrams, then click (or Tab-to and press Enter on) any region to see its name, one-line function, and a note connecting it to empathy/psychopathy/stress research specifically.

### Label Quiz

A region lights up (yellow glow) on one of the two diagrams, shown together. Pick its name from four choices. Correct answers raise that region's mastery level by one step; a wrong answer resets it to New. 13 questions per session (one per region), then a session summary.

### Function Match

The reverse of Label Quiz: you're given a one-line function description and must click the matching region directly on either diagram. Both diagrams are shown at once since the answer could be on either one.

### Circuit Trace

You're given the name of a named circuit (e.g. "Fear conditioning & extinction") and must click its regions **in the correct order** across both diagrams. A wrong click at any point ends that question and reveals the correct sequence with a short explanation of why the regions fire in that order. A correct full sequence raises mastery for every region in that circuit. 6 circuits per session.

### Case Vignettes

A short clinical/research scenario is shown; pick which region it most implicates from four choices, then read the explanation. The mode ships with 8 curated vignettes that always work offline.

**Optional AI-generated vignettes:** paste your own Anthropic API key into the field at the bottom of the Case Vignettes panel and click **Generate New Vignette** to get a fresh, never-repeating scenario written by Claude. The key is held only in the page's memory for that session — it is never written to disk, never sent to `localStorage`, and the only place it is sent is directly to Anthropic's API (`https://api.anthropic.com/v1/messages`) when you click Generate. Close or reload the tab and the key is gone. If you don't have a key or don't enter one, the button stays disabled and the curated bank works exactly the same as always.

### Mastery & Progress

Every region has a mastery level from **New** (grey) → **Learning** (blue) → **Reviewing** (amber) → **Mastered** (green), shown as the region's fill color on the diagram at all times. Progress is stored in your browser's `localStorage` and persists across sessions on the same device/browser. **Reset Progress** clears it completely.

---

## Configuration

No configuration file or environment variables are required to use the tool. The only optional input is the Anthropic API key you may paste into the Case Vignettes panel at runtime.

| Setting | Default | Description |
|---------|---------|--------------|
| Anthropic API key | none | Optional, runtime-only, enables "Generate New Vignette." Get one at console.anthropic.com if you want this feature. |

---

## Running the Tests

```bash
cd builds/2026-07-13-circuitlab
npm install
npx playwright test
```

37 tests across 4 spec files: `tests/diagram.spec.js`, `tests/quiz-modes.spec.js`, `tests/mastery.spec.js`, `tests/vignette.spec.js`. All network calls to Anthropic's API are intercepted with `page.route()` in tests — no live API calls are ever made by the test suite.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Progress resets every time I reopen the page | Browser is in private/incognito mode, or `localStorage` is disabled/cleared on close | Use a normal browsing window, or accept that progress won't persist in that mode |
| "Generate New Vignette" stays disabled | No API key entered, or key field only contains whitespace | Paste a valid Anthropic API key into the field |
| Generate New Vignette fails with an error message | Invalid/expired key, no network access, or Anthropic API is temporarily unavailable | Check the key, check your connection, or just use the curated bank (Next button) instead |
| Diagram regions look slightly crowded on a very small phone screen | The two SVG diagrams are dense with 13 total regions | Rotate to landscape or use a tablet/laptop for quiz modes; regions remain individually tappable at any size since the SVG scales |

---

## Known Limitations

- The brain diagrams are clean, labeled **schematic** representations for teaching purposes, not anatomically precise medical illustrations.
- Mastery is session-driven (correct/incorrect), not calendar-based spaced repetition — there's no "due tomorrow" scheduling yet (see FutureFeatures.md).
- Content (regions, circuits, curated vignettes) is fixed for this build; there's no in-app editor to add your own.
- AI-generated vignettes are not saved anywhere — each one is single-use for that session unless you note it down yourself.
