(function () {
  'use strict';

  /* ============================================================
     Tab switching
     ============================================================ */
  var tabButtons = Array.prototype.slice.call(document.querySelectorAll('.tab-btn'));
  var panels = {
    basics: document.getElementById('panel-basics'),
    artifact: document.getElementById('panel-artifact'),
    freq: document.getElementById('panel-freq'),
    cit: document.getElementById('panel-cit'),
    quiz: document.getElementById('panel-quiz'),
  };

  function switchTab(name) {
    tabButtons.forEach(function (btn) {
      var active = btn.getAttribute('data-tab') === name;
      btn.classList.toggle('active', active);
      btn.setAttribute('aria-selected', String(active));
    });
    Object.keys(panels).forEach(function (key) {
      panels[key].hidden = key !== name;
    });
  }

  tabButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      switchTab(btn.getAttribute('data-tab'));
    });
  });

  /* ============================================================
     Canvas drawing helpers
     ============================================================ */
  var PADDING = { left: 45, right: 15, top: 15, bottom: 30 };

  function clearCanvas(canvas) {
    var ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return ctx;
  }

  function plotDims(canvas) {
    return {
      w: canvas.width,
      h: canvas.height,
      plotW: canvas.width - PADDING.left - PADDING.right,
      plotH: canvas.height - PADDING.top - PADDING.bottom,
    };
  }

  function drawTimeFrame(ctx, canvas, yRange, preStimSamples, n, showOnsetMarker) {
    var dims = plotDims(canvas);
    var yMin = yRange[0];
    var yMax = yRange[1];
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    var zeroY = PADDING.top + dims.plotH * (1 - (0 - yMin) / (yMax - yMin));
    ctx.beginPath();
    ctx.moveTo(PADDING.left, zeroY);
    ctx.lineTo(dims.w - PADDING.right, zeroY);
    ctx.stroke();
    if (showOnsetMarker) {
      var stimX = PADDING.left + (preStimSamples / n) * dims.plotW;
      ctx.beginPath();
      ctx.moveTo(stimX, PADDING.top);
      ctx.lineTo(stimX, dims.h - PADDING.bottom);
      ctx.stroke();
      ctx.fillStyle = '#9aa7c2';
      ctx.font = '10px sans-serif';
      ctx.fillText('stimulus onset', Math.min(stimX + 3, dims.w - 90), dims.h - 4);
    }
    ctx.fillStyle = '#9aa7c2';
    ctx.font = '10px sans-serif';
    ctx.fillText(yMax.toFixed(0) + 'µV', 2, PADDING.top + 8);
    ctx.fillText(yMin.toFixed(0) + 'µV', 2, dims.h - PADDING.bottom);
  }

  function drawWaveformLine(ctx, canvas, waveform, yRange, lineWidth, color) {
    var dims = plotDims(canvas);
    var yMin = yRange[0];
    var yMax = yRange[1];
    var n = waveform.length;
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();
    for (var i = 0; i < n; i++) {
      var x = PADDING.left + (i / (n - 1)) * dims.plotW;
      var clamped = Math.max(yMin, Math.min(yMax, waveform[i]));
      var y = PADDING.top + dims.plotH * (1 - (clamped - yMin) / (yMax - yMin));
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }

  function drawLegend(ctx, canvas, entries) {
    var dims = plotDims(canvas);
    var x = dims.w - PADDING.right - 10;
    entries.forEach(function (entry, idx) {
      var y = PADDING.top + 10 + idx * 14;
      ctx.fillStyle = entry.color;
      ctx.font = '11px sans-serif';
      var textWidth = ctx.measureText(entry.label).width;
      ctx.fillText(entry.label, x - textWidth, y);
    });
  }

  function drawSpectrum(ctx, canvas, freqs, power, maxFreqToShow) {
    var dims = plotDims(canvas);
    var maxPower = 1e-9;
    for (var i = 0; i < power.length; i++) if (power[i] > maxPower) maxPower = power[i];
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(PADDING.left, dims.h - PADDING.bottom);
    ctx.lineTo(dims.w - PADDING.right, dims.h - PADDING.bottom);
    ctx.stroke();
    var showCount = freqs.length;
    for (var k = 0; k < freqs.length; k++) {
      if (freqs[k] > maxFreqToShow) {
        showCount = k;
        break;
      }
    }
    var barW = dims.plotW / showCount;
    ctx.fillStyle = '#5ec2ff';
    for (var b = 0; b < showCount; b++) {
      var barH = (power[b] / maxPower) * dims.plotH;
      ctx.fillRect(PADDING.left + b * barW, dims.h - PADDING.bottom - barH, Math.max(1, barW - 1), barH);
    }
    ctx.fillStyle = '#9aa7c2';
    ctx.font = '10px sans-serif';
    ctx.fillText('0 Hz', PADDING.left, dims.h - 4);
    ctx.fillText(maxFreqToShow + ' Hz', dims.w - PADDING.right - 32, dims.h - 4);
  }

  function drawHistogram(ctx, canvas, values, observedValue) {
    var dims = plotDims(canvas);
    var nBins = 30;
    var maxVal = observedValue;
    for (var i = 0; i < values.length; i++) if (values[i] > maxVal) maxVal = values[i];
    maxVal *= 1.08;
    if (maxVal <= 0) maxVal = 1;
    var binWidth = maxVal / nBins;
    var bins = new Array(nBins).fill(0);
    values.forEach(function (v) {
      var idx = Math.floor(v / binWidth);
      if (idx >= nBins) idx = nBins - 1;
      if (idx < 0) idx = 0;
      bins[idx]++;
    });
    var maxCount = 1;
    bins.forEach(function (c) {
      if (c > maxCount) maxCount = c;
    });
    var barW = dims.plotW / nBins;
    ctx.fillStyle = 'rgba(94,194,255,0.55)';
    bins.forEach(function (count, idx) {
      var barH = (count / maxCount) * dims.plotH;
      ctx.fillRect(PADDING.left + idx * barW, dims.h - PADDING.bottom - barH, Math.max(1, barW - 1), barH);
    });
    var xPos = PADDING.left + (observedValue / maxVal) * dims.plotW;
    ctx.strokeStyle = '#ffb454';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(xPos, PADDING.top);
    ctx.lineTo(xPos, dims.h - PADDING.bottom);
    ctx.stroke();
    ctx.fillStyle = '#e6ebf5';
    ctx.font = '11px sans-serif';
    ctx.fillText('null distribution of |permuted diff|', PADDING.left, 12);
    ctx.fillStyle = '#ffb454';
    ctx.fillText('observed', Math.min(xPos + 4, dims.w - 60), PADDING.top + 12);
  }

  /* ============================================================
     ERP Basics tab
     ============================================================ */
  function renderBasics() {
    var nTrials = parseInt(document.getElementById('basics-ntrials').value, 10);
    var noiseSD = parseFloat(document.getElementById('basics-noisesd').value);
    document.getElementById('basics-ntrials-value').textContent = String(nTrials);
    document.getElementById('basics-noisesd-value').textContent = String(noiseSD);

    var template = generateERPTemplate(350, 6, 100);
    var rng = mulberry32(1234);
    var g = makeGaussianRng(rng);
    var epochSet = generateEpochSet(template, noiseSD, nTrials, g, rng, 0, 0);
    var epochs = epochSet.epochs;
    var avg = averageEpochs(epochs);
    var baseline = Array.from(avg.slice(0, PRE_STIM_SAMPLES));
    var measuredSD = standardDeviation(baseline);
    var theoreticalSD = noiseSD / Math.sqrt(nTrials);
    var snrGain = noiseSD / measuredSD;

    document.getElementById('basics-measured-sd').textContent = measuredSD.toFixed(2) + ' µV';
    document.getElementById('basics-theory-sd').textContent = theoreticalSD.toFixed(2) + ' µV';
    document.getElementById('basics-snr-gain').textContent = '×' + snrGain.toFixed(2);

    var canvas = document.getElementById('basics-canvas');
    var ctx = clearCanvas(canvas);
    var yr = [-30, 30];
    drawTimeFrame(ctx, canvas, yr, PRE_STIM_SAMPLES, N_SAMPLES, true);
    var sampleTrials = epochs.slice(0, Math.min(8, epochs.length));
    sampleTrials.forEach(function (ep) {
      drawWaveformLine(ctx, canvas, ep, yr, 1, 'rgba(94,194,255,0.22)');
    });
    drawWaveformLine(ctx, canvas, avg, yr, 2.5, '#ffb454');
    drawLegend(ctx, canvas, [
      { label: 'single trials', color: 'rgba(94,194,255,0.6)' },
      { label: 'average (N=' + nTrials + ')', color: '#ffb454' },
    ]);
  }

  ['basics-ntrials', 'basics-noisesd'].forEach(function (id) {
    document.getElementById(id).addEventListener('input', renderBasics);
  });

  /* ============================================================
     Artifact Rejection tab
     ============================================================ */
  function renderArtifact() {
    var nTrials = parseInt(document.getElementById('artifact-ntrials').value, 10);
    var blinkRate = parseFloat(document.getElementById('artifact-blinkrate').value);
    var blinkAmp = parseFloat(document.getElementById('artifact-blinkamp').value);
    var threshold = parseFloat(document.getElementById('artifact-threshold').value);
    document.getElementById('artifact-ntrials-value').textContent = String(nTrials);
    document.getElementById('artifact-blinkrate-value').textContent = Math.round(blinkRate * 100) + '%';
    document.getElementById('artifact-blinkamp-value').textContent = String(blinkAmp);
    document.getElementById('artifact-threshold-value').textContent = String(threshold);

    var template = generateERPTemplate(350, 6, 100);
    var noiseSD = 3;
    var rng = mulberry32(777);
    var g = makeGaussianRng(rng);
    var epochSet = generateEpochSet(template, noiseSD, nTrials, g, rng, blinkRate, blinkAmp);
    var rejection = rejectArtifacts(epochSet.epochs, threshold, peakToPeak);

    document.getElementById('artifact-rejected').textContent = String(rejection.rejectedCount) + ' / ' + nTrials;
    document.getElementById('artifact-kept').textContent = String(rejection.clean.length) + ' / ' + nTrials;

    var canvas = document.getElementById('artifact-canvas');
    var ctx = clearCanvas(canvas);
    var yr = [-60, 60];
    drawTimeFrame(ctx, canvas, yr, PRE_STIM_SAMPLES, N_SAMPLES, true);
    var avgAll = averageEpochs(epochSet.epochs);
    drawWaveformLine(ctx, canvas, avgAll, yr, 2, 'rgba(255,107,107,0.85)');
    if (rejection.clean.length > 0) {
      var avgClean = averageEpochs(rejection.clean);
      drawWaveformLine(ctx, canvas, avgClean, yr, 2.5, '#4fd67f');
    }
    drawLegend(ctx, canvas, [
      { label: 'average, all trials', color: '#ff6b6b' },
      { label: 'average, after rejection', color: '#4fd67f' },
    ]);
  }

  ['artifact-ntrials', 'artifact-blinkrate', 'artifact-blinkamp', 'artifact-threshold'].forEach(function (id) {
    document.getElementById(id).addEventListener('input', renderArtifact);
  });

  /* ============================================================
     Frequency Domain tab
     ============================================================ */
  function renderFreq() {
    var alphaAmp = parseFloat(document.getElementById('freq-alpha-amp').value);
    var lineAmp = parseFloat(document.getElementById('freq-linenoise-amp').value);
    var broadbandSD = parseFloat(document.getElementById('freq-broadband-sd').value);
    var filterWindow = parseInt(document.getElementById('freq-filter-window').value, 10);
    document.getElementById('freq-alpha-amp-value').textContent = String(alphaAmp);
    document.getElementById('freq-linenoise-amp-value').textContent = String(lineAmp);
    document.getElementById('freq-broadband-sd-value').textContent = String(broadbandSD);
    document.getElementById('freq-filter-window-value').textContent = String(filterWindow) + (filterWindow === 1 ? ' (off)' : '');

    var n = N_SAMPLES;
    var sr = SAMPLE_RATE;
    var rng = mulberry32(4242);
    var g = makeGaussianRng(rng);
    var signal = new Array(n);
    for (var i = 0; i < n; i++) {
      var t = i / sr;
      signal[i] = alphaAmp * Math.sin(2 * Math.PI * 10 * t) + lineAmp * Math.sin(2 * Math.PI * 60 * t) + g() * broadbandSD;
    }
    var filtered = movingAverageFilter(signal, filterWindow);

    var timeCanvas = document.getElementById('freq-time-canvas');
    var timeCtx = clearCanvas(timeCanvas);
    var yr = [-15, 15];
    drawTimeFrame(timeCtx, timeCanvas, yr, 0, n, false);
    drawWaveformLine(timeCtx, timeCanvas, signal, yr, 1, 'rgba(94,194,255,0.35)');
    drawWaveformLine(timeCtx, timeCanvas, filtered, yr, 2, '#ffb454');
    drawLegend(timeCtx, timeCanvas, [
      { label: 'raw signal', color: 'rgba(94,194,255,0.6)' },
      { label: 'filtered', color: '#ffb454' },
    ]);

    var fftResult = fft(filtered, new Array(n).fill(0));
    var spectrum = powerSpectrum(fftResult.re, fftResult.im, sr);
    var specCanvas = document.getElementById('freq-spectrum-canvas');
    var specCtx = clearCanvas(specCanvas);
    drawSpectrum(specCtx, specCanvas, Array.from(spectrum.freqs), Array.from(spectrum.power), 80);
  }

  ['freq-alpha-amp', 'freq-linenoise-amp', 'freq-broadband-sd', 'freq-filter-window'].forEach(function (id) {
    document.getElementById(id).addEventListener('input', renderFreq);
  });

  /* ============================================================
     CIT Lab tab
     ============================================================ */
  var lastCitResult = null;

  function runCITTest() {
    var effectSlider = parseFloat(document.getElementById('cit-effect').value);
    var nProbe = parseInt(document.getElementById('cit-nprobe').value, 10);
    var nIrrelevant = parseInt(document.getElementById('cit-nirrelevant').value, 10);
    var innocent = document.getElementById('cit-innocent-toggle').checked;
    var effectiveEffect = innocent ? 0 : effectSlider;

    var baseTemplate = generateERPTemplate(350, 3, 120);
    var noiseSD = 6;
    var seedBase = Math.floor(Math.random() * 1e9);

    var probeTemplate = Float64Array.from(baseTemplate, function (v) {
      return v + effectiveEffect;
    });
    var rngProbe = mulberry32(seedBase);
    var gProbe = makeGaussianRng(rngProbe);
    var probeEpochs = generateEpochSet(probeTemplate, noiseSD, nProbe, gProbe, rngProbe, 0, 0).epochs;

    var rngIrr = mulberry32(seedBase + 999983);
    var gIrr = makeGaussianRng(rngIrr);
    var irrEpochs = generateEpochSet(baseTemplate, noiseSD, nIrrelevant, gIrr, rngIrr, 0, 0).epochs;

    var probeAmps = probeEpochs.map(function (ep) {
      return windowMeanAmplitude(ep, 300, 500);
    });
    var irrAmps = irrEpochs.map(function (ep) {
      return windowMeanAmplitude(ep, 300, 500);
    });

    var permRng = mulberry32(seedBase + 555);
    var result = permutationTest(probeAmps, irrAmps, 2000, permRng);

    var probeAvg = averageEpochs(probeEpochs);
    var irrAvg = averageEpochs(irrEpochs);

    document.getElementById('cit-observed-diff').textContent = result.observedDiff.toFixed(2) + ' µV';
    document.getElementById('cit-pvalue').textContent = result.pValue.toFixed(4);
    var detected = result.pValue < 0.05;
    var verdictEl = document.getElementById('cit-verdict');
    verdictEl.textContent = detected ? 'Detected (p < 0.05)' : 'Not detected (p ≥ 0.05)';
    verdictEl.style.color = detected ? 'var(--bad)' : 'var(--good)';

    var avgCanvas = document.getElementById('cit-avg-canvas');
    var avgCtx = clearCanvas(avgCanvas);
    var yr = [-10, 14];
    drawTimeFrame(avgCtx, avgCanvas, yr, PRE_STIM_SAMPLES, N_SAMPLES, true);
    drawWaveformLine(avgCtx, avgCanvas, irrAvg, yr, 2.5, '#5ec2ff');
    drawWaveformLine(avgCtx, avgCanvas, probeAvg, yr, 2.5, '#ff8fa3');
    drawLegend(avgCtx, avgCanvas, [
      { label: 'irrelevant', color: '#5ec2ff' },
      { label: 'probe', color: '#ff8fa3' },
    ]);

    var nullCanvas = document.getElementById('cit-null-canvas');
    var nullCtx = clearCanvas(nullCanvas);
    drawHistogram(nullCtx, nullCanvas, result.nullDistribution, Math.abs(result.observedDiff));

    lastCitResult = {
      observedDiff: result.observedDiff,
      pValue: result.pValue,
      nPermutations: result.nPermutations,
      nProbe: nProbe,
      nIrrelevant: nIrrelevant,
      innocent: innocent,
    };
  }

  document.getElementById('cit-run-test').addEventListener('click', runCITTest);
  ['cit-effect', 'cit-nprobe', 'cit-nirrelevant'].forEach(function (id) {
    document.getElementById(id).addEventListener('input', function () {
      document.getElementById(id + '-value').textContent = document.getElementById(id).value;
    });
  });

  function buildDeterministicExplanation(result) {
    var detected = result.pValue < 0.05;
    return (
      'Observed probe-minus-irrelevant amplitude difference: ' +
      result.observedDiff.toFixed(2) +
      ' µV, assessed against ' +
      result.nPermutations +
      ' label permutations. Permutation p-value = ' +
      result.pValue.toFixed(4) +
      ', which is ' +
      (detected ? 'below' : 'at or above') +
      ' the conventional 0.05 threshold, so this run is classified as ' +
      (detected
        ? '"detected" (the probe response differs from the irrelevant response more than chance alone would predict).'
        : '"not detected" (consistent with no distinguishable probe response).') +
      ' Remember: even a truly innocent subject with no real concealed knowledge will cross this threshold about 5% of the time by chance alone — a single test result is never proof on its own.'
    );
  }

  function explainCIT() {
    var output = document.getElementById('cit-explain-output');
    if (!lastCitResult) {
      output.textContent = 'Run the permutation test first.';
      return;
    }
    var apiKey = document.getElementById('cit-api-key').value.trim();
    var fallbackText = buildDeterministicExplanation(lastCitResult);
    if (!apiKey) {
      output.textContent = fallbackText;
      return;
    }
    output.textContent = 'Contacting Claude…';
    var prompt =
      'You are explaining a statistics result to a psychology researcher. A permutation test comparing probe vs ' +
      'irrelevant P300 amplitude gave an observed difference of ' +
      lastCitResult.observedDiff.toFixed(2) +
      ' microvolts, p-value ' +
      lastCitResult.pValue.toFixed(4) +
      ' from ' +
      lastCitResult.nPermutations +
      ' permutations, with ' +
      lastCitResult.nProbe +
      ' probe trials and ' +
      lastCitResult.nIrrelevant +
      ' irrelevant trials. In 2-3 sentences, explain what this result means and note the test’s false-positive limitation. Do not invent numbers not given.';

    fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 300,
        messages: [{ role: 'user', content: prompt }],
      }),
    })
      .then(function (response) {
        if (!response.ok) throw new Error('API error ' + response.status);
        return response.json();
      })
      .then(function (data) {
        var text = data && data.content && data.content[0] && typeof data.content[0].text === 'string' ? data.content[0].text : null;
        output.textContent = text || fallbackText;
      })
      .catch(function () {
        output.textContent = fallbackText;
      });
  }

  document.getElementById('cit-explain-btn').addEventListener('click', explainCIT);

  /* ============================================================
     Quiz
     ============================================================ */
  var quizQuestions = [];
  var quizIndex = 0;
  var quizScore = 0;
  var quizAnswered = false;

  function readBestScore() {
    try {
      return localStorage.getItem('erplab_quiz_best') || '0';
    } catch (e) {
      return '0';
    }
  }

  function writeBestScore(score) {
    try {
      var best = parseInt(readBestScore(), 10);
      if (score > best) localStorage.setItem('erplab_quiz_best', String(score));
    } catch (e) {
      /* localStorage unavailable (private mode) -- score simply won't persist */
    }
  }

  function renderQuizIntro() {
    document.getElementById('quiz-best-score').textContent = readBestScore();
    document.getElementById('quiz-intro').hidden = false;
    document.getElementById('quiz-active').hidden = true;
    document.getElementById('quiz-results').hidden = true;
  }

  function startQuiz() {
    var live = generateLiveQuestions(Date.now());
    var rng = mulberry32(Math.floor(Math.random() * 1e9));
    quizQuestions = fisherYatesShuffle(FIXED_QUESTIONS.concat(live), rng);
    quizIndex = 0;
    quizScore = 0;
    quizAnswered = false;
    document.getElementById('quiz-intro').hidden = true;
    document.getElementById('quiz-results').hidden = true;
    document.getElementById('quiz-active').hidden = false;
    renderQuizQuestion();
  }

  function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  function renderQuizQuestion() {
    var q = quizQuestions[quizIndex];
    document.getElementById('quiz-progress').textContent = 'Question ' + (quizIndex + 1) + ' / ' + quizQuestions.length;
    document.getElementById('quiz-question').textContent = q.prompt;
    var choicesEl = document.getElementById('quiz-choices');
    clearChildren(choicesEl);
    q.choices.forEach(function (choice, idx) {
      var btn = document.createElement('button');
      btn.textContent = choice;
      btn.setAttribute('data-testid', 'quiz-choice-' + idx);
      btn.addEventListener('click', function () {
        answerQuiz(idx);
      });
      choicesEl.appendChild(btn);
    });
    document.getElementById('quiz-feedback').hidden = true;
    document.getElementById('quiz-next').hidden = true;
    quizAnswered = false;
  }

  function answerQuiz(idx) {
    if (quizAnswered) return;
    quizAnswered = true;
    var q = quizQuestions[quizIndex];
    var buttons = document.getElementById('quiz-choices').querySelectorAll('button');
    buttons.forEach(function (b, i) {
      b.disabled = true;
      if (i === q.correctIndex) b.classList.add('correct');
      else if (i === idx) b.classList.add('incorrect');
    });
    if (idx === q.correctIndex) quizScore++;
    var feedback = document.getElementById('quiz-feedback');
    feedback.textContent = (idx === q.correctIndex ? 'Correct. ' : 'Incorrect. ') + q.explanation;
    feedback.hidden = false;
    document.getElementById('quiz-next').hidden = false;
  }

  function finishQuiz() {
    document.getElementById('quiz-active').hidden = true;
    document.getElementById('quiz-results').hidden = false;
    document.getElementById('quiz-final-score').textContent = String(quizScore);
    writeBestScore(quizScore);
  }

  document.getElementById('quiz-next').addEventListener('click', function () {
    quizIndex++;
    if (quizIndex >= quizQuestions.length) finishQuiz();
    else renderQuizQuestion();
  });

  document.getElementById('quiz-start').addEventListener('click', startQuiz);
  document.getElementById('quiz-restart').addEventListener('click', renderQuizIntro);

  /* ============================================================
     Initial render
     ============================================================ */
  renderBasics();
  renderArtifact();
  renderFreq();
  runCITTest();
  renderQuizIntro();
})();
