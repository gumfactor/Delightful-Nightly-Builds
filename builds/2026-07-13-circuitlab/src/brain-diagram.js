/* CircuitLab brain diagram controller: view switching, region activation, mastery/feedback styling.
   Operates on static SVG markup in index.html; no DOM elements are created here. */

var BrainDiagram = (function () {
  var regionActivateHandler = null;

  function allRegionEls() {
    return Array.prototype.slice.call(document.querySelectorAll('.region'));
  }

  function regionEl(regionId) {
    return document.querySelector('.region[data-region="' + regionId + '"]');
  }

  function onRegionKeydown(evt) {
    if (evt.key === 'Enter' || evt.key === ' ' || evt.key === 'Spacebar') {
      evt.preventDefault();
      activate(evt.currentTarget);
    }
  }

  function onRegionClick(evt) {
    activate(evt.currentTarget);
  }

  function activate(el) {
    var regionId = el.getAttribute('data-region');
    if (regionActivateHandler && regionId) {
      regionActivateHandler(regionId);
    }
  }

  function init(onActivate) {
    regionActivateHandler = onActivate;
    allRegionEls().forEach(function (el) {
      el.addEventListener('click', onRegionClick);
      el.addEventListener('keydown', onRegionKeydown);
    });
  }

  /** 'single' shows only the active view (Explore mode); 'both' shows both views stacked (quiz modes). */
  function setViewMode(mode) {
    var container = document.getElementById('brain-views');
    container.setAttribute('data-view-mode', mode);
  }

  function setActiveView(viewName) {
    document.querySelectorAll('.brain-view').forEach(function (el) {
      el.classList.toggle('active-view', el.getAttribute('data-view') === viewName);
    });
    document.querySelectorAll('.view-tab').forEach(function (tab) {
      var isActive = tab.getAttribute('data-view') === viewName;
      tab.classList.toggle('active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
  }

  function clearHighlights() {
    allRegionEls().forEach(function (el) {
      el.classList.remove('highlighted', 'flash-correct', 'flash-incorrect', 'circuit-selected');
      el.removeAttribute('data-circuit-order');
    });
  }

  function highlightRegion(regionId) {
    var el = regionEl(regionId);
    if (el) {
      el.classList.add('highlighted');
    }
  }

  function flashResult(regionId, isCorrect) {
    var el = regionEl(regionId);
    if (!el) {
      return;
    }
    el.classList.add(isCorrect ? 'flash-correct' : 'flash-incorrect');
  }

  function markCircuitProgress(progressIds) {
    allRegionEls().forEach(function (el) {
      el.classList.remove('circuit-selected');
      el.removeAttribute('data-circuit-order');
    });
    progressIds.forEach(function (regionId, index) {
      var el = regionEl(regionId);
      if (el) {
        el.classList.add('circuit-selected');
        el.setAttribute('data-circuit-order', String(index + 1));
      }
    });
  }

  function applyMastery(mastery) {
    allRegionEls().forEach(function (el) {
      var regionId = el.getAttribute('data-region');
      var level = mastery && typeof mastery[regionId] === 'number' ? mastery[regionId] : 0;
      for (var i = 0; i <= MASTERY_MAX; i++) {
        el.classList.remove('mastery-' + i);
      }
      el.classList.add('mastery-' + level);
      el.setAttribute('data-mastery', String(level));
    });
  }

  return {
    init: init,
    setViewMode: setViewMode,
    setActiveView: setActiveView,
    clearHighlights: clearHighlights,
    highlightRegion: highlightRegion,
    flashResult: flashResult,
    markCircuitProgress: markCircuitProgress,
    applyMastery: applyMastery,
    regionEl: regionEl,
  };
})();
