// Optional AI-generated practice scenario for the Scenario Quiz tab.
// If a session-only Anthropic API key is supplied, calls api.anthropic.com directly
// from the browser (Claude Haiku) to draft a new SDT scenario from a short research
// context typed by the user. If no key is supplied — or the call fails — a
// deterministic, string-seeded fallback generator produces a fully usable scenario
// with zero network calls. The key is never persisted (not written to localStorage
// or anywhere else) and no personal data is ever included in the prompt — only the
// short context string the user typed.

(function (global) {
  'use strict';

  const MODEL = 'claude-haiku-4-5-20251001';

  // Small deterministic string hash (djb2) so the fallback is reproducible for a
  // given context string within a session, rather than depending on Math.random().
  function hashString(str) {
    let hash = 5381;
    for (let i = 0; i < str.length; i++) {
      hash = (hash * 33) ^ str.charCodeAt(i);
    }
    return hash >>> 0;
  }

  function buildPrompt(context) {
    return [
      'You are helping write a practice scenario for a Signal Detection Theory (SDT) training tool.',
      `Research context supplied by the user: "${context}"`,
      '',
      'Write a short (3-5 sentence) plausible research scenario description for this context, framed ',
      'as a signal-present/signal-absent detection task. Then propose plausible hit, miss, false-alarm, ',
      'and correct-rejection counts (integers, hits+misses between 20 and 100, falseAlarms+correctRejections ',
      'the same total as hits+misses) that a real study in this area might produce.',
      '',
      'Respond with ONLY a JSON object, no other text, in exactly this shape:',
      '{"title": "...", "description": "...", "hits": 0, "misses": 0, "falseAlarms": 0, "correctRejections": 0}',
    ].join('\n');
  }

  // Deterministic fallback: derives plausible-looking counts from a hash of the
  // context string so the same input always yields the same scenario.
  function templateScenario(context) {
    const seed = hashString(context || 'signal detection');
    const nSignal = 40 + (seed % 21); // 40-60
    const nNoise = nSignal;
    const hitRatePct = 55 + (seed % 35); // 55-89
    const faRatePct = 10 + ((seed >> 8) % 35); // 10-44
    const hits = Math.round((hitRatePct / 100) * nSignal);
    const misses = nSignal - hits;
    const falseAlarms = Math.round((faRatePct / 100) * nNoise);
    const correctRejections = nNoise - falseAlarms;
    const trimmedContext = (context || 'a general detection task').trim();
    return {
      id: 'ai-generated-' + seed,
      title: 'Practice Scenario: ' + (trimmedContext || 'Detection Task'),
      domain: 'Generated practice scenario',
      description:
        'A hypothetical detection study in the context of "' + trimmedContext + '." ' +
        nSignal + ' signal-present trials and ' + nNoise + ' signal-absent trials were run; ' +
        'participants judged each as present or absent.',
      hits, misses, falseAlarms, correctRejections,
    };
  }

  function parseAiResponse(text, context) {
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error('AI response did not contain a JSON object');
    }
    const parsed = JSON.parse(jsonMatch[0]);
    const required = ['title', 'description', 'hits', 'misses', 'falseAlarms', 'correctRejections'];
    for (const field of required) {
      if (!(field in parsed)) {
        throw new Error('AI response JSON missing field: ' + field);
      }
    }
    return {
      id: 'ai-generated-' + hashString(context + text),
      title: String(parsed.title),
      domain: 'AI-generated practice scenario',
      description: String(parsed.description),
      hits: Math.max(0, Math.round(Number(parsed.hits))),
      misses: Math.max(0, Math.round(Number(parsed.misses))),
      falseAlarms: Math.max(0, Math.round(Number(parsed.falseAlarms))),
      correctRejections: Math.max(0, Math.round(Number(parsed.correctRejections))),
    };
  }

  async function fetchAiScenario(context, apiKey, fetchImpl) {
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
        messages: [{ role: 'user', content: buildPrompt(context) }],
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
    return parseAiResponse(block.text, context);
  }

  async function generateScenario(context, apiKey, fetchImpl) {
    if (!apiKey) {
      return { scenario: templateScenario(context), source: 'template' };
    }
    try {
      const scenario = await fetchAiScenario(context, apiKey, fetchImpl);
      return { scenario, source: 'ai' };
    } catch (err) {
      return {
        scenario: templateScenario(context),
        source: 'template-fallback',
        error: err.message,
      };
    }
  }

  const AiScenario = { buildPrompt, templateScenario, parseAiResponse, fetchAiScenario, generateScenario, hashString };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = AiScenario;
  } else {
    global.AiScenario = AiScenario;
  }
})(typeof window !== 'undefined' ? window : globalThis);
