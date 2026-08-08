# Why This? — Panel Prep

> **Date:** 2026-08-08

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Day of year 220 → `category_index = (220-1) % 9 = 3` → Category D — Creative / Generative. `builds/ideas.md` (fetched from the current open-PR branch, `claude/cool-sagan-7wrkhd`) held zero `pending` rows tagged Category D, so per Step 2c the lottery was skipped entirely and fresh generation (Step 2d) ran directly — no roll needed.

## The Decision

Five prior Category D builds exist: AI Lecture Builder (2/10 — "a power user replicates this with one prompt"), WeatherSong, Research Question Forge, Bridgework, and Vizstract. The lowest-rated one names its own failure mode precisely: a thin AI-prose wrapper with no deterministic value underneath. Three fresh ideas were drafted for tonight (see Alternatives below); Panel Prep was chosen because its core value — the NIH-rubric completeness/rigor checklist and the persona-weighted deterministic scoring — is fully computable with zero API key, and the optional AI layer only adds narrative richness on top of an already-useful deterministic critique. That is the same shape that Protocol Forge, Bridgework, and Vizstract used successfully, and it directly answers what sank AI Lecture Builder.

## Connection to User Context

PROFILE.md names "Grant writing" verbatim under "Things you do manually that you suspect could be automated or aided by a tool," and separately lists "write grants and manuscripts" as a recurring workflow under Active work projects. No prior build critiques grant-proposal *content* before submission — Protocol Forge (2026-07-19) checks ethics-compliance language, Manuscript Pipeline (2026-08-06) and Impact Ledger (2026-08-05) both operate on work that is already submitted or published, and Citation Vault (2026-07-29) is a reading ledger. The actual pre-submission "will a study section tear this apart" review — arguably the highest-stakes moment in the grant-writing process — has never been built.

## Why Tonight

Category rotation put Category D on the calendar for 2026-08-08. This is the sixth Category D build in the catalog and the first to target grant-proposal content directly (Research Question Forge generates new research questions; Bridgework generates teaching analogies; neither critiques an existing draft against a real scoring rubric).

## What I Hope the User Gets From This

1. A genuine "second pair of eyes" pass on a real grant draft before it goes to a real study section — the deterministic checklist alone catches missing power analyses, absent rigor/reproducibility language, and under-argued significance cases, all common real desk-reject reasons.
2. A concrete, evidence-based way to see whether a revision actually improved a draft, via the version-over-time score trend, rather than relying on gut feel.
3. If they supply an `ANTHROPIC_API_KEY`, three distinctly-voiced narrative critiques that approximate what a real, contentious study section discussion sounds like — useful for genuinely rehearsing pushback, not just getting a score.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| Public-talk hook/title generator for the user's empathy-and-AI outreach work | D | Structurally identical to AI Lecture Builder's failure mode (a single-shot prose generator with no deterministic core); would need the same rubric-plus-fallback shape as Panel Prep to be defensible, and Bridgework already covers the "make research accessible to a public audience" need via analogies. |
| Peer-review-style critique for manuscript drafts (not grants) | D | Manuscript Pipeline (2026-08-06) already owns "manuscript" as a keyword in the catalog for status tracking; layering content-critique onto the same noun risked reading as a near-duplicate. NIH's Significance/Innovation/Approach rubric is also a cleaner, more concrete deterministic scaffold than generic peer-review conventions, which vary by journal and field. |
| Investment-thesis "red team" critique generator (bear-case simulator for a stock thesis) | D | Investing has already appeared once in the last 10 builds (SiliconWatch, 2026-07-27, Category A) and PROFILE.md's stronger, more specifically-named friction points (grant writing, ethics applications) were still completely untouched by any Category D build; chose the domain with zero prior coverage over one with recent coverage. |
