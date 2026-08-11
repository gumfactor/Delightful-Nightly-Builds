// Optional AI historical-context note. Direct browser call to the Anthropic API
// using a session-only, never-persisted key. Sends only the round's aggregate
// public data (ticker/sector/industry/dates/pct move) — never the chart arrays.
// Always falls back to a deterministic template when no key is set or the call fails.

const ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages';
const ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001';

function buildFallbackNote(round) {
  const move = round.forward.pctChange;
  const dir = move > 0 ? 'gained' : move < 0 ? 'lost' : 'stayed roughly flat, moving';
  return (
    `${round.ticker} (${round.sector}) ${dir} ${Math.abs(move).toFixed(1)}% between ` +
    `${round.decisionDate} and ${round.forward.endDate}. This is a single historical data ` +
    `point, not a pattern — one ticker's quarter says very little about how predictable ` +
    `short-term stock moves are in general.`
  );
}

async function fetchAiNote(apiKey, round) {
  const direction = round.forward.pctChange > 0 ? 'up' : round.forward.pctChange < 0 ? 'down' : 'roughly flat';
  const payload = {
    model: ANTHROPIC_MODEL,
    max_tokens: 200,
    messages: [
      {
        role: 'user',
        content:
          `In 2-3 sentences, give plain-English historical context for why ${round.ticker} ` +
          `(sector: ${round.sector}, industry: ${round.industry}) might have moved ${direction} ` +
          `(${round.forward.pctChange.toFixed(1)}%) between ${round.decisionDate} and ` +
          `${round.forward.endDate}. Be factual and general — no investment advice.`,
      },
    ],
  };

  const response = await fetch(ANTHROPIC_API_URL, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'anthropic-dangerous-direct-browser-access': 'true',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Anthropic API error: ${response.status}`);
  }
  const data = await response.json();
  const text = data && data.content && data.content[0] && data.content[0].text;
  if (!text) throw new Error('Unexpected Anthropic response shape');
  return text.trim();
}

async function getAiOrFallbackNote(apiKey, round) {
  if (!apiKey) return buildFallbackNote(round);
  try {
    const note = await fetchAiNote(apiKey, round);
    return note || buildFallbackNote(round);
  } catch (e) {
    return buildFallbackNote(round);
  }
}
