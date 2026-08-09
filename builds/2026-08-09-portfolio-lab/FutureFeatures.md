# Future Features — Portfolio Lab

Concrete enhancements for a working, valuable tool — not things required to make tonight's build worth using.

1. **Long-only constrained frontier.** The current efficient frontier is the classic unconstrained analytical solution (shorting allowed in the wings). Adding a proper long-only quadratic program (e.g. a simple active-set or projected-gradient solver, from scratch, no external optimization library) would let the frontier line match the true feasible region of the Monte Carlo cloud exactly, rather than the cloud being a strict subset of what the line bounds.

2. **Custom asset basket.** Let the user edit the 12-ticker list in a config file (or a UI text box `fetch_data.py` reads) instead of the fixed teaching basket — e.g. swap in their actual IBKR holdings to see the diversification math on their own portfolio.

3. **Rolling-window history.** `fetch_data.py` currently overwrites `data.js` on every run with no memory of prior fetches. Persisting each run's stats to a small local SQLite file (matching the pattern used across most of this catalog's other data-fetching builds) would let a "how has this basket's efficient frontier shifted over the past year?" view exist.

4. **Multi-period backtest.** Pick a portfolio (from the mixer or the frontier) and see how it would actually have performed, period by period, over the fetched window — cumulative return chart alongside the risk/return scatter, not just the single-period expected-value math.

5. **Short-selling toggle for the Monte Carlo cloud.** Currently the cloud is always long-only. A toggle to sample from the full (potentially short) weight space would let a user directly compare the long-only feasible region against the unconstrained frontier side by side, rather than taking the dominance property on faith.

6. **Factor decomposition.** Break each asset's return into market/size/value-style factor exposures (even a simple single-factor CAPM beta against an equal-weighted market proxy computed from the basket itself, no external factor data needed) to teach *why* two assets are correlated, not just *that* they are.

7. **Printable/exportable summary.** A "Copy portfolio as Markdown" button on the Explainer and Frontier tabs (the same pattern used by Research Question Forge and Bridgework) so a specific mix and its stats can be pasted into notes or a lecture.

8. **Quiz difficulty tiers.** Currently every quiz round mixes two random assets at a random weight. A "hard mode" restricted to near-identical-Sharpe pairs (forcing genuinely careful reasoning about the trade-off rather than an obvious call) would extend the learning curve past the first few correct answers.
