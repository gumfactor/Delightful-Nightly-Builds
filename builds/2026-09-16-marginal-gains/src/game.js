// Marginal Gains — UI controller. Classic script; relies on window.Engine
// and window.AIAdvisor from engine.js / ai.js loaded before this file.
(function () {
  "use strict";

  var DAILY_KEY = "marginalgains_daily_v1";
  var HISTORY_KEY = "marginalgains_history_v1";
  var HISTORY_LIMIT = 200;
  var STREAK_MIN_PERCENT = 0; // any completed Daily Challenge extends the streak

  var State = {
    round: null, // { mode, budget, projects, allocation, dateStr }
    lastScore: null,
    tutorial: null
  };

  function readJSON(key, fallback) {
    try {
      var raw = window.localStorage.getItem(key);
      if (!raw) return fallback;
      return JSON.parse(raw);
    } catch (e) {
      return fallback;
    }
  }

  function writeJSON(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      // localStorage unavailable (private mode, quota, etc.) — game still works, just doesn't persist.
    }
  }

  function readDaily() {
    return readJSON(DAILY_KEY, null);
  }

  function readHistory() {
    return readJSON(HISTORY_KEY, []);
  }

  function appendHistory(entry) {
    var history = readHistory();
    history.push(entry);
    if (history.length > HISTORY_LIMIT) {
      history = history.slice(history.length - HISTORY_LIMIT);
    }
    writeJSON(HISTORY_KEY, history);
  }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === "class") node.className = attrs[k];
        else if (k === "text") node.textContent = attrs[k];
        else node.setAttribute(k, attrs[k]);
      });
    }
    (children || []).forEach(function (c) {
      if (c) node.appendChild(c);
    });
    return node;
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function navigateTo(viewName) {
    document.querySelectorAll(".view").forEach(function (v) {
      v.classList.add("hidden");
    });
    var target = byId("view-" + viewName);
    if (target) target.classList.remove("hidden");
    document.querySelectorAll(".nav-btn").forEach(function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-nav") === viewName);
    });
  }

  // ---------- Home ----------

  function renderHome() {
    var today = Engine.todayUTCString();
    var rec = readDaily();
    var statusEl = byId("daily-status");
    var dailyBtn = byId("btn-daily");
    if (rec && rec.date === today && rec.completed) {
      statusEl.textContent =
        "Today's Daily Challenge is complete — Grade " + rec.grade + " (" + rec.percent + "% of optimal). Come back after 00:00 UTC.";
      dailyBtn.disabled = true;
    } else {
      statusEl.textContent = "Daily Challenge available today — resets at 00:00 UTC.";
      dailyBtn.disabled = false;
    }
  }

  // ---------- Tutorial ----------

  function tutorialProject() {
    return {
      id: "tutorial-example",
      name: "Grant Progress Report",
      category: "Admin",
      threshold: 2,
      weight: 10,
      maxHours: 10,
      values: Engine.generateValueTable(2, 10, 10)
    };
  }

  function startTutorial() {
    var project = tutorialProject();
    State.tutorial = { project: project, hours: 0 };
    byId("tut-name").textContent = project.name;
    var slider = byId("tutorial-slider");
    slider.max = String(project.maxHours);
    slider.value = "0";
    updateTutorial(0);
    navigateTo("tutorial");
  }

  function updateTutorial(hours) {
    var project = State.tutorial.project;
    var h = Math.max(0, Math.min(hours, project.maxHours));
    State.tutorial.hours = h;
    var value = Engine.projectValueAt(project, h);
    var nextValue = Engine.projectValueAt(project, h + 1);
    byId("tut-hours").textContent = String(h);
    byId("tut-value").textContent = String(value);
    byId("tut-marginal").textContent = String(nextValue - value);
    drawTutorialChart(project, h);
  }

  function drawTutorialChart(project, currentHours) {
    var canvas = byId("tutorial-canvas");
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext("2d");
    var w = canvas.width;
    var h = canvas.height;
    var padL = 40;
    var padB = 30;
    var padT = 15;
    var padR = 15;
    var plotW = w - padL - padR;
    var plotH = h - padT - padB;
    var maxVal = project.values[project.values.length - 1] || 1;

    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = "#2b344a";
    ctx.fillStyle = "#9aa7c2";
    ctx.font = "11px sans-serif";
    ctx.lineWidth = 1;

    // axes
    ctx.beginPath();
    ctx.moveTo(padL, padT);
    ctx.lineTo(padL, padT + plotH);
    ctx.lineTo(padL + plotW, padT + plotH);
    ctx.stroke();
    ctx.fillText("value", 4, padT + 10);
    ctx.fillText("hours", padL + plotW - 24, h - 6);

    function xFor(hour) {
      return padL + (hour / project.maxHours) * plotW;
    }
    function yFor(val) {
      return padT + plotH - (val / maxVal) * plotH;
    }

    ctx.strokeStyle = "#5b9dff";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (var hh = 0; hh <= project.maxHours; hh++) {
      var px = xFor(hh);
      var py = yFor(project.values[hh]);
      if (hh === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    var cx = xFor(currentHours);
    var cy = yFor(project.values[currentHours]);
    ctx.fillStyle = "#4fd18b";
    ctx.beginPath();
    ctx.arc(cx, cy, 5, 0, Math.PI * 2);
    ctx.fill();
  }

  // ---------- Play ----------

  function startRound(mode, budget, projects, dateStr) {
    var allocation = {};
    projects.forEach(function (p) {
      allocation[p.id] = 0;
    });
    State.round = { mode: mode, budget: budget, projects: projects, allocation: allocation, dateStr: dateStr || null };
    renderPlayView();
    navigateTo("play");
  }

  function renderPlayView() {
    var round = State.round;
    byId("play-title").textContent =
      round.mode === "daily" ? "Daily Challenge — " + round.dateStr : "Practice Round";
    var list = byId("project-list");
    list.textContent = "";
    round.projects.forEach(function (p) {
      list.appendChild(buildProjectCard(p));
    });
    updateBudgetBar();
  }

  function buildProjectCard(project) {
    var hours = State.round.allocation[project.id] || 0;
    var card = el("div", { class: "project-card", "data-testid": "project-card-" + project.id }, [
      el("div", { class: "project-card-header" }, [
        el("h3", { text: project.name }),
        el("span", { class: "project-category", text: project.category })
      ]),
      el("p", { class: "project-blurb", text: project.blurb }),
      el("div", { class: "project-controls" }, [
        el("button", { type: "button", class: "stepper-btn", "data-action": "minus5", "data-project-id": project.id, text: "-5" }),
        el("button", { type: "button", class: "stepper-btn", "data-action": "minus1", "data-project-id": project.id, text: "-1" }),
        el("span", { class: "project-hours", id: "hours-" + project.id, "data-testid": "hours-" + project.id, text: String(hours) + "h" }),
        el("button", { type: "button", class: "stepper-btn", "data-action": "plus1", "data-project-id": project.id, text: "+1" }),
        el("button", { type: "button", class: "stepper-btn", "data-action": "plus5", "data-project-id": project.id, text: "+5" }),
        el("span", { class: "project-value", id: "value-" + project.id, "data-testid": "value-" + project.id, text: "value: " + Engine.projectValueAt(project, hours) })
      ])
    ]);
    return card;
  }

  function projectById(id) {
    return State.round.projects.filter(function (p) {
      return p.id === id;
    })[0];
  }

  function handleProjectStep(projectId, delta) {
    var project = projectById(projectId);
    if (!project) return;
    var current = State.round.allocation[projectId] || 0;
    var next = Math.max(0, Math.min(current + delta, project.maxHours));
    State.round.allocation[projectId] = next;
    byId("hours-" + projectId).textContent = String(next) + "h";
    byId("value-" + projectId).textContent = "value: " + Engine.projectValueAt(project, next);
    updateBudgetBar();
  }

  function totalAllocated() {
    var round = State.round;
    var sum = 0;
    round.projects.forEach(function (p) {
      sum += round.allocation[p.id] || 0;
    });
    return sum;
  }

  function updateBudgetBar() {
    var round = State.round;
    var used = totalAllocated();
    var pct = Math.min(100, (used / round.budget) * 100);
    var fill = byId("budget-bar-fill");
    fill.style.width = pct + "%";
    fill.classList.toggle("over-budget", used > round.budget);
    byId("budget-used").textContent = String(used);
    byId("budget-total").textContent = String(round.budget);
    byId("budget-remaining").textContent = String(round.budget - used);
    byId("btn-lock-in").disabled = used > round.budget;
  }

  // ---------- Results ----------

  function lockIn() {
    var round = State.round;
    var scoreResult = Engine.scoreRound(round.projects, round.allocation, round.budget);
    State.lastScore = scoreResult;

    var categoryBreakdown = {};
    round.projects.forEach(function (p) {
      if (!categoryBreakdown[p.category]) categoryBreakdown[p.category] = { playerVal: 0, optimalVal: 0 };
      var playerHours = round.allocation[p.id] || 0;
      var optHours = scoreResult.optimalAllocation[p.id] || 0;
      categoryBreakdown[p.category].playerVal += Engine.projectValueAt(p, playerHours);
      categoryBreakdown[p.category].optimalVal += Engine.projectValueAt(p, optHours);
    });

    var historyEntry = {
      mode: round.mode,
      date: round.dateStr || Engine.todayUTCString(),
      percent: scoreResult.percent,
      grade: scoreResult.grade,
      categoryBreakdown: categoryBreakdown
    };
    appendHistory(historyEntry);

    if (round.mode === "daily") {
      writeJSON(DAILY_KEY, {
        date: round.dateStr,
        allocation: round.allocation,
        percent: scoreResult.percent,
        grade: scoreResult.grade,
        completed: true
      });
    }

    renderResults(scoreResult);
    navigateTo("results");
  }

  function renderResults(scoreResult) {
    var round = State.round;
    byId("grade-badge").textContent = scoreResult.grade;
    byId("score-percent").textContent = String(scoreResult.percent);
    byId("score-player-total").textContent = String(scoreResult.playerTotal);
    byId("score-optimal-total").textContent = String(scoreResult.optimalTotal);

    var tbody = byId("results-tbody");
    tbody.textContent = "";
    round.projects.forEach(function (p) {
      var playerHours = round.allocation[p.id] || 0;
      var optHours = scoreResult.optimalAllocation[p.id] || 0;
      var row = el("tr", {}, [
        el("td", { text: p.name }),
        el("td", { text: String(playerHours) }),
        el("td", { text: String(optHours) }),
        el("td", { text: String(Engine.projectValueAt(p, playerHours)) }),
        el("td", { text: String(Engine.projectValueAt(p, optHours)) })
      ]);
      tbody.appendChild(row);
    });

    var advisorNote = byId("advisor-note");
    advisorNote.textContent = AIAdvisor.buildFallbackNote(round.projects, round.allocation, scoreResult);
    byId("ai-key-input").value = "";

    var shareEl = byId("share-text");
    if (round.mode === "daily") {
      shareEl.textContent = buildShareText(round, scoreResult);
      shareEl.classList.remove("hidden");
    } else {
      shareEl.classList.add("hidden");
      shareEl.textContent = "";
    }
  }

  function buildShareText(round, scoreResult) {
    var grid = round.projects
      .map(function (p) {
        var playerHours = round.allocation[p.id] || 0;
        var optHours = scoreResult.optimalAllocation[p.id] || 0;
        var diff = Math.abs(playerHours - optHours);
        if (diff <= 1) return "🟢"; // green
        if (diff <= 3) return "🟡"; // yellow
        return "🔴"; // red
      })
      .join("");
    return "Marginal Gains — Daily Challenge " + round.dateStr + "\nGrade " + scoreResult.grade + " (" + scoreResult.percent + "% of optimal)\n" + grid;
  }

  function handleGetCoaching() {
    var round = State.round;
    var scoreResult = State.lastScore;
    var advisorNote = byId("advisor-note");
    var key = byId("ai-key-input").value.trim();
    advisorNote.textContent = "Thinking…";
    AIAdvisor.getAICoaching(key, round.projects, round.allocation, scoreResult, window.fetch ? window.fetch.bind(window) : null).then(function (text) {
      advisorNote.textContent = text;
    });
  }

  // ---------- Dashboard ----------

  function computeDailyStreaks(history) {
    var dailyDates = history
      .filter(function (h) {
        return h.mode === "daily" && h.percent >= STREAK_MIN_PERCENT;
      })
      .map(function (h) {
        return h.date;
      });
    var unique = Array.from(new Set(dailyDates)).sort();
    if (unique.length === 0) return { current: 0, best: 0 };

    var best = 1;
    var run = 1;
    for (var i = 1; i < unique.length; i++) {
      var prev = new Date(unique[i - 1] + "T00:00:00Z").getTime();
      var cur = new Date(unique[i] + "T00:00:00Z").getTime();
      var dayDiff = Math.round((cur - prev) / 86400000);
      if (dayDiff === 1) {
        run += 1;
      } else if (dayDiff > 1) {
        run = 1;
      }
      if (run > best) best = run;
    }

    var today = Engine.todayUTCString();
    var last = unique[unique.length - 1];
    var current = 0;
    if (last === today || isYesterday(last, today)) {
      current = 1;
      for (var j = unique.length - 1; j > 0; j--) {
        var d1 = new Date(unique[j - 1] + "T00:00:00Z").getTime();
        var d2 = new Date(unique[j] + "T00:00:00Z").getTime();
        if (Math.round((d2 - d1) / 86400000) === 1) current += 1;
        else break;
      }
    }
    return { current: current, best: best };
  }

  function isYesterday(dateStr, todayStr) {
    var today = new Date(todayStr + "T00:00:00Z").getTime();
    var d = new Date(dateStr + "T00:00:00Z").getTime();
    return Math.round((today - d) / 86400000) === 1;
  }

  function renderDashboard() {
    var history = readHistory();
    var statsEl = byId("dashboard-stats");
    var catEl = byId("category-stats");
    statsEl.textContent = "";
    catEl.textContent = "";

    var roundsPlayed = history.length;
    var avgPercent = roundsPlayed === 0 ? 0 : Math.round(history.reduce(function (sum, h) { return sum + h.percent; }, 0) / roundsPlayed);
    var streaks = computeDailyStreaks(history);

    [
      { label: "Rounds Played", value: roundsPlayed },
      { label: "Average % of Optimal", value: avgPercent + "%" },
      { label: "Current Daily Streak", value: streaks.current },
      { label: "Best Daily Streak", value: streaks.best }
    ].forEach(function (s) {
      statsEl.appendChild(
        el("div", { class: "stat-tile" }, [
          el("span", { class: "stat-value", text: String(s.value) }),
          el("span", { class: "stat-label", text: s.label })
        ])
      );
    });

    var totals = {};
    history.forEach(function (h) {
      Object.keys(h.categoryBreakdown || {}).forEach(function (cat) {
        if (!totals[cat]) totals[cat] = { playerVal: 0, optimalVal: 0 };
        totals[cat].playerVal += h.categoryBreakdown[cat].playerVal;
        totals[cat].optimalVal += h.categoryBreakdown[cat].optimalVal;
      });
    });

    if (Object.keys(totals).length === 0) {
      catEl.appendChild(el("p", { class: "stat-label", text: "Play a round to see category performance." }));
    } else {
      Engine.CATEGORIES.forEach(function (cat) {
        var t = totals[cat];
        if (!t) return;
        var ratio = t.optimalVal === 0 ? 100 : Math.round((t.playerVal / t.optimalVal) * 100);
        catEl.appendChild(
          el("div", { class: "stat-tile" }, [
            el("span", { class: "stat-value", text: ratio + "%" }),
            el("span", { class: "stat-label", text: cat })
          ])
        );
      });
    }
  }

  // ---------- Wiring ----------

  function init() {
    document.querySelectorAll(".nav-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var target = btn.getAttribute("data-nav");
        if (target === "dashboard") renderDashboard();
        if (target === "home") renderHome();
        navigateTo(target);
      });
    });

    byId("btn-tutorial").addEventListener("click", startTutorial);
    byId("btn-tutorial-done").addEventListener("click", function () {
      navigateTo("home");
      renderHome();
    });
    byId("tutorial-slider").addEventListener("input", function (e) {
      updateTutorial(parseInt(e.target.value, 10));
    });

    byId("btn-daily").addEventListener("click", function () {
      var today = Engine.todayUTCString();
      var rec = readDaily();
      if (rec && rec.date === today && rec.completed) return;
      var draw = Engine.drawDailyProjects(today);
      startRound("daily", draw.budget, draw.projects, today);
    });

    byId("btn-practice").addEventListener("click", function () {
      navigateTo("difficulty");
    });
    document.querySelectorAll(".diff-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var tier = parseInt(btn.getAttribute("data-diff"), 10);
        var draw = Engine.drawPracticeProjects(tier);
        startRound("practice", draw.budget, draw.projects);
      });
    });

    byId("project-list").addEventListener("click", function (e) {
      var btn = e.target.closest ? e.target.closest(".stepper-btn") : null;
      if (!btn) return;
      var action = btn.getAttribute("data-action");
      var projectId = btn.getAttribute("data-project-id");
      var deltas = { minus5: -5, minus1: -1, plus1: 1, plus5: 5 };
      handleProjectStep(projectId, deltas[action]);
    });

    byId("btn-lock-in").addEventListener("click", lockIn);
    byId("btn-get-coaching").addEventListener("click", handleGetCoaching);

    byId("btn-play-again").addEventListener("click", function () {
      if (State.round.mode === "daily") {
        navigateTo("home");
        renderHome();
      } else {
        navigateTo("difficulty");
      }
    });
    byId("btn-back-home").addEventListener("click", function () {
      navigateTo("home");
      renderHome();
    });
    byId("btn-dashboard-home").addEventListener("click", function () {
      navigateTo("home");
      renderHome();
    });

    renderHome();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Exposed for tests only (Playwright drives the real DOM; this is a
  // convenience hook for assertions, never used to bypass the UI).
  window.__marginalGainsTestHooks = {
    getState: function () {
      return State;
    }
  };
})();
