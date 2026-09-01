# Why This — Fleet Drift

## Category and selection path

Day of year 244 → `category_index = (244-1) % 9 = 0` → **Category A — Dashboard/Visualizer**.

Category A's pending backlog held 4 rows: #3 (Lab Research Project Tracker, rated 4 — already rejected once with "No need — already use Teamwork.com for project tracking"), #6 (Open-Meteo Activity Planner, unrated), #26 (Research Pulse, unrated), #27 (Canada List Business Density Dashboard, unrated). Only #3 carries a numeric rating, so `R = 1` and `lottery_chance = min(75, 25 + 1*2) = 27%`. A 1–100 roll came back **58** — missed the gate — so tonight went to fresh idea generation rather than a backlog draw.

## Why not the backlog rows anyway (context for the fresh-idea decision)

- #6 (Open-Meteo Activity Planner) substantially overlaps three already-built Open-Meteo tools (Run Planner, Dockside, TripKit) that already cover running/golf/boating comfort scoring — a fourth would be a weak-differentiation repeat.
- #26 (Research Pulse) was already passed over once (2026-08-23) for reading as a fourth build on the same saved-topic literature feed as Paper Lens/PubMed Research Radar/Impact Ledger.
- #27 (Canada List Business Density Dashboard) needs a real exploration pass to pin down Statistics Canada's WDS table/vector IDs before a build session can commit to a reliable schema — this build container's egress restrictions (confirmed again tonight — see below) make that exploration unverifiable in-session, and guessing at vector IDs risks shipping a tool built on a wrong schema.

None of these were strong enough to build blind, so fresh generation was the right call rather than forcing a weak draw.

## Topic diversity check

Scanned the last 10 builds (2026-08-19 → 2026-08-30): Effort Ledger (F, grant/effort audit), Fairway Physics (G, golf physics), Renewal Radar (I, domain/cert admin), **Trading Book (A, IBKR investing)**, Lecture Loom (B, course formatting), Grant Vault (C, grant-writing knowledge base), Regression Lab (E, stats trainer), **EDGAR Lens (F, SEC filings)**, Zebra Lab (G, logic puzzle), Layer Guard (H, import architecture).

Investment/finance appeared twice (Trading Book, EDGAR Lens) — under the ">2 in 10 = saturated" threshold, so not disqualifying, but close enough that a third investment build tonight was deliberately avoided in favor of a different domain.

Separately, GitHub-backed tooling is the single most repeated *data source* across the full 78-build catalog (repo health scorecard x2 near-duplicate, developer activity/rhythm dashboards, ci-pulse, Landing Pattern, BugTrace, Waymark's local git history, Layer Guard, AgentLint). Within Category A specifically only 2 of 9 prior builds used GitHub (Health Scorecard, Developer Analytics Dashboard), so it wasn't off the table for tonight — but it meant a GitHub-sourced idea needed to bring a genuinely new analytical shape, not another repo-health/commit-rhythm/CI-performance dashboard.

## Three fresh ideas considered

1. **Fleet Drift** — a cross-repo dependency-version-drift dashboard: for every dependency that appears in 2+ of the user's owned repos, flag whether it's pinned to different versions across them (and by how much — patch/minor/major), plus a per-repo staleness rollup against each dependency's real latest release on PyPI/npm.
2. **Research Software Reproducibility Scorecard** — scans owned repos for reproducibility signals (dependency manifest present, LICENSE, tests, CI config, CITATION.cff, data-availability language in the README) and renders a per-repo scorecard dashboard, tracked over time.
3. **Canada List Market Landscape** — a live Wikidata SPARQL aggregate query (industry × Canadian-owned company counts) rendered as an industry-composition dashboard for The Canada List's editorial work.

## Why Fleet Drift won

- It directly answers a critique already recorded in this repo's own backlog: idea #14 (Multi-Repo Dependency Batch Auditor, 2026-08-15) was passed over for being "too close to the already-built `dep-check`... worth revisiting only if paired with something dep-check doesn't do (e.g. cross-repo shared-dependency-version drift detection)." That is exactly this build's core mechanic — dep-check (2026-06-19) classifies one repo's dependencies against PyPI in isolation; Fleet Drift's differentiating layer is the *cross-repo matrix* — which dependency is pinned inconsistently across repos the user actually owns, a question no single-repo audit can answer.
- It maps directly to two friction points named verbatim in PROFILE.md: "Managing many simultaneous projects" and "Keeping multiple data systems synchronized." A solo founder/lab director running several live codebases (this repo's own Landing Pattern build found 50 open PRs across this repository alone) has a real, recurring cost from not knowing that `requests==2.28.0` in one repo and `requests==2.31.0` in another is a live inconsistency until something breaks.
- It uses two well-documented, genuinely free, no-auth registries (PyPI's JSON API, the npm registry API) alongside `GITHUB_TOKEN`, which PROFILE.md's Data Sources section confirms is available — no new credential risk.
- Compared to option 2 (Reproducibility Scorecard): also strong and academically on-point, but lower data richness for a *dashboard* — it's fundamentally a single-source (GitHub-only) checklist scorer, closer to a linter's shape than a genuinely multi-axis visual dashboard. Fleet Drift's version matrix, severity heatmap, and staleness rollup give more surface for real charts and cross-filtering.
- Compared to option 3 (Canada List Market Landscape): a live Wikidata SPARQL aggregate query is technically feasible, but riskier to get right blind (query shape, exact property paths for "Canadian-owned business" vs. simple `country=Canada`, which would misclassify foreign subsidiaries with a Canadian office — a correctness risk CanFile/Provenance's existing one-hop-ownership-resolution logic was built specifically to avoid). Given this build container's confirmed inability to make live outbound calls to verify the query, shipping it unverified was a bigger risk than Fleet Drift's already-proven-shape (PyPI/npm JSON APIs, whose response shapes are stable and well-documented from prior sessions' work on `dep-check`).

Options 2 and 3 were appended to `builds/ideas.md` as new pending Category A rows for a future night rather than discarded.

## Idea Brief

The selected idea has no linked Idea Brief in `builds/ideas.md` (it was freshly generated tonight, not drawn from an existing backlog row) — no brief to read before the PRD.

## Network constraint encountered tonight

Confirmed again this session: this build container's Bash tool denies outbound `curl` to `pypi.org`, `registry.npmjs.org`, and `api.github.com` outright (permission denied, not even a 403 response). Per CLAUDE.md Step 2f, this is a build-environment constraint, not a reason to redesign around mock data — Fleet Drift is written against the real, documented PyPI JSON API (`GET /pypi/{name}/json`), npm registry API (`GET /{name}`), and GitHub REST API (`GET /user/repos`, Contents API) shapes, with every test injecting a fake `urlopen` transport. `GITHUB_TOKEN` is confirmed present in this container's own environment via `env`, but per PROFILE.md's Data Sources guidance it is reserved for the shipped tool's own runtime use, tested only via mocks in this session — not called live by the build session itself.
