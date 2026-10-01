/* Noise Lab UI: wires NoiseDSP to the page and Web Audio. */
(function () {
  'use strict';
  const DSP = window.NoiseDSP;
  const $ = (id) => document.getElementById(id);

  let params = DSP.hashToParams(location.hash) || DSP.presetParams('focus');
  let activePreset = DSP.hashToParams(location.hash) ? null : 'focus';
  let synth = null;
  let sampleRate = 44100;
  let audio = null; // { ctx, master, source, startedAt }
  let toneNode = null;
  let regenTimer = null;
  let sleepTimer = null;
  let pitchHz = 4000;

  // ---- control definitions ----------------------------------------------------------
  const FREQ_RANGE = [200, 16000];
  const mainControls = [
    { id: 'slope', label: 'Colour (spectral slope)', min: -2, max: 3, step: 0.1, get: (p) => p.slope, set: (p, v) => { p.slope = v; }, fmt: (v) => colourName(v) },
    { id: 'hp', label: 'Low cut', min: 0, max: 2000, step: 10, get: (p) => p.hp, set: (p, v) => { p.hp = v; }, fmt: (v) => (v === 0 ? 'off' : v + ' Hz') },
    { id: 'lp', label: 'High cut', min: 200, max: 20000, step: 100, get: (p) => p.lp, set: (p, v) => { p.lp = v; }, fmt: (v) => (v >= 20000 ? 'off' : v + ' Hz') },
  ];
  const advancedControls = [
    { id: 'notch-on', type: 'check', label: 'Notch filter on', get: (p) => p.notch.on, set: (p, v) => { p.notch.on = v; } },
    { id: 'notch-freq', label: 'Notch centre', log: FREQ_RANGE, get: (p) => p.notch.freq, set: (p, v) => { p.notch.freq = v; }, fmt: hz },
    { id: 'notch-width', label: 'Notch width', min: 0.1, max: 3, step: 0.1, get: (p) => p.notch.width, set: (p, v) => { p.notch.width = v; }, fmt: (v) => v.toFixed(1) + ' oct' },
    { id: 'notch-depth', label: 'Notch depth', min: 0, max: 60, step: 1, get: (p) => p.notch.depth, set: (p, v) => { p.notch.depth = v; }, fmt: (v) => v + ' dB' },
  ];
  params.bands.forEach((band, i) => {
    advancedControls.push(
      { id: 'band' + i + '-freq', label: 'Band ' + (i + 1) + ' centre', log: [60, 12000], get: (p) => p.bands[i].freq, set: (p, v) => { p.bands[i].freq = v; }, fmt: hz },
      { id: 'band' + i + '-width', label: 'Band ' + (i + 1) + ' width', min: 0.2, max: 3, step: 0.1, get: (p) => p.bands[i].width, set: (p, v) => { p.bands[i].width = v; }, fmt: (v) => v.toFixed(1) + ' oct' },
      { id: 'band' + i + '-gain', label: 'Band ' + (i + 1) + ' boost', min: -18, max: 18, step: 1, get: (p) => p.bands[i].gain, set: (p, v) => { p.bands[i].gain = v; }, fmt: (v) => (v > 0 ? '+' : '') + v + ' dB' }
    );
  });
  params.mods.forEach((mod, i) => {
    advancedControls.push(
      { id: 'mod' + i + '-rate', label: 'Swell ' + (i + 1) + ' rate', min: 0, max: 8, step: 0.01, get: (p) => p.mods[i].rate, set: (p, v) => { p.mods[i].rate = v; },
        fmt: (v) => (v === 0 ? 'off' : DSP.quantizedRate(v, sampleRate, DSP.LOOP_SIZE).toFixed(2) + ' Hz') },
      { id: 'mod' + i + '-depth', label: 'Swell ' + (i + 1) + ' depth', min: 0, max: 1, step: 0.05, get: (p) => p.mods[i].depth, set: (p, v) => { p.mods[i].depth = v; }, fmt: (v) => Math.round(v * 100) + '%' }
    );
  });

  function hz(value) { return value >= 1000 ? (value / 1000).toFixed(2) + ' kHz' : Math.round(value) + ' Hz'; }
  function colourName(slope) {
    if (slope < -0.5) return 'blue/violet (' + slope.toFixed(1) + ')';
    if (slope < 0.4) return 'white (' + slope.toFixed(1) + ')';
    if (slope < 1.5) return 'pink (' + slope.toFixed(1) + ')';
    return 'brown (' + slope.toFixed(1) + ')';
  }

  function buildControl(def, container) {
    const row = document.createElement('div');
    row.className = 'row';
    if (def.type === 'check') {
      const label = document.createElement('label');
      const input = document.createElement('input');
      input.type = 'checkbox'; input.id = def.id; input.dataset.testid = def.id;
      input.setAttribute('data-testid', def.id);
      input.addEventListener('change', () => { def.set(params, input.checked); changed(); });
      label.append(input, ' ' + def.label);
      row.append(label);
    } else {
      const label = document.createElement('label');
      label.htmlFor = def.id;
      const name = document.createElement('span'); name.textContent = def.label;
      const out = document.createElement('output'); out.id = 'out-' + def.id; out.setAttribute('data-testid', 'out-' + def.id);
      label.append(name, out);
      const input = document.createElement('input');
      input.type = 'range'; input.id = def.id; input.setAttribute('data-testid', def.id);
      if (def.log) { input.min = 0; input.max = 1000; input.step = 1; } else { input.min = def.min; input.max = def.max; input.step = def.step; }
      input.addEventListener('input', () => {
        const value = def.log ? DSP.freqFromSlider(input.value / 1000, def.log[0], def.log[1]) : Number(input.value);
        def.set(params, value);
        activePreset = null;
        changed();
      });
      row.append(label, input);
    }
    container.append(row);
  }

  function syncControls() {
    for (const def of mainControls.concat(advancedControls)) {
      const input = $(def.id);
      if (def.type === 'check') { input.checked = def.get(params); continue; }
      const value = def.get(params);
      input.value = def.log ? Math.round(DSP.sliderFromFreq(value, def.log[0], def.log[1]) * 1000) : value;
      $('out-' + def.id).textContent = def.fmt(value);
    }
    $('level').value = params.level;
    $('out-level').textContent = params.level + ' dBFS';
    document.querySelectorAll('#presets button').forEach((button) => {
      button.setAttribute('aria-pressed', String(button.dataset.key === activePreset));
    });
  }

  // ---- synthesis + drawing ----------------------------------------------------------
  function changed() {
    params = DSP.sanitizeParams(params);
    syncControls();
    clearTimeout(regenTimer);
    regenTimer = setTimeout(regenerate, 120);
    if (audio) setMasterGain(0.2);
  }

  function regenerate() {
    const result = DSP.synthesize(params, sampleRate, DSP.LOOP_SIZE, synth && synth.params.seed === params.seed ? synth.whites : undefined);
    synth = result;
    const lv = DSP.levels(result.channels[0], sampleRate);
    $('m-rms').textContent = (lv.rmsDbfs + params.level + 20).toFixed(1);
    $('m-a').textContent = (lv.aWeightedDbfs + params.level + 20).toFixed(1);
    $('m-peak').textContent = (lv.peakDbfs + params.level + 20).toFixed(1);
    drawSpectrum(result.channels[0]);
    if (audio) swapSource();
  }

  function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

  function drawSpectrum(samples) {
    const canvas = $('spectrum');
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 600;
    const height = canvas.clientHeight || 220;
    canvas.width = width * ratio; canvas.height = height * ratio;
    const ctx = canvas.getContext('2d');
    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, width, height);
    const spec = DSP.logSpectrum(samples, sampleRate, 200);
    let top = -Infinity;
    for (const value of spec.db) top = Math.max(top, value);
    const floor = top - 70;
    const pad = { left: 36, right: 8, top: 8, bottom: 22 };
    const x = (f) => pad.left + (Math.log(f / 20) / Math.log(1000)) * (width - pad.left - pad.right);
    const y = (db) => pad.top + (1 - (Math.max(floor, db) - floor) / (top - floor)) * (height - pad.top - pad.bottom);
    ctx.strokeStyle = cssVar('--line'); ctx.fillStyle = cssVar('--muted'); ctx.font = '11px system-ui'; ctx.lineWidth = 1;
    for (const f of [20, 100, 1000, 10000, 20000]) {
      ctx.beginPath(); ctx.moveTo(x(f), pad.top); ctx.lineTo(x(f), height - pad.bottom); ctx.stroke();
      ctx.textAlign = f === 20 ? 'left' : f === 20000 ? 'right' : 'center';
      ctx.fillText(f >= 1000 ? f / 1000 + 'k' : String(f), x(f), height - 6);
    }
    for (let db = 0; db >= -60; db -= 20) {
      ctx.beginPath(); ctx.moveTo(pad.left, y(top + db)); ctx.lineTo(width - pad.right, y(top + db)); ctx.stroke();
      ctx.textAlign = 'right'; ctx.fillText(db + ' dB', pad.left - 4, y(top + db) + 4);
    }
    ctx.beginPath(); ctx.moveTo(x(spec.freqs[0]), y(floor));
    for (let i = 0; i < spec.freqs.length; i++) ctx.lineTo(x(spec.freqs[i]), y(spec.db[i]));
    ctx.lineTo(x(spec.freqs[spec.freqs.length - 1]), y(floor)); ctx.closePath();
    ctx.fillStyle = cssVar('--fill'); ctx.fill();
    ctx.beginPath();
    for (let i = 0; i < spec.freqs.length; i++) {
      const target = i === 0 ? 'moveTo' : 'lineTo';
      ctx[target](x(spec.freqs[i]), y(spec.db[i]));
    }
    ctx.strokeStyle = cssVar('--curve'); ctx.lineWidth = 1.5; ctx.stroke();
  }

  // ---- audio ----------------------------------------------------------------------
  function ensureContext() {
    if (audio) return audio;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) { setStatus('Web Audio is not supported in this browser.'); return null; }
    const ctx = new AudioCtx();
    const master = ctx.createGain();
    master.gain.value = 0;
    master.connect(ctx.destination);
    audio = { ctx, master, source: null, startedAt: 0 };
    return audio;
  }

  function makeBuffer(ctx) {
    const buffer = ctx.createBuffer(2, DSP.LOOP_SIZE, sampleRate);
    buffer.copyToChannel(synth.channels[0], 0);
    buffer.copyToChannel(synth.channels[1], 1);
    return buffer;
  }

  function levelGain() { return DSP.dbToLinear(params.level + 20); }

  function setMasterGain(seconds) {
    if (!audio) return;
    const elapsed = (performance.now() - audio.startedAt) / 1000;
    const total = Number($('timer').value) * 60;
    const fade = DSP.fadeGain(elapsed, total, 30);
    audio.master.gain.setTargetAtTime(levelGain() * fade, audio.ctx.currentTime, seconds || 0.2);
  }

  function swapSource() {
    const { ctx, master } = audio;
    const next = ctx.createBufferSource();
    next.buffer = makeBuffer(ctx);
    next.loop = true;
    const fadeNode = ctx.createGain();
    fadeNode.gain.setValueAtTime(0, ctx.currentTime);
    fadeNode.gain.linearRampToValueAtTime(1, ctx.currentTime + 0.4);
    next.connect(fadeNode); fadeNode.connect(master);
    next.start();
    const previous = audio.source;
    audio.source = { node: next, fade: fadeNode };
    if (previous) {
      previous.fade.gain.cancelScheduledValues(ctx.currentTime);
      previous.fade.gain.setValueAtTime(previous.fade.gain.value, ctx.currentTime);
      previous.fade.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.4);
      previous.node.stop(ctx.currentTime + 0.5);
    }
  }

  function startPlayback() {
    const state = ensureContext();
    if (!state) return;
    if (!synth) regenerate();
    if (state.ctx.state === 'suspended') state.ctx.resume();
    state.startedAt = performance.now();
    swapSource();
    state.master.gain.cancelScheduledValues(state.ctx.currentTime);
    state.master.gain.setValueAtTime(0, state.ctx.currentTime);
    state.master.gain.linearRampToValueAtTime(levelGain(), state.ctx.currentTime + 2);
    $('play').textContent = 'Stop'; $('play').dataset.state = 'playing';
    clearInterval(sleepTimer);
    sleepTimer = setInterval(tickTimer, 1000);
    tickTimer();
  }

  function stopPlayback() {
    clearInterval(sleepTimer);
    $('timer-left').textContent = '';
    $('play').textContent = 'Play'; $('play').dataset.state = 'stopped';
    if (!audio) return;
    const { ctx, master } = audio;
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.setValueAtTime(master.gain.value, ctx.currentTime);
    master.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.6);
    const old = audio.source;
    if (old) old.node.stop(ctx.currentTime + 0.7);
    audio.source = null;
    setTimeout(() => { if (audio && !audio.source) { audio.ctx.close(); audio = null; } }, 900);
  }

  function tickTimer() {
    if (!audio) return;
    const total = Number($('timer').value) * 60;
    if (total <= 0) { $('timer-left').textContent = ''; return; }
    const elapsed = (performance.now() - audio.startedAt) / 1000;
    const left = Math.max(0, Math.ceil(total - elapsed));
    $('timer-left').textContent = Math.floor(left / 60) + ':' + String(left % 60).padStart(2, '0') + ' left';
    if (left === 0) stopPlayback(); else setMasterGain(0.5);
  }

  function togglePitch() {
    const state = ensureContext();
    if (!state) return;
    if (toneNode) {
      toneNode.gain.gain.setTargetAtTime(0, state.ctx.currentTime, 0.05);
      toneNode.osc.stop(state.ctx.currentTime + 0.3);
      toneNode = null;
      $('pitch-play').setAttribute('aria-pressed', 'false'); $('pitch-play').textContent = 'Play tone';
      return;
    }
    if (state.ctx.state === 'suspended') state.ctx.resume();
    const osc = state.ctx.createOscillator();
    const gain = state.ctx.createGain();
    osc.frequency.value = pitchHz;
    gain.gain.setValueAtTime(0, state.ctx.currentTime);
    gain.gain.linearRampToValueAtTime(0.01, state.ctx.currentTime + 0.3); // about -40 dBFS, deliberately quiet
    osc.connect(gain); gain.connect(state.ctx.destination);
    osc.start();
    toneNode = { osc, gain };
    $('pitch-play').setAttribute('aria-pressed', 'true'); $('pitch-play').textContent = 'Stop tone';
  }

  // ---- export + share ---------------------------------------------------------------
  function setStatus(text) { $('status').textContent = text; }

  function download(bytes, name) {
    const url = URL.createObjectURL(new Blob([bytes], { type: 'audio/wav' }));
    const link = document.createElement('a');
    link.href = url; link.download = name;
    document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  function exportWav(seconds, label) {
    if (!synth) regenerate();
    const loopSeconds = DSP.LOOP_SIZE / sampleRate;
    const repeats = seconds === 0 ? 1 : Math.ceil(seconds / loopSeconds);
    try {
      const bytes = DSP.encodeWav(synth.channels, sampleRate, repeats, levelGain(), params.seed);
      download(bytes, 'noise-lab-' + label + '.wav');
      setStatus('Exported ' + label + ' (' + (bytes.length / 1048576).toFixed(1) + ' MB, ' + (repeats * loopSeconds).toFixed(0) + ' s, stereo 16-bit). Loops without a click.');
    } catch (error) {
      setStatus('Export failed: ' + error.message);
    }
  }

  function copyLink() {
    const url = location.href.split('#')[0] + DSP.paramsToHash(params);
    history.replaceState(null, '', DSP.paramsToHash(params));
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(() => setStatus('Link copied.'), () => setStatus('Link is in the address bar.'));
    } else {
      setStatus('Link is in the address bar.');
    }
  }

  // ---- init -------------------------------------------------------------------------
  function init() {
    const presets = $('presets');
    for (const key of Object.keys(DSP.PRESETS)) {
      const button = document.createElement('button');
      button.textContent = DSP.PRESETS[key].name; button.dataset.key = key;
      button.setAttribute('data-testid', 'preset-' + key); button.setAttribute('aria-pressed', 'false');
      button.addEventListener('click', () => { params = DSP.presetParams(key); activePreset = key; changed(); });
      presets.append(button);
    }
    mainControls.forEach((def) => buildControl(def, $('controls')));
    advancedControls.forEach((def) => buildControl(def, $('advanced')));
    $('level').addEventListener('input', () => { params.level = Number($('level').value); changed(); });
    $('play').addEventListener('click', () => (audio && audio.source ? stopPlayback() : startPlayback()));
    $('timer').addEventListener('change', () => { if (audio) { audio.startedAt = performance.now(); tickTimer(); } });
    $('pitch').addEventListener('input', () => {
      pitchHz = DSP.freqFromSlider($('pitch').value / 1000, FREQ_RANGE[0], FREQ_RANGE[1]);
      $('out-pitch').textContent = hz(pitchHz);
      if (toneNode) toneNode.osc.frequency.setTargetAtTime(pitchHz, audio.ctx.currentTime, 0.02);
    });
    $('pitch').value = Math.round(DSP.sliderFromFreq(pitchHz, FREQ_RANGE[0], FREQ_RANGE[1]) * 1000);
    $('out-pitch').textContent = hz(pitchHz);
    $('pitch-play').addEventListener('click', togglePitch);
    $('pitch-apply').addEventListener('click', () => {
      params.notch = { on: true, freq: pitchHz, width: params.notch.width, depth: Math.max(30, params.notch.depth) };
      activePreset = null; changed(); setStatus('Notch centred on ' + hz(pitchHz) + '.');
    });
    $('export-loop').addEventListener('click', () => exportWav(0, 'loop'));
    $('export-1').addEventListener('click', () => exportWav(60, '1min'));
    $('export-10').addEventListener('click', () => exportWav(600, '10min'));
    $('share').addEventListener('click', copyLink);
    window.addEventListener('resize', () => { if (synth) drawSpectrum(synth.channels[0]); });
    syncControls();
    regenerate();
  }

  init();
}());
