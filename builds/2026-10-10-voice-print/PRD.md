# PRD — Voice Print

> **Build date:** 2026-10-10
> **Category:** D — Creative / Generative
> **Complexity:** Ambitious Project
> **Day of week:** Saturday

## Goal

A browser tool that learns your own writing voice from samples you supply, then scores any draft for AI-sounding prose and for drift from your voice, highlights the offending passages, and generates a targeted revision prompt.

## User Story

As a professor and founder who writes papers, course material, blog posts and a book and dislikes prose that sounds AI-generated, I want to paste a draft and see exactly which sentences read as machine-written and how far the draft sits from my own style, so that I can fix them (or hand a precise prompt to Claude) instead of guessing.

## Scope

### In Scope
- Deterministic analyzer (no network, no API): sentence/word tokenizer, stylometric metrics (sentence-length mean/burstiness, type-token ratio, em-dash and semicolon rate, contraction rate, first-person rate, paragraph length, question rate, long-word rate).
- AI-tell detector with located spans: stock vocabulary ("delve", "tapestry", "leverage"...), stock phrases ("it's important to note", "in today's fast-paced"), "not just X, but Y" / "it's not X, it's Y" constructions, transition overuse (Moreover, Furthermore), rule-of-three lists, tidy summary closers, em-dash overuse, uniform sentence rhythm, hedging density.
- Voice profile built from one or more baseline samples: metric means + signature function words + common sentence openers; saved in localStorage, exportable/importable as JSON.
- Draft comparison: per-metric deviation, 0-100 "AI-tell" score, 0-100 "voice match" score (when a profile exists).
- Visual output: highlighted draft with tooltips, sentence-length rhythm bar chart, metric comparison table.
- Revision prompt generator (copy to clipboard) listing flagged passages and the voice targets. The tool itself never sends text anywhere.
- Built-in demo texts (one machine-flavoured, one human-flavoured) generic, no personal data.
- Dark/light mode, mobile-responsive.

### Out of Scope
- Calling any LLM API from the page (privacy: drafts never leave the device).
- Claims of "AI detection" accuracy; this is a style linter, not a classifier.
- File upload formats beyond plain text / markdown paste.

## Tech Stack

- **Language:** HTML/CSS/JS (classic scripts, work from file://)
- **Framework:** None
- **Dependencies:** dev only: @playwright/test
- **Runtime requirement:** Open `index.html` in a browser

## Data Structure

Profile JSON: `{ version:1, name, createdAt, sampleCount, wordCount, metrics:{metric:{mean,sd}}, functionWords:{word:ratePer1k}, openers:{word:share} }`.
Analysis result: `{ metrics, sentences:[{text,start,end,words}], flags:[{start,end,type,label,weight,tip}], aiScore, voiceMatch, deviations }`.
Analyzer exposed as `window.VoicePrint` (also `module.exports` for Node).

## Folder Structure

```
builds/2026-10-10-voice-print/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── package.json
├── playwright.config.js
├── index.html
├── src/
│   ├── analyzer.js     (pure logic)
│   ├── samples.js      (demo texts)
│   ├── app.js          (UI)
│   └── style.css
└── tests/
    ├── analyzer.spec.js  (logic via page.evaluate)
    └── ui.spec.js
```

## Testing Strategy

Playwright. Logic tests call `window.VoicePrint` through `page.evaluate` on the loaded page: tokenizer, each detector (positive and negative cases), score bounds, profile build/merge, voice match ordering (own-style text scores higher than machine text), empty input. UI tests: demo load, highlights rendered, profile save/reload persistence, export JSON, prompt generation, empty-state handling, XSS-safe rendering of `<script>` in a draft.

## Success Criteria

1. Machine-flavoured demo text scores markedly higher AI-tell than human-flavoured demo text.
2. After building a profile from the human sample, a held-out human-style text has a higher voice match than the machine demo.
3. Every flag maps to a highlighted span in the UI with an explanation.
4. Profile persists across reload and round-trips through export/import.
5. 15+ Playwright tests pass; no network calls; draft HTML is escaped.
