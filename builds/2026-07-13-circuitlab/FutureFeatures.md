# Future Features — CircuitLab

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Timed drill mode** — an optional stopwatch per question in Label/Function/Circuit modes, with a "fastest correct time" tracked per region alongside mastery, for exam-speed drilling.
2. **Print/export study sheet** — a "Print Reference Sheet" button that renders all 13 regions + 6 circuits as a clean, single printable page (function, relevance, circuit membership) for offline review before a lecture.
3. **Keyboard shortcuts for choices** — number keys 1–4 to select a multiple-choice answer in Label/Vignette mode, so a full drill session can be done without touching the mouse.
4. **"Focus weak regions" mode** — a filter on Label/Function Match that only queues regions currently at mastery 0–1, for targeted review instead of the full 13 every time.

## Medium Effort (roughly one nightly build session)

5. **True date-based spaced repetition** — replace the session-driven 0–3 mastery levels with a real Leitner/SM-2 style schedule (next-review date per region stored in localStorage), and a "Due Today" count on load so it behaves like a proper flashcard app.
6. **Custom content packs** — let a JSON file of additional regions/circuits/vignettes be loaded via a file picker, so the same engine could be repointed at a different neuroscience subdomain (e.g. motor circuits) or another course entirely without code changes.
7. **AI-graded free-text vignette answers** — instead of multiple choice, let the user type their clinical reasoning for a vignette and use Claude to grade it against the target region/explanation with structured feedback, closer to how a real qualifying exam works.

## Ambitious Extensions (multi-session effort)

8. **Course/lab integration mode** — import real (de-identified) case material from the user's own forensic neuroscience lab or "Social Affective Neuroscience" course slides as additional vignettes, turning CircuitLab into a genuine exam-prep companion tied to the actual syllabus rather than generic curated content.
9. **Multi-user classroom mode** — a lightweight shared-nothing "class code" system (still no backend — e.g. exported/imported JSON progress files) so the tool could be handed to students for a homework assignment with instructor-visible aggregate mastery stats.

---

## Possible Integration Points

CircuitLab doesn't currently connect to anything else in `builds/index.md`, but its content-pack architecture (regions/circuits/vignettes as plain data) is a natural template for the "Course Concept Atlas" and "Metaphor Machine" ideas already sitting in `builds/ideas.md` — both could reuse the mastery-tracking and quiz-mode engine built here rather than starting from scratch.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Mastery decays only on wrong answers, never on time — a region "mastered" once could go untouched forever and still show green | Add the date-based spaced-repetition scheduler from Quick Win #5 |
| The medial-view subcortical cluster (amygdala/hypothalamus/hippocampus) is visually tight even after rebalancing | A dedicated zoomed-in "deep structures" inset view would give more room without cluttering the main diagram |
| No way to review *why* an answer was wrong after leaving the feedback screen | A session history log (last N answers with correct/incorrect) accessible from the stats panel |
