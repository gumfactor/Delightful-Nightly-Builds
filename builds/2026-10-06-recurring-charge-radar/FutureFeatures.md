# Future Features

1. **Merchant-name review pass with Claude (opt-in).** Send only merchant strings (never amounts or dates) to the Anthropic API to merge variants and label categories, behind an explicit flag.
2. **Cancellation helper.** For each zombie or unwanted charge, generate a dispute/cancellation email draft with dates and amounts filled in.
3. **Run-over-run diffing.** Persist each run to SQLite and report what changed since last time: new subscriptions, new price hikes, newly ended charges.
4. **Canadian tax tagging.** Flag business-use subscriptions (SaaS, hosting, domains) and export a CSV for the corporation's books, with GST/HST split.
5. **IBKR / credit card statement PDF import** so every card is covered without CSV export.
6. **Trial-to-paid detector.** Spot a $0 or tiny charge followed by a full-price charge, and warn before it happens.
7. **USD charge normalisation** using Bank of Canada rates so FX drift is shown separately from real price hikes.
8. **Calendar subscription feed** served locally so the `.ics` refreshes instead of being re-imported.
