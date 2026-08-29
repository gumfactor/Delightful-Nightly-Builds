// Zebra Lab — optional AI explainer.
// With no API key: returns the deterministic template from logic.js/data.js (no network call).
// With a key (entered by the user, kept only in sessionStorage): makes one direct
// client-side call to the Anthropic Messages API to polish the phrasing of the SAME
// factual content the fallback already produces — it never invents the underlying claim.

const ZL_AI_MODEL = 'claude-haiku-4-5-20251001';
const ZL_AI_ENDPOINT = 'https://api.anthropic.com/v1/messages';

function zlGetSessionApiKey() {
  try {
    return sessionStorage.getItem('zebralab_api_key') || '';
  } catch (e) {
    return '';
  }
}

function zlSetSessionApiKey(key) {
  try {
    if (key) sessionStorage.setItem('zebralab_api_key', key);
    else sessionStorage.removeItem('zebralab_api_key');
  } catch (e) {
    // sessionStorage unavailable (e.g. privacy mode) — silently no-op, fallback still works
  }
}

// Picks one Confound Control / Threat to Validity pairing present in a solved puzzle
// (first study position that has both attributes) to explain.
function zlPickExplainerPair(puzzle) {
  const hasConfound = puzzle.categories.some(function (c) {
    return c.id === 'confound';
  });
  const hasThreat = puzzle.categories.some(function (c) {
    return c.id === 'threat';
  });
  if (!hasConfound || !hasThreat) return null;
  const confoundCat = zlFindCategory(puzzle.categories, 'confound');
  const threatCat = zlFindCategory(puzzle.categories, 'threat');
  const confoundValIdx = puzzle.solution.confound[0];
  const threatValIdx = puzzle.solution.threat[0];
  return {
    confoundId: confoundCat.values[confoundValIdx].id,
    confoundLabel: confoundCat.values[confoundValIdx].label,
    threatId: threatCat.values[threatValIdx].id,
    threatLabel: threatCat.values[threatValIdx].label,
  };
}

async function zlFetchAIExplanation(pair, apiKey) {
  const fallback = zlComposeExplanation(pair.confoundId, pair.threatId);
  if (!apiKey) return { text: fallback, source: 'fallback' };

  const prompt =
    'In two short sentences, explain the relationship between the research-methods confound-control ' +
    'method "' +
    pair.confoundLabel +
    '" and the threat to validity "' +
    pair.threatLabel +
    '". Base your answer only on these established facts, just rephrase them more naturally: "' +
    fallback +
    '" Do not introduce any new claims.';

  try {
    const response = await fetch(ZL_AI_ENDPOINT, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: ZL_AI_MODEL,
        max_tokens: 200,
        messages: [{ role: 'user', content: prompt }],
      }),
    });
    if (!response.ok) return { text: fallback, source: 'fallback' };
    const data = await response.json();
    const text = data && data.content && data.content[0] && data.content[0].text;
    if (!text) return { text: fallback, source: 'fallback' };
    return { text: text.trim(), source: 'ai' };
  } catch (e) {
    return { text: fallback, source: 'fallback' };
  }
}
