# Manual — Mediation & Moderation Analysis Lab

## Opening the app

No build step, no server. Double-click `index.html` (or open it via `File > Open` in any browser) — it works directly from the `file://` path. Nothing is uploaded anywhere; everything runs locally in the page.

## Mediation Lab tab

1. Adjust the sliders to set the *true* data-generating relationships: how strongly X predicts M (path a), how strongly M predicts Y controlling for X (path b), and the direct effect of X on Y controlling for M (path c′). Adjust noise and sample size too.
2. Optionally type a seed (any text) — the same seed always regenerates the exact same sample, which is useful if you want to reuse a specific example across a lecture or a handout.
3. Click **Generate Sample**. The path diagram updates with the coefficients estimated from that one freshly-drawn sample, and the Results panel shows:
   - The four path estimates with standard errors
   - The indirect effect (a×b) and its 95% bootstrap confidence interval (2000 resamples)
   - The Sobel test (SE, z, p) shown alongside the bootstrap CI for comparison
   - The algebraic identity check (c should equal c′ + a×b, up to rounding)
   - A significance badge based on whether the bootstrap CI excludes zero
4. Click **Explain this in plain English** for a one-paragraph interpretation. Without an API key this is an instant deterministic summary built from the same numbers shown above. If you paste a Claude API key into the field at the bottom of the page, the app calls the Claude API directly from your browser instead — the key is never saved anywhere and is only sent to `api.anthropic.com`.

## Moderation Lab tab

1. Adjust the sliders for the true main effects (b1 for X, b2 for Z) and the true interaction strength (b3). X and Z are mean-centered automatically before the interaction term is formed.
2. Click **Generate Sample**. You get:
   - The full regression table (all four coefficients with SE, and the interaction's p-value)
   - A scatterplot of X vs Y, points colored by the moderator Z, with three simple-slope lines drawn at −1 SD / mean / +1 SD of Z
   - A simple-slopes table with slope, SE, t, and p at each of those three levels
   - The Johnson-Neyman region of significance — the exact moderator value(s) where the X→Y slope's significance flips — both as text and as a colored strip (green = significant, red = not) below the scatterplot
3. **Explain this in plain English** works the same way as in the Mediation tab.

## Quiz tab

Click **Start Quiz** for 16 questions: 8 fixed conceptual questions about mediation/moderation theory, and 8 questions built from a scenario generated fresh at that moment — the correct answer is always derived from the same engine that powers the two lab tabs, never a hardcoded fact. Answer each question to see immediate feedback and an explanation; at the end you get a score and a full review of every question. **Retake Quiz** starts over with a brand-new live scenario.

## Running the tests

From this folder:

```bash
npm install
npx playwright test
```

`playwright.config.js` points at this environment's pre-installed Chromium; on a different machine, remove the `launchOptions.executablePath` override (or point it at your own Chromium/Chrome install) and Playwright will use its own downloaded browser instead.
