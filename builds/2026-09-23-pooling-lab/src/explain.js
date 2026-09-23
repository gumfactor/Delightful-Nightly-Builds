/*
 * Pooling Lab — optional "Explain This" AI panel.
 *
 * Never calls the network unless the user has typed their own Anthropic API
 * key into the session-only field. Only numeric simulation summary values
 * are sent (no personal data). The response is always rendered via
 * `textContent`, never `innerHTML`, so a hostile or malformed API response
 * can never execute as script on this page.
 */
(function (global) {
  'use strict';

  function buildDeterministicExplanation(summary) {
    const weakest = summary.perGroup.reduce((a, b) => (b.shrinkageWeight < a.shrinkageWeight ? b : a));
    const strongest = summary.perGroup.reduce((a, b) => (b.shrinkageWeight > a.shrinkageWeight ? b : a));
    const iccText =
      summary.empiricalICC === null
        ? 'The empirical ICC could not be estimated (fewer than 2 usable groups).'
        : 'The empirical ICC estimated from this sample is ' +
          summary.empiricalICC.toFixed(3) +
          ', versus a true generating ICC of ' +
          summary.trueICC.toFixed(3) +
          '.';
    return (
      'True ICC = ' +
      summary.trueICC.toFixed(3) +
      '. ' +
      iccText +
      ' Group ' +
      weakest.id +
      ' (n=' +
      weakest.n +
      ') has the lowest shrinkage weight (' +
      weakest.shrinkageWeight.toFixed(2) +
      '), so its estimate is pulled hardest toward the grand mean (' +
      summary.grandMean.toFixed(2) +
      '). Group ' +
      strongest.id +
      ' (n=' +
      strongest.n +
      ') has the highest shrinkage weight (' +
      strongest.shrinkageWeight.toFixed(2) +
      '), so its own raw mean is trusted almost as-is.'
    );
  }

  function buildPrompt(summary) {
    const rows = summary.perGroup
      .map(
        (g) =>
          'group ' +
          g.id +
          ': n=' +
          g.n +
          ', raw mean=' +
          g.noPooling.toFixed(2) +
          ', shrinkage weight=' +
          g.shrinkageWeight.toFixed(2) +
          ', partial-pooling estimate=' +
          g.partialPooling.toFixed(2)
      )
      .join('; ');
    return (
      'You are explaining a multilevel-model partial-pooling simulation to a psychology researcher. ' +
      'Grand mean (complete pooling) = ' +
      summary.grandMean.toFixed(2) +
      '. True ICC = ' +
      summary.trueICC.toFixed(3) +
      '. Empirical ICC = ' +
      (summary.empiricalICC === null ? 'not computable' : summary.empiricalICC.toFixed(3)) +
      '. Per-group data: ' +
      rows +
      '. In 2-3 sentences, explain in plain English why the groups with smaller shrinkage weights shrink more toward the grand mean. Do not invent numbers not given.'
    );
  }

  /**
   * @param {string} apiKey - trimmed API key, may be empty.
   * @param {Object} summary - PoolingStats.computePoolingSummary output.
   * @param {HTMLElement} outputEl - element whose textContent is set with the result.
   * @param {Function} [fetchImpl] - injectable fetch for testing; defaults to global fetch.
   */
  function requestExplanation(apiKey, summary, outputEl, fetchImpl) {
    const doFetch = fetchImpl || (typeof fetch !== 'undefined' ? fetch : null);
    const fallback = buildDeterministicExplanation(summary);

    if (!apiKey) {
      outputEl.textContent = fallback;
      return Promise.resolve();
    }
    if (!doFetch) {
      outputEl.textContent = fallback;
      return Promise.resolve();
    }

    outputEl.textContent = 'Contacting Claude…';
    const prompt = buildPrompt(summary);

    return doFetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 300,
        messages: [{ role: 'user', content: prompt }],
      }),
    })
      .then(function (response) {
        if (!response.ok) throw new Error('API error ' + response.status);
        return response.json();
      })
      .then(function (data) {
        const text =
          data && data.content && data.content[0] && typeof data.content[0].text === 'string'
            ? data.content[0].text
            : null;
        outputEl.textContent = text || fallback;
      })
      .catch(function () {
        outputEl.textContent = fallback;
      });
  }

  global.PoolingExplain = { buildDeterministicExplanation, buildPrompt, requestExplanation };
})(typeof window !== 'undefined' ? window : globalThis);
