# Why This Build

## Category and selection path
Day of year 185 → `(185-1) % 9 = 4` → Category **E — Learning Aid**.

`builds/ideas.md` (synced from the most recent open PR, `claude/cool-sagan-fp5h9l`, before deciding) had zero `pending` rows tagged Category E — the backlog only contains A/B/F/G/H entries. Per Step 2c, an empty matching pool skips the lottery entirely and goes straight to fresh idea generation (Step 2d). No roll was made.

## Environment check that shaped the decision
Before generating ideas, I checked whether `ANTHROPIC_API_KEY` is actually present in this session (PROFILE.md and CLAUDE.md both state it's "always set in the build environment"). It is **not set** — only `ANTHROPIC_BASE_URL` is present. `GITHUB_TOKEN` is set. This ruled out any idea whose core differentiating value depends on a live Anthropic API call (e.g., an LLM-literacy trainer with live prompt grading), since a hard dependency on an absent credential would force an abort or a hollowed-out fallback. I deliberately picked an idea with zero AI dependency rather than build something whose main value proposition would be dead on arrival tonight.

## Topic diversity check
Last 10 builds (2026-06-24 → 2026-07-03): AI Lecture Builder, GitHub Developer Activity Explorer, Neurofact, ci-pulse, Project Pulse, GitHub Developer Analytics Dashboard, BIDS Dataset Organizer, PubMed Research Radar, WeatherSong, and Stats Coach (2026-06-25, E — Learning Aid, a research-methods statistical-test advisor with AI-generated code snippets). GitHub-flavored dev-analytics builds are saturated (3 of the last 10) but that's a different category. Stats Coach is the one topic-adjacent build (research methods / statistics), but it solves a different problem (which test to run) than tonight's build (is this study adequately powered, and what N do I need) — different enough to not read as a repeat, and the calibration notes never flag "statistics" as saturated the way "investment" is.

## Candidates considered
1. **Power Lab** (selected) — interactive power/sample-size explorer, sample-size calculator, effect-size converter, and a gamified "guess the power" quiz. No AI dependency; entirely deterministic, testable math.
2. **Bayesian Updating Visualizer** — interactive prior→posterior updating (beta-binomial), a base-rate-fallacy medical-test demo, and a quiz on posterior interpretation. Directly serves the explicit PROFILE.md learning goal "develop advanced Bayesian statistical workflows." A strong runner-up; appended to `builds/ideas.md` for a future night since it deserves its own full session rather than being compressed to fit alongside tonight's other modules.
3. **Statistical Pitfalls Flashcard Deck** (p-hacking, Simpson's paradox, regression to the mean, multiple comparisons) — rejected outright: it's mechanically identical to the existing Spaced Repetition Flashcards build (2026-06-16), which the calibration notes explicitly warn against (redundancy with a tool already in the user's stack scores low). Appended to the backlog as `skipped`-leaning but left `pending` in case a future session wants to fold it into an existing flashcard deck rather than build a new one.

## Why Power Lab wins
It ranks highly against the stated build-value order in PROFILE.md: it is a tool the user can actually use (sample-size sanity checks for grant methods sections and study design — "save real time" and "tools I'll actually use" are the top two ranked outcomes), not just something to look at once. It satisfies the Learning Aid ambition floor with genuine interactivity (live charts, not a static page), avoids the two failure patterns the rating notes call out repeatedly (no visual interface, and value depending on an unavailable dependency), and gives the user's own research-methods teaching a real classroom-usable artifact — a domain (grant writing / study design / research methods teaching) explicitly named in PROFILE.md's "recurring friction points" and "domains where a personal tool would add the most value."

The highest-rated build to date (Qualtrics Survey Data Inspector, 9/10) succeeded by solving a real, specific research-workflow problem with correct math and no gimmicks. Power Lab follows the same shape: real formulas, a real use case (a number you can paste into a grant), tested rigorously against known values — not a toy wrapped around an API call.
