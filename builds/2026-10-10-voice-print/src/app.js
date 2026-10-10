(function () {
  'use strict';
  const VP = window.VoicePrint;
  const STORAGE_KEY = 'voiceprint.profile.v1';
  const $ = (id) => document.getElementById(id);

  let profile = null;
  let timer = null;

  function loadProfile() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) profile = VP.validateProfile(JSON.parse(raw));
    } catch (err) {
      profile = null;
    }
  }

  function saveProfile() {
    try {
      if (profile) localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
      else localStorage.removeItem(STORAGE_KEY);
    } catch (err) {
      /* storage unavailable: profile lasts for this page view only */
    }
  }

  function renderProfileStatus() {
    $('profile-status').textContent = profile
      ? 'Profile ready: ' + profile.sampleCount + ' sample(s), ' + profile.wordCount + ' words. Avg sentence ' + profile.metrics.avgSentenceLen.mean.toFixed(1) + ' words.'
      : 'No profile yet. Drafts will be checked for AI tells only.';
  }

  function verdictClass(value, invert) {
    const good = invert ? value >= 70 : value <= 25;
    const warn = invert ? value >= 45 : value <= 55;
    return good ? 'good' : warn ? 'warn' : 'bad';
  }

  function fmt(value, metric) {
    if (metric === 'questionRate' || metric === 'longWordRate') return (value * 100).toFixed(0) + '%';
    return value.toFixed(value < 10 ? 2 : 1);
  }

  function renderHighlights(text, flags) {
    const box = $('highlighted');
    box.textContent = '';
    let cursor = 0;
    for (const flag of flags) {
      if (flag.start > cursor) box.appendChild(document.createTextNode(text.slice(cursor, flag.start)));
      const mark = document.createElement('mark');
      mark.dataset.type = flag.type;
      mark.title = flag.label + ': ' + flag.tip;
      mark.textContent = text.slice(flag.start, flag.end);
      box.appendChild(mark);
      cursor = flag.end;
    }
    if (cursor < text.length) box.appendChild(document.createTextNode(text.slice(cursor)));
  }

  function renderFlagSummary(result) {
    const list = $('flag-summary');
    list.textContent = '';
    const entries = VP.flagSummary(result).map((g) => ({ type: g.type, head: g.label + ' × ' + g.count, body: g.tip + ' e.g. ' + g.examples.map((e) => '"' + e + '"').join(', ') }));
    for (const g of result.globalFlags) entries.push({ type: g.type, head: g.label, body: g.tip });
    if (!entries.length) entries.push({ type: 'none', head: 'No flags', body: 'Nothing in this draft matches the known machine-prose habits.' });
    for (const entry of entries) {
      const li = document.createElement('li');
      li.dataset.type = entry.type;
      const strong = document.createElement('strong');
      strong.textContent = entry.head + '. ';
      li.appendChild(strong);
      li.appendChild(document.createTextNode(entry.body));
      list.appendChild(li);
    }
  }

  function renderRhythm(result) {
    const box = $('rhythm');
    box.textContent = '';
    const max = Math.max(1, ...result.sentences.map((s) => s.words));
    for (const sentence of result.sentences) {
      const bar = document.createElement('div');
      bar.className = 'bar';
      bar.style.height = Math.max(3, Math.round((sentence.words / max) * 100)) + 'px';
      bar.title = sentence.words + ' words: ' + sentence.text.slice(0, 80);
      box.appendChild(bar);
    }
  }

  function renderMetrics(result) {
    const body = $('metrics').querySelector('tbody');
    body.textContent = '';
    const rows = result.deviations.length
      ? result.deviations
      : VP.VOICE_METRICS.map((metric) => ({ metric, label: VP.METRIC_LABELS[metric], draft: result.metrics[metric], you: null, status: '' }));
    for (const row of rows) {
      const tr = document.createElement('tr');
      const cells = [row.label, fmt(row.draft, row.metric), row.you === null ? '–' : fmt(row.you, row.metric), row.status === 'close' ? 'close' : row.status === 'off' ? 'a bit off' : row.status === 'far' ? 'far from you' : ''];
      cells.forEach((value, i) => {
        const td = document.createElement('td');
        if (i > 0 && i < 3) td.className = 'num';
        if (i === 3 && value) td.className = row.status === 'close' ? 'good' : row.status === 'off' ? 'warn' : 'bad';
        td.textContent = value;
        tr.appendChild(td);
      });
      body.appendChild(tr);
    }
  }

  function analyze() {
    const text = $('draft').value;
    const results = $('results');
    if (!text.trim()) { results.hidden = true; return; }
    const result = VP.analyze(text, profile);
    results.hidden = false;
    $('ai-score').textContent = String(result.aiScore);
    $('ai-score').className = 'num ' + verdictClass(result.aiScore, false);
    $('ai-verdict').textContent = result.aiScore <= 25 ? 'Reads human' : result.aiScore <= 55 ? 'Some machine habits' : 'Heavily machine-flavoured';
    if (result.voiceMatch === null) {
      $('voice-score').textContent = '–';
      $('voice-score').className = 'num';
      $('voice-verdict').textContent = profile ? 'Draft too short (20+ words)' : 'Build a profile to see this';
    } else {
      $('voice-score').textContent = String(result.voiceMatch);
      $('voice-score').className = 'num ' + verdictClass(result.voiceMatch, true);
      $('voice-verdict').textContent = result.voiceMatch >= 70 ? 'Sounds like you' : result.voiceMatch >= 45 ? 'Drifting from your voice' : 'Not your voice';
    }
    renderHighlights(text, result.flags);
    renderFlagSummary(result);
    renderRhythm(result);
    renderMetrics(result);
    $('prompt').value = '';
    $('results').dataset.ready = '1';
  }

  function scheduleAnalyze() {
    clearTimeout(timer);
    timer = setTimeout(analyze, 150);
  }

  function showError(message) {
    $('profile-status').textContent = message;
  }

  $('build-profile').addEventListener('click', () => {
    try {
      profile = VP.buildProfile([$('baseline').value], profile);
      saveProfile();
      $('baseline').value = '';
      renderProfileStatus();
      analyze();
    } catch (err) {
      showError(err.message);
    }
  });
  $('demo-human').addEventListener('click', () => { $('baseline').value = window.VP_SAMPLES.human; });
  $('demo-machine').addEventListener('click', () => { $('draft').value = window.VP_SAMPLES.machine; analyze(); });
  $('clear-draft').addEventListener('click', () => { $('draft').value = ''; analyze(); });
  $('clear-profile').addEventListener('click', () => { profile = null; saveProfile(); $('profile-json').value = ''; renderProfileStatus(); analyze(); });
  $('draft').addEventListener('input', scheduleAnalyze);

  $('export-profile').addEventListener('click', () => {
    $('profile-json').value = profile ? JSON.stringify(profile, null, 2) : '';
    if (!profile) showError('Nothing to export: build a profile first.');
  });
  function importFromText(text) {
    try {
      profile = VP.validateProfile(JSON.parse(text));
      saveProfile();
      renderProfileStatus();
      analyze();
    } catch (err) {
      showError('Import failed: ' + err.message);
    }
  }
  $('import-profile').addEventListener('click', () => importFromText($('profile-json').value));
  $('import-file').addEventListener('change', (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => { $('profile-json').value = String(reader.result); importFromText(String(reader.result)); };
    reader.readAsText(file);
  });

  $('make-prompt').addEventListener('click', () => {
    const text = $('draft').value;
    if (!text.trim()) return;
    $('prompt').value = VP.buildRevisionPrompt(text, VP.analyze(text, profile), profile);
  });
  $('copy-prompt').addEventListener('click', async () => {
    const value = $('prompt').value;
    if (!value) return;
    try { await navigator.clipboard.writeText(value); $('copy-prompt').textContent = 'Copied'; }
    catch (err) { $('prompt').select(); }
  });

  loadProfile();
  renderProfileStatus();
  analyze();
})();
