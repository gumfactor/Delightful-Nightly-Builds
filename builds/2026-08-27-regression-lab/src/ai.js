/**
 * Regression Lab — optional AI explanation layer.
 * Calls the Anthropic API directly from the browser using a session-only
 * key (never persisted, never sent anywhere but api.anthropic.com).
 * Every call site has an unconditional deterministic fallback so the app
 * is fully functional with zero network access and no key.
 */

(function (root) {
  const ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001';
  const ANTHROPIC_ENDPOINT = 'https://api.anthropic.com/v1/messages';

  /**
   * Builds a deterministic, template-based explanation from the already-
   * computed diagnostic numbers. Used whenever no API key is set or the
   * live call fails for any reason.
   */
  function deterministicExplanation(context) {
    const { verdict, bp, reset, maxCooksD, cooksThreshold, r2 } = context;
    const r2Pct = (r2 * 100).toFixed(1);
    switch (verdict) {
      case 'heteroscedastic':
        return `The Breusch-Pagan test found a significant relationship between the fitted values and the squared residuals (p = ${bp.pValue.toFixed(4)}), meaning the spread of errors changes systematically across the range of predictions. Standard errors and confidence intervals from this fit are unreliable as-is — a heteroscedasticity-robust standard error or a variance-stabilizing transform would be the usual next step. R² is ${r2Pct}%, but that number alone hides the problem.`;
      case 'non-linear':
        return `Adding a squared term to the model came back significant (RESET-style test, p = ${reset.pValue.toFixed(4)}), which means a straight line is missing real curvature in the relationship. R² of ${r2Pct}% understates how well x actually predicts y — a polynomial or non-linear model would likely fit substantially better without needing more data.`;
      case 'outlier':
        return `One point's Cook's Distance (${maxCooksD.toFixed(2)}) is far above the ${cooksThreshold.toFixed(3)} rule-of-thumb threshold and dominates every other point's influence — removing it would noticeably change the fitted line. Worth checking whether that point is a data-entry error, a genuinely different regime, or real signal worth modeling separately before trusting this fit.`;
      default:
        return `Neither the Breusch-Pagan nor the RESET-style linearity test came back significant, and no single point's Cook's Distance stands out (max ${maxCooksD.toFixed(2)} vs. a ${cooksThreshold.toFixed(3)} threshold). With R² at ${r2Pct}%, this is a reasonably well-behaved fit — the classic OLS assumptions look defensible here.`;
    }
  }

  /**
   * Calls Claude Haiku directly from the browser with a user-supplied,
   * session-only API key. Returns { text, source: 'ai' | 'fallback' }.
   * Never throws — any failure resolves to the deterministic fallback.
   */
  async function explainDiagnostic(context, apiKey) {
    const fallback = { text: deterministicExplanation(context), source: 'fallback' };
    if (!apiKey) return fallback;

    const prompt = `You are a statistics tutor. In 2-3 plain-English sentences, explain what this regression diagnostic result means and why it matters for someone learning about OLS assumptions. Aggregate numbers only, no raw data: verdict=${context.verdict}, R2=${context.r2.toFixed(3)}, Breusch-Pagan p=${context.bp.pValue.toFixed(4)}, RESET p=${context.reset.pValue.toFixed(4)}, max Cook's D=${context.maxCooksD.toFixed(3)} (threshold ${context.cooksThreshold.toFixed(3)}).`;

    try {
      const response = await fetch(ANTHROPIC_ENDPOINT, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        body: JSON.stringify({
          model: ANTHROPIC_MODEL,
          max_tokens: 220,
          messages: [{ role: 'user', content: prompt }],
        }),
      });
      if (!response.ok) return fallback;
      const data = await response.json();
      const text = data && data.content && data.content[0] && data.content[0].text;
      if (!text) return fallback;
      return { text: text.trim(), source: 'ai' };
    } catch (err) {
      return fallback;
    }
  }

  const RegressionAI = { deterministicExplanation, explainDiagnostic };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = RegressionAI;
  }
  if (typeof root !== 'undefined') {
    root.RegressionAI = RegressionAI;
  }
})(typeof window !== 'undefined' ? window : global);
