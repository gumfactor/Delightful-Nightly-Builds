# Future Features — Replication Lab

1. Optional Claude tutor: paste your own study design (n, outcomes, stopping rule) and get a written power and risk review, using `ANTHROPIC_API_KEY` entered at runtime.
2. Paired, one-sample and correlation designs, plus unequal group sizes and non-normal data (skewed, outliers).
3. Sequential-testing corrections (O'Brien-Fleming, alpha spending) in the Peeking lab so the fix can be seen next to the problem.
4. Replication lab: simulate a published study, then a replication, and show how often the replication lands inside the original interval.
5. Export a lab as a self-contained PNG plus parameters, ready for slides or a grant's sample size justification.
6. Persist prediction history in localStorage to chart calibration across weeks, and add a classroom mode with a shared seed.
7. Move simulations to a Web Worker so larger repetition counts never block the page.
