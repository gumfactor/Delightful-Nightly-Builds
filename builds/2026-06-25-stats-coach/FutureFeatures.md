# Future Features — Stats Coach

1. **Sample size calculator integration** — After selecting a test, add a second panel that asks for desired power (0.80), alpha (0.05), and expected effect size, then computes the required N using scipy.stats power functions. The most common follow-up question after "which test?" is "how many participants do I need?"

2. **Assumption checker** — Add a separate tab where users can paste summary statistics (group means, SDs, n) and the app runs Shapiro-Wilk normality tests, Levene's equality of variance test, and reports whether the selected test's assumptions are met — with guidance on what to do if they're violated.

3. **APA write-up generator** — Accept the user's actual test results (t-value, df, p, effect size) and generate a ready-to-paste APA Results section sentence. Eliminates the "how do I write this up?" question that always follows "which test do I use?"

4. **Two-way and mixed ANOVA branch** — Extend the decision tree to handle factorial designs (two independent variables, or one between-subjects and one within-subjects factor). Currently the tree stops at one-way designs.

5. **Persistent history per design** — Store each query with a user-supplied label (e.g., "Study 2 — cortisol comparison") in the SQLite database and add a history sidebar. Useful for researchers running multiple studies who want to revisit earlier decisions without re-entering all parameters.

6. **Export to PDF** — Add a "Download summary" button that renders the recommendation, explanation, and code snippets as a clean PDF using pdfkit or weasyprint. Useful for sharing with supervisors or attaching to a pre-registration document.

7. **Shareable link via URL parameters** — Encode the design parameters into a query string so researchers can share a direct link to a specific recommendation (e.g., `?outcome=continuous&groups=2&paired=false&normality=violated`). Useful in lab meetings and course settings.
