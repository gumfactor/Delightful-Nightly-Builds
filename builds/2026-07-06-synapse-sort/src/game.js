// Synapse Sort — game engine and DOM rendering.
// Classic script; depends on globals defined in puzzles.js and storage.js
// (all loaded via <script src> tags sharing one top-level scope).

const MAX_MISTAKES = 4;

let gameState = null;

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

function shuffleArray(items) {
  const copy = items.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const tmp = copy[i];
    copy[i] = copy[j];
    copy[j] = tmp;
  }
  return copy;
}

function buildTiles(puzzle) {
  const tiles = [];
  puzzle.categories.forEach((category, categoryIndex) => {
    category.items.forEach((item) => {
      tiles.push({ item: item, categoryIndex: categoryIndex, difficulty: category.difficulty });
    });
  });
  return shuffleArray(tiles);
}

function getGameState() {
  return gameState;
}

// Builds the emoji share grid from guess history. Each guess row shows one
// colored square per selected tile, using that tile's TRUE category color —
// so a wrong guess shows how close it was, matching the genre's convention.
function generateShareGrid(puzzle, guessHistory, won, mistakes, maxMistakes) {
  const lines = [];
  lines.push("Synapse Sort — " + puzzle.title);
  guessHistory.forEach((guess) => {
    lines.push(guess.map((difficulty) => DIFFICULTY_EMOJI[difficulty]).join(""));
  });
  lines.push(won ? "Solved with " + mistakes + "/" + maxMistakes + " mistakes" : "Not solved — " + mistakes + "/" + maxMistakes + " mistakes");
  return lines.join("\n");
}

function initGame(mode, puzzle) {
  gameState = {
    mode: mode,
    puzzle: puzzle,
    tiles: buildTiles(puzzle),
    selected: [],
    solvedCategoryIndexes: [],
    mistakes: 0,
    guessHistory: [],
    gameOver: false,
    won: false,
    message: ""
  };
  render();
}

function isDailyAlreadyPlayed() {
  return window.SynapseSort.hasPlayedDate(todayString());
}

function startDailyGame() {
  const puzzle = getPuzzleForDate(todayString());
  document.getElementById("archive-panel").hidden = true;
  document.getElementById("stats-panel").hidden = true;
  if (isDailyAlreadyPlayed()) {
    renderAlreadyPlayed(puzzle);
    return;
  }
  initGame("daily", puzzle);
}

function startPracticeGame(puzzleId) {
  const puzzle = PUZZLES.find((p) => p.id === puzzleId);
  document.getElementById("archive-panel").hidden = true;
  document.getElementById("stats-panel").hidden = true;
  initGame("practice", puzzle);
}

function handleTileClick(item) {
  if (!gameState || gameState.gameOver) return;
  const idx = gameState.selected.indexOf(item);
  if (idx >= 0) {
    gameState.selected.splice(idx, 1);
  } else if (gameState.selected.length < 4) {
    gameState.selected.push(item);
  }
  gameState.message = "";
  render();
}

function handleDeselectAll() {
  if (!gameState || gameState.gameOver) return;
  gameState.selected = [];
  gameState.message = "";
  render();
}

function handleShuffle() {
  if (!gameState || gameState.gameOver) return;
  const remaining = gameState.tiles.filter(
    (t) => gameState.solvedCategoryIndexes.indexOf(t.categoryIndex) === -1
  );
  const solved = gameState.tiles.filter(
    (t) => gameState.solvedCategoryIndexes.indexOf(t.categoryIndex) !== -1
  );
  gameState.tiles = shuffleArray(remaining).concat(solved);
  render();
}

