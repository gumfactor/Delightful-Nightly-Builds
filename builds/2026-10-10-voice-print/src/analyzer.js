/* Voice Print analyzer: pure logic, no DOM, no network. Works in browsers (window.VoicePrint) and Node. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.VoicePrint = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const ABBREVIATIONS = new Set(['mr', 'mrs', 'ms', 'dr', 'prof', 'sr', 'jr', 'vs', 'etc', 'eg', 'ie', 'fig', 'al', 'st', 'no', 'inc', 'ltd', 'cf']);

  const FUNCTION_WORDS = ['the', 'of', 'and', 'to', 'a', 'in', 'that', 'is', 'it', 'for', 'as', 'with', 'was', 'on', 'be', 'by', 'this', 'but', 'not', 'or', 'are', 'from', 'at', 'an', 'have', 'which', 'if', 'so', 'we', 'i', 'you', 'they', 'what', 'about', 'just', 'than', 'then', 'there', 'when', 'because', 'would'];

  // Metrics compared against a voice profile (ttr and paragraph length are excluded: too length-dependent).
  const VOICE_METRICS = ['avgSentenceLen', 'sentenceLenCV', 'commaPerSentence', 'emDashPer1k', 'semicolonPer1k', 'contractionRate', 'firstPersonRate', 'questionRate', 'longWordRate'];

  const METRIC_LABELS = {
    avgSentenceLen: 'Words per sentence',
    sentenceLenCV: 'Rhythm variation (sd/mean)',
    commaPerSentence: 'Commas per sentence',
    emDashPer1k: 'Em dashes per 1,000 words',
    semicolonPer1k: 'Semicolons per 1,000 words',
    contractionRate: 'Contractions per 100 words',
    firstPersonRate: 'First person per 100 words',
    questionRate: 'Share of questions',
    longWordRate: 'Share of long words (9+ letters)',
    ttr: 'Vocabulary variety (first 400 words)',
    avgParagraphWords: 'Words per paragraph',
  };

  // ---------- tokenizing ----------

  function words(text) {
    return (text.match(/[A-Za-z][A-Za-z'’-]*/g) || []).map((w) => w.toLowerCase().replace(/’/g, "'"));
  }

  /** Split into sentences with offsets into the original text. */
  function splitSentences(text) {
    const sentences = [];
    const boundary = /[.!?]+["'”’)\]]*(?:\s+|$)|\n\s*\n/g;
    let start = 0;
    let match;
    const push = (from, to) => {
      const raw = text.slice(from, to);
      const lead = raw.length - raw.trimStart().length;
      const trimmed = raw.trim();
      if (!trimmed || !/[A-Za-z0-9]/.test(trimmed)) return;
      sentences.push({ text: trimmed, start: from + lead, end: from + lead + trimmed.length, words: words(trimmed).length });
    };
    while ((match = boundary.exec(text)) !== null) {
      const isPara = /^\n/.test(match[0]);
      if (!isPara) {
        const before = text.slice(start, match.index);
        const lastToken = (before.match(/([A-Za-z.]+)$/) || [])[1] || '';
        const bare = lastToken.replace(/\./g, '').toLowerCase();
        const singleInitial = /^[A-Z]$/.test(lastToken) && match[0].startsWith('.');
        const decimalLike = /\d$/.test(before) && /^\.\d/.test(text.slice(match.index));
        if (match[0].startsWith('.') && match[0].replace(/\s+$/, '') === '.' && (ABBREVIATIONS.has(bare) || singleInitial || decimalLike)) continue;
      }
      push(start, match.index + (isPara ? 0 : match[0].replace(/\s+$/, '').length));
      start = match.index + match[0].length;
      if (match[0].length === 0) boundary.lastIndex++;
    }
    push(start, text.length);
    return sentences;
  }

  function splitParagraphs(text) {
    return text.split(/\n\s*\n/).map((p) => p.trim()).filter(Boolean);
  }

  // ---------- metrics ----------

  function mean(values) {
    return values.length ? values.reduce((a, b) => a + b, 0) / values.length : 0;
  }

  function sd(values) {
    if (values.length < 2) return 0;
    const m = mean(values);
    return Math.sqrt(mean(values.map((v) => (v - m) ** 2)));
  }

  function computeMetrics(text, sentences) {
    const sents = sentences || splitSentences(text);
    const toks = words(text);
    const n = toks.length;
    const lens = sents.map((s) => s.words).filter((l) => l > 0);
    const per1k = (count) => (n ? (count / n) * 1000 : 0);
    const per100 = (count) => (n ? (count / n) * 100 : 0);
    const count = (re) => (text.match(re) || []).length;
    const paragraphs = splitParagraphs(text);
    const head = toks.slice(0, 400);
    const avg = mean(lens);
    return {
      words: n,
      sentences: sents.length,
      avgSentenceLen: avg,
      sentenceLenCV: avg ? sd(lens) / avg : 0,
      commaPerSentence: sents.length ? count(/,/g) / sents.length : 0,
      emDashPer1k: per1k(count(/—|\s--\s/g)),
      semicolonPer1k: per1k(count(/;/g)),
      contractionRate: per100(count(/\b[A-Za-z]+(?:n['’]t|['’](?:m|re|ve|ll|d))\b|\b(?:it|that|there|he|she|what|let|here)['’]s\b/gi)),
      firstPersonRate: per100(toks.filter((w) => ['i', "i'm", "i've", "i'll", "i'd", 'me', 'my', 'mine', 'we', 'our', 'us', "we're", "we've"].includes(w)).length),
      questionRate: sents.length ? sents.filter((s) => /\?["'”’)]*$/.test(s.text)).length / sents.length : 0,
      longWordRate: n ? toks.filter((w) => w.replace(/[^a-z]/g, '').length >= 9).length / n : 0,
      ttr: head.length ? new Set(head).size / head.length : 0,
      avgParagraphWords: paragraphs.length ? n / paragraphs.length : 0,
    };
  }

  function functionWordRates(text) {
    const toks = words(text);
    const rates = {};
    if (!toks.length) return rates;
    const counts = {};
    for (const w of toks) counts[w] = (counts[w] || 0) + 1;
    for (const fw of FUNCTION_WORDS) rates[fw] = ((counts[fw] || 0) / toks.length) * 1000;
    return rates;
  }

  function openerShares(sentences) {
    const counts = {};
    let total = 0;
    for (const s of sentences) {
      const first = words(s.text)[0];
      if (!first) continue;
      counts[first] = (counts[first] || 0) + 1;
      total++;
    }
    const shares = {};
    for (const [w, c] of Object.entries(counts)) shares[w] = c / total;
    return shares;
  }

  // ---------- AI-tell detectors ----------

  const word = (alts) => new RegExp('\\b(?:' + alts + ')\\b', 'gi');

  const DETECTORS = [
    { type: 'vocab', label: 'Stock AI vocabulary', weight: 1.6, tip: 'Overused in machine prose. Say the plain thing instead.',
      re: word('delv(?:e|es|ed|ing)|tapestry|testament|multifaceted|pivotal|myriad|plethora|underscor(?:e|es|ed|ing)|showcas(?:e|es|ed|ing)|leverag(?:e|es|ed|ing)|harness(?:es|ed|ing)?|foster(?:s|ed|ing)?|streamlin(?:e|es|ed|ing)|seamless(?:ly)?|holistic|synerg(?:y|ies)|elevat(?:e|es|ed|ing)|unlock(?:s|ed|ing)?|unleash(?:es|ed|ing)?|embark(?:s|ed|ing)?|intricate|intricacies|vibrant|bustling|beacon|cornerstone|paramount|meticulous(?:ly)?|commendable|invaluable|transformative|revolutioniz(?:e|es|ed|ing)|realm|ever-evolving|ever-changing|game-changer|navigat(?:e|es|ed|ing) the') },
    { type: 'phrase', label: 'Stock AI phrase', weight: 2.2, tip: 'Filler that announces importance instead of showing it. Cut or rewrite.',
      re: new RegExp("(?:it(?:'|’)?s|it is) (?:important|worth|crucial|essential) (?:to note|noting|to remember|to mention)|in today(?:'|’)?s (?:fast-paced|digital|modern|ever-changing|rapidly)[a-z -]*|in the (?:realm|world|landscape) of|at the end of the day|(?:a|the) testament to|plays? an? (?:crucial|pivotal|vital|key|significant) role|when it comes to|let(?:'|’)?s (?:dive|delve|explore|unpack)|(?:deep )?dive into|rich tapestry|navigate the complexities|shed(?:s|ding)? light on|paving the way|the key takeaway|look no further|i hope this helps|feel free to|stands as|serves as an?\\b|this highlights|a wide range of", 'gi') },
    { type: 'transition', label: 'Stiff transition', weight: 1.1, tip: 'Sentence-opening connective. Humans usually just start the next thought.',
      re: /(?:^|(?<=[.!?]["'”’)]?\s)|(?<=\n))(?:Moreover|Furthermore|Additionally|Consequently|Nevertheless|Notably|Importantly|Crucially|Indeed|In addition|In conclusion|In summary|To sum up|Overall|Ultimately),?/g },
    { type: 'contrast', label: '"Not just X, but Y" frame', weight: 2.6, tip: 'A signature machine rhythm. State Y directly.',
      re: new RegExp("\\bnot (?:just|only|merely|simply) [^.!?;\\n—–]{2,70}?(?:,?\\s*(?:but|and) (?:also |rather )?|\\s*[,;—–-]+\\s*(?:it|this|that|they|we|you)(?:(?:'|’)s|(?:'|’)re| is| are)?\\b)|\\b(?:it|this|that)(?:'|’)?s not (?:just |only |merely |simply )?[^.!?;\\n—–]{2,60}?\\s*[,;—–-]+\\s*(?:it|this|that)(?:'|’)?s\\b|\\b(?:it|this|that) is not (?:just |only |merely |simply )?[^.!?;\\n—–]{2,60}?\\s*[,;—–-]+\\s*(?:it|this|that) is\\b", 'gi') },
    { type: 'participle', label: 'Tacked-on participle', weight: 1.6, tip: '", highlighting/underscoring/showcasing..." adds a vague conclusion. Delete or make it a sentence.',
      re: /,\s+(?:highlighting|underscoring|showcasing|emphasizing|emphasising|reflecting|demonstrating|ensuring|fostering|contributing to|paving)\b/gi },
    { type: 'opener', label: 'Rhetorical opener', weight: 1.6, tip: 'Hook formula. Start with the claim.',
      re: /(?:^|(?<=[.!?]\s)|(?<=\n))(?:Have you ever wondered|Imagine (?:a|an|if|this|that|waking|walking)\b|What if I told you|Picture this|Ever wondered)/g },
    { type: 'triad', label: 'Rule-of-three list', weight: 0.7, tip: 'Tidy triplets recur in machine text. Keep them only when you have exactly three things.',
      re: /\b[A-Za-z-]{3,}, [A-Za-z-]{3,},? and [A-Za-z-]{3,}\b/g },
    { type: 'hedge', label: 'Soft hedge', weight: 0.5, tip: 'Hedges thin out claims. Commit or cite.',
      re: word('arguably|essentially|fundamentally|particularly|significantly|typically|generally|potentially|various|numerous') },
  ];

  /** Keep the highest-weight, then longest, non-overlapping flags. */
  function resolveFlags(flags) {
    const ordered = flags.slice().sort((a, b) => b.weight - a.weight || (b.end - b.start) - (a.end - a.start) || a.start - b.start);
    const kept = [];
    for (const flag of ordered) {
      if (!kept.some((k) => flag.start < k.end && flag.end > k.start)) kept.push(flag);
    }
    return kept.sort((a, b) => a.start - b.start);
  }

  function detectFlags(text, metrics) {
    const flags = [];
    for (const det of DETECTORS) {
      det.re.lastIndex = 0;
      let m;
      while ((m = det.re.exec(text)) !== null) {
        if (m[0].length === 0) { det.re.lastIndex++; continue; }
        flags.push({ start: m.index, end: m.index + m[0].length, type: det.type, label: det.label, weight: det.weight, tip: det.tip, text: m[0] });
      }
    }
    // Em dashes only count against you once they are frequent.
    if (metrics.emDashPer1k > 4) {
      const re = /—|\s--\s/g;
      let m;
      while ((m = re.exec(text)) !== null) {
        flags.push({ start: m.index, end: m.index + m[0].length, type: 'emdash', label: 'Em dash overuse', weight: 0.7, tip: 'Dashes are frequent in this draft. Keep the best one or two per page.', text: m[0] });
      }
    }
    return resolveFlags(flags);
  }

  function globalFlags(metrics) {
    const out = [];
    if (metrics.sentences >= 6 && metrics.sentenceLenCV < 0.38) {
      out.push({ type: 'rhythm', label: 'Even sentence rhythm', weight: 4, tip: 'Sentence lengths barely vary (' + metrics.sentenceLenCV.toFixed(2) + '). Mix in a very short sentence and one long one.' });
    }
    if (metrics.words >= 120 && metrics.contractionRate === 0 && metrics.firstPersonRate === 0) {
      out.push({ type: 'voiceless', label: 'No contractions or first person', weight: 3, tip: 'Nobody is speaking. Add "I", a contraction, or a concrete detail.' });
    }
    return out;
  }

  function aiScoreFrom(flags, extras, wordCount) {
    if (!wordCount) return 0;
    const total = flags.reduce((s, f) => s + f.weight, 0) + extras.reduce((s, f) => s + f.weight, 0);
    const density = (total / wordCount) * 100; // weighted flags per 100 words
    return Math.round(100 * (1 - Math.exp(-density / 9)));
  }

  // ---------- voice profile ----------

  function chunkSentences(sentences, size) {
    const chunks = [];
    for (let i = 0; i < sentences.length; i += size) chunks.push(sentences.slice(i, i + size));
    return chunks.filter((c) => c.length >= Math.min(size, 4));
  }

  function summarize(values) {
    return { n: values.length, mean: mean(values), sd: sd(values) };
  }

  function mergeStat(a, b) {
    if (!a) return b;
    if (!b) return a;
    const n = a.n + b.n;
    const m = (a.mean * a.n + b.mean * b.n) / n;
    const variance = (a.n * (a.sd ** 2 + (a.mean - m) ** 2) + b.n * (b.sd ** 2 + (b.mean - m) ** 2)) / n;
    return { n, mean: m, sd: Math.sqrt(variance) };
  }

  /** Build (or extend) a voice profile from one or more baseline texts. */
  function buildProfile(texts, existing, name) {
    const list = (Array.isArray(texts) ? texts : [texts]).filter((t) => t && words(t).length >= 40);
    if (!list.length) throw new Error('Need at least 40 words of baseline writing.');
    const metricValues = {};
    let totalWords = 0;
    const fwWeighted = {};
    const openerCounts = {};
    let openerTotal = 0;
    for (const text of list) {
      const sentences = splitSentences(text);
      const wc = words(text).length;
      totalWords += wc;
      const chunks = chunkSentences(sentences, 8);
      const units = chunks.length >= 2 ? chunks.map((c) => computeMetrics(c.map((s) => s.text).join(' '), c)) : [computeMetrics(text, sentences)];
      for (const metric of VOICE_METRICS) (metricValues[metric] = metricValues[metric] || []).push(...units.map((u) => u[metric]));
      const rates = functionWordRates(text);
      for (const fw of FUNCTION_WORDS) fwWeighted[fw] = (fwWeighted[fw] || 0) + (rates[fw] || 0) * wc;
      const shares = openerShares(sentences);
      for (const [w, share] of Object.entries(shares)) openerCounts[w] = (openerCounts[w] || 0) + share * sentences.length;
      openerTotal += sentences.length;
    }
    const metrics = {};
    for (const metric of VOICE_METRICS) {
      const fresh = summarize(metricValues[metric]);
      metrics[metric] = mergeStat(existing && existing.metrics && existing.metrics[metric], fresh);
    }
    const priorWords = existing ? existing.wordCount : 0;
    const functionWords = {};
    for (const fw of FUNCTION_WORDS) {
      const prior = existing && existing.functionWords ? existing.functionWords[fw] || 0 : 0;
      functionWords[fw] = (prior * priorWords + fwWeighted[fw]) / (priorWords + totalWords);
    }
    const priorOpenerTotal = existing ? existing.openerTotal || 0 : 0;
    const openerMerged = {};
    for (const [w, share] of Object.entries((existing && existing.openers) || {})) openerMerged[w] = share * priorOpenerTotal;
    for (const [w, c] of Object.entries(openerCounts)) openerMerged[w] = (openerMerged[w] || 0) + c;
    const allOpenerTotal = priorOpenerTotal + openerTotal;
    const openers = {};
    Object.entries(openerMerged).sort((a, b) => b[1] - a[1]).slice(0, 12).forEach(([w, c]) => { openers[w] = c / allOpenerTotal; });
    return {
      version: 1,
      name: name || (existing && existing.name) || 'My voice',
      createdAt: (existing && existing.createdAt) || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      sampleCount: (existing ? existing.sampleCount : 0) + list.length,
      wordCount: priorWords + totalWords,
      metrics,
      functionWords,
      openers,
      openerTotal: allOpenerTotal,
    };
  }

  function validateProfile(profile) {
    if (!profile || typeof profile !== 'object' || profile.version !== 1 || !profile.metrics || !profile.functionWords) {
      throw new Error('Not a Voice Print profile (expected version 1).');
    }
    for (const metric of VOICE_METRICS) {
      const stat = profile.metrics[metric];
      if (!stat || !Number.isFinite(stat.mean) || !Number.isFinite(stat.sd)) throw new Error('Profile is missing metric: ' + metric);
    }
    return profile;
  }

  function cosine(a, b, keys) {
    let dot = 0, na = 0, nb = 0;
    for (const k of keys) {
      const x = a[k] || 0, y = b[k] || 0;
      dot += x * y; na += x * x; nb += y * y;
    }
    return na && nb ? dot / Math.sqrt(na * nb) : 0;
  }

  /** Per-metric deviation against a profile and an overall 0-100 match. */
  function compareToProfile(metrics, fwRates, profile) {
    const deviations = [];
    let zSum = 0;
    for (const metric of VOICE_METRICS) {
      const stat = profile.metrics[metric];
      const floor = Math.max(Math.abs(stat.mean) * 0.15, metric === 'emDashPer1k' || metric === 'semicolonPer1k' ? 1 : 0.02);
      const spread = Math.max(stat.sd, floor);
      const z = (metrics[metric] - stat.mean) / spread;
      zSum += Math.min(Math.abs(z), 3);
      deviations.push({ metric, label: METRIC_LABELS[metric], draft: metrics[metric], you: stat.mean, z, status: Math.abs(z) < 1 ? 'close' : Math.abs(z) < 2 ? 'off' : 'far' });
    }
    const metricMatch = 1 - zSum / (VOICE_METRICS.length * 3);
    const fwSim = Math.max(0, Math.min(1, (cosine(fwRates, profile.functionWords, FUNCTION_WORDS) - 0.85) / 0.15));
    const voiceMatch = Math.round(100 * (0.75 * metricMatch + 0.25 * fwSim));
    return { deviations, voiceMatch };
  }

  // ---------- public analysis ----------

  function analyze(text, profile) {
    const clean = String(text || '');
    const sentences = splitSentences(clean);
    const metrics = computeMetrics(clean, sentences);
    const flags = detectFlags(clean, metrics);
    const extras = globalFlags(metrics);
    const result = {
      metrics,
      sentences,
      flags,
      globalFlags: extras,
      aiScore: aiScoreFrom(flags, extras, metrics.words),
      voiceMatch: null,
      deviations: [],
    };
    if (profile && metrics.words >= 20) {
      const cmp = compareToProfile(metrics, functionWordRates(clean), validateProfile(profile));
      result.voiceMatch = cmp.voiceMatch;
      result.deviations = cmp.deviations;
    }
    return result;
  }

  function flagSummary(result) {
    const groups = {};
    for (const f of result.flags) {
      const g = groups[f.type] || (groups[f.type] = { type: f.type, label: f.label, tip: f.tip, count: 0, examples: [] });
      g.count++;
      if (g.examples.length < 3 && !g.examples.includes(f.text.trim())) g.examples.push(f.text.trim());
    }
    return Object.values(groups).sort((a, b) => b.count - a.count);
  }

  /** Revision prompt to paste into an LLM. Nothing is sent anywhere by this tool. */
  function buildRevisionPrompt(text, result, profile) {
    const lines = [];
    lines.push('Revise the draft below so it reads like a specific person wrote it, not a model. Keep every fact and argument; change only the prose.');
    lines.push('');
    const groups = flagSummary(result);
    if (groups.length || result.globalFlags.length) {
      lines.push('Problems found by a style linter:');
      for (const g of groups) lines.push('- ' + g.label + ' x' + g.count + ' (e.g. ' + g.examples.map((e) => '"' + e + '"').join(', ') + '): ' + g.tip);
      for (const g of result.globalFlags) lines.push('- ' + g.label + ': ' + g.tip);
      lines.push('');
    }
    if (profile) {
      const m = profile.metrics;
      lines.push('Target voice (measured from the author\'s own writing):');
      lines.push('- Average sentence length about ' + m.avgSentenceLen.mean.toFixed(0) + ' words, with real variation (sd/mean about ' + m.sentenceLenCV.mean.toFixed(2) + ').');
      lines.push('- About ' + m.commaPerSentence.mean.toFixed(1) + ' commas per sentence; ' + m.contractionRate.mean.toFixed(1) + ' contractions and ' + m.firstPersonRate.mean.toFixed(1) + ' first-person words per 100 words.');
      lines.push('- Em dashes: about ' + m.emDashPer1k.mean.toFixed(1) + ' per 1,000 words. Semicolons: about ' + m.semicolonPer1k.mean.toFixed(1) + '.');
      const openers = Object.entries(profile.openers || {}).slice(0, 6).map(([w]) => w);
      if (openers.length) lines.push('- Frequent sentence openers: ' + openers.join(', ') + '.');
      lines.push('');
    }
    lines.push('Rules: no "not just X but Y" frames, no stock phrases, no closing summary sentence, prefer concrete nouns and verbs, vary sentence length. Return only the revised text.');
    lines.push('');
    lines.push('DRAFT:');
    lines.push(text);
    return lines.join('\n');
  }

  return { words, splitSentences, splitParagraphs, computeMetrics, functionWordRates, openerShares, detectFlags, globalFlags, aiScoreFrom, buildProfile, validateProfile, compareToProfile, analyze, flagSummary, buildRevisionPrompt, resolveFlags, VOICE_METRICS, METRIC_LABELS, FUNCTION_WORDS };
});
