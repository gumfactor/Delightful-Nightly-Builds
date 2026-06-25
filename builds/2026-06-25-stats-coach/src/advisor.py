"""Statistical test decision tree.

Given a research design specification, returns the appropriate
statistical test and pre-written code snippets.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TestRecommendation:
    test_name: str
    family: str
    assumptions: list[str]
    r_snippet: str
    python_snippet: str
    interpretation_notes: str


# Pre-written code snippets keyed by test name
_SNIPPETS: dict[str, dict[str, str]] = {
    "Independent Samples t-test": {
        "r": (
            "# Independent samples t-test\n"
            "result <- t.test(outcome ~ group, data = df, var.equal = FALSE)\n"
            "print(result)\n"
            "# Effect size (Cohen's d)\n"
            "library(effectsize)\n"
            "cohens_d(outcome ~ group, data = df)"
        ),
        "python": (
            "from scipy import stats\nimport pingouin as pg\n\n"
            "# Independent samples t-test (Welch's)\n"
            "t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)\n"
            "print(f't = {t_stat:.3f}, p = {p_val:.4f}')\n\n"
            "# Effect size\n"
            "result = pg.ttest(group1, group2)\n"
            "print(result[['T', 'p-val', 'cohen-d', 'CI95%']])"
        ),
        "interpretation": (
            "Report: t(df) = X.XX, p = .XXX, d = X.XX. "
            "A significant result (p < .05) means the group means differ more than expected by chance. "
            "Cohen's d: 0.2 = small, 0.5 = medium, 0.8 = large effect."
        ),
    },
    "Paired Samples t-test": {
        "r": (
            "# Paired samples t-test\n"
            "result <- t.test(pre_scores, post_scores, paired = TRUE)\n"
            "print(result)\n"
            "library(effectsize)\n"
            "cohens_d(pre_scores, post_scores, paired = TRUE)"
        ),
        "python": (
            "from scipy import stats\nimport pingouin as pg\n\n"
            "# Paired t-test\n"
            "t_stat, p_val = stats.ttest_rel(pre_scores, post_scores)\n"
            "print(f't = {t_stat:.3f}, p = {p_val:.4f}')\n\n"
            "result = pg.ttest(pre_scores, post_scores, paired=True)\n"
            "print(result[['T', 'p-val', 'cohen-d', 'CI95%']])"
        ),
        "interpretation": (
            "Report: t(df) = X.XX, p = .XXX, d = X.XX. "
            "Tests whether the mean difference between paired observations is zero. "
            "Positive d means the first condition scored higher on average."
        ),
    },
    "One-Way ANOVA": {
        "r": (
            "# One-way ANOVA\n"
            "model <- aov(outcome ~ group, data = df)\n"
            "summary(model)\n"
            "# Post-hoc comparisons\n"
            "TukeyHSD(model)\n"
            "# Effect size\n"
            "library(effectsize)\n"
            "eta_squared(model)"
        ),
        "python": (
            "from scipy import stats\nimport pingouin as pg\n\n"
            "# One-way ANOVA\n"
            "result = pg.anova(data=df, dv='outcome', between='group')\n"
            "print(result)\n\n"
            "# Post-hoc (Tukey)\n"
            "posthoc = pg.pairwise_tukey(data=df, dv='outcome', between='group')\n"
            "print(posthoc)"
        ),
        "interpretation": (
            "Report: F(df_between, df_within) = X.XX, p = .XXX, η² = X.XX. "
            "A significant F means at least two groups differ. "
            "Follow with Tukey HSD to identify which pairs differ. "
            "η²: 0.01 = small, 0.06 = medium, 0.14 = large."
        ),
    },
    "Repeated Measures ANOVA": {
        "r": (
            "# Repeated measures ANOVA\n"
            "library(ez)\n"
            "model <- ezANOVA(data = df, dv = outcome, wid = subject_id,\n"
            "                  within = condition, type = 3)\n"
            "print(model)"
        ),
        "python": (
            "import pingouin as pg\n\n"
            "# Repeated measures ANOVA\n"
            "result = pg.rm_anova(data=df, dv='outcome',\n"
            "                      within='condition', subject='subject_id')\n"
            "print(result)\n\n"
            "# Post-hoc pairwise tests\n"
            "posthoc = pg.pairwise_tests(data=df, dv='outcome',\n"
            "                             within='condition', subject='subject_id')\n"
            "print(posthoc)"
        ),
        "interpretation": (
            "Report: F(df_effect, df_error) = X.XX, p = .XXX, η²p = X.XX. "
            "Check Mauchly's test for sphericity; if violated, use Greenhouse-Geisser correction. "
            "Follow significant effects with pairwise comparisons (Bonferroni correction recommended)."
        ),
    },
    "Mann-Whitney U Test": {
        "r": (
            "# Mann-Whitney U test (Wilcoxon rank-sum)\n"
            "result <- wilcox.test(outcome ~ group, data = df, exact = FALSE)\n"
            "print(result)\n"
            "# Effect size r\n"
            "library(rstatix)\n"
            "wilcox_effsize(outcome ~ group, data = df)"
        ),
        "python": (
            "from scipy import stats\nimport pingouin as pg\n\n"
            "# Mann-Whitney U test\n"
            "stat, p_val = stats.mannwhitneyu(group1, group2, alternative='two-sided')\n"
            "print(f'U = {stat:.1f}, p = {p_val:.4f}')\n\n"
            "result = pg.mwu(group1, group2)\n"
            "print(result)"
        ),
        "interpretation": (
            "Report: U = X, p = .XXX, r = X.XX. "
            "Compares ranks rather than means — appropriate when normality is violated. "
            "Effect size r: 0.1 = small, 0.3 = medium, 0.5 = large."
        ),
    },
    "Wilcoxon Signed-Rank Test": {
        "r": (
            "# Wilcoxon signed-rank test\n"
            "result <- wilcox.test(pre_scores, post_scores, paired = TRUE, exact = FALSE)\n"
            "print(result)\n"
            "library(rstatix)\n"
            "wilcox_effsize(df, outcome ~ condition, paired = TRUE)"
        ),
        "python": (
            "from scipy import stats\nimport pingouin as pg\n\n"
            "# Wilcoxon signed-rank test\n"
            "stat, p_val = stats.wilcoxon(pre_scores, post_scores)\n"
            "print(f'W = {stat:.1f}, p = {p_val:.4f}')\n\n"
            "result = pg.wilcoxon(pre_scores, post_scores)\n"
            "print(result)"
        ),
        "interpretation": (
            "Report: W = X, p = .XXX, r = X.XX. "
            "Non-parametric alternative to the paired t-test. "
            "Tests whether the median difference between pairs is zero."
        ),
    },
    "Kruskal-Wallis Test": {
        "r": (
            "# Kruskal-Wallis test\n"
            "result <- kruskal.test(outcome ~ group, data = df)\n"
            "print(result)\n"
            "# Post-hoc Dunn test\n"
            "library(FSA)\n"
            "dunnTest(outcome ~ group, data = df, method = 'bonferroni')"
        ),
        "python": (
            "from scipy import stats\nimport scikit_posthocs as sp\n\n"
            "# Kruskal-Wallis\n"
            "stat, p_val = stats.kruskal(group1, group2, group3)\n"
            "print(f'H = {stat:.3f}, p = {p_val:.4f}')\n\n"
            "# Post-hoc Dunn test\n"
            "posthoc = sp.posthoc_dunn([group1, group2, group3],\n"
            "                           p_adjust='bonferroni')\n"
            "print(posthoc)"
        ),
        "interpretation": (
            "Report: H(df) = X.XX, p = .XXX. "
            "Non-parametric alternative to one-way ANOVA. "
            "A significant H means at least two groups differ in their rank distributions. "
            "Follow with Dunn's test (Bonferroni-corrected) to identify which pairs."
        ),
    },
    "Pearson Correlation": {
        "r": (
            "# Pearson correlation\n"
            "result <- cor.test(df$var1, df$var2, method = 'pearson')\n"
            "print(result)"
        ),
        "python": (
            "from scipy import stats\nimport pingouin as pg\n\n"
            "# Pearson correlation\n"
            "r, p_val = stats.pearsonr(var1, var2)\n"
            "print(f'r = {r:.3f}, p = {p_val:.4f}')\n\n"
            "result = pg.corr(var1, var2, method='pearson')\n"
            "print(result)"
        ),
        "interpretation": (
            "Report: r(df) = X.XX, p = .XXX. "
            "r measures strength and direction of linear relationship. "
            "|r|: 0.1 = small, 0.3 = medium, 0.5 = large. "
            "Square r to get variance explained (R²)."
        ),
    },
    "Spearman Correlation": {
        "r": (
            "# Spearman rank correlation\n"
            "result <- cor.test(df$var1, df$var2, method = 'spearman')\n"
            "print(result)"
        ),
        "python": (
            "from scipy import stats\nimport pingouin as pg\n\n"
            "# Spearman correlation\n"
            "rho, p_val = stats.spearmanr(var1, var2)\n"
            "print(f'rho = {rho:.3f}, p = {p_val:.4f}')\n\n"
            "result = pg.corr(var1, var2, method='spearman')\n"
            "print(result)"
        ),
        "interpretation": (
            "Report: ρ(df) = X.XX, p = .XXX. "
            "Non-parametric correlation measuring monotonic relationships. "
            "Appropriate when normality is violated or variables are ordinal. "
            "Interpret effect size as for Pearson r."
        ),
    },
    "Linear Regression": {
        "r": (
            "# Simple linear regression\n"
            "model <- lm(outcome ~ predictor, data = df)\n"
            "summary(model)\n"
            "confint(model)\n"
            "# Check assumptions\n"
            "plot(model)"
        ),
        "python": (
            "import pingouin as pg\nimport statsmodels.formula.api as smf\n\n"
            "# Linear regression\n"
            "model = smf.ols('outcome ~ predictor', data=df).fit()\n"
            "print(model.summary())\n\n"
            "# Pingouin alternative\n"
            "result = pg.linear_regression(df[['predictor']], df['outcome'])\n"
            "print(result)"
        ),
        "interpretation": (
            "Report: b = X.XX, SE = X.XX, t(df) = X.XX, p = .XXX, R² = X.XX. "
            "b is the slope: how much outcome changes per unit increase in predictor. "
            "R² is proportion of variance explained. "
            "Report standardized β for effect size."
        ),
    },
    "Chi-Square Test of Independence": {
        "r": (
            "# Chi-square test of independence\n"
            "contingency <- table(df$var1, df$var2)\n"
            "result <- chisq.test(contingency)\n"
            "print(result)\n"
            "# Effect size (Cramér's V)\n"
            "library(effectsize)\n"
            "cramers_v(contingency)"
        ),
        "python": (
            "from scipy import stats\nimport pingouin as pg\n\n"
            "# Chi-square test of independence\n"
            "contingency = pd.crosstab(df['var1'], df['var2'])\n"
            "chi2, p_val, dof, expected = stats.chi2_contingency(contingency)\n"
            "print(f'χ²({dof}) = {chi2:.3f}, p = {p_val:.4f}')\n\n"
            "# Cramér's V effect size\n"
            "result = pg.chi2_independence(df, 'var1', 'var2')\n"
            "print(result)"
        ),
        "interpretation": (
            "Report: χ²(df) = X.XX, p = .XXX, V = X.XX. "
            "Tests whether two categorical variables are associated. "
            "Cramér's V: 0.1 = small, 0.3 = medium, 0.5 = large. "
            "Check that expected cell counts ≥ 5; if not, use Fisher's exact test."
        ),
    },
    "Fisher's Exact Test": {
        "r": (
            "# Fisher's exact test\n"
            "contingency <- matrix(c(a, b, c, d), nrow = 2)\n"
            "result <- fisher.test(contingency)\n"
            "print(result)"
        ),
        "python": (
            "from scipy import stats\n\n"
            "# Fisher's exact test (2x2 table)\n"
            "contingency = [[a, b], [c, d]]  # fill in cell counts\n"
            "odds_ratio, p_val = stats.fisher_exact(contingency)\n"
            "print(f'OR = {odds_ratio:.3f}, p = {p_val:.4f}')"
        ),
        "interpretation": (
            "Report: OR = X.XX, p = .XXX (Fisher's exact). "
            "Use when expected cell counts < 5. "
            "The odds ratio tells you how many times more likely the outcome is in one group vs. the other."
        ),
    },
    "McNemar Test": {
        "r": (
            "# McNemar test for paired categorical data\n"
            "contingency <- matrix(c(a, b, c, d), nrow = 2)\n"
            "result <- mcnemar.test(contingency)\n"
            "print(result)"
        ),
        "python": (
            "from statsmodels.stats.contingency_tables import mcnemar\n\n"
            "# McNemar test\n"
            "contingency = [[a, b], [c, d]]  # discordant cells b and c are key\n"
            "result = mcnemar(contingency, exact=True)\n"
            "print(f'χ² = {result.statistic:.3f}, p = {result.pvalue:.4f}')"
        ),
        "interpretation": (
            "Report: χ²(1) = X.XX, p = .XXX. "
            "Tests whether proportions differ across two matched conditions (e.g., before/after). "
            "Only the discordant cells (b and c) matter for this test."
        ),
    },
    "One-Sample t-test": {
        "r": (
            "# One-sample t-test\n"
            "result <- t.test(scores, mu = null_value)\n"
            "print(result)"
        ),
        "python": (
            "from scipy import stats\n\n"
            "# One-sample t-test\n"
            "t_stat, p_val = stats.ttest_1samp(scores, popmean=null_value)\n"
            "print(f't = {t_stat:.3f}, p = {p_val:.4f}')"
        ),
        "interpretation": (
            "Report: t(df) = X.XX, p = .XXX, d = X.XX. "
            "Tests whether the sample mean differs from a known or hypothesized population value. "
            "Cohen's d = (sample_mean - null_value) / SD."
        ),
    },
    "Logistic Regression": {
        "r": (
            "# Binary logistic regression\n"
            "model <- glm(outcome ~ predictor1 + predictor2,\n"
            "             data = df, family = binomial)\n"
            "summary(model)\n"
            "exp(coef(model))  # Odds ratios\n"
            "exp(confint(model))  # 95% CI for ORs"
        ),
        "python": (
            "import statsmodels.formula.api as smf\n\n"
            "# Logistic regression\n"
            "model = smf.logit('outcome ~ predictor1 + predictor2',\n"
            "                   data=df).fit()\n"
            "print(model.summary())\n"
            "import numpy as np\n"
            "print(np.exp(model.params))  # Odds ratios"
        ),
        "interpretation": (
            "Report: OR = X.XX [95% CI: X.XX–X.XX], p = .XXX. "
            "Each OR tells you how the odds of the outcome change per unit increase in the predictor. "
            "OR > 1: predictor increases odds; OR < 1: predictor decreases odds. "
            "Report Nagelkerke R² or AUC as overall model fit."
        ),
    },
}

_ASSUMPTIONS: dict[str, list[str]] = {
    "Independent Samples t-test": [
        "Continuous outcome variable",
        "Two independent groups",
        "Approximately normal distributions (or n > 30 per group)",
        "Homogeneity of variance (Welch's t-test relaxes this)",
    ],
    "Paired Samples t-test": [
        "Continuous outcome variable",
        "Matched/related pairs",
        "Differences between pairs are approximately normally distributed",
    ],
    "One-Way ANOVA": [
        "Continuous outcome variable",
        "Three or more independent groups",
        "Approximately normal distributions within each group",
        "Homogeneity of variance across groups",
    ],
    "Repeated Measures ANOVA": [
        "Continuous outcome variable",
        "Same participants across all conditions",
        "Approximately normal distributions",
        "Sphericity (equal variances of difference scores)",
    ],
    "Mann-Whitney U Test": [
        "Ordinal or continuous outcome variable",
        "Two independent groups",
        "No normality assumption required",
    ],
    "Wilcoxon Signed-Rank Test": [
        "Ordinal or continuous outcome variable",
        "Matched/related pairs",
        "No normality assumption required",
        "Differences should be rankable",
    ],
    "Kruskal-Wallis Test": [
        "Ordinal or continuous outcome variable",
        "Three or more independent groups",
        "No normality assumption required",
    ],
    "Pearson Correlation": [
        "Two continuous variables",
        "Linear relationship",
        "Bivariate normality",
        "No significant outliers",
    ],
    "Spearman Correlation": [
        "Two ordinal or continuous variables",
        "Monotonic (not necessarily linear) relationship",
        "No normality assumption required",
    ],
    "Linear Regression": [
        "Continuous outcome variable",
        "Continuous predictor(s)",
        "Linear relationship",
        "Normally distributed residuals",
        "Homoscedasticity (equal variance of residuals)",
    ],
    "Chi-Square Test of Independence": [
        "Two categorical variables",
        "Independent observations",
        "Expected cell frequencies ≥ 5",
    ],
    "Fisher's Exact Test": [
        "Two categorical variables in a 2×2 table",
        "Independent observations",
        "Suitable when expected cell counts < 5",
    ],
    "McNemar Test": [
        "Paired categorical data (before/after or matched pairs)",
        "Binary outcome",
        "Discordant pairs provide the test information",
    ],
    "One-Sample t-test": [
        "Continuous outcome variable",
        "Single sample compared to known value",
        "Approximately normally distributed",
    ],
    "Logistic Regression": [
        "Binary categorical outcome",
        "Continuous or categorical predictors",
        "Logit-linear relationship",
        "No multicollinearity among predictors",
    ],
}


def recommend_test(
    outcome_type: str,
    num_groups: int,
    paired: bool,
    normality: str,
    relationship: bool,
    study_context: str = "",
) -> TestRecommendation:
    """Return the appropriate statistical test recommendation.

    Args:
        outcome_type: 'continuous', 'categorical', or 'ordinal'
        num_groups: 1, 2, or 3 (treat anything >=3 as 3+)
        paired: True if measures are matched/repeated
        normality: 'assumed', 'violated', or 'unknown'
        relationship: True if testing association between two variables
        study_context: optional free text fed to AI explainer

    Returns:
        TestRecommendation dataclass

    Raises:
        ValueError: if params are invalid
    """
    valid_outcomes = {"continuous", "categorical", "ordinal"}
    if outcome_type not in valid_outcomes:
        raise ValueError(f"outcome_type must be one of {valid_outcomes}")
    if normality not in {"assumed", "violated", "unknown"}:
        raise ValueError("normality must be 'assumed', 'violated', or 'unknown'")
    if num_groups < 1:
        raise ValueError("num_groups must be >= 1")

    # Treat normality as violated when unknown and groups are small (conservative)
    effective_normality = normality
    if normality == "unknown":
        effective_normality = "violated"

    test_name = _select_test(outcome_type, num_groups, paired, effective_normality, relationship)
    snippets = _SNIPPETS.get(test_name, {})

    return TestRecommendation(
        test_name=test_name,
        family=_family(test_name),
        assumptions=_ASSUMPTIONS.get(test_name, []),
        r_snippet=snippets.get("r", "# No R snippet available"),
        python_snippet=snippets.get("python", "# No Python snippet available"),
        interpretation_notes=snippets.get("interpretation", ""),
    )


def _select_test(
    outcome_type: str,
    num_groups: int,
    paired: bool,
    normality: str,
    relationship: bool,
) -> str:
    # Relationship (correlation / regression) branch
    if relationship:
        if outcome_type == "categorical":
            return "Logistic Regression"
        if normality == "violated" or outcome_type == "ordinal":
            return "Spearman Correlation"
        return "Pearson Correlation"

    # Categorical outcome
    if outcome_type == "categorical":
        if paired:
            return "McNemar Test"
        if num_groups == 2:
            return "Fisher's Exact Test"
        return "Chi-Square Test of Independence"

    # Ordinal outcome → always non-parametric
    if outcome_type == "ordinal":
        if num_groups == 1:
            return "Wilcoxon Signed-Rank Test"
        if num_groups == 2:
            return "Wilcoxon Signed-Rank Test" if paired else "Mann-Whitney U Test"
        return "Kruskal-Wallis Test"

    # Continuous outcome
    if num_groups == 1:
        return "One-Sample t-test"

    if num_groups == 2:
        if paired:
            if normality == "violated":
                return "Wilcoxon Signed-Rank Test"
            return "Paired Samples t-test"
        else:
            if normality == "violated":
                return "Mann-Whitney U Test"
            return "Independent Samples t-test"

    # 3+ groups
    if paired:
        if normality == "violated":
            return "Kruskal-Wallis Test"
        return "Repeated Measures ANOVA"
    else:
        if normality == "violated":
            return "Kruskal-Wallis Test"
        return "One-Way ANOVA"


def _family(test_name: str) -> str:
    parametric = {
        "Independent Samples t-test", "Paired Samples t-test",
        "One-Sample t-test", "One-Way ANOVA", "Repeated Measures ANOVA",
        "Pearson Correlation", "Linear Regression", "Logistic Regression",
    }
    if test_name in parametric:
        return "parametric"
    if test_name in {"Chi-Square Test of Independence", "Fisher's Exact Test", "McNemar Test"}:
        return "categorical"
    return "non-parametric"
