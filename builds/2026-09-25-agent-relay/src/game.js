// Agent Relay — UI state machine. Classic script; relies on Engine, Levels,
// Graph, AIDebrief globals loaded before this file. All DOM built via
// createElement/textContent — never innerHTML.

var STORAGE_KEY = "agent-relay-progress-v1";

var state = {
  screen: "home",
  currentLevel: null,
  isTutorial: false,
  isDaily: false,
  dailyDateStr: null,
  campaignIndex: -1,
  placement: null,
  order: [],
  selectedTaskId: null,
  lastResult: null
};

// ---------------------------------------------------------------------------
// Persistence
// ---------------------------------------------------------------------------

function defaultProgress() {
  return { campaign: {}, daily: { lastPlayedDate: null, streak: 0, history: {} } };
}

function loadProgress() {
  try {
    var raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultProgress();
    var parsed = JSON.parse(raw);
    var base = defaultProgress();
    return {
      campaign: parsed.campaign || base.campaign,
      daily: {
        lastPlayedDate: parsed.daily ? parsed.daily.lastPlayedDate : null,
        streak: parsed.daily && typeof parsed.daily.streak === "number" ? parsed.daily.streak : 0,
        history: (parsed.daily && parsed.daily.history) || {}
      }
    };
  } catch (e) {
    return defaultProgress();
  }
}

function saveProgress() {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch (e) {
    // Storage unavailable (private browsing, quota, etc.) — play continues, just unsaved.
  }
}

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

