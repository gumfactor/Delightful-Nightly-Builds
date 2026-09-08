# WhyThis — Secrets Sentinel

## Lottery process
Tonight's category (day of year 251, `(251-1) % 9 = 7`) is **H — Developer Tool**.

`builds/ideas.md` had 3 `pending` rows matching Category H: #34 Dead Code Detective, #35 Test Flakiness Static Scanner, #36 API Surface/SemVer Diff Checker. All three have a blank `Your Rating` (R = 0 rated entries), so `lottery_chance = min(75, 25 + 0*2) = 25%`. Rolled a random integer 1–100: **94**. 94 > 25, so the backlog draw was skipped and fresh ideas were generated instead. Pool size was 3.

## Fresh idea generation
Scanned the last 10 builds in `builds/index.md` (2026-08-28 through 2026-09-07) for topic saturation — finance/investing appeared once (EDGAR Lens) within that window, not saturated. Developer-tooling itself is the active category history to check: 9 prior H builds (Git Standup Reporter, dep-check, ci-pulse, Schema Sentinel, AgentLint, BugTrace, Landing Pattern, Snipvault, Layer Guard) are all static-analysis-over-current-source-tree or CLI-batch-report tools. The three pending backlog rows (#34–#36) are all variations on that same mechanic — #34 explicitly notes it "could reuse Layer Guard's module-discovery and first-party-import-classification code almost as-is," and #36 was passed over once already for being "structurally very close to Schema Sentinel's... shape."

Three fresh candidates for Category H, chosen to avoid that current-tree-static-analysis mechanic entirely:

1. **Secrets Sentinel** (winner) — walks full git *history* (not just the working tree) across the user's repos for committed credentials, using known-vendor regex patterns plus a from-scratch Shannon-entropy detector for unknown secret shapes, with an AI triage pass that reduces false positives without ever sending the actual secret value to the API.
2. **License Compliance Auditor** — cross-repo dependency license scan (PyPI/npm classifiers) flagging copyleft/unknown licenses that pose legal risk for commercial products (Canada List, Kwyeter).
3. **Config Drift Detector** — compares locally installed tool/package versions against what each repo's lockfiles/CI config pin, catching "works on my machine" mismatches before they cause CI failures.

**Secrets Sentinel won** because: (a) it's mechanically distinct from every prior H build — git-history-walking plus entropy scoring is a different engine than AST parsing or text-pattern linting over a single tree snapshot; (b) it directly operationalizes a hard rule this very repo already lives under (`STANDARDS.md`: "No credentials, API keys, or passwords hardcoded in source files") into a tool the user can point at *any* of their repos, not just this one; (c) it has real, non-trivial testable logic (entropy math, tiering, redaction-safety, still-in-HEAD-vs-history-only detection) rather than being a thin wrapper around an existing library; (d) the AI-integration signal in `CLAUDE.md` calls out classification/triage as a strong differentiating layer, and this build uses it for exactly that — cutting false positives on ambiguous high-entropy strings — while the redaction requirement (never sending the real secret to a third party) is itself a meaningful design constraint that had to be engineered and tested, not assumed.

License Compliance Auditor and Config Drift Detector are appended to `builds/ideas.md` as non-winners for future nights.

## Idea Brief
No linked Idea Brief — this idea was generated fresh tonight, not drawn from a backlog row with a brief.
