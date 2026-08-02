// Lexicon — core game logic (classic script, no ES modules, relies on WORD_BANK/CATEGORY_LABELS from words.js)

// Under Node (tests), words.js isn't loaded as a prior <script> tag, so pull its
// exports in explicitly, attaching them to the global object. In the browser this
// whole block is skipped and WORD_BANK / CATEGORY_LABELS resolve as plain identifiers
// from words.js's top-level scope (classic <script> tags share one lexical scope).
// This must be wrapped in a function: a bare top-level `var WORD_BANK` would hoist
// into the shared script scope and collide with words.js's `const WORD_BANK`,
// throwing a SyntaxError in the browser even though the assignment itself never runs.
(function loadWordBankForNode() {
  if (typeof module !== "undefined" && module.exports) {
    const words = require("./words.js");
    global.WORD_BANK = words.WORD_BANK;
    global.CATEGORY_LABELS = words.CATEGORY_LABELS;
  }
})();

const STORAGE_KEY = "lexicon_state_v1";
const EPOCH_DATE = "2026-01-01"; // fixed reference date for the daily cycle
const MIN_GUESSES_BEFORE_HINT = 2;

/** Deterministic PRNG (mulberry32) — same seed always produces the same sequence. */
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Fisher-Yates shuffle driven by a seeded PRNG, so the order is fixed forever. */
function seededShuffle(array, seed) {
  const rng = mulberry32(seed);
  const out = array.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

const DAILY_CYCLE_SEED = 20260802;
const DAILY_CYCLE = seededShuffle(WORD_BANK, DAILY_CYCLE_SEED);

/** Days between two YYYY-MM-DD UTC date strings. */
function daysBetween(dateStrA, dateStrB) {
  const [ay, am, ad] = dateStrA.split("-").map(Number);
  const [by, bm, bd] = dateStrB.split("-").map(Number);
  // Date.UTC takes a 0-indexed month; our date strings are 1-indexed (YYYY-MM-DD).
  const a = Date.UTC(ay, am - 1, ad);
  const b = Date.UTC(by, bm - 1, bd);
  return Math.round((b - a) / 86400000);
}

/** Returns today's UTC date as YYYY-MM-DD. */
function todayUTC() {
  const now = new Date();
  return now.toISOString().slice(0, 10);
}

/** Returns the deterministic word-bank entry for a given UTC YYYY-MM-DD date string. */
function dailyWordForDate(dateStr) {
  const dayIndex = daysBetween(EPOCH_DATE, dateStr);
  const cycleIndex = ((dayIndex % DAILY_CYCLE.length) + DAILY_CYCLE.length) % DAILY_CYCLE.length;
  return DAILY_CYCLE[cycleIndex];
}

/** Max guesses allowed for a word of the given length: length + 1, capped at 9. */
function maxGuessesForLength(length) {
  return Math.min(9, length + 1);
}

/**
 * Evaluate a guess against the answer using the two-pass Wordle algorithm.
 * Returns an array of "correct" | "present" | "absent", one per letter of guess.
 * Handles duplicate letters correctly: a letter is only marked "present" as many
 * times as it remains unaccounted-for in the answer after exact matches are removed.
 */
function evaluateGuess(guess, answer) {
  const guessLetters = guess.split("");
  const answerLetters = answer.split("");
  const result = new Array(guessLetters.length).fill("absent");
  const remaining = {};

  // Pass 1: exact matches
  for (let i = 0; i < guessLetters.length; i++) {
    if (guessLetters[i] === answerLetters[i]) {
      result[i] = "correct";
    } else {
      remaining[answerLetters[i]] = (remaining[answerLetters[i]] || 0) + 1;
    }
  }

  // Pass 2: present-but-wrong-position, limited by remaining counts
  for (let i = 0; i < guessLetters.length; i++) {
    if (result[i] === "correct") continue;
    const letter = guessLetters[i];
    if (remaining[letter] > 0) {
      result[i] = "present";
      remaining[letter] -= 1;
    }
  }

  return result;
}

/**
 * Aggregate per-letter keyboard state across all guesses so far.
 * Priority: correct > present > absent (a letter never downgrades).
 */
function aggregateKeyboardState(guesses, answer) {
  const priority = { correct: 3, present: 2, absent: 1 };
  const state = {};
  for (const guess of guesses) {
    const evaluation = evaluateGuess(guess, answer);
    for (let i = 0; i < guess.length; i++) {
      const letter = guess[i];
      const status = evaluation[i];
      if (!state[letter] || priority[status] > priority[state[letter]]) {
        state[letter] = status;
      }
    }
  }
  return state;
}

/** Convert an evaluation array into the emoji-grid line used for sharing. */
function evaluationToEmoji(evaluation) {
  const map = { correct: "\u{1F7E9}", present: "\u{1F7E8}", absent: "⬛" };
  return evaluation.map((status) => map[status]).join("");
}

/** Build the full shareable share-text block for a completed round. */
function buildShareText(guesses, answer, won) {
  const maxGuesses = maxGuessesForLength(answer.length);
  const lines = guesses.map((g) => evaluationToEmoji(evaluateGuess(g, answer)));
  const scoreLabel = won ? `${guesses.length}/${maxGuesses}` : `X/${maxGuesses}`;
  return [`Lexicon ${scoreLabel}`, ...lines].join("\n");
}

/** Deterministic fallback hint used when no AI key is configured. */
function fallbackHint(entry) {
  return `Starts with "${entry.word[0]}", ${entry.word.length} letters, category: ${CATEGORY_LABELS[entry.category]}.`;
}

// --- localStorage persistence ---

function defaultState() {
  return {
    lastPlayedDate: null,
    history: [],
    currentStreak: 0,
    maxStreak: 0,
    categoryStats: { neuro: { played: 0, won: 0 }, stats: { played: 0, won: 0 }, ai: { played: 0, won: 0 }, finance: { played: 0, won: 0 } },
    colorblindMode: false,
  };
}

function loadState(storage) {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);
    return Object.assign(defaultState(), parsed);
  } catch (e) {
    return defaultState();
  }
}

