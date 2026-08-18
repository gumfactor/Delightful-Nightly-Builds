/* Voxel Lab — UI wiring. Classic script, no bundler, no ES modules. */

(function () {
  const stats = window.VoxelStats;
  const mc = window.VoxelMonteCarlo;
  const { PIPELINE_STEPS } = window.VoxelPipeline;

  function $(selector) {
    return document.querySelector(selector);
  }
  function $$(selector) {
    return Array.from(document.querySelectorAll(selector));
  }

  function clearChildren(el) {
    while (el.firstChild) el.removeChild(el.firstChild);
  }

  // ---------------------------------------------------------------- Tabs --
  function initTabs() {
    const tabButtons = $$('.tab-btn');
    const panels = {
      pipeline: $('#panel-pipeline'),
      mc: $('#panel-mc'),
      quiz: $('#panel-quiz'),
    };
    tabButtons.forEach((btn) => {
      btn.addEventListener('click', () => {
        tabButtons.forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        Object.entries(panels).forEach(([key, panel]) => {
          panel.classList.toggle('active', key === btn.dataset.tab);
        });
      });
    });
  }

  // ------------------------------------------------------------ Pipeline --
  function initPipeline() {
    const stepNav = $('[data-testid="step-nav"]');
    const titleEl = $('[data-testid="step-title"]');
    const explanationEl = $('[data-testid="step-explanation"]');
    const pitfallEl = $('[data-testid="step-pitfall"]');
    const canvas = $('[data-testid="pipeline-canvas"]');
    const ctx = canvas.getContext('2d');
    const beforeBtn = $('[data-testid="phase-before"]');
    const afterBtn = $('[data-testid="phase-after"]');

    let currentStepIndex = 0;
    let currentPhase = 'before';

    function renderCurrent() {
      const step = PIPELINE_STEPS[currentStepIndex];
      const rng = stats.mulberry32(currentStepIndex * 1000 + (currentPhase === 'before' ? 1 : 2));
      step.render(ctx, canvas.width, canvas.height, currentPhase, rng);
    }

    function selectStep(index) {
      currentStepIndex = index;
      currentPhase = 'before';
      const step = PIPELINE_STEPS[index];
      titleEl.textContent = `${index + 1}. ${step.title}`;
      explanationEl.textContent = step.explanation;
      pitfallEl.textContent = `Pitfall if skipped: ${step.pitfall}`;
      beforeBtn.classList.add('active');
      afterBtn.classList.remove('active');
      $$('.step-nav-btn').forEach((btn, i) => btn.classList.toggle('active', i === index));
      renderCurrent();
    }

    PIPELINE_STEPS.forEach((step, i) => {
      const btn = document.createElement('button');
      btn.className = 'step-nav-btn';
      btn.dataset.testid = `step-nav-${step.id}`;
      btn.textContent = `${i + 1}`;
      btn.title = step.title;
      btn.addEventListener('click', () => selectStep(i));
      stepNav.appendChild(btn);
    });

    beforeBtn.addEventListener('click', () => {
      currentPhase = 'before';
      beforeBtn.classList.add('active');
      afterBtn.classList.remove('active');
      renderCurrent();
    });
    afterBtn.addEventListener('click', () => {
      currentPhase = 'after';
      afterBtn.classList.add('active');
      beforeBtn.classList.remove('active');
      renderCurrent();
    });

    selectStep(0);
  }

  // ------------------------------------------------------- Multiple Comparisons --
  const METHOD_LABELS = {
    none: 'None (uncorrected)',
    bonferroni: 'Bonferroni',
    fdr: 'Benjamini-Hochberg FDR',
    cluster: 'Cluster-extent',
  };
  const METHOD_COLORS = {
    none: '#f85149',
    bonferroni: '#58a6ff',
    fdr: '#3fb950',
    cluster: '#d29922',
  };

  function drawBarChart(canvas, methods) {
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.fillStyle = '#0b0f14';
    ctx.fillRect(0, 0, w, h);

    const entries = Object.entries(methods);
    const maxMean = Math.max(...entries.map(([, v]) => v.mean), 1);
    const marginL = 50;
    const marginB = 30;
    const plotW = w - marginL - 20;
    const plotH = h - marginB - 20;
    const barWidth = plotW / entries.length / 1.6;

    ctx.strokeStyle = '#30363d';
    ctx.beginPath();
    ctx.moveTo(marginL, 10);
    ctx.lineTo(marginL, h - marginB);
    ctx.lineTo(w - 10, h - marginB);
    ctx.stroke();

    entries.forEach(([method, v], i) => {
      const x = marginL + (i + 0.5) * (plotW / entries.length) - barWidth / 2;
      const barHeight = (v.mean / maxMean) * plotH;
      const y = h - marginB - barHeight;
      ctx.fillStyle = METHOD_COLORS[method];
      ctx.fillRect(x, y, barWidth, barHeight);
      ctx.fillStyle = '#e6edf3';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(v.mean.toFixed(1), x + barWidth / 2, y - 6);
      ctx.fillText(METHOD_LABELS[method].split(' ')[0], x + barWidth / 2, h - marginB + 16);
    });
    ctx.textAlign = 'left';
  }

  function drawSlice(canvas, voxels, width, height) {
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#0b0f14';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const cellSize = Math.min(canvas.width / width, canvas.height / height);
    for (const v of voxels) {
      ctx.fillStyle = v.significant ? '#f85149' : '#1c2733';
      ctx.fillRect(v.x * cellSize, v.y * cellSize, cellSize - 1, cellSize - 1);
    }
  }

  function initMonteCarloLab() {
    const voxelCountInput = $('[data-testid="mc-voxel-count"]');
    const alphaInput = $('[data-testid="mc-alpha"]');
    const trialsInput = $('[data-testid="mc-trials"]');
    const runBtn = $('[data-testid="mc-run"]');
    const meanEl = $('[data-testid="mc-mean"]');
    const barChart = $('[data-testid="mc-bar-chart"]');
    const slicesContainer = $('[data-testid="mc-slices"]');

    function run() {
      const voxelCount = Math.max(100, Math.min(20000, Number(voxelCountInput.value) || 5000));
      const alpha = Math.max(0.01, Math.min(0.1, Number(alphaInput.value) || 0.05));
      const trials = Math.max(1, Math.min(200, Number(trialsInput.value) || 50));
      const seed = Math.floor(Math.random() * 2 ** 31);
      const rng = stats.mulberry32(seed);

      const result = mc.runComparison({ voxelCount, alpha, trials, rng });
      window.__lastMCResult = result; // exposed for Playwright assertions

      clearChildren(meanEl);
      const summaryList = document.createElement('ul');
      summaryList.className = 'mc-summary-list';
      mc.METHODS.forEach((method) => {
        const item = document.createElement('li');
        item.textContent = `${METHOD_LABELS[method]}: mean ${result.methods[method].mean.toFixed(2)} false positives per trial (${trials} trials)`;
        summaryList.appendChild(item);
      });
      meanEl.appendChild(summaryList);

      drawBarChart(barChart, result.methods);

      clearChildren(slicesContainer);
      mc.METHODS.forEach((method) => {
        const cell = document.createElement('div');
        cell.className = 'mc-slice-cell';
        const label = document.createElement('div');
        label.className = 'mc-slice-label';
        label.textContent = METHOD_LABELS[method];
        const canvas = document.createElement('canvas');
        canvas.width = 160;
        canvas.height = 160;
        canvas.dataset.testid = `mc-slice-${method}`;
        cell.appendChild(label);
        cell.appendChild(canvas);
        slicesContainer.appendChild(cell);
        drawSlice(canvas, result.lastVoxelsByMethod[method], result.width, result.height);
      });
    }

    runBtn.addEventListener('click', run);
    run();
  }

  // ------------------------------------------------------------------ Quiz --
  function initQuiz() {
    const progressEl = $('[data-testid="quiz-progress"]');
    const questionEl = $('[data-testid="quiz-question"]');
    const choicesEl = $('[data-testid="quiz-choices"]');
    const feedbackEl = $('[data-testid="quiz-feedback"]');
    const nextBtn = $('[data-testid="quiz-next"]');
    const finalEl = $('[data-testid="quiz-final"]');

    const seed = Math.floor(Math.random() * 2 ** 31);
    const questions = window.VoxelQuiz.buildQuiz(seed);
    let currentIndex = 0;
    let score = 0;
    let answered = false;

    function renderQuestion() {
      answered = false;
      feedbackEl.textContent = '';
      nextBtn.disabled = true;
      const q = questions[currentIndex];
      progressEl.textContent = `Question ${currentIndex + 1} of ${questions.length} — Score: ${score}`;
      questionEl.textContent = q.prompt;
      clearChildren(choicesEl);
      q.choices.forEach((choiceText, i) => {
        const btn = document.createElement('button');
        btn.className = 'choice-btn';
        btn.dataset.testid = `quiz-choice-${i}`;
        btn.textContent = choiceText;
        btn.addEventListener('click', () => selectAnswer(i, q));
        choicesEl.appendChild(btn);
      });
    }

    function selectAnswer(index, q) {
      if (answered) return;
      answered = true;
      const correct = index === q.correctIndex;
      if (correct) score++;
      $$('.choice-btn').forEach((btn, i) => {
        btn.disabled = true;
        if (i === q.correctIndex) btn.classList.add('correct');
        if (i === index && !correct) btn.classList.add('incorrect');
      });
      feedbackEl.textContent = correct ? 'Correct!' : 'Not quite.';
      nextBtn.disabled = false;
    }

    function next() {
      if (!answered) return;
      currentIndex++;
      if (currentIndex >= questions.length) {
        showFinal();
      } else {
        renderQuestion();
      }
    }

    function showFinal() {
      questionEl.textContent = '';
      clearChildren(choicesEl);
      feedbackEl.textContent = '';
      progressEl.textContent = '';
      nextBtn.hidden = true;
      finalEl.hidden = false;
      const pct = Math.round((score / questions.length) * 100);
      finalEl.textContent = `Final score: ${score} / ${questions.length} (${pct}%)`;
    }

    nextBtn.addEventListener('click', next);
    renderQuestion();
  }

  document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initPipeline();
    initMonteCarloLab();
    initQuiz();
  });
})();
