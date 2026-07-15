# Future Features — Confound Hunter

1. **Vignette expansion / editor**: a way to add new vignettes without touching `data.js` directly —
   even a simple JSON import panel would let the deck grow past 30 over time, or let the user author
   scenarios drawn from real methods disasters they've seen in review.
2. **AI-generated bonus rounds**: an optional mode that calls the Anthropic API at runtime (user
   supplies `ANTHROPIC_API_KEY`) to generate fresh, never-seen vignettes on demand, reviewed against
   the same 10-flaw taxonomy — useful once the curated 30 start to feel memorized.
3. **Student/class mode**: export a student's mastery dashboard as a shareable summary (e.g., for a
   TA to check whether a research-methods section understands ceiling effects vs. regression to the
   mean before an exam).
4. **Timed mode**: an optional per-question countdown for an added-pressure variant, with a separate
   leaderboard-style personal-best time tracked alongside accuracy.
5. **Two-flaw vignettes**: a harder "double trouble" mode where a vignette contains two co-occurring
   flaws and the player must identify both — a natural extension once the single-flaw deck is mastered.
6. **Streak-based badges**: unlockable cosmetic badges for milestones (10-question streak, full
   Detective Finals sweep, 100% mastery on a flaw type) to add replay incentive beyond the grade screen.
7. **Import/export progress**: a JSON export/import of the three `localStorage` keys, so progress can
   move between browsers/devices without a backend.
