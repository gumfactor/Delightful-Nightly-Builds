/**
 * Regression Lab — quiz engine.
 * Two question types:
 *  - "diagnose": shows a real dataset's regression diagnostics and asks
 *    which issue is present. The correct answer is computed live by
 *    running the same math.js tests used elsewhere in the app — never a
 *    hardcoded label per dataset.
 *  - "concept": fixed conceptual multiple-choice questions about what the
 *    diagnostics mean and why they matter.
 */

(function (root) {
  const M = typeof module !== 'undefined' && module.exports
    ? require('./math.js')
    : root.RegressionMath;
  const D = typeof module !== 'undefined' && module.exports
    ? require('./datasets.js')
    : root.RegressionDatasets;

  const DIAGNOSIS_LABELS = {
    outlier: 'A high-leverage outlier is distorting the fit',
    'non-linear': 'The true relationship is non-linear',
    heteroscedastic: 'The variance of the errors is not constant (heteroscedasticity)',
    'well-behaved': 'No serious assumption violation — the fit looks sound',
  };

  /**
   * Runs the real diagnostic battery on a dataset and returns which single
   * issue best explains the pattern. Computed fresh every call — never a
   * stored answer key.
   */
  function diagnoseDataset(points) {
    const x = points.map((p) => p.x);
    const y = points.map((p) => p.y);
    const reg = M.simpleLinearRegression(x, y);
    const bp = M.breuschPaganTest(reg.fitted, reg.residuals);
    const reset = M.resetTest(x, y);
    const sortedCooksD = [...reg.cooksD].sort((a, b) => b - a);
    // A dominance ratio is only meaningful once the top point's own
    // influence is non-trivial — otherwise (e.g. a perfect fit, where
    // every Cook's Distance is exactly 0) dividing by a near-zero
    // runner-up would misreport "infinite" dominance for a point that
    // isn't influential at all.
    const MIN_MEANINGFUL_COOKS_D = 1e-6;
    let dominance;
    if (sortedCooksD[0] < MIN_MEANINGFUL_COOKS_D) {
      dominance = 0;
    } else if (sortedCooksD[1] < MIN_MEANINGFUL_COOKS_D) {
      dominance = Infinity;
    } else {
      dominance = sortedCooksD[0] / sortedCooksD[1];
    }

    let verdict;
    if (dominance > 5) verdict = 'outlier';
    else if (reset.significant) verdict = 'non-linear';
    else if (bp.significant) verdict = 'heteroscedastic';
    else verdict = 'well-behaved';

    return { verdict, reg, bp, reset, dominance, maxCooksD: sortedCooksD[0] };
  }

  const CONCEPT_QUESTIONS = [
    {
      id: 'c1',
      prompt: 'A residual-vs-fitted plot fans out into a funnel shape as fitted values increase. What does this most directly suggest?',
      options: ['Multicollinearity', 'Heteroscedasticity', 'A missing quadratic term', 'Perfect fit'],
      correct: 1,
      explanation: 'A funnel shape means the spread of residuals grows with the fitted value — the classic signature of non-constant error variance (heteroscedasticity), which the Breusch-Pagan test targets directly.',
    },
    {
      id: 'c2',
      prompt: 'On a Q-Q plot of standardized residuals, what pattern indicates the residuals are approximately normally distributed?',
      options: [
        'Points curve sharply away from the diagonal at both ends',
        'Points fall roughly along the 45° reference line',
        'Points cluster only in the middle',
        'Points form a U-shape',
      ],
      correct: 1,
      explanation: 'A Q-Q plot compares sorted sample quantiles to theoretical normal quantiles — points tracking the diagonal line means the two distributions match well.',
    },
    {
      id: 'c3',
      prompt: 'What does leverage (the hat value h_ii) measure for a data point in simple linear regression?',
      options: [
        'How far the point is from the regression line vertically',
        'How unusual the point\'s x-value is relative to the other x-values',
        'The point\'s contribution to R²',
        'Whether the point was recorded correctly',
      ],
      correct: 1,
      explanation: 'Leverage depends only on x, not y — it measures how far a point sits from the mean of the predictors. A point can have high leverage yet a small residual, or vice versa.',
    },
    {
      id: 'c4',
      prompt: 'Cook\'s Distance combines which two things?',
      options: [
        'The residual and R² only',
        'Leverage and the size of the residual',
        'Sample size and the intercept',
        'The correlation between two predictors',
      ],
      correct: 1,
      explanation: "Cook's Distance is large only when a point has both a sizable residual AND high leverage — it captures how much the fitted coefficients would change if that point were removed.",
    },
    {
      id: 'c5',
      prompt: 'The Variance Inflation Factor (VIF) for a predictor is 1 / (1 - R²), where R² comes from regressing that predictor on the other predictors. A VIF of 20 means:',
      options: [
        'The predictor explains 20% of the outcome',
        'The predictor is almost perfectly predictable from the other predictors, inflating its coefficient\'s standard error',
        'There are 20 predictors in the model',
        'The model has 20% more error than expected',
      ],
      correct: 1,
      explanation: 'High VIF means a predictor is redundant with the others — R_aux² close to 1 — which inflates SE(β) even though overall model fit (R²) may look fine.',
    },
    {
      id: 'c6',
      prompt: 'Why can adding an x² term and testing its coefficient (a RESET-style test) detect non-linearity?',
      options: [
        'It always improves R², so any improvement proves non-linearity',
        'If the true relationship curves, a straight line leaves a curved pattern in the residuals that a quadratic term will pick up as a significant coefficient',
        'It removes outliers automatically',
        'It converts the regression into logistic regression',
      ],
      correct: 1,
      explanation: 'A significant quadratic coefficient means curvature in the data is systematically unexplained by the straight-line fit — direct evidence the linearity assumption is violated.',
    },
    {
      id: 'c7',
      prompt: 'Multicollinearity between two predictors mainly threatens which part of a regression?',
      options: [
        'The overall R² of the model',
        'The precision (standard errors) of the individual coefficient estimates',
        'The number of data points needed',
        'Whether residuals are normally distributed',
      ],
      correct: 1,
      explanation: 'Two correlated predictors can still jointly predict y well (R² stays high), but the model can no longer tell their individual effects apart cleanly — so SE(β) inflates for both.',
    },
    {
      id: 'c8',
      prompt: 'A common rule of thumb flags a point as highly influential when its Cook\'s Distance exceeds:',
      options: ['1000', '4 / n', 'The R² value', 'The sample mean'],
      correct: 1,
      explanation: '4/n is a widely used (if somewhat aggressive) rule of thumb — it scales down as sample size grows, since any single point should matter less in a larger sample.',
    },
  ];

  /** Builds a shuffled, deterministic quiz session from a numeric seed. */
  function buildQuizSession(seed) {
    const rand = M.seededRandom(seed);
    const diagnoseKeys = D.PRESET_ORDER.filter((k) => k !== 'custom');

    function shuffle(arr) {
      const a = arr.slice();
      for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(rand() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
      }
      return a;
    }

    const diagnoseQuestions = shuffle(diagnoseKeys).map((key, idx) => {
      const preset = D.PRESETS[key];
      const diagnosis = diagnoseDataset(preset.points);
      const optionKeys = shuffle(['outlier', 'non-linear', 'heteroscedastic', 'well-behaved']);
      return {
        id: `d${idx}`,
        type: 'diagnose',
        presetKey: key,
        points: preset.points,
        reg: diagnosis.reg,
        prompt: `This dataset's regression diagnostics are shown below. Which issue best describes what's happening?`,
        options: optionKeys.map((k) => DIAGNOSIS_LABELS[k]),
        correctIndex: optionKeys.indexOf(diagnosis.verdict),
        verdict: diagnosis.verdict,
      };
    });

    const conceptQuestions = shuffle(CONCEPT_QUESTIONS).map((q) => ({
      id: q.id,
      type: 'concept',
      prompt: q.prompt,
      options: q.options,
      correctIndex: q.correct,
      explanation: q.explanation,
    }));

    return shuffle([...diagnoseQuestions, ...conceptQuestions]);
  }

  const RegressionQuiz = { diagnoseDataset, DIAGNOSIS_LABELS, CONCEPT_QUESTIONS, buildQuizSession };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = RegressionQuiz;
  }
  if (typeof root !== 'undefined') {
    root.RegressionQuiz = RegressionQuiz;
  }
})(typeof window !== 'undefined' ? window : global);
