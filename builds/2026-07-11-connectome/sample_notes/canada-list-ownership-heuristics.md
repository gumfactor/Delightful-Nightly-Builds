# Canada List — Ownership Classification Heuristics

Working notes on how to classify a company as Canadian-owned for The Canada
List. This keeps coming up as an edge case generator, not a simple lookup.

Heuristics so far:
- Headquarters location is necessary but not sufficient — a Canadian HQ with
  a foreign parent company should classify as foreign-owned, not Canadian.
- Public companies need a control-block test (who holds the largest voting
  stake), not just "listed on the TSX."
- Franchise brands are especially messy: the parent brand may be foreign-
  owned while individual franchise locations are Canadian small businesses.
  Need to decide which layer the classification applies to.
- Confidence should be an explicit field, not implied — ownership structures
  change (acquisitions, IPOs) and a stale "Canadian-owned" label is worse than
  an honest "uncertain, last verified date X."

This confidence and provenance idea generalizes beyond Canada List — any
knowledge base built from public structured data sources should show its
work, not just its conclusion.
