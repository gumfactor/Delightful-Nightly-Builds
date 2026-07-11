// Classic (non-module) script, loaded after stats.js and quiz-data.js --
// see the note at the top of charts.js for why this app avoids ES modules
// and wraps each file in an IIFE.
(function () {

const { computePower, powerLabel } = window.PowerLabStats;
const { QUIZ_BANK } = window.PowerLabQuizData;

const STORAGE_KEY = 'power-lab-quiz-state';

const BUCKETS = ['<50%', '50-70%', '70-90%', '>90%'];

function bucketForPower(power) {
  const pct = power * 100;
  if (pct < 50) return '<50%';
  if (pct < 70) return '50-70%';
  if (pct < 90) return '70-90%';
  return '>90%';
}

function defaultState() {
  return { score: 0, streak: 0, bestStreak: 0, answeredIds: [] };
}

function loadState(storage = window.localStorage) {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);
    return {
      score: Number.isFinite(parsed.score) ? parsed.score : 0,
      streak: Number.isFinite(parsed.streak) ? parsed.streak : 0,
      bestStreak: Number.isFinite(parsed.bestStreak) ? parsed.bestStreak : 0,
      answeredIds: Array.isArray(parsed.answeredIds) ? parsed.answeredIds : [],
    };
  } catch {
    return defaultState();
  }
}

function saveState(state, storage = window.localStorage) {
  storage.setItem(STORAGE_KEY, JSON.stringify(state));
}

// Picks the next question: prefers an unanswered scenario; once every
// scenario in the bank has been answered in the current cycle, resets the
// answered list and starts a fresh cycle rather than crashing or stalling.
function pickNextQuestion(state, bank = QUIZ_BANK) {
  const remaining = bank.filter((q) => !state.answeredIds.includes(q.id));
  if (remaining.length === 0) {
    state.answeredIds = [];
    return bank[0];
  }
  return remaining[0];
}

function initQuiz(root) {
  const state = loadState();
  let current = pickNextQuestion(state);
  let answered = false;

  const els = {
    description: root.querySelector('[data-testid="quiz-question"]'),
    buckets: root.querySelectorAll('[data-testid="quiz-bucket-btn"]'),
    feedback: root.querySelector('[data-testid="quiz-feedback"]'),
    score: root.querySelector('[data-testid="quiz-score"]'),
    streak: root.querySelector('[data-testid="quiz-streak"]'),
    nextBtn: root.querySelector('[data-testid="quiz-next-btn"]'),
  };

  function renderStats() {
    els.score.textContent = `Score: ${state.score}`;
    els.streak.textContent = `Streak: ${state.streak} (best: ${state.bestStreak})`;
  }

  function renderQuestion() {
    answered = false;
    els.description.textContent = current.description;
    els.feedback.hidden = true;
    els.feedback.textContent = '';
    els.nextBtn.hidden = true;
    els.buckets.forEach((btn) => {
      btn.disabled = false;
      btn.classList.remove('correct', 'incorrect');
    });
  }

  function handleBucketClick(evt) {
    if (answered) return;
    const chosen = evt.currentTarget.dataset.bucket;
    const power = computePower(current);
    const correctBucket = bucketForPower(power);
    const isCorrect = chosen === correctBucket;

    answered = true;
    state.answeredIds.push(current.id);
    if (isCorrect) {
      state.score += 1;
      state.streak += 1;
      state.bestStreak = Math.max(state.bestStreak, state.streak);
    } else {
      state.streak = 0;
    }
    saveState(state);
    renderStats();

    els.buckets.forEach((btn) => {
      btn.disabled = true;
      if (btn.dataset.bucket === correctBucket) btn.classList.add('correct');
      else if (btn === evt.currentTarget) btn.classList.add('incorrect');
    });

    const pct = (power * 100).toFixed(1);
    const verdict = isCorrect ? 'Correct!' : 'Not quite.';
    els.feedback.hidden = false;
    els.feedback.textContent =
      `${verdict} Actual power = ${pct}% (${powerLabel(power)}). ${current.insight}`;
    els.nextBtn.hidden = false;
  }

  function handleNext() {
    current = pickNextQuestion(state);
    renderQuestion();
  }

  els.buckets.forEach((btn) => btn.addEventListener('click', handleBucketClick));
  els.nextBtn.addEventListener('click', handleNext);

  renderStats();
  renderQuestion();

  return {
    getState: () => state,
    getCurrentQuestion: () => current,
  };
}

window.PowerLabQuiz = { initQuiz, bucketForPower, loadState, defaultState, QUIZ_BANK };

})();
