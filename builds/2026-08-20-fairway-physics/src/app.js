(function () {
  'use strict';

  var STATS_KEY = 'fairwayphysics_stats';
  var DAILY_KEY_PREFIX = 'fairwayphysics_daily_';
  var CADDIE_MODEL = 'claude-haiku-4-5-20251001';

  var ZONE_COLORS = {
    fairway: '#4caf6b',
    rough: '#7f9f5f',
    bunker: '#d9c48b',
    water: '#4a90d9',
    ob: 'rgba(192, 57, 43, 0.55)',
    green: '#a9dfb0'
  };

  var els = {};
  var state = null;

  function byId(id) {
    return document.getElementById(id);
  }

  function pad2(n) {
    return n < 10 ? '0' + n : String(n);
  }

  function todayUtcString() {
    var d = new Date();
    return d.getUTCFullYear() + '-' + pad2(d.getUTCMonth() + 1) + '-' + pad2(d.getUTCDate());
  }

  function distanceYd(a, b) {
    var dx = a.x - b.x;
    var dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function defaultStats() {
    return {
      roundsCompleted: 0,
      bestRoundScore: null,
      totalStrokesByHole: window.COURSE.map(function () {
        return [];
      }),
      practiceAttempts: 0
    };
  }

  function loadStats() {
    try {
      var raw = localStorage.getItem(STATS_KEY);
      if (!raw) return defaultStats();
      var parsed = JSON.parse(raw);
      if (!parsed.totalStrokesByHole || parsed.totalStrokesByHole.length !== window.COURSE.length) {
        return defaultStats();
      }
      return parsed;
    } catch (e) {
      return defaultStats();
    }
  }

  function saveStats(stats) {
    localStorage.setItem(STATS_KEY, JSON.stringify(stats));
  }

  function loadDailyRecord(dateStr) {
    try {
      var raw = localStorage.getItem(DAILY_KEY_PREFIX + dateStr);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  }

  function saveDailyRecord(dateStr, record) {
    localStorage.setItem(DAILY_KEY_PREFIX + dateStr, JSON.stringify(record));
  }

  function clearEl(el) {
    while (el.firstChild) {
      el.removeChild(el.firstChild);
    }
  }

  // --- Canvas rendering -----------------------------------------------

  function toCanvasXY(hole, point, canvas) {
    var marginX = 20;
    var marginY = 20;
    var pxPerYardX = (canvas.width - marginX * 2) / 140;
    var pxPerYardY = (canvas.height - marginY * 2) / (hole.yardage + 40);
    return {
      cx: canvas.width / 2 + point.x * pxPerYardX,
      cy: canvas.height - marginY - (point.y + 20) * pxPerYardY
    };
  }

  function drawCourse(hole) {
    var canvas = els.canvas;
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = ZONE_COLORS.rough;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw in a fixed back-to-front priority, not course-data array order:
    // a broad rough/fairway corridor rectangle can geometrically contain a
    // narrower hazard rectangle, and the last thing painted always wins on
    // a canvas — so hazards must always be painted after (on top of) the
    // corridor, regardless of which order course-data.js happens to list
    // them in. This mirrors engine.js's classifyLie priority for the same
    // reason: rendering order and lookup priority both need "hazards beat
    // corridor," just applied in opposite directions (last-drawn-wins vs.
    // first-match-wins).
    ['fairway', 'bunker', 'water', 'ob'].forEach(function (renderType) {
      hole.zones
        .filter(function (zone) {
          return zone.type === renderType;
        })
        .forEach(function (zone) {
          var topLeft = toCanvasXY(hole, { x: zone.xMin, y: zone.yMax }, canvas);
          var bottomRight = toCanvasXY(hole, { x: zone.xMax, y: zone.yMin }, canvas);
          ctx.fillStyle = ZONE_COLORS[zone.type];
          ctx.fillRect(topLeft.cx, topLeft.cy, bottomRight.cx - topLeft.cx, bottomRight.cy - topLeft.cy);
        });
    });

    var pinXY = toCanvasXY(hole, hole.pin, canvas);
    var greenRadiusPx = hole.greenRadius * ((canvas.width - 40) / 140);
    ctx.fillStyle = ZONE_COLORS.green;
    ctx.beginPath();
    ctx.arc(pinXY.cx, pinXY.cy, greenRadiusPx, 0, Math.PI * 2);
    ctx.fill();

    var teeXY = toCanvasXY(hole, hole.tee, canvas);
    ctx.fillStyle = '#333333';
    ctx.fillRect(teeXY.cx - 4, teeXY.cy - 4, 8, 8);

    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(pinXY.cx, pinXY.cy);
    ctx.lineTo(pinXY.cx, pinXY.cy - 16);
    ctx.stroke();
    ctx.fillStyle = '#e74c3c';
    ctx.beginPath();
    ctx.moveTo(pinXY.cx, pinXY.cy - 16);
    ctx.lineTo(pinXY.cx + 10, pinXY.cy - 12);
    ctx.lineTo(pinXY.cx, pinXY.cy - 8);
    ctx.fill();
  }

  function drawBall(hole, point) {
    var canvas = els.canvas;
    var ctx = canvas.getContext('2d');
    var xy = toCanvasXY(hole, point, canvas);
    ctx.fillStyle = '#ffffff';
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(xy.cx, xy.cy, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
  }

  function redraw(hole, ballPoint) {
    drawCourse(hole);
    drawBall(hole, ballPoint);
  }

  function animateFlight(hole, fromPoint, landingPoint, finalPoint) {
    var durationMs = 500;
    var start = performance.now();

    function frame(now) {
      var t = Math.min(1, (now - start) / durationMs);
      var current = {
        x: fromPoint.x + (landingPoint.x - fromPoint.x) * t,
        y: fromPoint.y + (landingPoint.y - fromPoint.y) * t
      };
      drawCourse(hole);
      var ctx = els.canvas.getContext('2d');
      var fromXY = toCanvasXY(hole, fromPoint, els.canvas);
      var toXY = toCanvasXY(hole, current, els.canvas);
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(fromXY.cx, fromXY.cy);
      ctx.lineTo(toXY.cx, toXY.cy);
      ctx.stroke();
      drawBall(hole, current);
      if (t < 1) {
        requestAnimationFrame(frame);
      } else {
        redraw(hole, finalPoint);
      }
    }
    requestAnimationFrame(frame);
  }

  // --- Caddie -----------------------------------------------------------

  function nearbyHazards(hole, fromY) {
    return hole.zones
      .filter(function (z) {
        return (z.type === 'water' || z.type === 'bunker' || z.type === 'ob') && z.yMax > fromY;
      })
      .sort(function (a, b) {
        return a.yMin - b.yMin;
      })
      .slice(0, 2)
      .map(function (z) {
        return z.type + ' ~' + Math.max(0, Math.round(z.yMin - fromY)) + ' yds ahead';
      });
  }

  function deterministicCaddieTip(hole) {
    var dist = Math.round(distanceYd(state.position, hole.pin));
    var hazards = nearbyHazards(hole, state.position.y);
    if (state.lie === 'green') {
      return 'On the green, ' + dist + ' yards from the hole — read the break before you commit to power.';
    }
    if (hazards.length) {
      return 'Trouble ahead: ' + hazards.join(' and ') + '. Consider laying up short rather than forcing the carry.';
    }
    if (dist > 200) {
      return 'Plenty of hole left (' + dist + ' yds to the pin). Favor a club you trust over max distance.';
    }
    if (dist <= 30) {
      return "You're close — a shorter, controlled swing beats overpowering it.";
    }
    return dist + ' yards to the pin with a clear look. Pick your normal club for that yardage and commit.';
  }

  function showCaddieTip(text) {
    els.caddieTip.textContent = text;
  }

  function askCaddie() {
    var hole = window.COURSE[state.holeIndex];
    var apiKey = els.apiKeyInput.value.trim();
    if (!apiKey) {
      showCaddieTip(deterministicCaddieTip(hole));
      return;
    }
    var prompt =
      'You are a golf caddie. In 1-2 short sentences, give strategy advice. Par ' +
      hole.par +
      ', ' +
      Math.round(distanceYd(state.position, hole.pin)) +
      ' yards to the pin, lie: ' +
      state.lie +
      ', wind ' +
      state.wind.windSpeedMph +
      ' mph, nearby hazards: ' +
      (nearbyHazards(hole, state.position.y).join('; ') || 'none') +
      '.';

    fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: CADDIE_MODEL,
        max_tokens: 120,
        messages: [{ role: 'user', content: prompt }]
      })
    })
      .then(function (response) {
        if (!response.ok) throw new Error('caddie request failed');
        return response.json();
      })
      .then(function (data) {
        var text = data && data.content && data.content[0] && data.content[0].text;
        if (!text) throw new Error('empty response');
        showCaddieTip(text);
      })
      .catch(function () {
        showCaddieTip(deterministicCaddieTip(hole));
      });
  }

  // --- Game flow ----------------------------------------------------------

  function createSession(mode, startHoleIndex) {
    return {
      mode: mode,
      holeIndex: startHoleIndex,
      strokesTaken: 0,
      position: null,
      lie: 'tee',
      wind: { windSpeedMph: 0, windDirectionDeg: 0 },
      scorecard: [],
      dateStr: todayUtcString()
    };
  }

  function windForHole(mode, dateStr, holeIndex) {
    if (mode === 'daily') {
      return window.FairwayEngine.dailySeed(dateStr, holeIndex);
    }
    return { windSpeedMph: 0, windDirectionDeg: 0 };
  }

  function compassLabel(deg) {
    var dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    return dirs[Math.round(deg / 45) % 8];
  }

  function updateHoleInfoDisplay() {
    var hole = window.COURSE[state.holeIndex];
    els.holeName.textContent = hole.name;
    els.holePar.textContent = String(hole.par);
    els.holeYardage.textContent = String(hole.yardage);
    els.strokeCount.textContent = String(state.strokesTaken + 1);
    els.distanceToPin.textContent = String(Math.round(distanceYd(state.position, hole.pin)));
    els.lieLabel.textContent = state.lie;
    els.windDisplay.textContent =
      state.wind.windSpeedMph + ' mph from the ' + compassLabel(state.wind.windDirectionDeg);
    els.shuffleWindBtn.classList.toggle('hidden', state.mode !== 'practice');
  }

  function toggleControls() {
    var onGreen = state.lie === 'green';
    els.shotControls.classList.toggle('hidden', onGreen);
    els.puttControls.classList.toggle('hidden', !onGreen);
  }

  function loadHole(index) {
    var hole = window.COURSE[index];
    state.holeIndex = index;
    state.strokesTaken = 0;
    state.position = { x: hole.tee.x, y: hole.tee.y };
    state.lie = 'tee';
    state.wind = windForHole(state.mode, state.dateStr, index);
    updateHoleInfoDisplay();
    toggleControls();
    redraw(hole, state.position);
    els.caddieTip.textContent = '';
    els.shotMessage.textContent = '';
  }

  function completeHole() {
    var hole = window.COURSE[state.holeIndex];
    var scoreInfo = window.FairwayEngine.scoreHole(state.strokesTaken, hole.par);
    state.scorecard.push({
      holeId: hole.id,
      name: hole.name,
      par: hole.par,
      strokes: state.strokesTaken,
      label: scoreInfo.label,
      delta: scoreInfo.delta
    });
    els.holeResultLabel.textContent =
      hole.name + ': ' + scoreInfo.label + ' (' + state.strokesTaken + ' strokes)';
    els.gameScreen.classList.add('hidden');
    els.holeCompletePanel.classList.remove('hidden');
  }

  function onContinueAfterHole() {
    els.holeCompletePanel.classList.add('hidden');
    if (state.mode === 'daily') {
      if (state.holeIndex < window.COURSE.length - 1) {
        els.gameScreen.classList.remove('hidden');
        loadHole(state.holeIndex + 1);
      } else {
        finishDailyRound();
      }
    } else {
      var stats = loadStats();
      stats.practiceAttempts += 1;
      stats.totalStrokesByHole[state.holeIndex].push(state.scorecard[state.scorecard.length - 1].strokes);
      saveStats(stats);
      showModeScreen();
    }
  }

  function finishDailyRound() {
    var total = state.scorecard.reduce(function (sum, h) {
      return sum + h.delta;
    }, 0);
    var record = { completed: true, dateStr: state.dateStr, scorecard: state.scorecard, total: total };
    saveDailyRecord(state.dateStr, record);

    var stats = loadStats();
    stats.roundsCompleted += 1;
    if (stats.bestRoundScore === null || total < stats.bestRoundScore) {
      stats.bestRoundScore = total;
    }
    state.scorecard.forEach(function (h, i) {
      stats.totalStrokesByHole[i].push(h.strokes);
    });
    saveStats(stats);

    showScorecard(record.scorecard, record.total, record.dateStr);
  }

  function showScorecard(scorecard, total, dateStr) {
    clearEl(els.scorecardBody);
    var emojiMap = {
      Eagle: '🦅',
      Birdie: '🐦',
      Par: '⛳',
      Bogey: '🟨',
      'Double Bogey': '🟥'
    };
    var emojiLine = scorecard
      .map(function (h) {
        return emojiMap[h.label] || '🟥';
      })
      .join('');

    scorecard.forEach(function (h) {
      var tr = document.createElement('tr');
      [String(h.holeId), String(h.par), String(h.strokes), h.label].forEach(function (text) {
        var td = document.createElement('td');
        td.textContent = text;
        tr.appendChild(td);
      });
      els.scorecardBody.appendChild(tr);
    });
    els.roundTotal.textContent = window.FairwayEngine.formatScoreLabel(total);
    els.shareText.value =
      '⛳ Fairway Physics — Daily Round ' +
      dateStr +
      '\n' +
      emojiLine +
      '\nTotal: ' +
      window.FairwayEngine.formatScoreLabel(total);

    els.gameScreen.classList.add('hidden');
    els.modeScreen.classList.add('hidden');
    els.scorecardPanel.classList.remove('hidden');
  }

  function showModeScreen() {
    els.gameScreen.classList.add('hidden');
    els.scorecardPanel.classList.add('hidden');
    els.holeCompletePanel.classList.add('hidden');
    els.statsPanel.classList.add('hidden');

    var record = loadDailyRecord(todayUtcString());
    var completed = !!(record && record.completed);
    els.dailyModeBtn.classList.toggle('hidden', completed);
    els.dailyCompletedMessage.classList.toggle('hidden', !completed);
    els.viewDailyResultBtn.classList.toggle('hidden', !completed);

    els.modeScreen.classList.remove('hidden');
  }

  function startDaily() {
    state = createSession('daily', 0);
    els.modeScreen.classList.add('hidden');
    els.gameScreen.classList.remove('hidden');
    loadHole(0);
  }

  function startPractice() {
    var holeIndex = parseInt(els.practiceHoleSelect.value, 10);
    state = createSession('practice', holeIndex);
    els.modeScreen.classList.add('hidden');
    els.gameScreen.classList.remove('hidden');
    loadHole(holeIndex);
  }

  function viewDailyResult() {
    var record = loadDailyRecord(todayUtcString());
    if (record) {
      showScorecard(record.scorecard, record.total, record.dateStr);
    }
  }

  function takeShot() {
    var hole = window.COURSE[state.holeIndex];
    var shotInput = {
      club: els.clubSelect.value,
      powerPct: Number(els.powerSlider.value),
      aimDeg: Number(els.aimSlider.value),
      shape: els.shapeSelect.value,
      windSpeedMph: state.wind.windSpeedMph,
      windDirectionDeg: state.wind.windDirectionDeg
    };
    var fromPoint = { x: state.position.x, y: state.position.y };
    var result = window.FairwayEngine.resolveShot({ position: fromPoint }, shotInput, hole);
    state.strokesTaken += 1;

    if (result.penalty) {
      state.strokesTaken += 1;
      els.shotMessage.textContent =
        'Penalty! Into the ' + result.finalLie.toUpperCase() + ' — replay from the same spot (+1 stroke).';
      animateFlight(hole, fromPoint, result.landingPoint, fromPoint);
      updateHoleInfoDisplay();
      toggleControls();
      return;
    }

    els.shotMessage.textContent = '';
    state.position = result.resultPosition;
    state.lie = result.finalLie;
    animateFlight(hole, fromPoint, result.landingPoint, result.finalPoint);

    var holed = distanceYd(state.position, hole.pin) <= window.FairwayEngine.HOLE_CAPTURE_RADIUS_YD;
    if (holed) {
      completeHole();
      return;
    }
    updateHoleInfoDisplay();
    toggleControls();
  }

  function takePutt() {
    var hole = window.COURSE[state.holeIndex];
    var puttInput = {
      powerPct: Number(els.puttPowerSlider.value),
      aimDeg: Number(els.puttAimSlider.value)
    };
    var fromPoint = { x: state.position.x, y: state.position.y };
    var result = window.FairwayEngine.resolvePutt(fromPoint, hole, puttInput);
    state.strokesTaken += 1;
    animateFlight(hole, fromPoint, result.newPoint, result.newPoint);

    if (result.holed) {
      state.position = hole.pin;
      completeHole();
      return;
    }
    state.position = result.newPoint;
    state.lie = 'green';
    updateHoleInfoDisplay();
    toggleControls();
  }

  function shuffleWind() {
    state.wind = {
      windSpeedMph: Math.floor(Math.random() * 21),
      windDirectionDeg: Math.floor(Math.random() * 360)
    };
    updateHoleInfoDisplay();
  }

  function renderStatsPanel() {
    var stats = loadStats();
    els.roundsCompleted.textContent = String(stats.roundsCompleted);
    els.bestRoundScore.textContent =
      stats.bestRoundScore === null ? '—' : window.FairwayEngine.formatScoreLabel(stats.bestRoundScore);
    els.practiceAttempts.textContent = String(stats.practiceAttempts);

    clearEl(els.holeAverageBody);
    window.COURSE.forEach(function (hole, i) {
      var strokesList = stats.totalStrokesByHole[i] || [];
      var avg =
        strokesList.length > 0
          ? (strokesList.reduce(function (a, b) { return a + b; }, 0) / strokesList.length).toFixed(1)
          : '—';
      var tr = document.createElement('tr');
      [String(hole.id), String(hole.par), avg].forEach(function (text) {
        var td = document.createElement('td');
        td.textContent = text;
        tr.appendChild(td);
      });
      els.holeAverageBody.appendChild(tr);
    });
  }

  function copyShareResult() {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(els.shareText.value).catch(function () {});
      }
    } catch (e) {
      // Clipboard access can be blocked by permissions/sandboxing — non-fatal.
    }
  }

  function populateStaticOptions() {
    Object.keys(window.FairwayEngine.CLUBS).forEach(function (key) {
      if (key === 'putter') return;
      var opt = document.createElement('option');
      opt.value = key;
      opt.textContent = window.FairwayEngine.CLUBS[key].label;
      els.clubSelect.appendChild(opt);
    });
    els.clubSelect.value = 'driver';

    window.COURSE.forEach(function (hole, idx) {
      var opt = document.createElement('option');
      opt.value = String(idx);
      opt.textContent = 'Hole ' + hole.id + ' — ' + hole.name + ' (Par ' + hole.par + ')';
      els.practiceHoleSelect.appendChild(opt);
    });
  }

  function bindElements() {
    [
      'statsBtn', 'statsPanel', 'roundsCompleted', 'bestRoundScore', 'practiceAttempts',
      'holeAverageBody', 'closeStatsBtn', 'modeScreen', 'dailyModeBtn', 'practiceHoleSelect',
      'startPracticeBtn', 'dailyCompletedMessage', 'viewDailyResultBtn', 'gameScreen', 'holeName',
      'holePar', 'holeYardage', 'strokeCount', 'distanceToPin', 'lieLabel', 'windDisplay',
      'shuffleWindBtn', 'shotMessage', 'shotControls', 'clubSelect', 'powerSlider', 'powerValue',
      'aimSlider', 'aimValue', 'shapeSelect', 'shotBtn', 'puttControls', 'puttPowerSlider',
      'puttPowerValue', 'puttAimSlider', 'puttAimValue', 'puttBtn', 'apiKeyInput', 'caddieBtn',
      'caddieTip', 'holeCompletePanel', 'holeResultLabel', 'continueBtn', 'scorecardPanel',
      'scorecardBody', 'roundTotal', 'shareText', 'copyShareBtn', 'backToMenuBtn'
    ].forEach(function (id) {
      els[id] = byId(id);
    });
    els.canvas = byId('courseCanvas');
  }

  function bindEvents() {
    els.statsBtn.addEventListener('click', function () {
      renderStatsPanel();
      els.statsPanel.classList.remove('hidden');
    });
    els.closeStatsBtn.addEventListener('click', function () {
      els.statsPanel.classList.add('hidden');
    });
    els.dailyModeBtn.addEventListener('click', startDaily);
    els.startPracticeBtn.addEventListener('click', startPractice);
    els.viewDailyResultBtn.addEventListener('click', viewDailyResult);

    els.powerSlider.addEventListener('input', function () {
      els.powerValue.textContent = els.powerSlider.value;
    });
    els.aimSlider.addEventListener('input', function () {
      els.aimValue.textContent = els.aimSlider.value;
    });
    els.puttPowerSlider.addEventListener('input', function () {
      els.puttPowerValue.textContent = els.puttPowerSlider.value;
    });
    els.puttAimSlider.addEventListener('input', function () {
      els.puttAimValue.textContent = els.puttAimSlider.value;
    });

    els.shotBtn.addEventListener('click', takeShot);
    els.puttBtn.addEventListener('click', takePutt);
    els.shuffleWindBtn.addEventListener('click', shuffleWind);
    els.caddieBtn.addEventListener('click', askCaddie);
    els.continueBtn.addEventListener('click', onContinueAfterHole);
    els.copyShareBtn.addEventListener('click', copyShareResult);
    els.backToMenuBtn.addEventListener('click', showModeScreen);
  }

  function init() {
    bindElements();
    populateStaticOptions();
    bindEvents();
    showModeScreen();
  }

  init();
})();
