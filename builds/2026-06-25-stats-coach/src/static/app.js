(function () {
  'use strict';

  // Toggle button groups
  function initToggleGroup(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.querySelectorAll('.toggle-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        container.querySelectorAll('.toggle-btn').forEach(function (b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
      });
    });
  }

  initToggleGroup('paired_toggle');
  initToggleGroup('normality_toggle');
  initToggleGroup('relationship_toggle');

  // Tab switching for code panels
  document.querySelectorAll('.tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      var targetId = tab.getAttribute('data-tab');
      document.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('active'); });
      document.querySelectorAll('.tab-panel').forEach(function (p) { p.classList.remove('active'); });
      tab.classList.add('active');
      var panel = document.getElementById('panel-' + targetId);
      if (panel) panel.classList.add('active');
    });
  });

  function getToggleValue(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return null;
    var active = container.querySelector('.toggle-btn.active');
    return active ? active.getAttribute('data-value') : null;
  }

  function showError(msg) {
    var el = document.getElementById('error_msg');
    el.textContent = msg;
    el.style.display = 'block';
  }

  function hideError() {
    var el = document.getElementById('error_msg');
    el.style.display = 'none';
  }

  document.getElementById('submit_btn').addEventListener('click', function () {
    hideError();

    var outcomeType = document.getElementById('outcome_type').value;
    var numGroups = parseInt(document.getElementById('num_groups').value, 10);
    var pairedRaw = getToggleValue('paired_toggle');
    var normality = getToggleValue('normality_toggle');
    var relationshipRaw = getToggleValue('relationship_toggle');
    var studyContext = document.getElementById('study_context').value.trim();

    var paired = pairedRaw === 'true';
    var relationship = relationshipRaw === 'true';

    var resultsSection = document.getElementById('results');
    resultsSection.style.display = 'block';

    var loadingEl = document.getElementById('loading_indicator');
    var contentEl = document.getElementById('results_content');
    loadingEl.style.display = 'flex';
    contentEl.style.display = 'none';

    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    fetch('/api/advise', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        outcome_type: outcomeType,
        num_groups: numGroups,
        paired: paired,
        normality: normality,
        relationship: relationship,
        study_context: studyContext,
      }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        loadingEl.style.display = 'none';

        if (!result.ok) {
          showError(result.data.error || 'Unknown error from server.');
          resultsSection.style.display = 'none';
          return;
        }

        var data = result.data;

        document.getElementById('result_test_name').textContent = data.test_name;

        var badge = document.getElementById('result_family_badge');
        badge.textContent = data.family || '';
        badge.className = 'badge ' + (data.family || '');

        var cachedEl = document.getElementById('cached_indicator');
        cachedEl.textContent = data.cached ? '⚡ From cache' : '';

        // Render AI explanation as paragraphs
        var explanationEl = document.getElementById('result_explanation');
        explanationEl.innerHTML = '';
        var paragraphs = (data.ai_explanation || '').split(/\n\n+/).filter(Boolean);
        paragraphs.forEach(function (para) {
          var p = document.createElement('p');
          p.textContent = para.trim();
          explanationEl.appendChild(p);
        });

        // Assumptions
        var assumptionsList = document.getElementById('result_assumptions');
        assumptionsList.innerHTML = '';
        (data.assumptions || []).forEach(function (a) {
          var li = document.createElement('li');
          li.textContent = a;
          assumptionsList.appendChild(li);
        });

        document.getElementById('result_r_code').textContent = data.r_code || '';
        document.getElementById('result_python_code').textContent = data.python_code || '';
        document.getElementById('result_interpretation').textContent = data.interpretation || '';

        contentEl.style.display = 'block';
      })
      .catch(function (err) {
        loadingEl.style.display = 'none';
        resultsSection.style.display = 'none';
        showError('Network error: ' + err.message);
      });
  });
})();
