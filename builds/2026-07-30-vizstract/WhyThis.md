# WhyThis — Vizstract: Visual Abstract Generator

## Category and rotation
Today is 2026-07-30, day-of-year 211. `category_index = (211 - 1) % 9 = 3` → **Category D — Creative / Generative**.

## Lottery check
Read `builds/ideas.md` (resynced from the most recent open PR branch, `claude/cool-sagan-4agz2q`, before checking). Filtered for `Category = D` and `Status = pending`: **zero rows**. No Category D idea has ever been logged to the backlog — every prior D build (AI Lecture Builder, WeatherSong, Research Question Forge, Bridgework) was freshly generated the same night and none were the "runner-up" of a prior session. Per Step 2c, an empty pool skips the lottery entirely and goes straight to Step 2d (fresh generation). No roll was made.

## Prior Category D builds (context, not to repeat)
- 2026-06-24 **AI Lecture Builder** — rated 2/10. Critique on file: "a power user replicates this with one prompt in the Claude interface" — a single-shot AI-content wrapper with a tabbed viewer bolted on, no differentiating mechanic.
- 2026-07-03 **WeatherSong** — live weather deterministically mapped into Web Audio synthesis + Canvas visuals. Unrated.
- 2026-07-12 **Research Question Forge** — taxonomy × compatibility-rule-engine combinatorial text generator (question/hypothesis skeletons). Unrated.
- 2026-07-21 **Bridgework** — same taxonomy × compatibility-rule-engine architecture as Research Question Forge, applied to analogy generation, explicitly built to sidestep the AI Lecture Builder critique. Unrated.

Two of the last three D builds already share one architecture (taxonomy cross-product + compatibility rules + optional AI polish). A third build on that exact mechanic — even on a new topic — would read as a template being re-skinned, not a new idea. The bar for tonight was a **genuinely different generative mechanic**, not prose generation at all.

## Topic-domain saturation check (last 10 builds, 2026-07-19 → 2026-07-29)
Protocol Forge (ethics protocols), CanFile (Canada List ownership), Bridgework (analogies/public education), Bayes Lab (Bayesian stats learning), Heuristic Hunt (cognitive-bias game), BugTrace (dev-tool bug mining), TripKit (travel/life admin), SiliconWatch (AI-infra investing), Voiceprint (writing-quality audit), Citation Vault (reading/citation tracker).

Four of these ten (Protocol Forge, Bridgework, Bayes Lab, Citation Vault) sit somewhere in "academic/research," but each targets a distinct, PROFILE.md-named friction point (ethics applications; public education/book writing; a named Bayesian learning goal; literature reviews) and none is a design/graphics tool. No single narrow topic (GitHub, investing, weather, Canada-data) appears more than twice, so nothing crosses the "more than twice → saturated" line from CLAUDE.md. Given PROFILE.md's own "Creative pursuits" section names "writing academic papers," "designing university courses," and "developing AI-assisted knowledge systems" as the user's actual creative outlets, an academic-adjacent Creative/Generative build is on-target rather than a retread — provided the mechanic is new, which the design/layout-engine approach below is.

## Candidate ideas considered

1. **Vizstract — Visual Abstract Generator** *(selected)*. A deterministic SVG layout engine (5 study-design templates, hand-authored icon library, text-fitting algorithm, 5 color themes) that turns structured study metadata into a downloadable SVG/PNG visual abstract — the graphic format increasingly required or expected for manuscript and grant submissions. Optional Claude Haiku extracts the structured fields from a pasted free-text abstract; a deterministic keyword/regex extractor covers the no-key case. Chosen because the core value is an actual rendering/layout engine (text-fitting, non-overlapping regions, icon composition) that a single Claude prompt cannot replicate — the opposite failure mode of AI Lecture Builder — and it targets "write grants and manuscripts" and "public-facing articles," both named PROFILE.md friction points, with a genuinely new artifact (a downloadable graphic file) that no prior build produces.

2. **EchoScape** — an ambient soundscape generator sonifying the user's own live GitHub commit activity (a "coding session soundtrack" keyed to today's commit velocity and file-type mix). Passed over: it reuses WeatherSong's exact mechanic (live data → deterministic Web Audio + Canvas mapping) on a new data source rather than introducing a new one, and GitHub is already the backbone of a large share of the catalog (Worklog, Pipeline Pulse, ci-pulse, BugTrace, two Developer Analytics/Activity dashboards).

3. **Lab Fable** — a branching interactive-fiction generator that turns a real published finding (looked up by DOI via the free Crossref API, the same data source Citation Vault already uses) into a short branching teaching scenario. Passed over: structurally, this is a third "combinatorial content generator seeded from an academic corpus" build (after Research Question Forge and Bridgework) wearing a narrative skin — the same architecture-reuse concern that ruled out repeating Bridgework's pattern applies here too, and it does not address an unmet need the way a graphic-deliverable tool does.

Non-winners 2 and 3 are appended to `builds/ideas.md` tonight under Category D so they remain available (and open to a rating) for a future session; idea 1 (the winner) is not added to the backlog per Step 2d.

## Deployment model
This is a one-off creative tool invoked whenever the user is preparing a submission or a graphic — not a recurring/scheduled task and not an event response — so a standalone browser app is the right deployment model (no Routine/Skill/Hook wrapper needed).
