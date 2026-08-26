# Future Features — Thesis Breaker

1. **Split the Margin/Debt Risk rule into two independent categories** (Margin Trend and Debt Risk). Right now they're conflated into one rule, which means Narrative Fragility's contradiction check can flag a thesis's "low debt" claim as contradicted purely because of a margin-driven trigger, even when the debt number itself is fine. Two separate rules would make every persona's rationale and the narrative-fragility cross-check more precise.

2. **Live sector-average P/E instead of a static reference table.** The Valuation Stretch check currently compares trailing P/E against a hand-set per-sector threshold (`SECTOR_PE_THRESHOLDS` in `src/rules.py`). A real sector/industry average — e.g. computed from a basket of sector-representative tickers fetched at check time — would make the valuation check adaptive to actual market conditions instead of a fixed number that will eventually go stale.

3. **A `portfolio` command** that runs `check` across every ticker in a watchlist file in one pass, producing a single ranked HTML report (highest bear-case score first) instead of one ticker at a time.

4. **Direct SEC EDGAR Form 4 parsing** as an alternative or supplement to yfinance's insider-transactions table, for tickers where Yahoo's scrape is incomplete or delayed relative to the actual regulatory filing.

5. **A Routine wrapper** that re-runs `check` automatically on a schedule (e.g. weekly) for every ticker with a saved thesis, and only surfaces a notification when the bear-case score has moved meaningfully since the last run — turning this from a pull tool into a pull tool that only interrupts you when something changed.

6. **A "thesis diff" view**: when re-checking the same ticker+thesis pair, show exactly which of the 5 categories flipped status since the last run (e.g. Growth Deceleration went from clear to triggered) rather than requiring the user to compare two full reports side by side.

7. **Confidence-weighted persona scores.** Right now every triggered category contributes its full weight to a persona's score regardless of how close the underlying number was to the threshold (e.g. a P/E of 35.1 counts the same as a P/E of 90 against a 35.0 threshold). A magnitude-aware score (how far past the threshold, not just whether it was crossed) would make the severity number more informative.

8. **A short-interest and options-skew data layer** (both available via yfinance for many tickers) as additional inputs to the Governance Hawk / Macro Bear personas, for a fuller picture of market positioning beyond insider transactions alone.
