# Future Features — Promptbook

1. **Cross-session episode credit.** Currently an episode only looks forward to the next prompt
   in the *same* session, so a fix that lands two prompts later gets no credit for the original
   ask. A future version could track a "topic thread" across a whole session (or even across a
   same-day resumed session) and attribute the eventual commit/test-pass back to the prompt that
   started it.

2. **Prompt similarity clustering.** Group near-duplicate prompts ("fix the failing test",
   "the test is still failing", "fix it") so the library surfaces one representative high-scoring
   version instead of five near-identical low-signal entries.

3. **Per-task-type score calibration.** Right now every task type shares the same scoring
   formula, but a `research` prompt (which may never touch a file or run a test) will always
   score low even when it succeeded perfectly. A type-aware formula (e.g. "did the assistant's
   reply directly answer the question" for research prompts) would be more honest.

4. **A `promote` command.** Let the user hand-mark a prompt as a reusable "template" (optionally
   parameterizing out project-specific details like file paths), building a curated top-tier
   list on top of the automatically-scored raw library.

5. **Team/repo-scoped libraries.** For someone running a lab and supervising students who also
   use Claude Code, an opt-in mode to merge multiple people's local libraries (with explicit
   consent per person) into one shared best-practices prompt bank.

6. **Trend view.** A `stats --since 30d` style view showing whether average prompt score is
   trending up over time — a rough proxy for whether prompting technique is actually improving.

7. **Export to the Claude Code Skill format directly.** Let a high-scoring prompt be exported as
   a ready-made `/skill-name` slash command file, closing the loop from "this worked once" to
   "this is now reusable on demand."
