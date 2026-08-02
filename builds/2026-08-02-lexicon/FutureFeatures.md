# Future Features — Lexicon

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **Guess history replay animation** — Animate tile flips row-by-row on submit (CSS transform + delayed class application) instead of the instant color snap, matching the feel of the game this mechanic is drawn from.
2. **Keyboard shortcut hints** — A small "?" button showing physical-keyboard usage (type letters, Enter to submit, Backspace to delete) for first-time users who don't notice the on-screen keyboard is clickable.
3. **Copy-to-clipboard button** — Add a one-click "Copy" button next to the share-text block instead of requiring manual text selection.

## Medium Effort (roughly one nightly build session)

4. **Word bank expansion + rotation warning** — Grow the bank past 48 words (e.g. to 90+, one per category) and add a small in-app note when the cycle is about to repeat, so returning daily players know when "new" words will resume.
5. **Difficulty tiers** — Tag each word bank entry with a difficulty level (common term vs. specialist jargon) and let daily puzzles alternate tiers by weekday, or let practice mode filter by difficulty.
6. **Cross-domain "mixed" daily mode** — A second daily puzzle track that draws from all four categories in rotation (Mon=neuro, Tue=stats, etc.) instead of one continuous 48-word cycle, so a given weekday always trains the same domain.

## Ambitious Extensions (multi-session effort)

7. **AI-generated word bank growth** — Use the Anthropic API (with the user's own key, same session-only pattern as the bonus hint) to propose new candidate words + clues for a domain, with the user reviewing and approving additions before they're committed to `words.js` — turning the fixed 48-word bank into a growable, curated one without needing another full nightly build session to hand-author more entries.
8. **Personal vocabulary import** — Let the user paste in their own glossary (e.g. from lecture notes, a paper's terminology section, or The Canada List's own domain jargon) and generate a custom practice category from it, extending the game beyond the four built-in domains to whatever the user is currently studying or building.

---

## Possible Integration Points

- **Voiceprint (2026-07-28)** and **Connectome (2026-07-11)** both already parse the user's own writing/notes for patterns — a future build could feed Lexicon's "personal vocabulary import" idea (above) directly from a Connectome-indexed note corpus, turning any indexed knowledge base into an automatically generated practice category.
- **CircuitLab (2026-07-13)** and **Bayes Lab / Signal Detection Lab (2026-07-22, 2026-07-31)** already use the direct-browser Anthropic API call pattern with a session-only key — the AI word-bank-growth idea (above) would reuse that exact integration shape rather than inventing a new one.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Fixed 48-word bank means the daily cycle repeats every 48 days | Word bank expansion (Future Feature #4) |
| No way to review past daily words you've already solved, beyond the raw stats counts | Add a small history view listing each past daily date, word, and result |
| AI bonus hint is single-shot with no retry UI if the request fails for a transient reason (network blip, rate limit) | Add a visible retry button instead of silently falling back to the deterministic hint on every failure |
