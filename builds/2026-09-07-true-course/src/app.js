/* True Course — game UI and state. Classic script, no ES modules, no
 * bundler, so the game opens directly via file://. All dynamic text is
 * inserted via textContent/createElement — never innerHTML — so nothing
 * from a puzzle, a shared result, or an AI response can execute as markup.
 */
(function () {
  'use strict';

  var TC = window.TC;
  var STORAGE_KEY = 'trueCourseState_v1';

  var CHAPTERS = [
    { type: 'buoyage', rounds: 6, title: 'Chapter 1 — Buoyage' },
    { type: 'right-of-way', rounds: 8, title: 'Chapter 2 — Right of Way' },
    { type: 'tide-window', rounds: 6, title: 'Chapter 3 — Tide Windows' },
    { type: 'set-drift', rounds: 8, title: 'Chapter 4 — Set & Drift' },
  ];

  var TYPE_LABELS = {
    buoyage: 'Buoyage',
    'right-of-way': 'Right of Way',
    'tide-window': 'Tide Windows',
    'set-drift': 'Set & Drift',
  };

  var UNLOCK_THRESHOLD = 0.7;

  // ---- Persistence -------------------------------------------------

  function defaultState() {
    var mastery = {};
    var chaptersUnlocked = {};
    var chapterBest = {};
    CHAPTERS.forEach(function (c, i) {
      mastery[c.type] = { attempts: 0, correct: 0 };
      chaptersUnlocked[c.type] = i === 0;
      chapterBest[c.type] = 0;
    });
    return {
      mastery: mastery,
      chaptersUnlocked: chaptersUnlocked,
      chapterBest: chapterBest,
      daily: { date: null, completed: false, score: 0, results: [] },
    };
  }

  function loadState() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return defaultState();
      var parsed = JSON.parse(raw);
      var fresh = defaultState();
      // Merge shallowly so a schema addition never crashes an old save.
      return Object.assign(fresh, parsed, {
        mastery: Object.assign(fresh.mastery, parsed.mastery || {}),
        chaptersUnlocked: Object.assign(
          fresh.chaptersUnlocked,
          parsed.chaptersUnlocked || {}
        ),
        chapterBest: Object.assign(fresh.chapterBest, parsed.chapterBest || {}),
        daily: Object.assign(fresh.daily, parsed.daily || {}),
      });
    } catch (e) {
      return defaultState();
    }
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      /* localStorage unavailable (private mode, quota) — game still works
       * for the current session, just without persistence. */
    }
  }

  function recordAttempt(state, type, wasCorrect) {
    var m = state.mastery[type];
    m.attempts += 1;
    if (wasCorrect) m.correct += 1;
  }

  // ---- DOM helpers ---------------------------------------------------

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        if (key === 'class') node.className = attrs[key];
        else if (key === 'text') node.textContent = attrs[key];
        else if (key.indexOf('on') === 0 && typeof attrs[key] === 'function') {
          node.addEventListener(key.slice(2), attrs[key]);
        } else {
          node.setAttribute(key, attrs[key]);
        }
      });
    }
    (children || []).forEach(function (child) {
      if (child) node.appendChild(child);
    });
    return node;
  }

  function screenRoot() {
    return document.getElementById('screen');
  }

  function clearScreen() {
    var root = screenRoot();
    while (root.firstChild) root.removeChild(root.firstChild);
    return root;
  }

  // ---- Puzzle prompt building -----------------------------------------

  function buildQuestion(puzzle) {
    var p = puzzle.params;
    if (puzzle.type === 'set-drift') {
      return (
        'You want to make good a track of ' +
        p.trackDeg +
        '°T for ' +
        p.distanceNm +
        ' nm. Your boat makes ' +
        p.boatSpeedKts +
        ' kts through the water. The current sets ' +
        p.setDeg +
        '°T at ' +
        p.driftKts +
        ' kts. What course should you steer (°T)?'
      );
    }
    if (puzzle.type === 'tide-window') {
      return (
        'Low tide is ' +
        p.h0 +
        ' m at ' +
        TC.formatClock(p.t0) +
        '. The next high tide is ' +
        p.h1 +
        ' m at ' +
        TC.formatClock(p.t1) +
        '. Your boat draws ' +
        p.draft +
        ' m and you want a ' +
        p.margin +
        ' m safety margin. Charted depth here (at chart datum) is ' +
        p.chartedDepth +
        ' m. What is the earliest safe departure time?'
      );
    }
    if (puzzle.type === 'right-of-way') {
      return (
        'You are on a heading of ' +
        p.yourHeadingDeg +
        '°T. Another power-driven vessel is on a heading of ' +
        p.otherHeadingDeg +
        '°T, and you spot her bearing ' +
        p.bearingToOtherDeg +
        '°T from you. Who must give way?'
      );
    }
    if (puzzle.type === 'buoyage') {
      if (puzzle.variant === 'side') {
        return (
          'You are heading ' +
          (p.direction === 'inbound' ? 'inbound, returning from sea' : 'outbound, toward open water') +
          ' and see buoy #' +
          p.number +
          ', colored ' +
          p.color +
          '. Which side should you keep it on?'
        );
      }
      if (puzzle.variant === 'shape') {
        return 'You spot a ' + p.color + ' buoy. What shape should it be?';
      }
      return (
        'You spot buoy #' +
        p.number +
        '. Under IALA System B ("red right returning"), what color should it be?'
      );
    }
    return '';
  }

  var RIGHT_OF_WAY_LABELS = {
    you: 'You must give way',
    other: 'The other vessel must give way (you are stand-on)',
    both: 'Both vessels alter course to starboard (head-on)',
  };

  // ---- Game state -------------------------------------------------

  var session = {
    mode: null, // 'voyage' | 'practice' | 'daily'
    chapterIndex: 0,
    roundIndex: 0,
    correctInChapter: 0,
    puzzle: null,
    rng: null,
    practiceType: null,
    dailyPuzzles: null,
    dailyResults: [],
    aiKey: '', // session-only, never persisted or exposed on the debug hook
  };

  window.__TC_DEBUG = {
    getCurrentPuzzle: function () {
      return session.puzzle;
    },
    getState: function () {
      return loadState();
    },
    getSession: function () {
      return {
        mode: session.mode,
        chapterIndex: session.chapterIndex,
        roundIndex: session.roundIndex,
        correctInChapter: session.correctInChapter,
      };
    },
  };

  // ---- Screens -------------------------------------------------------

  function renderMenu() {
    var state = loadState();
    var root = clearScreen();

    var panel = el('div', { class: 'panel' }, [
      el('h2', { text: 'Choose your mode' }),
      el('div', { class: 'menu-grid' }, [
        el(
          'button',
          {
            class: 'tc-btn tc-btn-primary',
            'data-testid': 'menu-voyage-btn',
            onclick: startVoyage,
          },
          [document.createTextNode('Voyage Mode')]
        ),
        el(
          'button',
          {
            class: 'tc-btn',
            'data-testid': 'menu-practice-btn',
            onclick: function () {
              renderPracticeChooser();
            },
          },
          [document.createTextNode('Practice')]
        ),
        el(
          'button',
          {
            class: 'tc-btn',
            'data-testid': 'menu-daily-btn',
            onclick: startDaily,
          },
          [document.createTextNode('Daily Challenge')]
        ),
        el(
          'button',
          {
            class: 'tc-btn',
            'data-testid': 'menu-dashboard-btn',
            onclick: renderDashboard,
          },
          [document.createTextNode('Mastery Dashboard')]
        ),
      ]),
    ]);
    root.appendChild(panel);

    var todayKey = todayUtcString();
    var dailyDone = state.daily.date === todayKey && state.daily.completed;
    if (dailyDone) {
      root.appendChild(
        el('div', { class: 'panel', 'data-testid': 'daily-done-note' }, [
          el('p', {
            text:
              "Today's Daily Challenge is complete: " +
              state.daily.score +
              ' / ' +
              state.daily.results.length +
              '. Come back after 00:00 UTC for a new one.',
          }),
        ])
      );
    }
  }

  function renderPracticeChooser() {
    var root = clearScreen();
    var buttons = CHAPTERS.map(function (c) {
      return el(
        'button',
        {
          class: 'tc-btn',
          'data-testid': 'practice-choose-' + c.type,
          onclick: function () {
            startPractice(c.type);
          },
        },
        [document.createTextNode(TYPE_LABELS[c.type])]
      );
    });
    root.appendChild(
      el('div', { class: 'panel' }, [
        el('h2', { text: 'Practice — pick a puzzle type' }),
        el('div', { class: 'choice-grid' }, buttons),
        backButton(),
      ])
    );
  }

  function backButton() {
    return el(
      'button',
      { class: 'tc-btn tc-btn-small', 'data-testid': 'back-to-menu-btn', onclick: renderMenu },
      [document.createTextNode('← Menu')]
    );
  }

  function todayUtcString() {
    var now = new Date();
    return (
      now.getUTCFullYear() +
      '-' +
      String(now.getUTCMonth() + 1).padStart(2, '0') +
      '-' +
      String(now.getUTCDate()).padStart(2, '0')
    );
  }

  // ---- Voyage mode -----------------------------------------------

  function startVoyage() {
    session.mode = 'voyage';
    session.chapterIndex = 0;
    var state = loadState();
    // Resume at the first unlocked chapter the player hasn't finished,
    // rather than always forcing chapter 1.
    for (var i = CHAPTERS.length - 1; i >= 0; i--) {
      if (state.chaptersUnlocked[CHAPTERS[i].type]) {
        session.chapterIndex = i;
        break;
      }
    }
    beginChapter(session.chapterIndex);
  }

  function beginChapter(chapterIndex) {
    session.chapterIndex = chapterIndex;
    session.roundIndex = 0;
    session.correctInChapter = 0;
    session.rng = TC.mulberry32((Date.now() ^ (Math.random() * 1e9)) >>> 0);
    nextVoyageRound();
  }

  function nextVoyageRound() {
    var chapter = CHAPTERS[session.chapterIndex];
    if (session.roundIndex >= chapter.rounds) {
      finishChapter();
      return;
    }
    session.puzzle = TC.generatePuzzle(chapter.type, session.rng);
    renderPuzzleScreen({
      title: chapter.title + ' — Round ' + (session.roundIndex + 1) + '/' + chapter.rounds,
      onAnswered: function (wasCorrect) {
        if (wasCorrect) session.correctInChapter += 1;
        var state = loadState();
        recordAttempt(state, session.puzzle.type, wasCorrect);
        saveState(state);
        session.roundIndex += 1;
      },
      onNext: nextVoyageRound,
    });
  }

  function finishChapter() {
    var chapter = CHAPTERS[session.chapterIndex];
    var accuracy = session.correctInChapter / chapter.rounds;
    var state = loadState();
    if (accuracy > (state.chapterBest[chapter.type] || 0)) {
      state.chapterBest[chapter.type] = accuracy;
    }
    var unlockedNext = false;
    var nextChapter = CHAPTERS[session.chapterIndex + 1];
    if (nextChapter && accuracy >= UNLOCK_THRESHOLD && !state.chaptersUnlocked[nextChapter.type]) {
      state.chaptersUnlocked[nextChapter.type] = true;
      unlockedNext = true;
    }
    saveState(state);

    var root = clearScreen();
    var pct = Math.round(accuracy * 100);
    var children = [
      el('h2', { text: chapter.title + ' complete' }),
      el('p', {
        text: 'Score: ' + session.correctInChapter + ' / ' + chapter.rounds + ' (' + pct + '%)',
        'data-testid': 'chapter-result',
      }),
    ];
    if (accuracy < UNLOCK_THRESHOLD && nextChapter) {
      children.push(
        el('p', {
          text:
            'You need ' +
            Math.round(UNLOCK_THRESHOLD * 100) +
            '% to unlock ' +
            nextChapter.title +
            '. Try again!',
        })
      );
    } else if (unlockedNext) {
      children.push(
        el('p', { text: nextChapter.title + ' is now unlocked!', 'data-testid': 'unlock-note' })
      );
    } else if (!nextChapter) {
      children.push(el('p', { text: 'You’ve completed every chapter. Well steered!' }));
    }

    var buttons = [
      el(
        'button',
        {
          class: 'tc-btn tc-btn-primary',
          'data-testid': 'replay-chapter-btn',
          onclick: function () {
            beginChapter(session.chapterIndex);
          },
        },
        [document.createTextNode('Replay Chapter')]
      ),
    ];
    if (unlockedNext) {
      buttons.push(
        el(
          'button',
          {
            class: 'tc-btn',
            'data-testid': 'next-chapter-btn',
            onclick: function () {
              beginChapter(session.chapterIndex + 1);
            },
          },
          [document.createTextNode('Next Chapter →')]
        )
      );
    }
    buttons.push(backButton());

    children.push(el('div', { class: 'choice-grid' }, buttons));
    root.appendChild(el('div', { class: 'panel' }, children));
  }

  // ---- Practice mode ---------------------------------------------

  function startPractice(type) {
    session.mode = 'practice';
    session.practiceType = type;
    session.rng = TC.mulberry32((Date.now() ^ (Math.random() * 1e9)) >>> 0);
    nextPracticeRound();
  }

  function nextPracticeRound() {
    session.puzzle = TC.generatePuzzle(session.practiceType, session.rng);
    renderPuzzleScreen({
      title: 'Practice — ' + TYPE_LABELS[session.practiceType],
      onAnswered: function (wasCorrect) {
        var state = loadState();
        recordAttempt(state, session.puzzle.type, wasCorrect);
        saveState(state);
      },
      onNext: nextPracticeRound,
    });
  }

  // ---- Daily challenge ---------------------------------------------

  function startDaily() {
    var state = loadState();
    var todayKey = todayUtcString();
    if (state.daily.date === todayKey && state.daily.completed) {
      renderDailyResults(state.daily);
      return;
    }

    session.mode = 'daily';
    var rng = TC.mulberry32(TC.dailySeed(todayKey));
    var order = [];
    for (var i = 0; i < 5; i++) {
      order.push(TC.CHAPTER_ORDER[i % TC.CHAPTER_ORDER.length]);
    }
    session.dailyPuzzles = order.map(function (type) {
      return TC.generatePuzzle(type, rng);
    });
    session.roundIndex = 0;
    session.dailyResults = [];
    nextDailyRound();
  }

  function nextDailyRound() {
    if (session.roundIndex >= session.dailyPuzzles.length) {
      finishDaily();
      return;
    }
    session.puzzle = session.dailyPuzzles[session.roundIndex];
    renderPuzzleScreen({
      title: 'Daily Challenge — ' + (session.roundIndex + 1) + '/' + session.dailyPuzzles.length,
      onAnswered: function (wasCorrect) {
        session.dailyResults.push(wasCorrect);
        var state = loadState();
        recordAttempt(state, session.puzzle.type, wasCorrect);
        saveState(state);
        session.roundIndex += 1;
      },
      onNext: nextDailyRound,
    });
  }

  function finishDaily() {
    var score = session.dailyResults.filter(Boolean).length;
    var state = loadState();
    state.daily = {
      date: todayUtcString(),
      completed: true,
      score: score,
      results: session.dailyResults.slice(),
    };
    saveState(state);
    renderDailyResults(state.daily);
  }

  function renderDailyResults(daily) {
    var root = clearScreen();
    var grid = daily.results
      .map(function (r) {
        return r ? '✅' : '❌';
      })
      .join(' ');
    var shareText = 'True Course ' + daily.date + '\n' + daily.score + '/' + daily.results.length + '\n' + grid;

    var panel = el('div', { class: 'panel' }, [
      el('h2', { text: 'Daily Challenge — ' + daily.date }),
      el('p', { text: 'Score: ' + daily.score + ' / ' + daily.results.length }),
      el('div', { class: 'share-box', 'data-testid': 'daily-share-box', text: shareText }),
      el(
        'button',
        {
          class: 'tc-btn tc-btn-small',
          'data-testid': 'copy-share-btn',
          onclick: function () {
            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(shareText).catch(function () {});
            }
          },
        },
        [document.createTextNode('Copy Result')]
      ),
    ]);
    root.appendChild(panel);
    root.appendChild(buildAiNotePanel(daily.score, daily.results.length));
    root.appendChild(el('div', { class: 'panel' }, [backButton()]));
  }

  // ---- Puzzle screen (shared by all modes) ---------------------------

  function renderPuzzleScreen(opts) {
    var root = clearScreen();
    var puzzle = session.puzzle;

    var canvas = el('canvas', { width: '360', height: '260', 'data-testid': 'puzzle-canvas' });

    var panel = el('div', { class: 'panel' }, [
      el('h3', { text: opts.title, 'data-testid': 'round-title' }),
      el('p', { text: buildQuestion(puzzle), 'data-testid': 'question-text' }),
      canvas,
    ]);

    var answerArea = el('div', { class: 'answer-area', 'data-testid': 'answer-area' });
    panel.appendChild(answerArea);

    var feedback = el('div', { 'data-testid': 'feedback' });
    panel.appendChild(feedback);

    root.appendChild(panel);

    drawPuzzleCanvas(canvas, puzzle, false, null);

    var answered = false;

    function submitAnswer(chosen) {
      if (answered) return;
      answered = true;
      var wasCorrect = evaluateAnswer(puzzle, chosen);

      drawPuzzleCanvas(canvas, puzzle, true, chosen);

      feedback.className = 'feedback ' + (wasCorrect ? 'correct' : 'incorrect');
      feedback.textContent = wasCorrect
        ? 'Correct! ' + explainAnswer(puzzle)
        : 'Not quite. ' + explainAnswer(puzzle);

      var nextBtn = el(
        'button',
        {
          class: 'tc-btn tc-btn-primary',
          'data-testid': 'next-btn',
          onclick: function () {
            opts.onNext();
          },
        },
        [document.createTextNode('Next →')]
      );
      panel.appendChild(nextBtn);

      opts.onAnswered(wasCorrect);
    }

    if (puzzle.type === 'set-drift') {
      var input = el('input', {
        type: 'number',
        min: '0',
        max: '359',
        'data-testid': 'answer-input',
      });
      var submitBtn = el(
        'button',
        {
          class: 'tc-btn tc-btn-primary',
          'data-testid': 'submit-btn',
          onclick: function () {
            var val = parseFloat(input.value);
            if (isNaN(val)) return;
            submitAnswer(val);
          },
        },
        [document.createTextNode('Steer')]
      );
      answerArea.appendChild(
        el('div', { class: 'numeric-input-row' }, [input, submitBtn])
      );
    } else {
      var choices = puzzle.choices || ['you', 'other', 'both'];
      var choiceGrid = el('div', { class: 'choice-grid' });
      choices.forEach(function (choice) {
        var label = choiceLabel(puzzle, choice);
        choiceGrid.appendChild(
          el(
            'button',
            {
              class: 'tc-btn',
              'data-testid': 'choice-btn',
              'data-choice': choice,
              onclick: function () {
                submitAnswer(choice);
              },
            },
            [document.createTextNode(label)]
          )
        );
      });
      answerArea.appendChild(choiceGrid);
    }
  }

  function choiceLabel(puzzle, choice) {
    if (puzzle.type === 'right-of-way') return RIGHT_OF_WAY_LABELS[choice];
    return choice.charAt(0).toUpperCase() + choice.slice(1);
  }

  function drawPuzzleCanvas(canvas, puzzle, revealed, chosen) {
    if (puzzle.type === 'set-drift') {
      var headingGuess = revealed && typeof chosen === 'number' ? chosen : null;
      TC.render.drawSetDriftDiagram(canvas, puzzle, revealed, headingGuess);
    } else if (puzzle.type === 'right-of-way') {
      TC.render.drawVesselDiagram(canvas, puzzle);
    } else if (puzzle.type === 'tide-window') {
      var startTime = null;
      if (revealed) {
        var result = TC.tideWindowStart({
          t0: puzzle.params.t0,
          h0: puzzle.params.h0,
          t1: puzzle.params.t1,
          h1: puzzle.params.h1,
          requiredHeight: puzzle.params.requiredHeight,
        });
        startTime = result.startTime;
      }
      TC.render.drawTideCurve(canvas, puzzle, revealed, startTime);
    } else if (puzzle.type === 'buoyage') {
      var color = puzzle.params.color || TC.buoyage.colorForNumber(puzzle.params.number);
      var shape = TC.buoyage.shapeForColor(color);
      TC.render.drawBuoy(canvas, color, shape);
    }
  }

  function evaluateAnswer(puzzle, chosen) {
    if (puzzle.type === 'set-drift') {
      return TC.angularDistance(chosen, puzzle.correctAnswer) <= puzzle.tolerance;
    }
    return chosen === puzzle.correctAnswer;
  }

  function explainAnswer(puzzle) {
    if (puzzle.type === 'set-drift') {
      return (
        'Steer ' +
        puzzle.correctAnswer +
        '°T — SOG ' +
        puzzle.sogKts.toFixed(1) +
        ' kts, ETA ' +
        puzzle.etaHours.toFixed(1) +
        ' hr.'
      );
    }
    if (puzzle.type === 'tide-window') {
      return 'Safe to depart at ' + puzzle.correctAnswer + '.';
    }
    if (puzzle.type === 'right-of-way') {
      return RIGHT_OF_WAY_LABELS[puzzle.correctAnswer] + ' (' + puzzle.encounterType + ').';
    }
    if (puzzle.type === 'buoyage') {
      return 'Correct answer: ' + puzzle.correctAnswer + '.';
    }
    return '';
  }

  // ---- Mastery dashboard --------------------------------------------

  function renderDashboard() {
    var state = loadState();
    var root = clearScreen();

    var rows = CHAPTERS.map(function (c) {
      var m = state.mastery[c.type];
      var acc = m.attempts > 0 ? Math.round((m.correct / m.attempts) * 100) : 0;
      var unlocked = state.chaptersUnlocked[c.type];
      var tr = el('tr', {}, [
        el('td', { text: TYPE_LABELS[c.type] }),
        el('td', { text: m.attempts + '' }),
        el('td', { text: acc + '%' }),
        el('td', {}, [
          el('span', {
            class: 'badge ' + (unlocked ? 'badge-unlocked' : 'badge-locked'),
            text: unlocked ? 'Unlocked' : 'Locked',
          }),
        ]),
      ]);
      return tr;
    });

    var table = el('table', { class: 'dashboard', 'data-testid': 'dashboard-table' }, [
      el('thead', {}, [
        el('tr', {}, [
          el('th', { text: 'Puzzle Type' }),
          el('th', { text: 'Attempts' }),
          el('th', { text: 'Accuracy' }),
          el('th', { text: 'Chapter' }),
        ]),
      ]),
      el('tbody', {}, rows),
    ]);

    root.appendChild(
      el('div', { class: 'panel' }, [el('h2', { text: 'Mastery Dashboard' }), table, backButton()])
    );
  }

  // ---- First Mate's Log (optional AI commentary) ----------------------

  function deterministicFirstMateNote(score, total) {
    var pct = total > 0 ? Math.round((score / total) * 100) : 0;
    if (pct >= 90) return "First Mate's Log: Sharp watch tonight, skipper — that's a clean plot from buoy to horizon.";
    if (pct >= 70) return "First Mate's Log: Solid run. A couple of soundings to double-check, but the course holds.";
    if (pct >= 40) return "First Mate's Log: Choppy water out there tonight — worth another pass through the chart table.";
    return "First Mate's Log: Rough crossing. Drop anchor, review the rules, and try again when the tide turns.";
  }

  function fetchFirstMateNote(apiKey, score, total) {
    var prompt =
      'You are a laconic ship’s first mate. In one short encouraging or bracing sentence ' +
      '(under 30 words), react to a navigation trainee scoring ' +
      score +
      ' out of ' +
      total +
      ' on tonight’s puzzles. Aggregate score only, no other detail.';

    return fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 100,
        messages: [{ role: 'user', content: prompt }],
      }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error('AI request failed');
        return res.json();
      })
      .then(function (data) {
        var text = data && data.content && data.content[0] && data.content[0].text;
        if (!text) throw new Error('empty AI response');
        return text;
      });
  }

  function buildAiNotePanel(score, total) {
    var panel = el('div', { class: 'panel' }, [
      el('h3', { text: "First Mate's Log (optional)" }),
      el('label', { text: 'Anthropic API key (used only in this browser tab, never stored)' }),
      el('input', { type: 'password', 'data-testid': 'ai-key-input' }),
    ]);
    var noteBox = el('div', { class: 'ai-note', 'data-testid': 'ai-note-box' });
    var fetchBtn = el(
      'button',
      {
        class: 'tc-btn tc-btn-small',
        'data-testid': 'ai-fetch-btn',
        onclick: function () {
          var keyInput = panel.querySelector('[data-testid="ai-key-input"]');
          var key = keyInput ? keyInput.value : '';
          noteBox.textContent = 'Consulting the first mate…';
          if (!key) {
            noteBox.textContent = deterministicFirstMateNote(score, total);
            return;
          }
          fetchFirstMateNote(key, score, total)
            .then(function (text) {
              noteBox.textContent = text;
            })
            .catch(function () {
              noteBox.textContent = deterministicFirstMateNote(score, total);
            });
        },
      },
      [document.createTextNode('Get Note')]
    );
    panel.appendChild(fetchBtn);
    panel.appendChild(noteBox);
    return panel;
  }

  // ---- Boot -----------------------------------------------------------

  document.addEventListener('DOMContentLoaded', function () {
    renderMenu();
  });
})();
