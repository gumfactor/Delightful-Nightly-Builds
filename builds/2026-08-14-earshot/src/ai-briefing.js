/**
 * Optional AI exposure briefing. Direct browser call to the Anthropic API
 * using a session-only, never-persisted key. Sends only a completed
 * session's aggregate numbers (venue label, avg/peak dB, duration, dose %)
 * — never raw audio, waveform data, or the per-second series. Always falls
 * back to a deterministic template when no key is set or the call fails.
 */

const ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages';
const ANTHROPIC_MODEL = 'claude-haiku-4-5-20251001';

function buildFallbackBriefing(session) {
  const parts = [];
  parts.push(
    `${session.venue || 'This session'} averaged ${session.avgDb.toFixed(1)} dB(A) over ` +
      `${Math.round(session.durationSec)}s, peaking at ${session.peakDb.toFixed(1)} dB(A).`
  );
  if (session.doseDeltaPct < 1) {
    parts.push('That contributes a negligible amount to today\'s recommended noise exposure dose.');
  } else if (session.doseDeltaPct < 25) {
    parts.push(`That used about ${session.doseDeltaPct.toFixed(1)}% of today's recommended NIOSH noise dose — a small contribution.`);
  } else {
    parts.push(`That alone used ${session.doseDeltaPct.toFixed(1)}% of today's recommended NIOSH noise dose — worth noting if you'll be in similarly loud places again today.`);
  }
  return parts.join(' ');
}

async function fetchAiBriefing(apiKey, session) {
  const payload = {
    model: ANTHROPIC_MODEL,
    max_tokens: 200,
    messages: [
      {
        role: 'user',
        content:
          `Write a 2-3 sentence, plain-English noise-exposure briefing for someone who just measured ` +
          `ambient sound at "${session.venue || 'an unnamed location'}". Average level: ` +
          `${session.avgDb.toFixed(1)} dB(A). Peak level: ${session.peakDb.toFixed(1)} dB(A). ` +
          `Duration: ${Math.round(session.durationSec)} seconds. This session used ` +
          `${session.doseDeltaPct.toFixed(1)}% of a standard NIOSH daily 85dB/8hr noise exposure dose. ` +
          `Be factual, reassuring where warranted, and note any hearing-safety consideration only if ` +
          `genuinely relevant. No medical advice, no alarmism.`,
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

async function getAiOrFallbackBriefing(apiKey, session) {
  if (!apiKey) return buildFallbackBriefing(session);
  try {
    const text = await fetchAiBriefing(apiKey, session);
    return text || buildFallbackBriefing(session);
  } catch (err) {
    return buildFallbackBriefing(session);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { buildFallbackBriefing, fetchAiBriefing, getAiOrFallbackBriefing };
}
