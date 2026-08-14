/**
 * UI wiring: tabs, live meter, calibration, and history dashboard.
 * Relies on globals defined by audio-math.js, storage.js, audio-engine.js,
 * chart.js, and ai-briefing.js (all loaded as classic scripts before this one).
 */

(function () {
  const state = loadState();
  const engine = createAudioEngine({ sampleIntervalMs: 100 });

  let activeContext = null; // 'live' | 'calibration' | null
  let liveReadings = [];
  let liveSessionStartMs = 0;
  let lastSavedSummary = null; // { avgDb, peakDb, durationSec, series }

  let calibRawDb = null;

  let historySearchTerm = '';
  let historySortKey = 'endedAt';
  let historySortDir = 'desc';
  let selectedSessionId = null;
  let aiKey = '';

  const ZONE_BANDS = ZONES.map((z) => ({ maxDb: z.max === Infinity ? 130 : z.max, color: z.color }));

  // ---------- DOM lookups ----------
  const el = (id) => document.getElementById(id);

  const tabButtons = document.querySelectorAll('[data-tab-button]');
  const tabPanels = document.querySelectorAll('[data-tab-panel]');

  function showTab(name) {
    tabButtons.forEach((btn) => btn.classList.toggle('active', btn.dataset.tabButton === name));
    tabPanels.forEach((panel) => panel.classList.toggle('active', panel.dataset.tabPanel === name));
    if (name === 'history') renderHistory();
  }

  tabButtons.forEach((btn) => {
    btn.addEventListener('click', () => showTab(btn.dataset.tabButton));
  });

  // ---------- shared engine reading dispatch ----------
  engine.on('reading', (reading) => {
    if (activeContext === 'live') handleLiveReading(reading);
    else if (activeContext === 'calibration') handleCalibReading(reading);
  });

  engine.on('error', () => {
    showMicError('Something went wrong while reading the microphone. Try stopping and starting again.');
  });

  function showMicError(message) {
    const box = el('mic-error');
    box.textContent = message;
    box.hidden = !message;
  }

  // ================= LIVE METER =================

  function renderCalibrationBanner() {
    const banner = el('uncalibrated-banner');
    if (state.calibration.calibratedAt) {
      banner.hidden = true;
    } else {
      banner.hidden = false;
      banner.textContent =
        'Uncalibrated — readings are relative, not an authoritative sound level. Visit the Calibration tab to set a reference offset.';
    }
  }

  function updateReadingDisplay(reading) {
    const suffix = state.calibration.calibratedAt ? '' : ' (uncalibrated)';
    el('db-reading').textContent = `${reading.db.toFixed(1)} dB(A)${suffix}`;
    const badge = el('zone-badge');
    badge.textContent = `${reading.zone.icon} ${reading.zone.label}`;
    badge.style.color = reading.zone.color;
    badge.dataset.zone = reading.zone.key;
  }

  function drawLiveChart() {
    const canvas = el('live-chart');
    const nowT = liveReadings.length ? liveReadings[liveReadings.length - 1].t : 0;
    const windowed = liveReadings.filter((r) => nowT - r.t <= 60);
    drawDbLineChart(canvas, windowed, { minDb: 30, maxDb: 110, zoneBands: ZONE_BANDS });
  }

  function handleLiveReading(reading) {
    liveReadings.push(reading);
    updateReadingDisplay(reading);
    drawLiveChart();
  }

  function resetLiveDisplay() {
    el('db-reading').textContent = '-- dB';
    el('zone-badge').textContent = '';
    el('zone-badge').removeAttribute('data-zone');
    drawDbLineChart(el('live-chart'), [], { minDb: 30, maxDb: 110, zoneBands: ZONE_BANDS });
  }

  el('start-meter-btn').addEventListener('click', async () => {
    showMicError('');
    el('save-session-panel').hidden = true;
    el('session-summary').hidden = true;
    try {
      await engine.start(state.calibration.offsetDb);
    } catch (err) {
      showMicError('Microphone access was denied or is unavailable. Grant microphone permission and try again.');
      return;
    }
    activeContext = 'live';
    liveReadings = [];
    liveSessionStartMs = Date.now();
    el('start-meter-btn').hidden = true;
    el('stop-meter-btn').hidden = false;
  });

  el('stop-meter-btn').addEventListener('click', () => {
    engine.stop();
    activeContext = null;
    el('start-meter-btn').hidden = false;
    el('stop-meter-btn').hidden = true;

    const durationSec = (Date.now() - liveSessionStartMs) / 1000;
    if (liveReadings.length === 0) {
      showMicError('No readings were captured — try measuring for a bit longer.');
      resetLiveDisplay();
      return;
    }
    const dbValues = liveReadings.map((r) => r.db);
    const avgDb = dbValues.reduce((a, b) => a + b, 0) / dbValues.length;
    const peakDb = Math.max(...dbValues);

    lastSavedSummary = { avgDb, peakDb, durationSec, series: liveReadings.slice() };

    el('session-summary').hidden = false;
    el('summary-avg').textContent = avgDb.toFixed(1);
    el('summary-peak').textContent = peakDb.toFixed(1);
    el('summary-duration').textContent = durationSec.toFixed(1);
    el('save-session-panel').hidden = false;
    el('venue-input').value = '';
    el('note-input').value = '';
  });

  el('save-session-btn').addEventListener('click', () => {
    if (!lastSavedSummary) return;
    const venue = el('venue-input').value.trim();
    if (!venue) {
      el('venue-validation').textContent = 'Enter a venue or location name before saving.';
      el('venue-validation').hidden = false;
      return;
    }
    el('venue-validation').hidden = true;
    const note = el('note-input').value.trim();
    const endedAt = new Date().toISOString();
    const startedAt = new Date(Date.now() - lastSavedSummary.durationSec * 1000).toISOString();
    const doseDeltaPct = computeDosePercent(lastSavedSummary.avgDb, lastSavedSummary.durationSec);

    addSession(state, {
      id: genId(),
      venue,
      note,
      startedAt,
      endedAt,
      durationSec: lastSavedSummary.durationSec,
      avgDb: lastSavedSummary.avgDb,
      peakDb: lastSavedSummary.peakDb,
      doseDeltaPct,
      series: lastSavedSummary.series,
    });

    lastSavedSummary = null;
    el('save-session-panel').hidden = true;
    el('session-summary').hidden = true;
    resetLiveDisplay();
    renderHistory();
  });

  el('discard-session-btn').addEventListener('click', () => {
    lastSavedSummary = null;
    el('save-session-panel').hidden = true;
    el('session-summary').hidden = true;
    resetLiveDisplay();
  });

  // ================= CALIBRATION =================

  function renderCalibrationStatus() {
    const box = el('calibration-status');
    if (state.calibration.calibratedAt) {
      box.textContent = `Calibrated: offset ${state.calibration.offsetDb.toFixed(1)} dB (set ${new Date(state.calibration.calibratedAt).toLocaleString()}, reference ${state.calibration.referenceLabel} dB)`;
    } else {
      box.textContent = 'Not calibrated — Live Meter readings are relative only.';
    }
  }

  function handleCalibReading(reading) {
    calibRawDb = reading.db;
    el('calib-raw-reading').textContent = `${reading.db.toFixed(1)} dB (raw, uncalibrated)`;
  }

  el('calib-start-btn').addEventListener('click', async () => {
    showMicError('');
    try {
      await engine.start(0);
    } catch (err) {
      showMicError('Microphone access was denied or is unavailable. Grant microphone permission and try again.');
      return;
    }
    activeContext = 'calibration';
    calibRawDb = null;
    el('calib-start-btn').hidden = true;
    el('calib-stop-btn').hidden = false;
  });

  el('calib-stop-btn').addEventListener('click', () => {
    engine.stop();
    activeContext = null;
    el('calib-start-btn').hidden = false;
    el('calib-stop-btn').hidden = true;
  });

  el('calib-set-btn').addEventListener('click', () => {
    const refValue = parseFloat(el('calib-reference-input').value);
    if (Number.isNaN(refValue)) {
      el('calib-validation').textContent = 'Enter a numeric reference dB value first.';
      el('calib-validation').hidden = false;
      return;
    }
    if (calibRawDb === null) {
      el('calib-validation').textContent = 'Start calibration sampling first so a raw reading is available.';
      el('calib-validation').hidden = false;
      return;
    }
    el('calib-validation').hidden = true;
    const offset = refValue - calibRawDb;
    saveCalibration(state, offset, refValue);
    renderCalibrationStatus();
    renderCalibrationBanner();
  });

  el('calib-reset-btn').addEventListener('click', () => {
    resetCalibration(state);
    renderCalibrationStatus();
    renderCalibrationBanner();
  });

  // ================= HISTORY =================

  function filteredSortedSessions() {
    const term = historySearchTerm.trim().toLowerCase();
    let list = state.sessions.filter((s) => !term || s.venue.toLowerCase().includes(term));
    list = list.slice().sort((a, b) => {
      let av = a[historySortKey];
      let bv = b[historySortKey];
      if (typeof av === 'string') {
        av = av.toLowerCase();
        bv = bv.toLowerCase();
      }
      if (av < bv) return historySortDir === 'asc' ? -1 : 1;
      if (av > bv) return historySortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return list;
  }

  function renderDailyDose() {
    const pct = cumulativeDosePct(state, new Date().toISOString());
    el('daily-dose-summary').textContent = doseSafetyMessage(pct);
  }

  function renderHistoryTable() {
    const tbody = el('history-tbody');
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);

    const sessions = filteredSortedSessions();
    el('history-empty').hidden = sessions.length !== 0;

    sessions.forEach((session) => {
      const row = document.createElement('tr');
      row.dataset.testid = 'history-row';
      row.dataset.sessionId = session.id;

      const dateCell = document.createElement('td');
      dateCell.textContent = new Date(session.endedAt).toLocaleString();
      row.appendChild(dateCell);

      const venueCell = document.createElement('td');
      venueCell.textContent = session.venue;
      row.appendChild(venueCell);

      const avgCell = document.createElement('td');
      avgCell.textContent = session.avgDb.toFixed(1);
      row.appendChild(avgCell);

      const peakCell = document.createElement('td');
      peakCell.textContent = session.peakDb.toFixed(1);
      row.appendChild(peakCell);

      const durCell = document.createElement('td');
      durCell.textContent = `${Math.round(session.durationSec)}s`;
      row.appendChild(durCell);

      const doseCell = document.createElement('td');
      doseCell.textContent = `${session.doseDeltaPct.toFixed(1)}%`;
      row.appendChild(doseCell);

      row.addEventListener('click', () => selectSession(session.id));
      tbody.appendChild(row);
    });
  }

  function renderTrend() {
    const chronological = state.sessions.slice().sort((a, b) => new Date(a.endedAt) - new Date(b.endedAt));
    drawTrendChart(
      el('trend-chart'),
      chronological.map((s) => s.avgDb),
      { minDb: 30, maxDb: 110 }
    );
  }

  function selectSession(id) {
    selectedSessionId = id;
    const session = state.sessions.find((s) => s.id === id);
    const panel = el('session-detail');
    if (!session) {
      panel.hidden = true;
      return;
    }
    panel.hidden = false;
    el('detail-venue').textContent = session.venue;
    el('detail-note').textContent = session.note || '(no note)';
    el('detail-avg').textContent = session.avgDb.toFixed(1);
    el('detail-peak').textContent = session.peakDb.toFixed(1);
    el('detail-duration').textContent = `${Math.round(session.durationSec)}s`;
    el('detail-dose').textContent = `${session.doseDeltaPct.toFixed(1)}%`;
    el('ai-briefing-text').textContent = '';
    drawDbLineChart(el('detail-chart'), session.series, { minDb: 30, maxDb: 110, zoneBands: ZONE_BANDS });
  }

  el('history-search').addEventListener('input', (e) => {
    historySearchTerm = e.target.value;
    renderHistoryTable();
  });

  document.querySelectorAll('[data-sort-key]').forEach((th) => {
    th.addEventListener('click', () => {
      const key = th.dataset.sortKey;
      if (historySortKey === key) {
        historySortDir = historySortDir === 'asc' ? 'desc' : 'asc';
      } else {
        historySortKey = key;
        historySortDir = 'asc';
      }
      renderHistoryTable();
    });
  });

  el('delete-session-btn').addEventListener('click', () => {
    if (!selectedSessionId) return;
    deleteSession(state, selectedSessionId);
    selectedSessionId = null;
    el('session-detail').hidden = true;
    renderHistory();
  });

  el('ai-key-input').addEventListener('input', (e) => {
    aiKey = e.target.value.trim();
  });

  el('ai-briefing-btn').addEventListener('click', async () => {
    const session = state.sessions.find((s) => s.id === selectedSessionId);
    if (!session) return;
    el('ai-briefing-text').textContent = 'Loading...';
    const text = await getAiOrFallbackBriefing(aiKey, session);
    el('ai-briefing-text').textContent = text;
  });

  function renderHistory() {
    renderDailyDose();
    renderHistoryTable();
    renderTrend();
  }

  // ================= INIT =================
  renderCalibrationBanner();
  renderCalibrationStatus();
  resetLiveDisplay();
  renderHistory();
  showTab('live');
})();
