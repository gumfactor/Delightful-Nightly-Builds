# Why This Build

## Selection path

Tonight's category (day-of-year 204, index 5) is **F — Data Explorer**. The `builds/ideas.md` backlog had 4 pending Category F rows: #1 (Canada List CSV Quality Inspector, rated 7), #10 (SEC EDGAR Financial History Extractor, unrated), #19 (ClinicalTrials.gov Explorer, unrated), #20 (Citation & Publication Landscape Explorer, unrated). With R=1 rated idea, `lottery_chance = min(75, 25 + 1*2) = 27%`. Rolled 86/100 — above the threshold, so the lottery did not fire and I moved to fresh-idea generation per Step 2d, rather than an automatic draw.

## Candidates considered

1. **Canada List CSV Quality Inspector** (built) — a rule-engine QC pass over a business-directory CSV export: structural/format/encoding validation, exact + near-duplicate detection, cleaned CSV with per-row flags and a keep/review/drop recommendation, plus an optional Claude Haiku layer to confirm ambiguous near-duplicates and suggest canonical category mappings.
2. **ClinicalTrials.gov Explorer** (backlog #19) — a data explorer over the free ClinicalTrials.gov API v2, scoped to forensic/affective-neuroscience-relevant trials.
3. **SEC EDGAR Financial History Extractor** (backlog #10) — pulls 5 years of financial statement data for a ticker list via SEC EDGAR's free API.

## Why #1 won

- **Directly named friction point.** PROFILE.md lists "The Canada List ingestion and quality control pipeline" verbatim under "Things you do manually that you suspect could be automated or aided by a tool." Neither candidate 2 nor 3 maps to a named friction point as directly — ClinicalTrials.gov is closer to "research-landscape awareness" (a nice-to-have already partially covered by GrantScope/PubMed Research Radar), and SEC EDGAR overlaps with the investment domain, which the last 10 builds already show is not a priority right now.
- **The Canada List has zero prior QC-specific builds.** CanFile (2026-07-20) targeted Canadian-ownership *lookup* for a single company; this build targets *batch ingestion quality control*, a different stage of the same real, active, named project — genuinely new ground, not a re-tread.
- **Proven shape, new domain.** The 2026-06-17 Qualtrics Survey Data Inspector (CSV in → rule-based QC report + flagged/cleaned CSV out) is the highest-rated build in the catalog at 9/10. This build transplants that exact proven architecture — terminal + JSON + HTML report, a flags column appended to a cleaned CSV — onto a different real dataset shape (business directory rows instead of survey exports), rather than inventing an unproven pattern.
- **Addresses the backlog's own stated concern.** Backlog #1's rating note (7/10) flagged "unclear what role Playwright plays here vs. a pure Python validator." STANDARDS.md's ambition floor for Category F only requires a visual output layer, not a browser app — this build resolves that by rendering a self-contained HTML dashboard from Python (the Qualtrics/TrialScope pattern), with no Playwright dependency and no interactive-upload shell that would add complexity without adding capability.
- **Real AI-differentiating layer.** Per CLAUDE.md's AI integration signal, near-duplicate confirmation and category-normalization are genuinely ambiguous judgment calls (not mechanical data transformation) — a good fit for optional Claude Haiku enrichment with a fully deterministic fallback, rather than AI bolted on for its own sake.
- **Topic diversity.** Canadian-ownership/Canada List topics have appeared twice in the last 10 builds (CanEcon Pulse, CanFile) — below the 3-appearance saturation threshold in CLAUDE.md, and this build's actual task (ingestion QC) is materially different from both.

Candidates 2 and 3 were not weak ideas — both are appended to `builds/ideas.md` as new pending rows for a future night when they have more topical distance from recent builds.

## Deviations from the raw backlog description

Backlog #1 described a "browser-based tool ... to inspect and validate CSV uploads." This build instead implements it as a Python CLI that renders a static, self-contained HTML report (no upload flow, no Playwright), for the reasons above. The core value proposition — catch bad rows before ingestion, with a reviewable visual report — is fully preserved; only the delivery mechanism changed, informed directly by the user's own skepticism recorded in the backlog rating note.
