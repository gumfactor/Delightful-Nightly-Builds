/* Vizstract — field extraction from a pasted free-text study abstract.
   Two paths: a deterministic regex/keyword extractor that always works
   with zero network calls, and an optional direct-from-browser call to
   the Anthropic API using a user-supplied, session-only key. The AI path
   falls back to the deterministic result on any network or parse failure. */
(function () {
  "use strict";
  window.Vizstract = window.Vizstract || {};

  var ANTHROPIC_ENDPOINT = "https://api.anthropic.com/v1/messages";
  var ANTHROPIC_MODEL = "claude-haiku-4-5-20251001";

  function deterministicExtract(text) {
    text = String(text || "");
    var result = {};
    var lower = text.toLowerCase();

    var lines = text.split(/\r?\n/);
    var firstLine = "";
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].trim()) {
        firstLine = lines[i].trim();
        break;
      }
    }
    if (firstLine && firstLine.length <= 150 && firstLine.length < text.trim().length) {
      result.title = firstLine;
    }

    var nMatch = text.match(/\bN\s*=\s*(\d{1,6})\b/i);
    if (nMatch) result.sampleSize = nMatch[1];

    var popMatch = text.match(/([A-Z][^.]{0,20}\b(?:participants|students|adults|patients|subjects|respondents|volunteers)\b[^.]{0,80})\./i);
    if (popMatch) result.population = popMatch[1].trim();

    if (/correlat/.test(lower)) result.designType = "correlate";
    if (/(pre-post|pre\/post|before and after|baseline[^.]{0,40}follow[- ]?up)/.test(lower)) result.designType = "prepost";
    if (!result.designType && /(survey|cross-sectional)/.test(lower)) result.designType = "survey";
    if (!result.designType && /(intervention|randomized controlled trial|\brct\b|longitudinal|over \d+ (weeks|months|days))/.test(lower)) result.designType = "process";
    if (!result.designType) result.designType = "compare";

    var hasIncrease = /\b(increase|higher|greater|elevated|improv(?:ed|ement))\b/.test(lower);
    var hasDecrease = /\b(decrease|lower|reduc(?:ed|tion)|diminish)\b/.test(lower);
    var hasNone = /\b(no significant|no difference|not significant|null result)\b/.test(lower);
    if (hasIncrease && hasDecrease) result.effectDirection = "mixed";
    else if (hasIncrease) result.effectDirection = "increase";
    else if (hasDecrease) result.effectDirection = "decrease";
    else if (hasNone) result.effectDirection = "none";

    var ivdv = text.match(/effect(?:s)? of\s+([^,.;]{2,50})\s+on\s+([^,.;]{2,50})/i);
    if (ivdv) {
      result.ivLabel = ivdv[1].trim();
      result.dvLabel = ivdv[2].trim();
    } else {
      var relMatch = text.match(/relationship between\s+([^,.;]{2,50})\s+and\s+([^,.;]{2,50})/i);
      if (relMatch) {
        result.ivLabel = relMatch[1].trim();
        result.dvLabel = relMatch[2].trim();
      }
    }

    var findingMatch = text.match(/([^.]*?\b(?:found that|results (?:indicated|showed|suggest)|revealed that)\b[^.]*)\./i);
    if (findingMatch) {
      result.headlineFinding = findingMatch[1].trim();
    } else {
      var trimmed = text.trim();
      if (trimmed) result.headlineFinding = trimmed.slice(0, 160) + (trimmed.length > 160 ? "…" : "");
    }

    var statMatch = text.match(/\b([pP]\s*[<=>]\s*\.?\d+(?:\.\d+)?|[rR]\s*=\s*-?\.?\d+(?:\.\d+)?|d\s*=\s*-?\.?\d+(?:\.\d+)?)\b/);
    if (statMatch) result.statDetail = statMatch[1].replace(/\s+/g, " ");

    return result;
  }

  async function extractWithAI(abstractText, apiKey) {
    var prompt =
      "You are extracting structured fields from a research-study abstract for a visual-abstract generator.\n" +
      'Return ONLY a single JSON object (no markdown fences, no commentary) with these exact keys:\n' +
      '{"title": string, "designType": one of ["compare","correlate","process","survey","prepost"], ' +
      '"population": string, "ivLabel": string, "dvLabel": string, "sampleSize": string, ' +
      '"headlineFinding": string, "effectDirection": one of ["increase","decrease","none","mixed"], "statDetail": string}\n' +
      "Leave a field as an empty string if it cannot be determined from the text. Keep every string under 90 characters.\n\n" +
      "Abstract:\n" + abstractText;

    var response = await fetch(ANTHROPIC_ENDPOINT, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true"
      },
      body: JSON.stringify({
        model: ANTHROPIC_MODEL,
        max_tokens: 500,
        messages: [{ role: "user", content: prompt }]
      })
    });

    if (!response.ok) {
      throw new Error("Anthropic API error: " + response.status);
    }
    var payload = await response.json();
    var text = payload && payload.content && payload.content[0] && payload.content[0].text;
    if (!text) throw new Error("Empty AI response");
    var jsonStart = text.indexOf("{");
    var jsonEnd = text.lastIndexOf("}");
    if (jsonStart === -1 || jsonEnd === -1) throw new Error("No JSON object found in AI response");
    return JSON.parse(text.slice(jsonStart, jsonEnd + 1));
  }

  async function extract(abstractText, apiKey) {
    if (apiKey) {
      try {
        var aiResult = await extractWithAI(abstractText, apiKey);
        return { source: "ai", data: aiResult };
      } catch (e) {
        return { source: "fallback", data: deterministicExtract(abstractText), error: String((e && e.message) || e) };
      }
    }
    return { source: "fallback", data: deterministicExtract(abstractText) };
  }

  window.Vizstract.Extract = {
    deterministicExtract: deterministicExtract,
    extractWithAI: extractWithAI,
    extract: extract,
    ANTHROPIC_MODEL: ANTHROPIC_MODEL,
    ANTHROPIC_ENDPOINT: ANTHROPIC_ENDPOINT
  };
})();