function handleSubmit() {
  if (!gameState || gameState.gameOver || gameState.selected.length !== 4) return;
  const selectedTiles = gameState.selected.map((item) =>
    gameState.tiles.find((t) => t.item === item)
  );
  const categoryIndexes = selectedTiles.map((t) => t.categoryIndex);
  const guessColors = selectedTiles.map((t) => t.difficulty);
  gameState.guessHistory.push(guessColors);

  const allSame = categoryIndexes.every((c) => c === categoryIndexes[0]);

  if (allSame) {
    gameState.solvedCategoryIndexes.push(categoryIndexes[0]);
    gameState.selected = [];
    gameState.message = "Correct! " + gameState.puzzle.categories[categoryIndexes[0]].name;
    if (gameState.solvedCategoryIndexes.length === 4) {
      finishGame(true);
      return;
    }
  } else {
    gameState.mistakes += 1;
    const counts = {};
    categoryIndexes.forEach((c) => {
      counts[c] = (counts[c] || 0) + 1;
    });
    const maxCount = Math.max.apply(null, Object.values(counts));
    gameState.selected = [];
    if (maxCount === 3) {
      gameState.message = "One away...";
    } else {
      gameState.message = "Not quite — try again.";
    }
    if (gameState.mistakes >= MAX_MISTAKES) {
      finishGame(false);
      return;
    }
  }
  render();
}

function finishGame(won) {
  gameState.gameOver = true;
  gameState.won = won;
  if (!won) {
    // Reveal every remaining category so the player sees the full answer.
    gameState.puzzle.categories.forEach((_, idx) => {
      if (gameState.solvedCategoryIndexes.indexOf(idx) === -1) {
        gameState.solvedCategoryIndexes.push(idx);
      }
    });
  }
  if (gameState.mode === "daily") {
    window.SynapseSort.recordDailyResult(todayString(), won, gameState.mistakes);
  }
  render();
  renderResultPanel();
}

function renderResultPanel() {
  const panel = document.getElementById("result-panel");
  const heading = document.getElementById("result-heading");
  const shareText = document.getElementById("share-grid-text");
  heading.textContent = gameState.won ? "Solved!" : "Better luck tomorrow";
  const text = generateShareGrid(
    gameState.puzzle,
    gameState.guessHistory,
    gameState.won,
    gameState.mistakes,
    MAX_MISTAKES
  );
  shareText.textContent = text;
  shareText.dataset.shareText = text;
  panel.hidden = false;
}

function renderAlreadyPlayed(puzzle) {
  const stats = window.SynapseSort.getStats();
  const record = stats.history[todayString()];
  document.getElementById("tile-grid").innerHTML = "";
  document.getElementById("solved-categories").innerHTML = "";
  document.getElementById("controls").hidden = true;
  document.getElementById("puzzle-title").textContent = puzzle.title;
  document.getElementById("puzzle-counter").textContent =
    "Puzzle #" + (getPuzzleIndexForDate(todayString()) + 1) + " of " + PUZZLES.length;
  gameState = {
    mode: "daily",
    puzzle: puzzle,
    tiles: buildTiles(puzzle),
    selected: [],
    solvedCategoryIndexes: puzzle.categories.map((_, i) => i),
    mistakes: record.mistakes,
    guessHistory: [],
    gameOver: true,
    won: record.won,
    message: "You already played today's puzzle."
  };
  document.getElementById("message-banner").textContent = gameState.message;
  document.getElementById("result-panel").hidden = true;
  renderSolvedCategories();
}

function renderSolvedCategories() {
  const container = document.getElementById("solved-categories");
  container.innerHTML = "";
  gameState.solvedCategoryIndexes.forEach((idx) => {
    const category = gameState.puzzle.categories[idx];
    const row = document.createElement("div");
    row.className = "solved-row difficulty-" + category.difficulty;
    row.setAttribute("data-testid", "solved-category");
    row.setAttribute("data-difficulty", category.difficulty);
    const label = document.createElement("div");
    label.className = "solved-row-name";
    label.textContent = category.name + " (" + DIFFICULTY_LABEL[category.difficulty] + ")";
    const items = document.createElement("div");
    items.className = "solved-row-items";
    items.textContent = category.items.join(" · ");
    row.appendChild(label);
    row.appendChild(items);
    container.appendChild(row);
  });
}

