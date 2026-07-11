# Quant Screening Workflow Notes

Trying to formalize the personal investment screening workflow instead of
running it ad hoc every time. The recurring friction is the same one that
shows up in the AI agent handoff problem: losing context between sessions.
A screening pass done three months ago should inform this month's pass, not
start from zero — preserving context between passes matters as much as the
screening rules themselves.

Workflow sketch:
1. Pull a candidate list from a fixed rule set (sector, market cap band,
   valuation screen) so the starting universe is reproducible, not vibes-based.
2. For each candidate, log the screening decision and the reasoning — pass,
   watch, or reject — with the price and key metric at the time.
3. Revisit rejected names periodically; a rejection six months ago may no
   longer hold if the underlying metric that drove it has changed.

This is really the same underlying idea as the ownership confidence note for
Canada List: a knowledge base is only trustworthy if it shows its reasoning
and its freshness, not just a final label.
