// Optional "explain this in plain English" layer. Sends ONLY the already-
// computed aggregate statistics for the current sample (never raw X/M/Y/Z
// rows) directly from the browser to the Claude API, using a session-only
// API key the user types into a field (never written to localStorage or
// sent anywhere but api.anthropic.com). With no key set, an unconditional
// deterministic template is returned and zero network calls are made.

const AI_MODEL = 'claude-3-5-haiku-20241022';

function fmtPValue(p) {
  return p < 0.001 ? '<0.001' : p.toFixed(3);
}

function deterministicMediationExplanation(stats) {
  const sig = stats.ciExcludesZero ? 'statistically significant' : 'not statistically significant';
  const dir = stats.indirect >= 0 ? 'positive' : 'negative';
  return (
    `The indirect effect (a x b = ${stats.indirect.toFixed(3)}) is ${dir} and ${sig} at the ` +
    `95% level: the bootstrap confidence interval [${stats.bootstrapCI[0].toFixed(3)}, ` +
    `${stats.bootstrapCI[1].toFixed(3)}] ${stats.ciExcludesZero ? 'excludes' : 'includes'} zero. ` +
    `The direct effect after accounting for the mediator (c' = ${stats.cPrime.toFixed(3)}) ` +
    `${Math.abs(stats.cPrime) < Math.abs(stats.c) ? 'is smaller than' : 'is not smaller than'} ` +
    `the total effect (c = ${stats.c.toFixed(3)}), consistent with ${Math.abs(stats.cPrime) < Math.abs(stats.c) ? 'at least partial' : 'little'} mediation through M.`
  );
}

function deterministicModerationExplanation(stats) {
  const sig = stats.interactionSignificant ? 'a statistically significant' : 'no statistically significant';
  let regionText;
  if (!stats.jnRoots) {
    regionText = 'The Johnson-Neyman analysis found no finite boundary, meaning the slope\'s significance does not change sign anywhere in the moderator\'s realistic range.';
  } else if (stats.jnRoots.length === 1) {
    regionText = `The Johnson-Neyman boundary sits at Z = ${stats.jnRoots[0].toFixed(2)} (relative to the moderator's mean).`;
  } else {
    regionText = `The Johnson-Neyman region of significance lies outside Z = ${stats.jnRoots[0].toFixed(2)} to ${stats.jnRoots[1].toFixed(2)} (relative to the moderator's mean).`;
  }
  return (
    `This sample shows ${sig} interaction effect (b3 = ${stats.beta[3].toFixed(3)}, p = ${fmtPValue(stats.interactionP)}). ` +
    `${regionText} ` +
    `At +1 SD of the moderator the simple slope is ${stats.simpleSlopes[2].slope.toFixed(3)} (${stats.simpleSlopes[2].significant ? 'significant' : 'not significant'}), ` +
    `while at -1 SD it is ${stats.simpleSlopes[0].slope.toFixed(3)} (${stats.simpleSlopes[0].significant ? 'significant' : 'not significant'}).`
  );
}

async function requestAIExplanation(kind, stats, apiKey) {
  const fallback = kind === 'mediation'
    ? deterministicMediationExplanation(stats)
    : deterministicModerationExplanation(stats);

  if (!apiKey) {
    return { text: fallback, source: 'deterministic' };
  }

  const aggregatePayload = kind === 'mediation'
    ? {
        a: stats.a, b: stats.b, cPrime: stats.cPrime, c: stats.c,
        indirect: stats.indirect, bootstrapCI: stats.bootstrapCI,
        sobelZ: stats.sobelZ, sobelP: stats.sobelP,
      }
    : {
        beta: stats.beta, interactionP: stats.interactionP,
        simpleSlopes: stats.simpleSlopes.map(s => ({ label: s.label, slope: s.slope, p: s.p })),
        jnRoots: stats.jnRoots,
      };

  const prompt =
    `You are helping a psychology professor interpret a ${kind} analysis result for teaching purposes. ` +
    `Here are the computed statistics as JSON: ${JSON.stringify(aggregatePayload)}. ` +
    `Write a 2-3 sentence plain-English interpretation suitable for a student, focused on what the ` +
    `numbers mean substantively. Do not invent any numbers not given above.`;

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: AI_MODEL,
        max_tokens: 220,
        messages: [{ role: 'user', content: prompt }],
      }),
    });
    if (!response.ok) return { text: fallback, source: 'deterministic' };
    const data = await response.json();
    const text = data && data.content && data.content[0] && data.content[0].text;
    if (!text) return { text: fallback, source: 'deterministic' };
    return { text, source: 'ai' };
  } catch (e) {
    return { text: fallback, source: 'deterministic' };
  }
}
