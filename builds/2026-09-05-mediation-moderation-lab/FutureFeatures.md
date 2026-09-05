# Future Features

1. **CSV upload for real data.** Let the user paste or upload their own X/M/Y (or X/Z/Y) columns instead of only simulated data, running the exact same engine against real study data — turning this from a pure teaching simulator into something usable for the user's own research, at the cost of needing input validation and column-mapping UI.

2. **Multiple mediators / moderated mediation.** Extend the mediation engine to parallel or serial multi-mediator models, and add a combined moderated-mediation ("conditional indirect effect") mode — the natural next step up in complexity once single-mediator/single-moderator models are mastered.

3. **Downloadable lecture handout.** A button that exports the currently-displayed sample's path diagram, stats table, and plain-English explanation as a single PDF or PNG, so a specific generated example (tied to a memorable seed) can be dropped straight into lecture slides or a student handout.

4. **Shareable scenario links.** Encode the current sliders + seed into a URL fragment so a specific worked example can be shared with a TA or student via a link rather than requiring them to manually match every slider.

5. **A third "assumptions" tab.** Add a dedicated normality/homoscedasticity/independence diagnostics view for the residuals of the fitted mediation/moderation models (reusing Regression Lab's diagnostic-plot approach), since mediation and moderation models inherit all the same OLS assumptions that a full course would also want to cover.

6. **Effect-size interpretation guide.** Add a reference panel translating the raw path coefficients into standardized effect sizes (e.g. partially standardized indirect effect, kappa-squared) with rule-of-thumb interpretation bands, since raw unstandardized coefficients depend on the arbitrary scale chosen for the synthetic X/M/Z/Y variables.

7. **Timed/graded quiz mode for coursework.** A stricter quiz mode with a time limit and a printable/exportable score report, so the existing quiz tab could double as an actual homework assignment rather than only a self-study tool.
