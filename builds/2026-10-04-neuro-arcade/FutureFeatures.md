# Future Features — Neuro Arcade

1. Add Iowa Gambling Task and a digit-span task (forward/backward), so the arcade covers decision-making under uncertainty and short-term memory.
2. Use `event.timeStamp` from keydown and the rAF timestamp for onset to remove one source of timing jitter, and add a calibration screen measuring display refresh and input latency.
3. Optional Claude debrief (runtime `ANTHROPIC_API_KEY`) that turns a class CSV into a plain-language discussion handout. It must send only aggregated, de-identified numbers.
4. Class mode: a single shareable URL with a session code so students' CSVs land in one place (for example a Firebase collection) instead of manual import.
5. Bayesian summary of the pooled data (posterior of the Stroop interference effect per group) exported as R-ready CSV or a ready-made Rmd.
6. Psychopathy/empathy-relevant social tasks (dictator game, empathy-for-pain rating) to match the lab's research areas.
7. Adaptive n-back (1-back up to 4-back) with level changes based on d′.
8. PWA manifest and service worker so it installs on a phone and works offline in a lecture hall.
