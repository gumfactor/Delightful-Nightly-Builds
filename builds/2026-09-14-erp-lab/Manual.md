# Manual — ERP Lab

## What it is

An interactive, single-file-friendly browser trainer for event-related potential (ERP/EEG) methodology and the P300 Concealed Information Test (CIT), a real forensic-neuroscience paradigm. Every statistic on the page is computed live from synthetic EEG data generated in your browser — nothing is precomputed or hardcoded.

## How to run it

Open `index.html` directly in any modern browser (double-click it, or `open index.html` / drag it into a browser tab). No server, no build step, no install required. It also works offline — the only optional network call is the AI-explain panel, and only if you supply your own Anthropic API key.

## Tabs

- **ERP Basics** — averages N synthetic single trials and shows how the measured noise floor shrinks toward the theoretical `noiseSD / √N` prediction as N increases. Drag the sliders to see the effect live.
- **Artifact Rejection** — simulates eye-blink-contaminated trials and shows how peak-to-peak amplitude thresholding cleans the averaged waveform. Adjust the blink rate/amplitude and rejection threshold to see the trade-off between keeping enough trials and keeping clean ones.
- **Frequency Domain** — a synthetic signal mixing a 10 Hz "alpha" oscillation, 60 Hz line noise, and broadband noise, decomposed by a from-scratch FFT. The low-pass filter slider shows how a simple moving average removes the 60 Hz peak while mostly preserving the 10 Hz one.
- **CIT Lab** — the centerpiece. Simulates a Concealed Information Test: "probe" (crime-relevant) vs. "irrelevant" stimulus conditions, with a permutation test on P300-window amplitude determining whether the difference is statistically distinguishable from chance. Toggle "Simulate an innocent suspect" to see the test's real false-positive rate in action — click "Run Permutation Test" repeatedly with the toggle checked and watch it occasionally still report "Detected."
- **Quiz** — 16 questions per attempt: 8 fixed conceptual questions plus 8 freshly generated each time from the same math functions used in the tabs above (so the questions and their correct answers are never hardcoded). Your best score persists in this browser's `localStorage` for the session.

## Optional AI-explain panel (CIT Lab tab)

Paste your own Anthropic API key into the password field and click "Explain These Results" for a plain-English narrative of the current permutation-test output. Leave the field blank and you still get a full deterministic explanation built from the same numbers — no network call is made without a key. The key is never stored (not in `localStorage`, not anywhere) — it lives only in that input field until you reload the page.

## Running the tests

```
npm install
npx playwright test
```

32 Playwright tests cover the math core (FFT correctness against a hand-computed DFT, Parseval's theorem, the SNR √N law, permutation-test null/effect calibration), UI interaction across all 5 tabs, XSS-safety of the AI-explain panel against a hostile mocked API response, zero-network-calls-without-a-key, and a 375px mobile-viewport layout check.

## Known limitations

- All EEG data is synthetic — this is a teaching tool for the statistical methodology, not a real EEG analysis package and not a validated forensic instrument.
- The CIT Lab tab models a single subject, single session. A real CIT/GKT protocol used in practice involves multiple blocks and careful stimulus counterbalancing beyond this build's scope (see `FutureFeatures.md`).
- The AI-explain panel requires the browser to be able to reach `api.anthropic.com` directly; some corporate networks may block this.
