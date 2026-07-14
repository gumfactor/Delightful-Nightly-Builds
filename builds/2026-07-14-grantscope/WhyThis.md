# Why This? — GrantScope

> **Date:** 2026-07-14

---

## How This Idea Was Selected

**Selection method:** Fresh generation.

Tonight's category (day of year 195, `category_index = 5`) is **F — Data Explorer**. Two pending backlog ideas matched Category F: idea #1 (The Canada List CSV Quality Inspector, rating 7/10) and idea #10 (SEC EDGAR Financial History Extractor, rating blank/5 default). Only idea #1 had a numeric rating, so `R = 1` and `lottery_chance = min(75, 25 + 1*2) = 27%`. A random roll of 1–100 came back 71, which is above the 27% threshold, so the fresh-idea path was taken and the lottery pool was not drawn from.

## The Decision

Three fresh Category F candidates were generated (see Alternatives Considered). GrantScope — an NIH RePORTER-backed grant-funding landscape explorer scoped to the user's own research domain — was chosen because it is the only one of the three that pairs a genuinely novel, free/no-auth live data source (no prior build in the catalog has touched NIH RePORTER) with one of PROFILE.md's most concretely named friction points: "grant writing" and "research administration," listed explicitly under "Things you do manually that you suspect could be automated or aided by a tool." The preference prior also weighed in: the highest-rated build in the entire catalog is 2026-06-17's Qualtrics Survey Data Inspector (9/10), a Category F build that turned raw research-adjacent data into a structured, actionable report — the same shape this build follows, applied to a different (funding-landscape) research-support problem instead of data QC.

## Connection to User Context

PROFILE.md names the user's research domain explicitly and repeatedly: "forensic and affective neuroscience," "empathy, psychopathy, and stress research," and courses including "Social Affective Neuroscience." GrantScope's five default saved topics are seeded directly from these named areas rather than generic placeholders. The tool also targets "grant writing" and "research administration," both listed under friction points the user has explicitly flagged as manual and automatable.

## Why Tonight

Category rotation put tonight on F — Data Explorer. The last two Category F builds were 2026-07-05's TrialScope (behavioral/RT data QC) and 2026-06-26's GitHub Developer Activity Explorer; neither touches funding/grant data, so this is a genuinely new topic within the category rather than a repeat. The topic-diversity check across the last 10 builds (2026-07-04 through 2026-07-13) found no saturation in the funding/grants domain and confirmed GitHub-sourced data has already appeared three times recently (Pipeline Pulse, Worklog, Schema Sentinel), which was an additional reason to steer away from another GitHub-data build tonight even though GitHub ideas were on the candidate list.

## What I Hope the User Gets From This

1. A concrete, evidence-backed answer to "who is funding work like mine right now, and through what mechanism" — the kind of landscape scan that normally takes an afternoon of manual NIH RePORTER website searching.
2. A starting point for grant-strategy conversations: which ICs (Institutes/Centers) are most active in this space, which activity codes (R01 vs. R21 vs. K-series) are being used, and roughly what award sizes are typical.
3. A tool that compounds — re-running `sync` periodically keeps the local funding picture current without re-doing the research from scratch each time.

## Alternatives Considered

| Idea | Category | Why Not Chosen |
|------|----------|----------------|
| ClinicalTrials.gov Explorer for forensic/affective-neuroscience-relevant trials | F | Useful for research-landscape awareness, but weaker tie to a named PROFILE.md friction point than the grant-funding angle — "grant writing" and "research administration" are named explicitly, while trial-landscape scanning is not. Added to `builds/ideas.md` as a future candidate. |
| Crossref-backed citation/publication landscape explorer for the user's research domain | F | Solid idea, but overlaps conceptually with the already-built PubMed Research Radar (2026-07-02) and Connectome (2026-07-11) in the "external research feed" space; GrantScope's funding-data angle is more differentiated from existing catalog entries. Added to `builds/ideas.md` as a future candidate. |
| SEC EDGAR Financial History Extractor (backlog idea #10) | F | Pending backlog idea, but investment/finance-adjacent — the preference prior shows investment builds have a mixed track record (two prior investment builds were discarded as redundant with existing tools/each other), and it wasn't selected in tonight's lottery roll (71 > 27% threshold) anyway. |
