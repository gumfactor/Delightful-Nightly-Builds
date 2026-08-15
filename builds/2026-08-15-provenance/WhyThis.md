# WhyThis.md — Provenance

## Path: Fresh generation, not the lottery

Category B — Productivity Utility (day of year 227, `(227-1) % 9 = 1`). The backlog had two `pending` rows tagged Category B, but both turned out to be undocumented duplicates of already-shipped builds:

- Idea #4, "Cross-Agent Project Activity Workstreams" (rated 9/10, had a full Idea Brief) — this is **Worklog** (2026-07-10). Worklog's own build log describes implementing "the highest-rated backlog idea (9/10, Idea Brief)" — a direct match.
- Idea #7, "Morning Briefing" — this is **Morning Briefing** (2026-06-22, rated 5/10 in the catalog: "over-engineered for a use case existing tools cover adequately").

Both were corrected from `pending` to `built` in `builds/ideas.md` before drawing (see BUILD_LOG.md for why this correction didn't survive from the last time someone made it, on 2026-08-06). With the pool empty, Step 2c routes straight to fresh generation — no lottery roll happened because there was nothing left to roll for.

## Topic diversity check

Scanned the last 10 builds (2026-08-05 through 2026-08-14):

| Domain | Count | Verdict |
|---|---|---|
| Investment/finance | 2 (Portfolio Lab, Quarter Call) | At the threshold, not over it — steered away from a third rather than ruled it out |
| Academic/research admin | 4 (Impact Ledger, Manuscript Pipeline, Waymark, Panel Prep) | Treated as saturated — CLAUDE.md's diversity rule names investment by example but says "apply the same check to other domains that have repeated," and four grant/manuscript/citation/decision-log tools in ten nights is a real pattern |

This ruled out another grant-writing, manuscript-tracking, or citation tool even though PROFILE.md names several still-unaddressed academic friction points (e.g. "Research administration" broadly) — the specific sub-friction points that map cleanly to a productivity tool have mostly been hit, and a fifth research-admin build in ten nights would be redundant by any reasonable reading of the diversity rule.

## Three candidates considered

**1. Provenance — batch Canadian-ownership classifier for The Canada List (chosen).**
CanFile (2026-07-20) already proved the technique — Wikidata search + claims (`P17` country, `P159` headquarters, `P749`/`P127` parent/owner with one-hop country resolution) plus an optional Claude Haiku enrichment layer, always falling back to a transparent deterministic rule engine — for looking up **one company at a time**. But the real friction PROFILE.md names is "The Canada List ingestion and quality control pipeline," which is a batch workload: a curator has a spreadsheet of dozens or hundreds of candidate businesses to research, not one name typed into a REPL. Category B's canonical shape is explicitly "batch processors," and turning a proven single-lookup technique into an actual batch tool — with resumable local caching so a 200-row CSV doesn't re-query Wikidata for rows already resolved on a prior run, and a CSV in → enriched CSV out interface that drops straight into a spreadsheet workflow — is a genuine, non-redundant extension rather than a rebuild. It reuses CanFile's *architecture* (same public API, same rule shape) without importing a single line from CanFile's folder, and it is the first build in the catalog to treat Canada List ownership research as a batch job instead of a lookup.

**2. Course Material Batch Formatter — rejected.**
Take a folder of raw lecture notes/outlines and batch-convert them into a consistent slide-outline + handout format via Claude. Targets a real PROFILE.md friction point ("Course material creation") and fits the "batch processor" shape, but it carries the same failure signature that scored 2026-06-24's AI Lecture Builder a 2/10: "a power user replicates this with one prompt in the Claude interface." Batching doesn't fix that critique if the core value is still "ask Claude to reformat text" — there's no deterministic, verifiable layer underneath the AI call the way Provenance has (the rule engine works and is testable with zero API key).

**3. Multi-Repo Dependency Batch Auditor — rejected.**
Batch-check `requirements.txt`/`package.json` across multiple local repos against PyPI/npm for outdated or vulnerable pins. This is close to a straight re-run of `dep-check` (2026-06-19, "Python Dependency Auditor"), just pointed at multiple repos instead of one — not enough differentiation to justify a second build on the same problem.

## Idea Brief

No linked Idea Brief for this idea (it's freshly generated tonight, not drawn from the backlog).