function clearChildren(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

function gradeEmoji(grade) {
  if (grade === "gold") return "🥇";
  if (grade === "silver") return "🥈";
  return "🥉";
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function isConsecutiveDay(prevDateStr, dateStr) {
  if (!prevDateStr) return false;
  var prev = new Date(prevDateStr + "T00:00:00Z");
  var cur = new Date(dateStr + "T00:00:00Z");
  var diffDays = Math.round((cur.getTime() - prev.getTime()) / 86400000);
  return diffDays === 1;
}

function computeNewStreak(daily, dateStr) {
  if (isConsecutiveDay(daily.lastPlayedDate, dateStr)) return daily.streak + 1;
  return 1;
}

function buildShareText(dateStr, result, streak) {
  return (
    "Agent Relay Daily " +
    dateStr +
    " — " +
    gradeEmoji(result.grade) +
    " " +
    result.makespan +
    "m (optimal " +
    result.optimal +
    "m) · streak " +
    streak +
    (streak > 0 ? " 🔥" : "")
  );
}

// ---------------------------------------------------------------------------
// View switching
// ---------------------------------------------------------------------------

function showView(id) {
  var views = document.querySelectorAll(".view");
  for (var i = 0; i < views.length; i++) views[i].classList.add("hidden");
  document.getElementById(id).classList.remove("hidden");
  state.screen = id;

  var navBtns = document.querySelectorAll(".nav-btn");
  for (var j = 0; j < navBtns.length; j++) navBtns[j].classList.remove("active");
  if (id === "view-home") {
    var homeBtn = document.querySelector('[data-nav="home"]');
    if (homeBtn) homeBtn.classList.add("active");
  }
  if (id === "view-dashboard") {
    var dashBtn = document.querySelector('[data-nav="dashboard"]');
    if (dashBtn) dashBtn.classList.add("active");
  }
}

// ---------------------------------------------------------------------------
// Home screen
// ---------------------------------------------------------------------------

function renderDailyStatus() {
  var el = document.getElementById("daily-status");
  var today = Engine.todayUTCString();
  var streakText = progress.daily.streak + (progress.daily.streak > 0 ? " 🔥" : "");
  if (progress.daily.lastPlayedDate === today) {
    var h = progress.daily.history[today];
    el.textContent =
      "Today's challenge complete — " +
      gradeEmoji(h.grade) +
      " " +
      h.makespan +
      "m (optimal " +
      h.optimal +
      "m). Streak: " +
      streakText;
  } else {
    el.textContent = "Streak: " + streakText + ". Today's challenge is ready.";
  }
}

function showStoredDailyResult(h, dateStr) {
  var level = { id: "daily-" + dateStr, title: "Daily Challenge — " + dateStr, flavor: "", tasks: h.tasks, numLanes: h.numLanes };
  var result = { level: level, placed: h.placed, makespan: h.makespan, optimal: h.optimal, grade: h.grade };
  state.lastResult = result;
  state.isDaily = true;
  state.dailyDateStr = dateStr;
  state.isTutorial = false;
  state.campaignIndex = -1;
  renderResult(result, true, dateStr);
  showView("view-result");
}

// ---------------------------------------------------------------------------
// Level select (campaign)
// ---------------------------------------------------------------------------

function unlockedCampaignCount() {
  var levels = Levels.CAMPAIGN_LEVELS;
  var unlocked = 1;
  for (var i = 0; i < levels.length; i++) {
    if (progress.campaign[levels[i].id] && i + 2 > unlocked) unlocked = i + 2;
  }
  return Math.min(unlocked, levels.length);
}

function renderLevelSelect() {
  var list = document.getElementById("level-list");
  clearChildren(list);
  var levels = Levels.CAMPAIGN_LEVELS;
  var unlockedCount = unlockedCampaignCount();

  levels.forEach(function (level, idx) {
    var unlocked = idx < unlockedCount;
    var card = document.createElement("button");
    card.type = "button";
    card.className = "level-card" + (unlocked ? "" : " locked");
    card.setAttribute("data-testid", "level-btn-" + level.id);
    card.disabled = !unlocked;

    var title = document.createElement("div");
    title.className = "level-card-title";
    title.textContent = level.title;
    card.appendChild(title);

    var meta = document.createElement("div");
    meta.className = "level-card-meta";
    meta.textContent = level.tasks.length + " tasks · " + level.numLanes + " lanes";
    card.appendChild(meta);

    var best = progress.campaign[level.id];
    var bestEl = document.createElement("div");
    bestEl.className = "level-card-best";
    bestEl.textContent = !unlocked ? "Locked" : best ? "Best: " + gradeEmoji(best.bestGrade) + " " + best.bestMakespan + "m" : "Not played";
    card.appendChild(bestEl);

    if (unlocked) {
      card.addEventListener("click", function () {
        startLevel(level, { campaignIndex: idx });
      });
    }
    list.appendChild(card);
  });
}

// ---------------------------------------------------------------------------
// Play screen
// ---------------------------------------------------------------------------

function tutorialStepText() {
  var placedCount = Object.keys(state.placement.placed).length;
  if (placedCount === 0) {
    return 'Step 1: "Clone Repository" has no dependencies, so it’s the only task in Ready. Click it, then click either lane to place it.';
  }
  if (placedCount === 1) {
    return "Step 2: two tasks just became ready. Click one and place it on Lane 1, then click the other and place it on Lane 2 — running them in parallel beats stacking both on one lane.";
  }
  if (placedCount === 2) {
    return "Step 3: one task left. Place it, then hit Submit.";
  }
  return "All tasks placed — hit Submit to see your time, or Reset to try a different lane split.";
}

function startLevel(level, opts) {
  opts = opts || {};
  state.currentLevel = level;
  state.isTutorial = !!opts.isTutorial;
  state.isDaily = !!opts.isDaily;
  state.dailyDateStr = opts.dailyDateStr || null;
  state.campaignIndex = typeof opts.campaignIndex === "number" ? opts.campaignIndex : -1;
  state.placement = Engine.initState(level.numLanes);
  state.order = [];
  state.selectedTaskId = null;

  document.getElementById("play-title").textContent = level.title;
  document.getElementById("play-flavor").textContent = level.flavor;

  var tutBanner = document.getElementById("tutorial-banner");
  if (state.isTutorial) {
    tutBanner.classList.remove("hidden");
  } else {
    tutBanner.classList.add("hidden");
  }

  renderPlayScreen();
  showView("view-play");
}

function taskStateFor(level, placement, id) {
  if (placement.placed.hasOwnProperty(id)) return "placed";
  var ready = Engine.computeReadySet(level.tasks, placement.placed);
  for (var i = 0; i < ready.length; i++) {
    if (ready[i].id === id) return "ready";
  }
  return "locked";
}

function renderPlayScreen() {
  var level = state.currentLevel;
  var placement = state.placement;

  Graph.renderGraph(document.getElementById("graph-canvas"), level.tasks, function (id) {
    return taskStateFor(level, placement, id);
  });

  renderReadyTray(level, placement);
  renderLanes(level, placement);

  var complete = Engine.isComplete(placement, level.tasks);
  document.getElementById("btn-submit").disabled = !complete;

  var liveEl = document.getElementById("live-makespan");
  var ms = Engine.currentMakespan(placement);
  liveEl.textContent = complete ? "All tasks placed — finish time: " + ms + "m" : "Time so far: " + ms + "m";

  if (state.isTutorial) {
    document.getElementById("tutorial-banner").textContent = tutorialStepText();
  }
}

function renderReadyTray(level, placement) {
  var tray = document.getElementById("ready-tray");
  clearChildren(tray);
  var ready = Engine.computeReadySet(level.tasks, placement.placed);

  if (ready.length === 0) {
    var msg = document.createElement("p");
    msg.className = "ready-empty";
    msg.textContent = Engine.isComplete(placement, level.tasks) ? "All tasks placed." : "Waiting on placed tasks to finish…";
    tray.appendChild(msg);
    return;
  }

  ready.forEach(function (task) {
    var card = document.createElement("button");
    card.type = "button";
    card.className = "task-card" + (state.selectedTaskId === task.id ? " selected" : "");
    card.setAttribute("data-testid", "ready-" + task.id);

    var nameEl = document.createElement("div");
    nameEl.className = "task-card-name";
    nameEl.textContent = task.name;
    var durEl = document.createElement("div");
    durEl.className = "task-card-duration";
    durEl.textContent = task.duration + "m";
    card.appendChild(nameEl);
    card.appendChild(durEl);

    card.addEventListener("click", function () {
      state.selectedTaskId = state.selectedTaskId === task.id ? null : task.id;
      renderPlayScreen();
    });
    tray.appendChild(card);
  });
}

function buildLaneBuckets(level, placement) {
  var byLane = [];
  for (var i = 0; i < level.numLanes; i++) byLane.push([]);
  level.tasks.forEach(function (t) {
    var p = placement.placed[t.id];
    if (p) byLane[p.lane].push({ task: t, placement: p });
  });
  byLane.forEach(function (items) {
    items.sort(function (a, b) {
      return a.placement.start - b.placement.start;
    });
  });
  return byLane;
}

function appendTaskBlocks(laneEl, items) {
  items.forEach(function (item) {
    var block = document.createElement("div");
    block.className = "task-block";
    block.style.height = Math.max(28, item.task.duration * 6) + "px";
    var nameEl = document.createElement("div");
    nameEl.className = "task-block-name";
    nameEl.textContent = item.task.name;
    var timeEl = document.createElement("div");
    timeEl.className = "task-block-time";
    timeEl.textContent = item.placement.start + "–" + item.placement.finish + "m";
    block.appendChild(nameEl);
    block.appendChild(timeEl);
    laneEl.appendChild(block);
  });
}

function renderLanes(level, placement) {
  var lanesEl = document.getElementById("lanes");
  clearChildren(lanesEl);
  var byLane = buildLaneBuckets(level, placement);

  byLane.forEach(function (items, laneIdx) {
    var laneEl = document.createElement("button");
    laneEl.type = "button";
    laneEl.className = "lane-column lane-clickable";
    laneEl.setAttribute("data-testid", "lane-" + laneIdx);
    laneEl.disabled = !state.selectedTaskId;

    var header = document.createElement("div");
    header.className = "lane-header";
    header.textContent = "Lane " + (laneIdx + 1) + " — free at " + placement.laneFreeAt[laneIdx] + "m";
    laneEl.appendChild(header);

    appendTaskBlocks(laneEl, items);

    laneEl.addEventListener("click", function () {
      if (!state.selectedTaskId) return;
      var task = null;
      for (var i = 0; i < level.tasks.length; i++) {
        if (level.tasks[i].id === state.selectedTaskId) {
          task = level.tasks[i];
          break;
        }
      }
      if (!task) return;
      state.placement = Engine.applyPlacement(state.placement, task, laneIdx);
      state.order.push({ taskId: task.id, lane: laneIdx });
      state.selectedTaskId = null;
      renderPlayScreen();
    });

    lanesEl.appendChild(laneEl);
  });
}

// ---------------------------------------------------------------------------
// Result screen
// ---------------------------------------------------------------------------

function finishLevel(level, placement) {
  var solver = Engine.solveOptimal(level.tasks, level.numLanes);
  var makespan = Engine.currentMakespan(placement);
  var grade = Engine.gradeForMakespan(makespan, solver.optimal);
  var result = { level: level, placed: placement.placed, makespan: makespan, optimal: solver.optimal, grade: grade };
  state.lastResult = result;

  if (state.isTutorial) {
    // No persistence for tutorial runs.
  } else if (state.isDaily) {
    var newStreak = computeNewStreak(progress.daily, state.dailyDateStr);
    progress.daily.streak = newStreak;
    progress.daily.lastPlayedDate = state.dailyDateStr;
    progress.daily.history[state.dailyDateStr] = {
      makespan: makespan,
      optimal: solver.optimal,
      grade: grade,
      placed: placement.placed,
      tasks: level.tasks,
      numLanes: level.numLanes
    };
    saveProgress();
  } else {
    var existing = progress.campaign[level.id];
    if (!existing || makespan < existing.bestMakespan) {
      progress.campaign[level.id] = { bestMakespan: makespan, bestGrade: grade };
      saveProgress();
    }
  }

  renderResult(result, state.isDaily, state.dailyDateStr);
  showView("view-result");
}

function renderLaneRecap(container, level, placed) {
  clearChildren(container);
  var fakePlacement = { placed: placed, laneFreeAt: [] };
  var byLane = buildLaneBuckets(level, fakePlacement);
  byLane.forEach(function (items, laneIdx) {
    var laneEl = document.createElement("div");
    laneEl.className = "lane-column";
    var header = document.createElement("div");
    header.className = "lane-header";
    header.textContent = "Lane " + (laneIdx + 1);
    laneEl.appendChild(header);
    appendTaskBlocks(laneEl, items);
    container.appendChild(laneEl);
  });
}

function renderResult(result, isDaily, dateStr) {
  var badge = document.getElementById("result-badge");
  badge.className = "result-badge grade-" + result.grade;
  badge.textContent = gradeEmoji(result.grade) + " " + capitalize(result.grade);

  var summary = document.getElementById("result-summary");
  var diff = result.makespan - result.optimal;
  summary.textContent = "Your time: " + result.makespan + "m — Optimal: " + result.optimal + "m" + (diff > 0 ? " (+" + diff + "m)" : "");

  renderLaneRecap(document.getElementById("result-lanes"), result.level, result.placed);

  var shareEl = document.getElementById("daily-share");
  if (isDaily) {
    shareEl.textContent = buildShareText(dateStr, result, progress.daily.streak);
    shareEl.classList.remove("hidden");
  } else {
    shareEl.classList.add("hidden");
    shareEl.textContent = "";
  }

  document.getElementById("ai-note").textContent = "";
  document.getElementById("ai-key-input").value = "";

  var playAgainBtn = document.getElementById("btn-play-again");
  if (isDaily) {
    playAgainBtn.classList.add("hidden");
  } else {
    playAgainBtn.classList.remove("hidden");
  }

  var nextBtn = document.getElementById("btn-next-level");
  var hasNext = !isDaily && !state.isTutorial && state.campaignIndex >= 0 && state.campaignIndex < Levels.CAMPAIGN_LEVELS.length - 1;
  if (hasNext) {
    nextBtn.classList.remove("hidden");
  } else {
    nextBtn.classList.add("hidden");
  }
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

function renderDashboard() {
  var dailyBlock = document.getElementById("dashboard-daily");
  clearChildren(dailyBlock);
  var h3 = document.createElement("h3");
  h3.textContent = "Daily Challenge";
  dailyBlock.appendChild(h3);
  var p = document.createElement("p");
  var streakText = progress.daily.streak + (progress.daily.streak > 0 ? " 🔥" : "");
  p.textContent = "Current streak: " + streakText + ". Last played: " + (progress.daily.lastPlayedDate || "never") + ".";
  dailyBlock.appendChild(p);

  var campaignBlock = document.getElementById("dashboard-campaign");
  clearChildren(campaignBlock);
  var h3b = document.createElement("h3");
  h3b.textContent = "Campaign Best Scores";
  campaignBlock.appendChild(h3b);
  var table = document.createElement("div");
  table.className = "dashboard-table";
  Levels.CAMPAIGN_LEVELS.forEach(function (level) {
    var row = document.createElement("div");
    row.className = "dashboard-row";
    row.setAttribute("data-testid", "dashboard-" + level.id);
    var name = document.createElement("span");
    name.textContent = level.title;
    var best = progress.campaign[level.id];
    var scoreEl = document.createElement("span");
    scoreEl.textContent = best ? gradeEmoji(best.bestGrade) + " " + best.bestMakespan + "m" : "—";
    row.appendChild(name);
    row.appendChild(scoreEl);
    table.appendChild(row);
  });
  campaignBlock.appendChild(table);
}

// ---------------------------------------------------------------------------
// Wiring
// ---------------------------------------------------------------------------

var progress = loadProgress();

document.getElementById("btn-tutorial").addEventListener("click", function () {
  startLevel(Levels.TUTORIAL_LEVEL, { isTutorial: true });
});

document.getElementById("btn-campaign").addEventListener("click", function () {
  renderLevelSelect();
  showView("view-level-select");
});

document.getElementById("btn-daily").addEventListener("click", function () {
  var today = Engine.todayUTCString();
  if (progress.daily.lastPlayedDate === today) {
    showStoredDailyResult(progress.daily.history[today], today);
  } else {
    startLevel(Engine.generateDailyLevel(today), { isDaily: true, dailyDateStr: today });
  }
});

var backButtons = document.querySelectorAll('[data-back="home"]');
for (var bi = 0; bi < backButtons.length; bi++) {
  backButtons[bi].addEventListener("click", function () {
    renderDailyStatus();
    showView("view-home");
  });
}

var navButtons = document.querySelectorAll(".nav-btn");
for (var ni = 0; ni < navButtons.length; ni++) {
  navButtons[ni].addEventListener("click", function (evt) {
    var target = evt.currentTarget.getAttribute("data-nav");
    if (target === "home") {
      renderDailyStatus();
      showView("view-home");
    } else if (target === "dashboard") {
      renderDashboard();
      showView("view-dashboard");
    }
  });
}

document.getElementById("btn-reset").addEventListener("click", function () {
  state.placement = Engine.initState(state.currentLevel.numLanes);
  state.order = [];
  state.selectedTaskId = null;
  renderPlayScreen();
});

document.getElementById("btn-submit").addEventListener("click", function () {
  if (!Engine.isComplete(state.placement, state.currentLevel.tasks)) return;
  finishLevel(state.currentLevel, state.placement);
});

document.getElementById("btn-exit-play").addEventListener("click", function () {
  showView(state.isDaily || state.isTutorial ? "view-home" : "view-level-select");
  if (state.isDaily || state.isTutorial) renderDailyStatus();
  else renderLevelSelect();
});

document.getElementById("btn-play-again").addEventListener("click", function () {
  startLevel(state.currentLevel, {
    isTutorial: state.isTutorial,
    isDaily: state.isDaily,
    dailyDateStr: state.dailyDateStr,
    campaignIndex: state.campaignIndex
  });
});

document.getElementById("btn-next-level").addEventListener("click", function () {
  var nextIdx = state.campaignIndex + 1;
  startLevel(Levels.CAMPAIGN_LEVELS[nextIdx], { campaignIndex: nextIdx });
});

document.getElementById("btn-back-menu").addEventListener("click", function () {
  renderDailyStatus();
  showView("view-home");
});

document.getElementById("btn-get-debrief").addEventListener("click", function () {
  var key = document.getElementById("ai-key-input").value.trim();
  var noteEl = document.getElementById("ai-note");
  noteEl.textContent = "Thinking…";
  var result = state.lastResult;
  if (!result) return;
  var solverResultLike = { optimal: result.optimal };
  var playerResultLike = { makespan: result.makespan, grade: result.grade, placed: result.placed };
  AIDebrief.getAICoaching(key, result.level, playerResultLike, solverResultLike).then(function (note) {
    noteEl.textContent = note;
  });
});

renderDailyStatus();
showView("view-home");
