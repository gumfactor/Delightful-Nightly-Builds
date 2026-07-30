/* Vizstract — UI wiring: form state, live preview, library panel,
   export buttons, and the optional AI/deterministic extraction flow. */
(function () {
  "use strict";
  window.Vizstract = window.Vizstract || {};

  var state = { id: null, theme: "indigo" };

  function els() {
    return {
      title: document.getElementById("title-input"),
      designType: document.getElementById("design-type-select"),
      population: document.getElementById("population-input"),
      iv: document.getElementById("iv-input"),
      dv: document.getElementById("dv-input"),
      n: document.getElementById("n-input"),
      finding: document.getElementById("finding-textarea"),
      direction: document.getElementById("direction-select"),
      stat: document.getElementById("stat-input"),
      libraryName: document.getElementById("library-name-input"),
      abstract: document.getElementById("abstract-textarea"),
      apiKey: document.getElementById("apikey-input")
    };
  }

  function collectFormData() {
    var e = els();
    return {
      id: state.id,
      name: e.libraryName.value,
      title: e.title.value,
      designType: e.designType.value,
      population: e.population.value,
      ivLabel: e.iv.value,
      dvLabel: e.dv.value,
      sampleSize: e.n.value,
      headlineFinding: e.finding.value,
      effectDirection: e.direction.value,
      statDetail: e.stat.value,
      theme: state.theme
    };
  }

  function applyDataToForm(data, opts) {
    opts = opts || {};
    var e = els();
    if (data.title !== undefined) e.title.value = data.title || "";
    if (data.designType !== undefined && window.Vizstract.Templates.all[data.designType]) e.designType.value = data.designType;
    if (data.population !== undefined) e.population.value = data.population || "";
    if (data.ivLabel !== undefined) e.iv.value = data.ivLabel || "";
    if (data.dvLabel !== undefined) e.dv.value = data.dvLabel || "";
    if (data.sampleSize !== undefined) e.n.value = data.sampleSize || "";
    if (data.headlineFinding !== undefined) e.finding.value = data.headlineFinding || "";
    if (data.effectDirection !== undefined && ["increase", "decrease", "none", "mixed"].indexOf(data.effectDirection) >= 0) {
      e.direction.value = data.effectDirection;
    }
    if (data.statDetail !== undefined) e.stat.value = data.statDetail || "";
    if (data.theme && window.Vizstract.Render.THEMES[data.theme]) state.theme = data.theme;
    if (opts.setName && data.name !== undefined) e.libraryName.value = data.name || "";
    if (opts.setId) state.id = data.id || null;
  }

  function mergeExtracted(current, extracted) {
    var merged = {};
    for (var k in current) merged[k] = current[k];
    ["title", "designType", "population", "ivLabel", "dvLabel", "sampleSize", "headlineFinding", "effectDirection", "statDetail"].forEach(function (key) {
      var value = extracted[key];
      if (value !== undefined && value !== null && String(value).trim() !== "") {
        merged[key] = value;
      }
    });
    return merged;
  }

  function sanitizeFilename(name) {
    var base = String(name || "vizstract").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-+|-+$)/g, "");
    return base || "vizstract";
  }

  function validateData(data) {
    if (!data.title || !data.title.trim()) return "Please enter a study title before exporting.";
    return null;
  }

  function showMessage(text) {
    var el = document.querySelector('[data-testid="validation-message"]');
    el.textContent = text || "";
    el.hidden = !text;
  }

  function updateValidation(data) {
    var msg = validateData(data);
    showMessage(msg);
    return !msg;
  }

  function hideSavedNote() {
    var note = document.querySelector('[data-testid="saved-note"]');
    note.hidden = true;
    note.textContent = "";
  }

  function renderPreview() {
    hideSavedNote();
    var data = collectFormData();
    var svg = window.Vizstract.Render.renderSVG(data);
    document.querySelector('[data-testid="preview-svg"]').innerHTML = svg;
    updateValidation(data);
  }

  function renderThemeSwatches() {
    var row = document.querySelector('[data-testid="theme-row"]');
    row.innerHTML = "";
    Object.keys(window.Vizstract.Render.THEMES).forEach(function (key) {
      var theme = window.Vizstract.Render.THEMES[key];
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "theme-swatch";
      btn.setAttribute("data-testid", "theme-swatch");
      btn.setAttribute("data-theme", key);
      btn.setAttribute("aria-pressed", String(state.theme === key));
      btn.setAttribute("aria-label", key + " theme");
      btn.title = key;
      btn.style.background = theme.accent;
      btn.addEventListener("click", function () {
        state.theme = key;
        renderThemeSwatches();
        renderPreview();
      });
      row.appendChild(btn);
    });
  }

  function renderLibraryList() {
    var container = document.querySelector('[data-testid="library-list"]');
    var items = window.Vizstract.Library.list();
    if (!items.length) {
      container.innerHTML = '<p class="library-empty">No saved abstracts yet.</p>';
      return;
    }
    var esc = window.Vizstract.Render.escapeXml;
    var html = "";
    items.forEach(function (item) {
      var label = window.Vizstract.Templates.get(item.designType).label;
      html +=
        '<div class="library-item" data-testid="library-item" data-id="' + esc(item.id) + '">' +
          '<div class="library-item-info">' +
            '<div class="library-item-name">' + esc(item.name || item.title || "Untitled") + "</div>" +
            '<div class="library-item-meta">' + esc(label) + "</div>" +
          "</div>" +
          '<div class="library-item-actions">' +
            '<button type="button" data-action="load" data-testid="btn-load">Load</button>' +
            '<button type="button" data-action="delete" data-testid="btn-delete">Delete</button>' +
          "</div>" +
        "</div>";
    });
    container.innerHTML = html;
  }

  function wireLiveFields() {
    var ids = [
      "title-input", "design-type-select", "population-input", "iv-input",
      "dv-input", "n-input", "finding-textarea", "direction-select", "stat-input"
    ];
    ids.forEach(function (id) {
      var el = document.getElementById(id);
      el.addEventListener("input", renderPreview);
      el.addEventListener("change", renderPreview);
    });
  }

  function wireLibraryList() {
    document.querySelector('[data-testid="library-list"]').addEventListener("click", function (e) {
      var actionBtn = e.target.closest("[data-action]");
      if (!actionBtn) return;
      var itemEl = actionBtn.closest('[data-testid="library-item"]');
      var id = itemEl.getAttribute("data-id");
      if (actionBtn.getAttribute("data-action") === "load") {
        var entry = window.Vizstract.Library.get(id);
        if (entry) {
          applyDataToForm(entry, { setName: true, setId: true });
          renderThemeSwatches();
          renderPreview();
        }
      } else if (actionBtn.getAttribute("data-action") === "delete") {
        window.Vizstract.Library.remove(id);
        if (state.id === id) state.id = null;
        renderLibraryList();
      }
    });
  }

  var BLANK_ENTRY = {
    id: null, name: "", title: "", designType: "compare", population: "",
    ivLabel: "", dvLabel: "", sampleSize: "", headlineFinding: "",
    effectDirection: "none", statDetail: "", theme: "indigo"
  };

  function wireActions() {
    document.querySelector('[data-testid="btn-clear"]').addEventListener("click", function () {
      applyDataToForm(BLANK_ENTRY, { setName: true, setId: true });
      renderThemeSwatches();
      renderPreview();
    });

    document.querySelector('[data-testid="btn-save"]').addEventListener("click", function () {
      var data = collectFormData();
      if (!updateValidation(data)) return;
      if (!data.name || !data.name.trim()) data.name = data.title;
      var saved = window.Vizstract.Library.save(data);
      state.id = saved.id;
      renderLibraryList();
      var note = document.querySelector('[data-testid="saved-note"]');
      note.textContent = 'Saved "' + saved.name + '".';
      note.hidden = false;
    });

    document.querySelector('[data-testid="btn-download-svg"]').addEventListener("click", function () {
      var data = collectFormData();
      if (!updateValidation(data)) return;
      var svg = window.Vizstract.Render.renderSVG(data);
      window.Vizstract.Export.downloadSVG(svg, sanitizeFilename(data.title) + ".svg");
    });

    document.querySelector('[data-testid="btn-download-png"]').addEventListener("click", function () {
      var data = collectFormData();
      if (!updateValidation(data)) return;
      var svg = window.Vizstract.Render.renderSVG(data);
      window.Vizstract.Export
        .downloadPNG(svg, window.Vizstract.Render.CANVAS_W, window.Vizstract.Render.CANVAS_H, sanitizeFilename(data.title) + ".png")
        .catch(function (err) {
          showMessage("Could not generate PNG: " + (err && err.message ? err.message : String(err)));
        });
    });

    document.querySelector('[data-testid="btn-extract"]').addEventListener("click", async function () {
      var e = els();
      var statusEl = document.querySelector('[data-testid="extract-status"]');
      var abstractText = e.abstract.value;
      if (!abstractText || !abstractText.trim()) {
        statusEl.textContent = "Paste an abstract first.";
        return;
      }
      statusEl.textContent = "Extracting…";
      var apiKey = e.apiKey.value.trim();
      try {
        var result = await window.Vizstract.Extract.extract(abstractText, apiKey || null);
        var current = collectFormData();
        var merged = mergeExtracted(current, result.data || {});
        applyDataToForm(merged, {});
        renderThemeSwatches();
        renderPreview();
        if (result.source === "ai") {
          statusEl.textContent = "Fields extracted with Claude Haiku.";
        } else if (result.error) {
          statusEl.textContent = "AI extraction unavailable (" + result.error + ") — used the deterministic fallback instead.";
        } else {
          statusEl.textContent = "No API key supplied — used the deterministic keyword extractor (no network call made).";
        }
      } catch (err) {
        statusEl.textContent = "Extraction failed: " + (err && err.message ? err.message : String(err));
      }
    });
  }

  function init() {
    var e = els();
    window.Vizstract.Templates.order.forEach(function (key) {
      var opt = document.createElement("option");
      opt.value = key;
      opt.textContent = window.Vizstract.Templates.all[key].label;
      e.designType.appendChild(opt);
    });
    e.designType.value = "compare";
    e.direction.value = "none";

    renderThemeSwatches();
    renderLibraryList();
    renderPreview();
    wireLiveFields();
    wireLibraryList();
    wireActions();
  }

  document.addEventListener("DOMContentLoaded", init);

  window.Vizstract.App = {
    collectFormData: collectFormData,
    applyDataToForm: applyDataToForm,
    mergeExtracted: mergeExtracted,
    sanitizeFilename: sanitizeFilename,
    validateData: validateData,
    renderPreview: renderPreview
  };
})();