function render() {
  if (!gameState) return;
  document.getElementById("result-panel").hidden = true;
  document.getElementById("controls").hidden = false;
  document.getElementById("puzzle-title").textContent = gameState.puzzle.title;
  const index =
    gameState.mode === "daily"
      ? getPuzzleIndexForDate(todayString())
      : PUZZLES.findIndex((p) => p.id === gameState.puzzle.id);
  document.getElementById("puzzle-counter").textContent =
    "Puzzle #" + (index + 1) + " of " + PUZZLES.length + (gameState.mode === "practice" ? " (practice)" : "");

  document.getElementById("mistakes-tracker").textContent =
    "Mistakes: " + gameState.mistakes + " / " + MAX_MISTAKES;
  document.getElementById("message-banner").textContent = gameState.message;

  renderSolvedCategories();

  const grid = document.getElementById("tile-grid");
  grid.innerHTML = "";
  const unsolvedTiles = gameState.tiles.filter(
    (t) => gameState.solvedCategoryIndexes.indexOf(t.categoryIndex) === -1
  );
  unsolvedTiles.forEach((tile) => {
    const btn = document.createElement("button");
    btn.className = "tile" + (gameState.selected.indexOf(tile.item) >= 0 ? " selected" : "");
    btn.textContent = tile.item;
    btn.setAttribute("data-testid", "tile");
    btn.setAttribute("data-item", tile.item);
    btn.setAttribute("aria-pressed", gameState.selected.indexOf(tile.item) >= 0 ? "true" : "false");
    btn.disabled = gameState.gameOver;
    btn.addEventListener("click", () => handleTileClick(tile.item));
    grid.appendChild(btn);
  });

  const submitBtn = document.getElementById("submit-btn");
  submitBtn.disabled = gameState.selected.length !== 4 || gameState.gameOver;
}

function renderArchiveList() {
  const list = document.getElementById("archive-list");
  list.innerHTML = "";
  PUZZLES.forEach((puzzle, idx) => {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.className = "archive-item";
    btn.setAttribute("data-testid", "archive-item");
    btn.setAttribute("data-id", puzzle.id);
    btn.textContent = "#" + (idx + 1) + " — " + puzzle.title;
    btn.addEventListener("click", () => {
      document.getElementById("archive-panel").hidden = true;
      startPracticeGame(puzzle.id);
    });
    li.appendChild(btn);
    list.appendChild(li);
  });
}

function renderStatsPanel() {
  const stats = window.SynapseSort.getStats();
  const content = document.getElementById("stats-content");
  const winRate = stats.gamesPlayed > 0 ? Math.round((stats.wins / stats.gamesPlayed) * 100) : 0;
  const avgMistakes = stats.gamesPlayed > 0 ? (stats.totalMistakes / stats.gamesPlayed).toFixed(1) : "0.0";
  content.innerHTML = "";
  const rows = [
    ["Games played", stats.gamesPlayed],
    ["Wins", stats.wins],
    ["Win rate", winRate + "%"],
    ["Current streak", stats.currentStreak],
    ["Best streak", stats.bestStreak],
    ["Average mistakes", avgMistakes]
  ];
  rows.forEach(([label, value]) => {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.setAttribute("data-testid", "stat-value");
    dd.setAttribute("data-stat", label);
    dd.textContent = String(value);
    content.appendChild(dt);
    content.appendChild(dd);
  });
  document.getElementById("stats-panel").hidden = false;
}

function initTheme() {
  const saved = window.SynapseSort.getTheme();
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = saved || (prefersDark ? "dark" : "light");
  document.documentElement.setAttribute("data-theme", theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  window.SynapseSort.setTheme(next);
}

function wireControls() {
  document.getElementById("submit-btn").addEventListener("click", handleSubmit);
  document.getElementById("shuffle-btn").addEventListener("click", handleShuffle);
  document.getElementById("deselect-btn").addEventListener("click", handleDeselectAll);
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

  document.getElementById("archive-btn").addEventListener("click", () => {
    document.getElementById("stats-panel").hidden = true;
    document.getElementById("archive-panel").hidden = false;
    renderArchiveList();
  });
  document.getElementById("back-to-daily-btn").addEventListener("click", () => {
    document.getElementById("archive-panel").hidden = true;
    startDailyGame();
  });
  document.getElementById("stats-btn").addEventListener("click", () => {
    document.getElementById("archive-panel").hidden = true;
    renderStatsPanel();
  });
  document.getElementById("close-stats-btn").addEventListener("click", () => {
    document.getElementById("stats-panel").hidden = true;
  });
  document.getElementById("copy-share-btn").addEventListener("click", () => {
    const text = document.getElementById("share-grid-text").dataset.shareText || "";
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(() => {});
    }
    const btn = document.getElementById("copy-share-btn");
    const original = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => {
      btn.textContent = original;
    }, 1500);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  wireControls();
  startDailyGame();
});
