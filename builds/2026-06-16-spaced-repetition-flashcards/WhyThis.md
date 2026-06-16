# WhyThis — Spaced Repetition Flashcards

## Tonight's Category

**E — Learning Aid** (day 167 of year, category_index = (167−1) % 9 = 4)
Category E has never been built in this system.

## Lottery Result

**Fresh ideas** — no E-category entries in `builds/ideas.md` backlog. Went straight to fresh idea generation.

## Candidate Ideas Generated

1. **SM-2 Spaced Repetition Flashcard Engine** ← selected
   Pre-built decks on Bayesian statistics, Python research patterns, and Git workflows — directly targeting the user's stated learning goals. SM-2 algorithm is testable, non-trivial, and genuinely useful (proven to improve long-term retention).

2. **Interactive Git Decision Tree Reference**
   A visual branching guide to git workflows organized by real-world scenario ("I need to undo a commit", "I need to save work before switching branches"). Decision tree UI leading to exact commands with explanations. Added to `ideas.md` as ID 12.

3. **Python Research Cookbook** (searchable snippet library)
   Filterable, copy-on-click code snippet reference for common Python patterns in research: data loading, pandas operations, scipy stats, matplotlib, pathlib, logging. Added to `ideas.md` as ID 13.

## Why I Picked the Flashcard Engine

The SM-2 spaced repetition algorithm is empirically the most effective way to memorize structured knowledge — it surfaces cards you're weakest on most frequently and extends intervals for cards you know well. Three specific properties make this the strongest idea for this user tonight:

1. **Directly targets stated learning goals**: PROFILE.md lists "Bayesian statistical workflows", "Git/GitHub proficiency", and "Python developer skills" as explicit learning goals. The three pre-built decks map exactly to these.

2. **Daily utility on a phone**: The user reviews builds on their phone in the morning. A 5-minute flashcard session during a commute or coffee break costs nothing and compounds over weeks into real knowledge. The mobile-first dark UI design serves this directly.

3. **Ships immediately useful**: Unlike tools that require data entry or configuration, the flashcard engine ships with 50 pre-written cards covering real content the user needs. No setup required — open the file, start learning.

4. **Non-trivial, testable logic**: The SM-2 algorithm is interesting to implement correctly (EF adjustments, interval progression, date arithmetic) and produces clearly verifiable test cases. This is not a trivial CRUD build.

5. **No external dependencies**: Single HTML file, localStorage, no network required. No API keys, no cloud services, no maintenance overhead.

## Non-Winners Added to ideas.md

- ID 12: Interactive Git Decision Tree Reference (E, ambitious)
- ID 13: Python Research Cookbook — Searchable Snippet Library (E, focused)
