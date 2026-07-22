// Builds the AI-narrative paragraph interpreting the current computed numbers.
// If a session-only Anthropic API key is supplied, calls api.anthropic.com directly
// from the browser. If not, produces a deterministic template from the same numbers.
// No personal data is ever included in the prompt — only scenario label/description
// and the already-on-screen computed statistics.

(function (global) {
  'use strict';

  const MODEL = 'claude-haiku-4-5-20251001';

  function fmtPct(x) {
    return (x * 100).toFixed(1) + '%';
  }

  function buildPrompt(state) {
    const { scenarioLabel, scenarioDescription, p0, prior, posterior, n, successes, ci, probGreater, bf, pValue, wilson } = state;
    return [
      `You are helping a researcher interpret a Bayesian analysis. Write a plain-English paragraph (4-6 sentences, no headers, no bullet points) explaining what the following result means for their study. Be precise but not overly technical.`,
      ``,
      `Scenario: ${scenarioLabel} — ${scenarioDescription}`,
      `Threshold/null value (p0): ${p0}`,
      `Prior: Beta(${prior.alpha}, ${prior.beta})`,
      `Data observed: ${successes} successes out of ${n} trials`,
      `Posterior: Beta(${posterior.alpha}, ${posterior.beta}), mean ${fmtPct(posterior.mean)}`,
      `95% credible interval: [${fmtPct(ci.lower)}, ${fmtPct(ci.upper)}]`,
      `P(true rate > ${p0}): ${fmtPct(probGreater)}`,
      `Bayes factor BF10 (effect vs. null): ${bf.bf10.toFixed(2)} (${bf.label})`,
      `For contrast, the frequentist answer: 95% Wilson CI [${fmtPct(wilson.lower)}, ${fmtPct(wilson.upper)}], exact binomial test p = ${pValue.toFixed(4)}`,
    ].join('\n');
  }

  function templateNarrative(state) {
    const { scenarioLabel, p0, posterior, n, successes, ci, probGreater, bf, pValue } = state;
    const evidenceSide = bf.bf10 >= 1 ? 'in favor of the effect over the null' : 'in favor of the null over the effect';
    return (
      `After observing ${successes} out of ${n} trials in the "${scenarioLabel}" scenario, the posterior distribution ` +
      `Beta(${posterior.alpha}, ${posterior.beta}) puts the best estimate of the true rate at ${fmtPct(posterior.mean)}, ` +
      `with 95% credible interval [${fmtPct(ci.lower)}, ${fmtPct(ci.upper)}] — meaning, given this prior and this data, there is a 95% ` +
      `probability the true rate falls in that range. The probability the true rate exceeds ${p0} is ${fmtPct(probGreater)}. ` +
      `The Bayes factor (BF10 = ${bf.bf10.toFixed(2)}) represents ${bf.label}, ${evidenceSide}. ` +
      `For comparison, the classical (frequentist) two-sided test against the same threshold gives p = ${pValue.toFixed(4)} — ` +
      `a statement about how often this procedure would be wrong in repeated sampling, not a probability about the true rate itself, ` +
      `which is the core interpretive difference between the two frameworks.`
    );
  }

  // Calls the Anthropic Messages API directly from the browser with a session-only key.
  // Never persists the key; never sends anything beyond the already-displayed numbers.
  async function fetchAiNarrative(state, apiKey, fetchImpl) {
    const doFetch = fetchImpl || global.fetch;
    const response = await doFetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 400,
        messages: [{ role: 'user', content: buildPrompt(state) }],
      }),
    });
    if (!response.ok) {
      throw new Error('Anthropic API request failed with status ' + response.status);
    }
    const data = await response.json();
    const block = (data.content || []).find((c) => c.type === 'text');
    if (!block || !block.text) {
      throw new Error('Anthropic API response contained no text content');
    }
    return block.text;
  }

  async function generateNarrative(state, apiKey, fetchImpl) {
    if (!apiKey) {
      return { text: templateNarrative(state), source: 'template' };
    }
    try {
      const text = await fetchAiNarrative(state, apiKey, fetchImpl);
      return { text, source: 'ai' };
    } catch (err) {
      return { text: templateNarrative(state) + '\n\n(AI narrative unavailable, showing template instead: ' + err.message + ')', source: 'template-fallback' };
    }
  }

  const AiNarrative = { buildPrompt, templateNarrative, fetchAiNarrative, generateNarrative };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = AiNarrative;
  } else {
    global.AiNarrative = AiNarrative;
  }
})(typeof window !== 'undefined' ? window : globalThis);
