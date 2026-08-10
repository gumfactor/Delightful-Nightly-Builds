// Optional AI Data Quality Briefing. If a session-only Anthropic API key is
// supplied, calls api.anthropic.com directly from the browser (Claude
// Haiku) to turn the run's aggregate issue counts into a one-paragraph
// plain-English briefing. If no key is supplied — or the call fails — a
// deterministic rule-based template produces a fully usable briefing with
// zero network calls.
//
// Privacy guarantee by construction: the only argument this module ever
// receives is a `summary` object of counts (see validator.js's
// `summary: { totalRows, validRows, errorRows, warningRows, byCode }`) —
// never a parsed row or a single cell value. No raw business data can reach
// this module, let alone the network.

(function (global) {
  'use strict';

  const MODEL = 'claude-haiku-4-5-20251001';

  const CODE_LABELS = {
    missing_required_column: 'a required column missing entirely from the header',
    unexpected_column: 'columns not defined in your schema',
    malformed_row: 'rows with the wrong number of fields',
    missing_required_value: 'empty values in required columns',
    invalid_url: 'invalid website URLs',
    invalid_email: 'invalid email addresses',
    invalid_number: 'non-numeric values in a number column',
    invalid_date: 'invalid dates',
    invalid_enum: 'values outside the allowed category list',
    whitespace: 'stray leading/trailing whitespace',
    encoding_control_char: 'non-printable control characters',
    encoding_replacement_char: 'characters that suggest the file is not valid UTF-8',
    encoding_mojibake: 'text that looks mis-decoded (mojibake)',
    duplicate_row: 'exact duplicate rows',
    duplicate_key: 'duplicate values in a column marked unique (e.g. repeated business listings)',
  };

  function buildPrompt(summary) {
    return [
      'You are a data-quality assistant reviewing a CSV ingestion QC run for a business directory.',
      'You are given ONLY aggregate issue counts — never any actual row data.',
      'Aggregate summary (JSON): ' + JSON.stringify(summary),
      '',
      'Write one short paragraph (3-5 sentences) in plain English telling the operator what to fix ',
      'first before ingesting this file, prioritizing the highest-count issue types. Be specific and ',
      'practical. Do not invent data that is not in the summary. Respond with plain text only, no markdown.',
    ].join('\n');
  }

  function topCodes(byCode, n) {
    return Object.entries(byCode || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, n);
  }

  // Deterministic, rule-based fallback — no randomness, no network.
  function templateBriefing(summary) {
    const { totalRows, validRows, errorRows, warningRows, byCode } = summary;
    if (!totalRows) {
      return 'No rows were found in this file — nothing to report.';
    }
    const pctValid = Math.round((validRows / totalRows) * 100);
    const sentences = [];
    sentences.push(
      `Of ${totalRows} row(s) checked, ${validRows} (${pctValid}%) are clean, ` +
        `${errorRows} contain blocking errors, and ${warningRows} have non-blocking warnings.`
    );

    const top = topCodes(byCode, 3);
    if (top.length > 0) {
      const parts = top.map(([code, count]) => `${CODE_LABELS[code] || code} (${count})`);
      sentences.push(`The most common issues are: ${parts.join('; ')}.`);
    }

    if (errorRows > 0) {
      sentences.push('Fix the flagged errors before this file is ingested into the live directory.');
    } else if (warningRows > 0) {
      sentences.push('No blocking errors were found, but review the warnings before ingesting.');
    } else {
      sentences.push('This file is clean and ready to ingest.');
    }

    return sentences.join(' ');
  }

  async function fetchAiBriefing(summary, apiKey, fetchImpl) {
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
        max_tokens: 300,
        messages: [{ role: 'user', content: buildPrompt(summary) }],
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
    return block.text.trim();
  }

  async function generateBriefing(summary, apiKey, fetchImpl) {
    if (!apiKey) {
      return { text: templateBriefing(summary), source: 'template' };
    }
    try {
      const text = await fetchAiBriefing(summary, apiKey, fetchImpl);
      return { text, source: 'ai' };
    } catch (err) {
      return { text: templateBriefing(summary), source: 'template-fallback', error: err.message };
    }
  }

  const AiBriefing = { buildPrompt, templateBriefing, fetchAiBriefing, generateBriefing, CODE_LABELS };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = AiBriefing;
  } else {
    global.AiBriefing = AiBriefing;
  }
})(typeof window !== 'undefined' ? window : globalThis);
