/* Reviewer 2 — game logic and UI. Logic functions are exposed on window.R2 for testing. */
(function () {
  'use strict';

  const STORE_KEY = 'reviewer2.stats.v1';
  const KEY_STORE = 'reviewer2.apikey';
  const ROUND_SIZE = 8;
  const AI_MODEL = 'claude-haiku-5-5';
  const RANKS = [
    [0, 'Desk Rejection'], [40, 'Reviewer 3'], [90, 'Reviewer 2'],
    [150, 'Reviewer 1'], [210, 'Associate Editor'],
  ];

  // ---------- pure logic ----------
  function hashString(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function shuffle(list, rng) {
    const out = list.slice();
    for (let i = out.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  }

  function utcDate(now) {
    return (now || new Date()).toISOString().slice(0, 10);
  }

  function dailyCases(dateStr, cases) {
    const rng = mulberry32(hashString('daily:' + dateStr));
    return shuffle(cases, rng).slice(0, ROUND_SIZE);
  }

  /** Four flaw ids (correct one included), shuffled deterministically by rng. */
  function choicesFor(caseObj, flaws, rng) {
    const others = shuffle(flaws.map((f) => f.id).filter((id) => id !== caseObj.flaw), rng).slice(0, 3);
    return shuffle(others.concat(caseObj.flaw), rng);
  }

  function scoreFor(correct, streakAfter, usedHint) {
    if (!correct) return 0;
    const bonus = Math.min(Math.max(streakAfter - 1, 0), 5) * 2;
    return Math.max(10 + bonus - (usedHint ? 4 : 0), 1);
  }

  function rankFor(points) {
    let title = RANKS[0][1];
    for (const [min, name] of RANKS) if (points >= min) title = name;
    return title;
  }

  function emptyStats() {
    return { flaws: {}, bestStreak: 0, daily: {}, total: 0 };
  }

  function recordAnswer(stats, flawId, correct) {
    const entry = stats.flaws[flawId] || { seen: 0, right: 0 };
    entry.seen += 1;
    if (correct) entry.right += 1;
    stats.flaws[flawId] = entry;
    return stats;
  }

  /** Practice picks favour flaws the player misses most (weight = 1 + miss rate * 4; unseen = 3). */
  function pickPractice(stats, cases, count, rng) {
    const pool = cases.slice();
    const picked = [];
    while (picked.length < count && pool.length) {
      const weights = pool.map((c) => {
        const e = stats.flaws[c.flaw];
        if (!e || !e.seen) return 3;
        return 1 + (1 - e.right / e.seen) * 4;
      });
      const total = weights.reduce((sum, w) => sum + w, 0);
      let roll = rng() * total;
      let idx = 0;
      while (idx < pool.length - 1 && roll >= weights[idx]) { roll -= weights[idx]; idx++; }
      picked.push(pool.splice(idx, 1)[0]);
    }
    return picked;
  }

  function validateCase(obj, flaws) {
    if (!obj || typeof obj !== 'object') return false;
    const ids = flaws.map((f) => f.id);
    return ['title', 'text', 'hint', 'explain'].every((k) => typeof obj[k] === 'string' && obj[k].trim().length > 5)
      && ids.includes(obj.flaw);
  }

  function parseAiCase(raw, flaws) {
    if (typeof raw !== 'string') return null;
    const start = raw.indexOf('{');
    const end = raw.lastIndexOf('}');
    if (start < 0 || end <= start) return null;
    try {
      const obj = JSON.parse(raw.slice(start, end + 1));
      if (!validateCase(obj, flaws)) return null;
      return { id: 'ai-' + Date.now(), flaw: obj.flaw, title: obj.title, text: obj.text, hint: obj.hint, explain: obj.explain };
    } catch (err) {
      return null;
    }
  }

  async function fetchAiCase(apiKey, flaws, avoidFlaw) {
    const list = flaws.map((f) => `${f.id}: ${f.name} — ${f.blurb}`).join('\n');
    const flawId = avoidFlaw ? flaws.filter((f) => f.id !== avoidFlaw)[Math.floor(Math.random() * (flaws.length - 1))].id : flaws[Math.floor(Math.random() * flaws.length)].id;
    const prompt = `Write one fictional 2–4 sentence summary of a neuroscience or psychology study that contains exactly one methodological flaw: "${flawId}".\nFlaw types:\n${list}\n\nThe summary must not name the flaw. Reply with only JSON: {"flaw":"${flawId}","title":"short title","text":"the study summary","hint":"a one-line nudge","explain":"2 sentences explaining the flaw and the fix"}`;
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({ model: AI_MODEL, max_tokens: 600, messages: [{ role: 'user', content: prompt }] }),
    });
    if (!res.ok) throw new Error('API error ' + res.status);
    const data = await res.json();
    const text = (data.content || []).map((b) => b.text || '').join('');
    const parsed = parseAiCase(text, flaws);
    if (!parsed) throw new Error('The model returned an unusable case. Try again.');
    return parsed;
  }

  function loadStats() {
    try {
      const raw = localStorage.getItem(STORE_KEY);
      if (raw) return Object.assign(emptyStats(), JSON.parse(raw));
    } catch (err) { /* storage unavailable: fall through */ }
    return emptyStats();
  }

  function saveStats(stats) {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(stats)); } catch (err) { /* ignore */ }
  }

  window.R2 = {
    hashString, mulberry32, shuffle, dailyCases, choicesFor, scoreFor, rankFor,
    recordAnswer, pickPractice, validateCase, parseAiCase, fetchAiCase, emptyStats, utcDate, ROUND_SIZE,
  };

  // ---------- UI ----------
  const $ = (sel) => document.querySelector(sel);
  const flawById = Object.fromEntries(FLAWS.map((f) => [f.id, f]));
  let stats = loadStats();
  let round = null;

  function show(screen) {
    ['home', 'play', 'results'].forEach((name) => { $('#screen-' + name).hidden = name !== screen; });
  }

  function renderHome() {
    const today = utcDate();
    const done = stats.daily[today];
    $('#daily-status').textContent = done === undefined ? 'Not played yet today.' : `Today's score: ${done}. Replay for practice, score won't change.`;
    $('#best-streak').textContent = stats.bestStreak;
    $('#total-points').textContent = stats.total;
    $('#rank').textContent = rankFor(stats.total);
    const rows = FLAWS.map((f) => {
      const e = stats.flaws[f.id] || { seen: 0, right: 0 };
      const pct = e.seen ? Math.round((100 * e.right) / e.seen) : null;
      return `<li data-testid="flaw-row"><span>${f.name}</span><span class="pct">${pct === null ? '—' : pct + '%'} <small>(${e.seen})</small></span></li>`;
    });
    $('#flaw-stats').innerHTML = rows.join('');
    const hasKey = !!safeSession(KEY_STORE);
    $('#key-input').value = '';
    $('#key-status').textContent = hasKey ? 'Key set for this tab.' : 'No key set.';
    show('home');
  }

  function safeSession(key, value) {
    try {
      if (value === undefined) return sessionStorage.getItem(key);
      if (value === null) sessionStorage.removeItem(key); else sessionStorage.setItem(key, value);
    } catch (err) { /* ignore */ }
    return null;
  }

  function startRound(mode, cases) {
    round = { mode, cases, index: 0, points: 0, streak: 0, bestStreak: 0, correct: 0, answered: false, hintUsed: false, results: [], rng: mulberry32(hashString(mode + utcDate() + Date.now())) };
    if (mode === 'daily') round.rng = mulberry32(hashString('choices:' + utcDate()));
    renderCase();
  }

  function renderCase() {
    const c = round.cases[round.index];
    round.answered = false;
    round.hintUsed = false;
    round.choices = choicesFor(c, FLAWS, round.rng);
    $('#progress').textContent = `Case ${round.index + 1} / ${round.cases.length}`;
    $('#points').textContent = round.points;
    $('#streak').textContent = round.streak;
    $('#case-title').textContent = c.title;
    $('#case-text').textContent = c.text;
    $('#hint').hidden = true;
    $('#hint').textContent = '';
    $('#hint-btn').disabled = false;
    $('#feedback').hidden = true;
    $('#next-btn').hidden = true;
    $('#choices').innerHTML = '';
    round.choices.forEach((id) => {
      const btn = document.createElement('button');
      btn.className = 'choice';
      btn.dataset.testid = 'choice';
      btn.setAttribute('data-testid', 'choice');
      btn.dataset.flaw = id;
      btn.textContent = flawById[id].name;
      btn.addEventListener('click', () => answer(id));
      $('#choices').appendChild(btn);
    });
    show('play');
  }

  function answer(flawId) {
    if (round.answered) return;
    round.answered = true;
    const c = round.cases[round.index];
    const correct = flawId === c.flaw;
    round.streak = correct ? round.streak + 1 : 0;
    round.bestStreak = Math.max(round.bestStreak, round.streak);
    const gained = scoreFor(correct, round.streak, round.hintUsed);
    round.points += gained;
    if (correct) round.correct += 1;
    round.results.push({ flaw: c.flaw, correct });
    recordAnswer(stats, c.flaw, correct);
    document.querySelectorAll('.choice').forEach((btn) => {
      btn.disabled = true;
      if (btn.dataset.flaw === c.flaw) btn.classList.add('right');
      else if (btn.dataset.flaw === flawId) btn.classList.add('wrong');
    });
    const fb = $('#feedback');
    fb.hidden = false;
    fb.className = correct ? 'ok' : 'bad';
    $('#feedback-head').textContent = correct ? `Correct. +${gained}` : `Not quite. It was: ${flawById[c.flaw].name}`;
    $('#feedback-body').textContent = c.explain;
    $('#points').textContent = round.points;
    $('#streak').textContent = round.streak;
    $('#hint-btn').disabled = true;
    const last = round.index === round.cases.length - 1;
    $('#next-btn').textContent = last ? 'See results' : 'Next case';
    $('#next-btn').hidden = false;
    saveStats(stats);
  }

  function finishRound() {
    const today = utcDate();
    stats.bestStreak = Math.max(stats.bestStreak, round.bestStreak);
    if (round.mode === 'daily' && stats.daily[today] === undefined) {
      stats.daily[today] = round.points;
      stats.total += round.points;
    } else if (round.mode !== 'daily') {
      stats.total += round.points;
    }
    saveStats(stats);
    $('#final-score').textContent = round.points;
    $('#final-correct').textContent = `${round.correct} / ${round.cases.length}`;
    $('#final-rank').textContent = rankFor(round.points);
    const missed = round.results.filter((r) => !r.correct).map((r) => flawById[r.flaw].name);
    $('#missed').innerHTML = missed.length
      ? '<h3>Review these</h3><ul>' + [...new Set(missed)].map((n) => `<li>${n}</li>`).join('') + '</ul>'
      : '<p>No misses. Flawless review.</p>';
    show('results');
  }

  function setBusy(msg) {
    $('#ai-status').textContent = msg;
  }

  async function startFresh() {
    const key = safeSession(KEY_STORE);
    if (!key) { setBusy('Enter an Anthropic API key first.'); return; }
    setBusy('Asking Claude for a new case…');
    try {
      const cases = [];
      for (let i = 0; i < 3; i++) cases.push(await fetchAiCase(key, FLAWS, cases[i - 1] && cases[i - 1].flaw));
      setBusy('');
      startRound('fresh', cases);
    } catch (err) {
      setBusy('Could not generate a case: ' + err.message);
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('#daily-btn').addEventListener('click', () => startRound('daily', dailyCases(utcDate(), CASES)));
    $('#practice-btn').addEventListener('click', () => startRound('practice', pickPractice(stats, CASES, ROUND_SIZE, mulberry32(Date.now()))));
    $('#fresh-btn').addEventListener('click', startFresh);
    $('#key-save').addEventListener('click', () => {
      const val = $('#key-input').value.trim();
      safeSession(KEY_STORE, val || null);
      $('#key-input').value = '';
      $('#key-status').textContent = val ? 'Key set for this tab.' : 'No key set.';
    });
    $('#hint-btn').addEventListener('click', () => {
      if (round.answered) return;
      round.hintUsed = true;
      $('#hint').textContent = round.cases[round.index].hint;
      $('#hint').hidden = false;
      $('#hint-btn').disabled = true;
    });
    $('#next-btn').addEventListener('click', () => {
      if (round.index === round.cases.length - 1) finishRound();
      else { round.index += 1; renderCase(); }
    });
    $('#home-btn').addEventListener('click', renderHome);
    $('#reset-btn').addEventListener('click', () => {
      if (window.confirm('Erase all stats?')) { stats = emptyStats(); saveStats(stats); renderHome(); }
    });
    renderHome();
  });
})();