function saveState(storage, state) {
  storage.setItem(STORAGE_KEY, JSON.stringify(state));
}

/** Record a completed round's result into state. Practice rounds do not affect daily stats. */
function recordResult(state, { date, entry, won, guessCount, guesses, isPractice }) {
  if (isPractice) return state;
  state.lastPlayedDate = date;
  state.history.push({ date, word: entry.word, won, guessCount, guesses: guesses || [] });
  state.currentStreak = won ? state.currentStreak + 1 : 0;
  state.maxStreak = Math.max(state.maxStreak, state.currentStreak);
  const catStats = state.categoryStats[entry.category];
  catStats.played += 1;
  if (won) catStats.won += 1;
  return state;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    mulberry32,
    seededShuffle,
    daysBetween,
    dailyWordForDate,
    maxGuessesForLength,
    evaluateGuess,
    aggregateKeyboardState,
    evaluationToEmoji,
    buildShareText,
    fallbackHint,
    defaultState,
    loadState,
    saveState,
    recordResult,
    DAILY_CYCLE,
    EPOCH_DATE,
  };
}

// --- UI wiring (browser only) ---

const KEYBOARD_ROWS = [
  ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
  ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
  ["ENTER", "Z", "X", "C", "V", "B", "N", "M", "BACKSPACE"],
];

