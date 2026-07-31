# Future Features — Signal Detection Lab

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **CSV export of quiz history** — Add a "Download History" button on the Scenario Quiz tab that serializes `localStorage`'s `sdtLabQuizState` (overall + per-scenario attempts/correct) to a CSV file via a client-side `Blob` download, useful for tracking a class's aggregate quiz performance across a term.
2. **Rating-scale toggle on the calculator** — Add a second input mode alongside raw counts: paste a confidence-rating response distribution (e.g., 1–6 "sure no" to "sure yes") and derive multiple (FA, hit) operating points at once, plotting them directly on the ROC curve instead of the single-criterion sweep.
3. **Copy-as-citation button** — On the Calculator tab, add a "Copy APA-style sentence" button that formats the current d'/c/A'/B'' results into a ready-to-paste methods-section sentence (e.g., "Sensitivity was d′ = 1.34 (hit rate = 69.7%, false-alarm rate = 20.5%), with a slightly conservative response criterion (c = 0.16)...").
4. **Keyboard-accessible criterion control** — The Explainer tab's criterion line currently only responds to mouse drag/click; add arrow-key nudging when the canvas has focus, for accessibility and non-mouse users.

## Medium Effort (roughly one nightly build session)

5. **Unequal-variance Gaussian model toggle** — Add a second SDT model where the signal distribution's standard deviation is a free parameter (not fixed at 1), which changes the shape of the ROC curve from symmetric to asymmetric — the more realistic model for many real recognition-memory studies, and a natural progression from tonight's equal-variance-only scope.
6. **Batch CSV import for the Calculator** — Accept a CSV of many participants' or many conditions' hit/miss/FA/CR counts, compute d'/c for each row, and render a sortable results table plus a scatterplot of all operating points on one ROC space — turns the single-case calculator into a real study-analysis tool.
7. **Rating-scale (multi-point) ROC fitting** — Given a set of empirical (FA, hit) pairs from confidence ratings, fit the maximum-likelihood equal-variance ROC curve to them (rather than only the single-criterion analytic sweep) and report the fitted d_a alongside a goodness-of-fit statistic.

## Ambitious Extensions (multi-session effort)

8. **Course-mode assignment builder** — A companion "instructor view" where scenarios can be authored, grouped into an assignment, and shared as a link students open; aggregate (anonymized, no personal data) class performance is stored locally and exportable — would turn this from a personal trainer into an actual teaching tool deployable in the Social Affective Neuroscience or AI Applications for Psychologists courses.
9. **Meta-d' / metacognitive sensitivity module** — Extend the model to include confidence-rating-based meta-d' (Maniscalco & Lau, 2012), the standard measure of metacognitive accuracy in perceptual-decision research — a natural fit for a forensic/affective neuroscience lab studying self-monitoring in psychopathic traits.

---

## Possible Integration Points

- **CircuitLab** (2026-07-13) — both are browser-based interactive trainers with Canvas 2D visualizations and a Leitner/score-tracking pattern; a shared "neuroscience course toolkit" landing page linking CircuitLab, Bayes Lab, Power Lab, and this build would make the growing set of teaching tools easier to find and use together in a course.
- **Bayes Lab** (2026-07-22) — both compute a threshold-free summary statistic (AUC here, Bayes factor there) alongside a classical/parametric counterpart; a future build could combine them into a single "research methods toolkit" tab-of-tabs if the user wants one consolidated reference tool instead of several standalone files.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Only the equal-variance Gaussian SDT model is implemented; real recognition-memory data is often better fit by an unequal-variance model, which produces a curved-rather-than-symmetric zROC | Add the unequal-variance model as a togglable second mode (Future Feature #5) |
| The Explainer tab's criterion drag only responds to mouse input, not touch or keyboard | Add touch event handlers and arrow-key support for full accessibility |
| The 6 scenario-quiz cases are static and hand-authored; repeated quiz sessions will eventually exhaust their novelty | The AI-generated practice scenario path already provides unlimited fresh scenarios when a key is supplied — document this more prominently in the UI as the "unlimited practice" path |
| Quiz scoring only tracks aggregate correct/attempts per scenario, not which specific sub-answer (bucket vs. bias) was wrong | Split `byScenario` tracking into separate bucket-accuracy and bias-accuracy counters for more actionable feedback |
