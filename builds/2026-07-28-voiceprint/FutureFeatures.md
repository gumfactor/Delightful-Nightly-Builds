# Future Features — Voiceprint

1. **`.docx` and Google Docs input.** Most of the user's actual blog/book drafting happens in
   Word or Google Docs, not raw Markdown. Adding a `.docx` reader (via `python-docx`, already a
   common dependency in this ecosystem) would remove the "export to Markdown first" friction that
   currently limits how often this gets used.

2. **Per-project trend dashboard.** `history` currently reports one file at a time. A `dashboard`
   command that renders one HTML page showing every tracked file's score trend side by side (e.g.
   every chapter of the "Stress and Coping" book) would make the SQLite history genuinely more
   useful than a single-file sparkline.

3. **Expandable/community phrase list.** Let the user supply a `--phrases custom.txt` file to add
   their own recurring tics (words they personally overuse) on top of the built-in AI-tell list,
   so the tool learns the user's own writing voice, not just generic AI tells.

4. **Track rewrites, not just scores.** When `--ai` is used, save the suggested rewrites to the
   history database alongside the score, so `history --detail` can show what was suggested last
   time and whether the user actually applied it (compare against the next run's text).

5. **Editor integration.** A lightweight VS Code extension or a pre-commit/pre-push git hook that
   runs Voiceprint against staged `.md` files and warns (without blocking) when a score drops below
   a threshold — turning this from a manual "remember to run it" tool into an ambient one.

6. **Readability cross-check.** Add a standard readability metric (Flesch-Kincaid grade level) next
   to the Human Voice Score — formulaic AI prose and merely-complex prose are different problems,
   and surfacing both prevents conflating "sounds like AI" with "hard to read."

7. **Per-genre calibration.** The penalty weights are tuned for general prose. Academic writing
   legitimately uses more passive voice and hedge words than a blog post; a `--genre academic`
   flag that relaxes those specific thresholds would reduce false positives for manuscript drafts.

8. **Batch summary report.** `batch` currently prints one report per file with no aggregate view.
   A single summary table (file, score, delta since last run, top issue) at the end of a batch run
   would make it useful for reviewing an entire folder of chapters at a glance.