function initGame(root, storage) {
  const state = loadState(storage);
  let mode = "daily"; // "daily" | "practice"
  let entry = dailyWordForDate(todayUTC());
  let guesses = [];
  let currentGuess = "";
  let finished = false;
  let won = false;
  let anthropicKey = "";

  const elBoard = root.querySelector("[data-testid='board']");
  const elKeyboard = root.querySelector("[data-testid='keyboard']");
  const elHint = root.querySelector("[data-testid='hint']");
  const elMessage = root.querySelector("[data-testid='message']");
  const elResult = root.querySelector("[data-testid='result-modal']");
  const elResultText = root.querySelector("[data-testid='result-text']");
  const elShareText = root.querySelector("[data-testid='share-text']");
  const elStats = root.querySelector("[data-testid='stats-panel']");
  const elModeDaily = root.querySelector("[data-testid='mode-daily']");
  const elModePractice = root.querySelector("[data-testid='mode-practice']");
  const elPracticeCategory = root.querySelector("[data-testid='practice-category']");
  const elColorblindToggle = root.querySelector("[data-testid='colorblind-toggle']");
  const elAiKeyInput = root.querySelector("[data-testid='ai-key-input']");
  const elAiHintButton = root.querySelector("[data-testid='ai-hint-button']");
  const elAiHintText = root.querySelector("[data-testid='ai-hint-text']");

  function setMessage(text) {
    elMessage.textContent = text;
  }

  function renderBoard() {
    elBoard.textContent = "";
    const maxGuesses = maxGuessesForLength(entry.word.length);
    elBoard.style.setProperty("--word-length", entry.word.length);
    for (let row = 0; row < maxGuesses; row++) {
      const rowEl = document.createElement("div");
      rowEl.className = "guess-row";
      rowEl.dataset.testid = "guess-row";
      const guess = guesses[row];
      const typed = row === guesses.length ? currentGuess : "";
      for (let col = 0; col < entry.word.length; col++) {
        const tile = document.createElement("div");
        tile.className = "tile";
        let letter = "";
        let status = "";
        if (guess) {
          letter = guess[col];
          status = evaluateGuess(guess, entry.word)[col];
        } else if (typed) {
          letter = typed[col] || "";
        }
        if (status) {
          tile.classList.add(status);
          if (state.colorblindMode) {
            const marker = { correct: "✓", present: "●", absent: "✗" }[status];
            tile.dataset.marker = marker;
          }
        }
        tile.textContent = letter;
        rowEl.appendChild(tile);
      }
      elBoard.appendChild(rowEl);
    }
  }

  function renderKeyboard() {
    elKeyboard.textContent = "";
    const keyState = aggregateKeyboardState(guesses, entry.word);
    for (const row of KEYBOARD_ROWS) {
      const rowEl = document.createElement("div");
      rowEl.className = "keyboard-row";
      for (const key of row) {
        const keyEl = document.createElement("button");
        keyEl.type = "button";
        keyEl.className = "key";
        keyEl.dataset.testid = `key-${key}`;
        keyEl.textContent = key === "BACKSPACE" ? "⌫" : key === "ENTER" ? "⏎" : key;
        if (key.length === 1 && keyState[key]) {
          keyEl.classList.add(keyState[key]);
        }
        keyEl.addEventListener("click", () => handleKey(key));
        rowEl.appendChild(keyEl);
      }
      elKeyboard.appendChild(rowEl);
    }
  }

  function renderHint() {
    if (guesses.length >= MIN_GUESSES_BEFORE_HINT || finished) {
      elHint.textContent = entry.clue;
      elHint.hidden = false;
    } else {
      elHint.textContent = "";
      elHint.hidden = true;
    }
  }

  function renderStats() {
    const winPct = state.history.length ? Math.round((state.history.filter((h) => h.won).length / state.history.length) * 100) : 0;
    elStats.textContent = "";
    const rows = [
      ["Games played", state.history.length],
      ["Win %", `${winPct}%`],
      ["Current streak", state.currentStreak],
      ["Max streak", state.maxStreak],
    ];
    for (const [label, value] of rows) {
      const p = document.createElement("p");
      p.textContent = `${label}: ${value}`;
      elStats.appendChild(p);
    }
    for (const cat of Object.keys(CATEGORY_LABELS)) {
      const s = state.categoryStats[cat];
      const pct = s.played ? Math.round((s.won / s.played) * 100) : 0;
      const p = document.createElement("p");
      p.textContent = `${CATEGORY_LABELS[cat]}: ${s.won}/${s.played} (${pct}%)`;
      elStats.appendChild(p);
    }
  }

  function renderResultModal() {
    if (!finished) {
      elResult.hidden = true;
      return;
    }
    elResult.hidden = false;
    elResultText.textContent = won ? `Solved in ${guesses.length}!` : `Out of guesses. The word was ${entry.word}.`;
    elShareText.textContent = buildShareText(guesses, entry.word, won);
  }

  function renderAll() {
    renderBoard();
    renderKeyboard();
    renderHint();
    renderStats();
    renderResultModal();
  }

  function finishRound(didWin) {
    finished = true;
    won = didWin;
    state.categoryStats[entry.category] = state.categoryStats[entry.category] || { played: 0, won: 0 };
    recordResult(state, { date: todayUTC(), entry, won: didWin, guessCount: guesses.length, guesses: guesses.slice(), isPractice: mode === "practice" });
    saveState(storage, state);
    setMessage(didWin ? "Solved!" : `Out of guesses — the word was ${entry.word}.`);
  }

  function handleKey(key) {
    if (finished) return;
    if (key === "BACKSPACE") {
      currentGuess = currentGuess.slice(0, -1);
    } else if (key === "ENTER") {
      submitGuess();
      return;
    } else if (/^[A-Z]$/.test(key) && currentGuess.length < entry.word.length) {
      currentGuess += key;
    }
    renderBoard();
  }

  function submitGuess() {
    if (currentGuess.length !== entry.word.length) {
      setMessage(`Guess must be ${entry.word.length} letters.`);
      return;
    }
    guesses.push(currentGuess);
    const isCorrect = currentGuess === entry.word;
    currentGuess = "";
    renderAll();
    if (isCorrect) {
      finishRound(true);
      renderAll();
    } else if (guesses.length >= maxGuessesForLength(entry.word.length)) {
      finishRound(false);
      renderAll();
    } else {
      setMessage("");
    }
  }

  function setModeButtonActive(activeEl, inactiveEl) {
    activeEl.classList.add("active");
    inactiveEl.classList.remove("active");
  }

  function startDaily() {
    mode = "daily";
    setModeButtonActive(elModeDaily, elModePractice);
    entry = dailyWordForDate(todayUTC());
    currentGuess = "";
    const today = todayUTC();
    const todaysEntry = state.history.find((h) => h.date === today);
    if (todaysEntry) {
      guesses = todaysEntry.guesses.slice();
      finished = true;
      won = todaysEntry.won;
    } else {
      guesses = [];
      finished = false;
      won = false;
    }
    setMessage("");
    renderAll();
  }

  function startPractice(category) {
    mode = "practice";
    setModeButtonActive(elModePractice, elModeDaily);
    const pool = WORD_BANK.filter((w) => w.category === category);
    entry = pool[Math.floor(Math.random() * pool.length)];
    guesses = [];
    currentGuess = "";
    finished = false;
    won = false;
    setMessage("");
    renderAll();
  }

  async function requestAiHint() {
    if (!anthropicKey) {
      elAiHintText.textContent = fallbackHint(entry);
      return;
    }
    try {
      const response = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-api-key": anthropicKey,
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify({
          model: "claude-haiku-4-5-20251001",
          max_tokens: 60,
          messages: [
            {
              role: "user",
              content: `Give one short, creative clue (under 15 words, no spoilers of the word itself) for the term "${entry.word}" in the domain of ${CATEGORY_LABELS[entry.category]}. Do not say the word.`,
            },
          ],
        }),
      });
      if (!response.ok) throw new Error("AI hint request failed");
      const data = await response.json();
      const text = data.content && data.content[0] && data.content[0].text ? data.content[0].text : fallbackHint(entry);
      elAiHintText.textContent = text;
    } catch (e) {
      elAiHintText.textContent = fallbackHint(entry);
    }
  }

  elModeDaily.addEventListener("click", startDaily);
  elModePractice.addEventListener("click", () => startPractice(elPracticeCategory.value));
  elPracticeCategory.addEventListener("change", () => {
    if (mode === "practice") startPractice(elPracticeCategory.value);
  });
  elColorblindToggle.addEventListener("change", () => {
    state.colorblindMode = elColorblindToggle.checked;
    saveState(storage, state);
    renderBoard();
  });
  elAiKeyInput.addEventListener("input", () => {
    anthropicKey = elAiKeyInput.value.trim();
  });
  elAiHintButton.addEventListener("click", requestAiHint);

  document.addEventListener("keydown", (e) => {
    if (elResult && !elResult.hidden) return;
    const key = e.key === "Enter" ? "ENTER" : e.key === "Backspace" ? "BACKSPACE" : e.key.toUpperCase();
    if (key === "ENTER" || key === "BACKSPACE" || /^[A-Z]$/.test(key)) {
      handleKey(key);
    }
  });

  elColorblindToggle.checked = state.colorblindMode;
  startDaily();

  return {
    handleKey,
    submitGuess,
    startDaily,
    startPractice,
    getState: () => state,
    getEntry: () => entry,
    getGuesses: () => guesses,
    isFinished: () => finished,
  };
}

if (typeof window !== "undefined") {
  window.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("app");
    if (root) {
      window.__lexicon = initGame(root, window.localStorage);
    }
  });
}
