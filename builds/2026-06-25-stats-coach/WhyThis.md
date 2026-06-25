# WhyThis — Stats Coach

## Lottery or Fresh?
Fresh ideas — no Category E (Learning Aid) entries in the backlog.

## Roll
N/A (no lottery draw; pool was empty).

## Pool Size
0 pending Category E ideas.

## Candidates Considered
1. **Stats Coach** (selected) — interactive statistical test advisor with AI-generated explanations
2. **Neuroscience Brain Region Explorer** — interactive SVG brain map with AI explanations of each region
3. **Academic Writing Coach** — paste an academic paragraph, receive AI critique on clarity, hedging language, and APA style

## Why Stats Coach Won
The Qualtrics Survey Data Inspector (9/10) succeeded by solving a specific, real professional workflow with no clean tool equivalent. Stats Coach targets the same user profile — a researcher/professor who regularly fields "which test should I use?" questions from students and junior researchers.

The key differentiators that make this worth building rather than just prompting Claude:
1. **Stateful multi-step form** — accumulates context across inputs before generating; a single prompt requires the user to format all context manually every time
2. **Persistent cache** — same design → instant response; useful as a teaching tool students can use repeatedly without burning API quota
3. **Dual code output** — R and Python snippets together, something the user's students need since some use R (RStudio) and some use Python (scipy/pingouin)
4. **Shareable / deployable** — the user can point students to a running local server instance during a lab meeting or lecture

The AI Lecture Builder (2/10) failed because "a power user replicates this with one prompt." Stats Coach avoids that failure mode: the interactive form, SQLite cache, and dual-language code output are all things a single prompt cannot provide.

Non-winners added to ideas.md: Neuroscience Brain Region Explorer, Academic Writing Coach.

## Idea Brief
No idea brief (fresh idea, not from backlog).

## Category
E — Learning Aid. Decision tree + browser UI satisfies the interactivity requirement.
