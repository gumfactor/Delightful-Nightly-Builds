# Why This? — Star Atlas

> **Date:** 2026-09-21

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day-of-year 264 → `category_index = (264 - 1) % 9 = 2` → Category C — Personal Knowledge Tool. `builds/ideas.md` (read from the most recent open PR branch, `claude/cool-sagan-10kqlj`) had 7 pending Category C rows, none with a numeric rating (R = 0), so `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled 75 (`python3 -c "import random; print(random.randint(1,100))"`) — above the 25% threshold, so the draw missed and selection went to fresh generation. Pool size: 7 pending Category C ideas (#15, #16, #28, #29, #41, #55, #56).

## The Decision

Rather than inventing something disconnected from the existing backlog, fresh generation reviewed the 7 pending Category C rows plus the last 10 builds for topic saturation. Idea #56 ("GitHub Stars Knowledge Library") stood out as the strongest candidate still on the table: it is the only pending Category C idea with a genuinely zero-manual-entry real data source (the user's own GitHub stars, via the already-available `GITHUB_TOKEN`), and its 2026-09-12 note explicitly flagged it as worth building on "a future Category C ... night." Tonight is that night. Built and expanded it into Star Atlas.

## Connection to User Context

PROFILE.md lists "Agentic AI systems and workflows," "AI infrastructure and semiconductors," and "Startup strategy" among the topics the user regularly reads about and rabbit-holes on — exactly the kind of repo someone stars on GitHub and then loses track of. The user also names "Managing many simultaneous projects" and general context loss as recurring friction points. A stars list accumulates silently and becomes useless without structure; Star Atlas turns it into an actual reference library instead of a graveyard.

## Why Tonight

Category rotation put Category C up tonight (2026-09-21). The last three Category C builds — Grant Vault (2026-08-25, mines the user's own grant documents), Promptbook (2026-09-03, mines the user's own Claude Code session transcripts), and Throughline (2026-09-12, syncs the user's own publication/citation record) — established a clear, successful pattern for this category: take a real, already-existing personal data trail and turn it into a zero-manual-entry searchable knowledge base with optional AI enrichment. Star Atlas continues that pattern with a data source (GitHub stars) none of the 10 prior Category C builds have touched.

## What I Hope the User Gets From This

1. A fast way to answer "didn't I star something for this already?" instead of re-Googling or re-discovering a tool from scratch
2. Visibility into what kinds of things he actually stars (via `stats`), which can surface patterns in his own interests he might not have noticed
3. A dashboard he can open on his phone (per PROFILE.md's stated preference for mobile-readable tools) to browse his own curated tool library

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Lab Method / SOP Knowledge Base (backlog #15) | C | Its own 2026-08-16 note flags heavy mechanism overlap with the already-built Protocol Forge (2026-07-19, IRB-compliance rule engine); still true tonight, so passed again. |
| Highlight Vault (backlog #28) | C | Real value, but still lacks a concrete zero-manual-entry data format (no real export file named) — its 2026-08-25 note already flagged this as the open question, and that gap wasn't closed tonight either. |
| Supervision Notebook (backlog #29) | C | Depends on sustained manual per-meeting entry, the same pattern that scored AI Session Context Bridge (2026-06-06) a 3/10 for being "no better than a markdown file." Worth revisiting only with a low-friction capture mechanism. |
| GitHub Gists Snippet Library (new, logged as backlog #69) | C | A real zero-manual-entry angle, but a typical gist corpus is small and sporadic compared to a full stars list. |
| Own-Repo README & Docs Index (new, logged as backlog #70) | C | Real gap, but genuinely useful content search needs a chunking/relevance layer that pushes it past tonight's scope alongside a full sync-and-tag pipeline. |
