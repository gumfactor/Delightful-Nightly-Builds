/*
 * Almanac — UI wiring, network calls, Chart.js rendering, localStorage.
 * Depends on window.Almanac (src/analytics.js) and the global Chart (CDN).
 * Classic script, no ES modules — opens directly via file://.
 */
(function () {
  "use strict";

  var GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search";
  var ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive";
  var RECENT_KEY = "almanac.recentLocations";
  var SETTINGS_KEY = "almanac.lastSettings";
  var MAX_RECENT = 5;

  var MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  // -- DOM refs --------------------------------------------------------
  var el = {
    searchInput: document.getElementById("locationSearchInput"),
    searchBtn: document.getElementById("locationSearchBtn"),
    searchError: document.getElementById("searchError"),
    searchResults: document.getElementById("searchResults"),
    recentWrap: document.getElementById("recentWrap"),
    recentList: document.getElementById("recentLocations"),
    selectedWrap: document.getElementById("selectedLocationWrap"),
    selectedText: document.getElementById("selectedLocationText"),
    startYear: document.getElementById("startYear"),
    endYear: document.getElementById("endYear"),
    startMonth: document.getElementById("startMonth"),
    endMonth: document.getElementById("endMonth"),
    activityPreset: document.getElementById("activityPreset"),
    customThresholds: document.getElementById("customThresholds"),
    customTempMin: document.getElementById("customTempMin"),
    customTempMax: document.getElementById("customTempMax"),
    customWind: document.getElementById("customWind"),
    customPrecip: document.getElementById("customPrecip"),
    fetchBtn: document.getElementById("fetchBtn"),
    statusMessage: document.getElementById("statusMessage"),
    resultsSection: document.getElementById("resultsSection"),
    summaryCards: document.getElementById("summaryCards"),
    extremeEventsPanel: document.getElementById("extremeEventsPanel"),
    yearTableBody: document.getElementById("yearTableBody"),
    yearChartVariable: document.getElementById("yearChartVariable"),
    exportDailyCsvBtn: document.getElementById("exportDailyCsvBtn"),
    exportSummaryCsvBtn: document.getElementById("exportSummaryCsvBtn")
  };

  // -- State -------------------------------------------------------------
  var state = {
    selectedLocation: null,
    dailyRaw: null, // full-year daily data as fetched
    dailyFiltered: null, // after month-window filter
    climatology: null,
    extremeEvents: null,
    suitability: null,
    yearSummary: null,
    yearSort: { key: "year", dir: "asc" }
  };

  var charts = { climatology: null, year: null };

  // -- localStorage helpers (never throw) --------------------------------
  function safeGetJSON(key, fallback) {
    try {
      var raw = window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function safeSetJSON(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      /* storage unavailable or full — degrade silently, not a core feature */
    }
  }

  function loadRecentLocations() {
    return safeGetJSON(RECENT_KEY, []);
  }

  function saveRecentLocation(loc) {
    var recents = loadRecentLocations();
    recents = recents.filter(function (r) {
      return !(r.latitude === loc.latitude && r.longitude === loc.longitude);
    });
    recents.unshift(loc);
    if (recents.length > MAX_RECENT) recents = recents.slice(0, MAX_RECENT);
    safeSetJSON(RECENT_KEY, recents);
    renderRecentLocations();
  }

  function loadLastSettings() {
    return safeGetJSON(SETTINGS_KEY, null);
  }

  function saveLastSettings() {
    safeSetJSON(SETTINGS_KEY, {
      startYear: el.startYear.value,
      endYear: el.endYear.value,
      startMonth: el.startMonth.value,
      endMonth: el.endMonth.value,
      activityPreset: el.activityPreset.value,
      customTempMin: el.customTempMin.value,
      customTempMax: el.customTempMax.value,
      customWind: el.customWind.value,
      customPrecip: el.customPrecip.value
    });
  }

  // -- Setup ---------------------------------------------------------------
  function populateMonthSelects() {
    [el.startMonth, el.endMonth].forEach(function (select) {
      MONTH_NAMES.forEach(function (name, i) {
        var opt = document.createElement("option");
        opt.value = String(i + 1);
        opt.textContent = name;
        select.appendChild(opt);
      });
    });
    el.startMonth.value = "1";
    el.endMonth.value = "12";
  }

  function applyDefaultYearRange() {
    var currentYear = new Date().getUTCFullYear();
    el.endYear.value = String(currentYear - 1);
    el.startYear.value = String(currentYear - 11);
  }

  function restoreLastSettings() {
    var s = loadLastSettings();
    if (!s) return;
    if (s.startYear) el.startYear.value = s.startYear;
    if (s.endYear) el.endYear.value = s.endYear;
    if (s.startMonth) el.startMonth.value = s.startMonth;
    if (s.endMonth) el.endMonth.value = s.endMonth;
    if (s.activityPreset) el.activityPreset.value = s.activityPreset;
    if (s.customTempMin) el.customTempMin.value = s.customTempMin;
    if (s.customTempMax) el.customTempMax.value = s.customTempMax;
    if (s.customWind) el.customWind.value = s.customWind;
    if (s.customPrecip) el.customPrecip.value = s.customPrecip;
    toggleCustomThresholds();
  }

  function toggleCustomThresholds() {
    el.customThresholds.hidden = el.activityPreset.value !== "custom";
  }

  // -- Rendering: search / recents / selection ------------------------------
  function clearChildren(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function locationLabel(loc) {
    var parts = [loc.name];
    if (loc.admin1) parts.push(loc.admin1);
    if (loc.country) parts.push(loc.country);
    return parts.join(", ");
  }

  function renderLocationList(listEl, locations, onPick) {
    clearChildren(listEl);
    locations.forEach(function (loc) {
      var li = document.createElement("li");
      li.textContent = locationLabel(loc); // textContent only — never innerHTML with API text
      li.addEventListener("click", function () {
        onPick(loc);
      });
      listEl.appendChild(li);
    });
    listEl.hidden = locations.length === 0;
  }

  function renderRecentLocations() {
    var recents = loadRecentLocations();
    el.recentWrap.hidden = recents.length === 0;
    renderLocationList(el.recentList, recents, selectLocation);
  }

  function selectLocation(loc) {
    state.selectedLocation = loc;
    el.selectedWrap.hidden = false;
    el.selectedText.textContent = locationLabel(loc);
    el.searchResults.hidden = true;
    el.fetchBtn.disabled = false;
    saveRecentLocation(loc);
  }

  // -- Networking ------------------------------------------------------------
  function fetchJSON(url) {
    return fetch(url).then(function (resp) {
      return resp.json().then(
        function (body) {
          if (!resp.ok || body.error) {
            var reason = (body && body.reason) || "Request failed (HTTP " + resp.status + ")";
            throw new Error(reason);
          }
          return body;
        },
        function () {
          throw new Error("Request failed (HTTP " + resp.status + ") and the response was not valid JSON");
        }
      );
    });
  }

  function showStatus(text, isError) {
    el.statusMessage.hidden = !text;
    el.statusMessage.textContent = text || "";
    el.statusMessage.style.color = isError ? "var(--error)" : "";
  }

  function doSearch() {
    var query = el.searchInput.value.trim();
    el.searchError.hidden = true;
    if (!query) {
      el.searchError.textContent = "Type a location name to search.";
      el.searchError.hidden = false;
      return;
    }
    el.searchBtn.disabled = true;
    fetchJSON(GEOCODE_URL + "?name=" + encodeURIComponent(query) + "&count=5")
      .then(function (body) {
        var results = body.results || [];
        if (results.length === 0) {
          el.searchError.textContent = 'No locations found for "' + query + '". Try a different spelling or a nearby larger city.';
          el.searchError.hidden = false;
          el.searchResults.hidden = true;
          return;
        }
        var mapped = results.map(function (r) {
          return {
            name: r.name,
            admin1: r.admin1 || "",
            country: r.country || "",
            latitude: r.latitude,
            longitude: r.longitude,
            timezone: r.timezone || "auto"
          };
        });
        if (mapped.length === 1) {
          selectLocation(mapped[0]);
        } else {
          renderLocationList(el.searchResults, mapped, selectLocation);
        }
      })
      .catch(function (err) {
        el.searchError.textContent = "Location search failed: " + err.message;
        el.searchError.hidden = false;
      })
      .then(function () {
        el.searchBtn.disabled = false;
      });
  }

  function currentActivityPreset() {
    var val = el.activityPreset.value;
    if (val === "custom") {
      return {
        label: "Custom",
        tempMinC: parseFloat(el.customTempMin.value),
        tempMaxC: parseFloat(el.customTempMax.value),
        maxWindKmh: parseFloat(el.customWind.value),
        maxPrecipMm: parseFloat(el.customPrecip.value)
      };
    }
    return window.Almanac.ACTIVITY_PRESETS[val];
  }

  function doFetchHistorical() {
    if (!state.selectedLocation) return;
    var startYear = parseInt(el.startYear.value, 10);
    var endYear = parseInt(el.endYear.value, 10);
    if (!startYear || !endYear || startYear > endYear) {
      showStatus("Enter a valid start year at or before the end year.", true);
      return;
    }
    saveLastSettings();
    el.fetchBtn.disabled = true;
    el.resultsSection.hidden = true;
    showStatus("Fetching historical data from Open-Meteo…", false);

    var loc = state.selectedLocation;
    var url =
      ARCHIVE_URL +
      "?latitude=" + encodeURIComponent(loc.latitude) +
      "&longitude=" + encodeURIComponent(loc.longitude) +
      "&start_date=" + startYear + "-01-01" +
      "&end_date=" + endYear + "-12-31" +
      "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max" +
      "&timezone=auto";

    fetchJSON(url)
      .then(function (body) {
        var daily = body.daily;
        if (!daily || !daily.time || daily.time.length === 0) {
          showStatus("Open-Meteo returned no data for that location and range.", true);
          return;
        }
        state.dailyRaw = daily;
        processAndRender();
        showStatus("Loaded " + daily.time.length + " days of data.", false);
      })
      .catch(function (err) {
        showStatus("Could not fetch historical data: " + err.message, true);
      })
      .then(function () {
        el.fetchBtn.disabled = false;
      });
  }

  // -- Analysis + rendering ---------------------------------------------------
  function processAndRender() {
    var A = window.Almanac;
    var startMonth = parseInt(el.startMonth.value, 10);
    var endMonth = parseInt(el.endMonth.value, 10);
    var filtered =
      startMonth === 1 && endMonth === 12 ? state.dailyRaw : A.filterByMonthWindow(state.dailyRaw, startMonth, endMonth);
    state.dailyFiltered = filtered;

    if (filtered.time.length === 0) {
      showStatus("No days fall within the selected season window.", true);
      el.resultsSection.hidden = true;
      return;
    }

    state.climatology = A.computeMonthlyClimatology(filtered);
    state.extremeEvents = A.detectExtremeEvents(filtered, A.DEFAULT_THRESHOLDS);
    state.suitability = A.computeSuitability(filtered, currentActivityPreset());
    state.yearSummary = A.computeYearSummary(filtered, state.extremeEvents, state.suitability);

    el.resultsSection.hidden = false;
    renderSummaryCards();
    renderClimatologyChart();
    renderYearChart();
    renderExtremeEvents();
    renderYearTable();
  }

  function renderSummaryCards() {
    clearChildren(el.summaryCards);
    var years = state.yearSummary.length;
    var totalHeat = state.yearSummary.reduce(function (a, y) { return a + y.heatWaveCount; }, 0);
    var totalCold = state.yearSummary.reduce(function (a, y) { return a + y.coldSnapCount; }, 0);
    var pct = state.suitability.pct;

    var cards = [
      { label: "Years of data", value: String(years) },
      { label: "Days analyzed", value: String(state.dailyFiltered.time.length) },
      { label: "% days suitable (" + currentActivityPreset().label + ")", value: pct === null ? "—" : pct.toFixed(1) + "%" },
      { label: "Total heat-wave events", value: String(totalHeat) },
      { label: "Total cold-snap events", value: String(totalCold) }
    ];
    cards.forEach(function (c) {
      var div = document.createElement("div");
      div.className = "card";
      var val = document.createElement("div");
      val.className = "value";
      val.textContent = c.value;
      var label = document.createElement("div");
      label.className = "label";
      label.textContent = c.label;
      div.appendChild(val);
      div.appendChild(label);
      el.summaryCards.appendChild(div);
    });
  }

  function renderClimatologyChart() {
    var ctx = document.getElementById("climatologyChart");
    if (!ctx || typeof Chart === "undefined") return;
    var labels = MONTH_NAMES.map(function (n) { return n.slice(0, 3); });
    var p10 = state.climatology.map(function (m) { return m.tempMax ? m.tempMax.p10 : null; });
    var p50 = state.climatology.map(function (m) { return m.tempMax ? m.tempMax.p50 : null; });
    var p90 = state.climatology.map(function (m) { return m.tempMax ? m.tempMax.p90 : null; });

    if (charts.climatology) charts.climatology.destroy();
    charts.climatology = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          { label: "P90 high", data: p90, borderColor: "#e0a35f", fill: "+1", backgroundColor: "rgba(224,163,95,0.15)" },
          { label: "P50 (median) high", data: p50, borderColor: "#2f6f4f" },
          { label: "P10 high", data: p10, borderColor: "#5f9be0", fill: false }
        ]
      },
      options: { responsive: true, scales: { y: { title: { display: true, text: "°C" } } } }
    });
  }

  function renderYearChart() {
    var ctx = document.getElementById("yearChart");
    if (!ctx || typeof Chart === "undefined") return;
    var variable = el.yearChartVariable.value;
    var labels = state.yearSummary.map(function (y) { return y.year; });
    var data = state.yearSummary.map(function (y) { return y[variable]; });

    if (charts.year) charts.year.destroy();
    charts.year = new Chart(ctx, {
      type: "bar",
      data: { labels: labels, datasets: [{ label: variable, data: data, backgroundColor: "#2f6f4f" }] },
      options: { responsive: true }
    });
  }

  function renderExtremeEvents() {
    clearChildren(el.extremeEventsPanel);
    var ee = state.extremeEvents;

    function addEventList(title, events, formatter) {
      var h4 = document.createElement("h4");
      h4.textContent = title + " (" + events.length + ")";
      el.extremeEventsPanel.appendChild(h4);
      if (events.length === 0) {
        var none = document.createElement("p");
        none.textContent = "None in the selected range.";
        el.extremeEventsPanel.appendChild(none);
        return;
      }
      var ul = document.createElement("ul");
      events.slice(0, 15).forEach(function (e) {
        var li = document.createElement("li");
        li.textContent = formatter(e);
        ul.appendChild(li);
      });
      el.extremeEventsPanel.appendChild(ul);
      if (events.length > 15) {
        var more = document.createElement("p");
        more.textContent = "+" + (events.length - 15) + " more (see CSV export for the full list).";
        el.extremeEventsPanel.appendChild(more);
      }
    }

    addEventList("Heat waves (≥3 consecutive days ≥30°C)", ee.heatWaveEvents, function (e) {
      return e.startDate + " to " + e.endDate + " (" + e.length + " days)";
    });
    addEventList("Cold snaps (≥2 consecutive days ≤-10°C)", ee.coldSnapEvents, function (e) {
      return e.startDate + " to " + e.endDate + " (" + e.length + " days)";
    });

    var rainP = document.createElement("p");
    rainP.textContent = "Heavy rain days (≥25mm): " + ee.heavyRainDates.length;
    el.extremeEventsPanel.appendChild(rainP);

    var windP = document.createElement("p");
    windP.textContent = "High wind days (≥40km/h): " + ee.highWindDates.length;
    el.extremeEventsPanel.appendChild(windP);
  }

  function fmtNum(v, digits) {
    return typeof v === "number" && !isNaN(v) ? v.toFixed(digits) : "—";
  }

  function renderYearTable() {
    var rows = state.yearSummary.slice();
    var key = state.yearSort.key;
    var dir = state.yearSort.dir === "asc" ? 1 : -1;
    rows.sort(function (a, b) {
      var av = a[key], bv = b[key];
      if (av === bv) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      return av > bv ? dir : -dir;
    });

    clearChildren(el.yearTableBody);
    rows.forEach(function (y) {
      var tr = document.createElement("tr");
      var cells = [
        y.year,
        fmtNum(y.avgTempMax, 1),
        fmtNum(y.avgTempMin, 1),
        fmtNum(y.totalPrecip, 0),
        String(y.heatWaveCount),
        String(y.coldSnapCount),
        String(y.heavyRainDayCount),
        String(y.highWindDayCount),
        y.suitablePct === null ? "—" : y.suitablePct.toFixed(1) + "%"
      ];
      cells.forEach(function (val) {
        var td = document.createElement("td");
        td.textContent = String(val);
        tr.appendChild(td);
      });
      el.yearTableBody.appendChild(tr);
    });
  }

  function handleTableSort(evt) {
    var th = evt.target.closest ? evt.target.closest("th[data-sort]") : null;
    if (!th) return;
    var key = th.getAttribute("data-sort");
    if (state.yearSort.key === key) {
      state.yearSort.dir = state.yearSort.dir === "asc" ? "desc" : "asc";
    } else {
      state.yearSort = { key: key, dir: "asc" };
    }
    if (state.yearSummary) renderYearTable();
  }

  // -- CSV export ---------------------------------------------------------
  function triggerDownload(filename, content, mime) {
    var blob = new Blob([content], { type: mime || "text/csv" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  function exportDailyCsv() {
    if (!state.dailyFiltered) return;
    var d = state.dailyFiltered;
    var headers = ["date", "temp_max_c", "temp_min_c", "precipitation_mm", "wind_speed_max_kmh"];
    var rows = d.time.map(function (t, i) {
      return [t, d.temperature_2m_max[i], d.temperature_2m_min[i], d.precipitation_sum[i], d.wind_speed_10m_max[i]];
    });
    var csv = window.Almanac.formatCSV(headers, rows);
    triggerDownload("almanac-daily-" + locationSlug() + ".csv", csv);
  }

  function exportSummaryCsv() {
    if (!state.yearSummary) return;
    var headers = [
      "year", "avg_temp_max_c", "avg_temp_min_c", "total_precip_mm",
      "heat_wave_events", "cold_snap_events", "heavy_rain_days", "high_wind_days", "pct_suitable_days"
    ];
    var rows = state.yearSummary.map(function (y) {
      return [y.year, y.avgTempMax, y.avgTempMin, y.totalPrecip, y.heatWaveCount, y.coldSnapCount, y.heavyRainDayCount, y.highWindDayCount, y.suitablePct];
    });
    var csv = window.Almanac.formatCSV(headers, rows);
    triggerDownload("almanac-summary-" + locationSlug() + ".csv", csv);
  }

  function locationSlug() {
    if (!state.selectedLocation) return "export";
    return state.selectedLocation.name.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  }

  // -- Wire up events -------------------------------------------------------
  function init() {
    populateMonthSelects();
    applyDefaultYearRange();
    restoreLastSettings();
    renderRecentLocations();

    el.searchBtn.addEventListener("click", doSearch);
    el.searchInput.addEventListener("keydown", function (evt) {
      if (evt.key === "Enter") doSearch();
    });
    el.activityPreset.addEventListener("change", function () {
      toggleCustomThresholds();
      if (state.dailyFiltered) processAndRender();
    });
    [el.customTempMin, el.customTempMax, el.customWind, el.customPrecip].forEach(function (input) {
      input.addEventListener("change", function () {
        if (state.dailyFiltered) processAndRender();
      });
    });
    el.fetchBtn.addEventListener("click", doFetchHistorical);
    el.yearChartVariable.addEventListener("change", renderYearChart);
    document.getElementById("yearTable").querySelector("thead").addEventListener("click", handleTableSort);
    el.exportDailyCsvBtn.addEventListener("click", exportDailyCsv);
    el.exportSummaryCsvBtn.addEventListener("click", exportSummaryCsv);
  }

  init();

  // Exposed for tests only — read-only introspection, no test-only branching in app logic.
  window.__almanacTestState = state;
})();
