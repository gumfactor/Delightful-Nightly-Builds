# Future Features — Trading Book

Ideas for a working, valuable tool — not things needed to make tonight's build worth using.

1. **Multi-currency FX normalization.** Positions currently show market value in their native currency (USD, CAD, etc.) with no conversion. A future version could pull a free FX rate (e.g. Bank of Canada Valet, already used by CanEcon Pulse) and add a normalized "home currency" total to the hero stats.

2. **Benchmark overlay.** Add a second line on the Net Liquidation Trend chart tracking a benchmark (e.g. SPY) scaled to the account's starting value on the same date range, so relative performance is visible at a glance — would need the user to run a companion `fetch_benchmark.py` locally (yfinance) the same way Portfolio Lab and Quarter Call already do.

3. **Per-position cost-basis history.** Right now each `sync` overwrites the previous day's position rows. A future version could keep every day's position-level snapshot (not just the account-level trend) so a per-symbol "how has this position's unrealized P&L moved" mini-chart becomes possible.

4. **Alerting.** A `check` command that compares the latest snapshot against user-configured thresholds (e.g. "unrealized P&L on any single position exceeds -10%") and prints a warning — useful as a pre-market routine before the user opens TWS.

5. **Multi-account support.** IBKR Financial Advisor accounts can hold several sub-accounts; `ib_insync`'s `accountSummary()` can be scoped per account. A future version could accept `--account` and store a separate history per account ID rather than assuming a single account.

6. **Options Greeks panel.** For `OPT` security-type positions, IBKR's API can return delta/gamma/theta/vega via `reqMktData` with generic tick types. A dedicated Options tab summarizing portfolio-level Greeks exposure would be a natural extension for a more active options trader.
