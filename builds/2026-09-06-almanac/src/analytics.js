/*
 * Almanac — deterministic analytics engine.
 * Pure functions only: no DOM, no fetch, no globals besides the single
 * window.Almanac export below. Every function here is unit-tested in
 * tests/analytics.spec.js via page.evaluate().
 *
 * Classic script (no ES module syntax) so index.html can be opened directly
 * via file:// without a server or bundler.
 */
(function (global) {
  "use strict";

  var ACTIVITY_PRESETS = {
    running: { label: "Running", tempMinC: 0, tempMaxC: 22, maxWindKmh: 30, maxPrecipMm: 2 },
    golf: { label: "Golf", tempMinC: 12, tempMaxC: 28, maxWindKmh: 25, maxPrecipMm: 1 },
    boating: { label: "Boating", tempMinC: 15, tempMaxC: 32, maxWindKmh: 20, maxPrecipMm: 1 }
  };

  var DEFAULT_THRESHOLDS = {
    heatMaxC: 30,
    heatWaveMinDays: 3,
    coldMinC: -10,
    coldSnapMinDays: 2,
    heavyRainMm: 25,
    highWindKmh: 40
  };

  function isNum(v) {
    return typeof v === "number" && !isNaN(v);
  }

  function validNumbers(arr) {
    var out = [];
    for (var i = 0; i < arr.length; i++) {
      if (isNum(arr[i])) out.push(arr[i]);
    }
    return out;
  }

  function computePercentile(sortedAsc, p) {
    if (!sortedAsc || sortedAsc.length === 0) return null;
    if (sortedAsc.length === 1) return sortedAsc[0];
    var idx = (p / 100) * (sortedAsc.length - 1);
    var lo = Math.floor(idx);
    var hi = Math.ceil(idx);
    if (lo === hi) return sortedAsc[lo];
    var frac = idx - lo;
    return sortedAsc[lo] + (sortedAsc[hi] - sortedAsc[lo]) * frac;
  }

  function computePercentiles(values, percentileList) {
    var plist = percentileList || [10, 25, 50, 75, 90];
    var valid = validNumbers(values);
    if (valid.length === 0) return null;
    var sorted = valid.slice().sort(function (a, b) {
      return a - b;
    });
    var result = { count: valid.length };
    var sum = 0;
    for (var i = 0; i < valid.length; i++) sum += valid[i];
    result.mean = sum / valid.length;
    for (var j = 0; j < plist.length; j++) {
      result["p" + plist[j]] = computePercentile(sorted, plist[j]);
    }
    return result;
  }

  function findRuns(boolArray) {
    var runs = [];
    var i = 0;
    while (i < boolArray.length) {
      if (boolArray[i]) {
        var start = i;
        while (i < boolArray.length && boolArray[i]) i++;
        runs.push({ startIndex: start, length: i - start });
      } else {
        i++;
      }
    }
    return runs;
  }

  function extractYear(dateStr) {
    return dateStr.slice(0, 4);
  }

  function extractMonth(dateStr) {
    return parseInt(dateStr.slice(5, 7), 10);
  }

  function dailyLength(daily) {
    return daily && daily.time ? daily.time.length : 0;
  }

  function detectExtremeEvents(daily, thresholds) {
    var t = thresholds || DEFAULT_THRESHOLDS;
    var n = dailyLength(daily);
    var heatBool = [];
    var coldBool = [];
    var rainBool = [];
    var windBool = [];
    for (var i = 0; i < n; i++) {
      var tMax = daily.temperature_2m_max[i];
      var tMin = daily.temperature_2m_min[i];
      var precip = daily.precipitation_sum[i];
      var wind = daily.wind_speed_10m_max[i];
      heatBool.push(isNum(tMax) && tMax >= t.heatMaxC);
      coldBool.push(isNum(tMin) && tMin <= t.coldMinC);
      rainBool.push(isNum(precip) && precip >= t.heavyRainMm);
      windBool.push(isNum(wind) && wind >= t.highWindKmh);
    }

    function toEvents(bool, minLen) {
      var runs = findRuns(bool).filter(function (r) {
        return r.length >= minLen;
      });
      return runs.map(function (r) {
        return {
          startIndex: r.startIndex,
          length: r.length,
          startDate: daily.time[r.startIndex],
          endDate: daily.time[r.startIndex + r.length - 1]
        };
      });
    }

    var heavyRainDates = [];
    var highWindDates = [];
    for (var k = 0; k < n; k++) {
      if (rainBool[k]) heavyRainDates.push(daily.time[k]);
      if (windBool[k]) highWindDates.push(daily.time[k]);
    }

    return {
      heatWaveEvents: toEvents(heatBool, t.heatWaveMinDays),
      coldSnapEvents: toEvents(coldBool, t.coldSnapMinDays),
      heavyRainDates: heavyRainDates,
      highWindDates: highWindDates
    };
  }

  function computeSuitability(daily, preset) {
    var n = dailyLength(daily);
    var perYear = {};
    var totalDays = 0;
    var suitableDays = 0;
    for (var i = 0; i < n; i++) {
      var tMax = daily.temperature_2m_max[i];
      var tMin = daily.temperature_2m_min[i];
      var precip = daily.precipitation_sum[i];
      var wind = daily.wind_speed_10m_max[i];
      if (!isNum(tMax) || !isNum(tMin) || !isNum(precip) || !isNum(wind)) continue;
      totalDays++;
      var year = extractYear(daily.time[i]);
      if (!perYear[year]) perYear[year] = { totalDays: 0, suitableDays: 0 };
      perYear[year].totalDays++;
      var suitable =
        tMax <= preset.tempMaxC &&
        tMin >= preset.tempMinC &&
        wind <= preset.maxWindKmh &&
        precip <= preset.maxPrecipMm;
      if (suitable) {
        suitableDays++;
        perYear[year].suitableDays++;
      }
    }
    var years = Object.keys(perYear);
    for (var y = 0; y < years.length; y++) {
      var rec = perYear[years[y]];
      rec.pct = rec.totalDays ? (100 * rec.suitableDays) / rec.totalDays : null;
    }
    return {
      totalDays: totalDays,
      suitableDays: suitableDays,
      pct: totalDays ? (100 * suitableDays) / totalDays : null,
      perYear: perYear
    };
  }

  function computeYearSummary(daily, extremeEvents, suitability) {
    var n = dailyLength(daily);
    var yearIndices = {};
    for (var i = 0; i < n; i++) {
      var year = extractYear(daily.time[i]);
      if (!yearIndices[year]) yearIndices[year] = [];
      yearIndices[year].push(i);
    }
    var years = Object.keys(yearIndices).sort();

    function countEventsInYear(events, year) {
      var c = 0;
      for (var e = 0; e < events.length; e++) {
        if (extractYear(events[e].startDate) === year) c++;
      }
      return c;
    }

    function countDatesInYear(dates, year) {
      var c = 0;
      for (var d = 0; d < dates.length; d++) {
        if (extractYear(dates[d]) === year) c++;
      }
      return c;
    }

    return years.map(function (year) {
      var idxs = yearIndices[year];
      var tMaxVals = [];
      var tMinVals = [];
      var precipVals = [];
      for (var k = 0; k < idxs.length; k++) {
        var idx = idxs[k];
        if (isNum(daily.temperature_2m_max[idx])) tMaxVals.push(daily.temperature_2m_max[idx]);
        if (isNum(daily.temperature_2m_min[idx])) tMinVals.push(daily.temperature_2m_min[idx]);
        if (isNum(daily.precipitation_sum[idx])) precipVals.push(daily.precipitation_sum[idx]);
      }
      var avgTempMax = tMaxVals.length ? tMaxVals.reduce(function (a, b) { return a + b; }, 0) / tMaxVals.length : null;
      var avgTempMin = tMinVals.length ? tMinVals.reduce(function (a, b) { return a + b; }, 0) / tMinVals.length : null;
      var totalPrecip = precipVals.reduce(function (a, b) { return a + b; }, 0);
      var suit = (suitability && suitability.perYear && suitability.perYear[year]) || null;
      return {
        year: year,
        totalDays: idxs.length,
        avgTempMax: avgTempMax,
        avgTempMin: avgTempMin,
        totalPrecip: totalPrecip,
        heatWaveCount: countEventsInYear(extremeEvents.heatWaveEvents, year),
        coldSnapCount: countEventsInYear(extremeEvents.coldSnapEvents, year),
        heavyRainDayCount: countDatesInYear(extremeEvents.heavyRainDates, year),
        highWindDayCount: countDatesInYear(extremeEvents.highWindDates, year),
        suitableDays: suit ? suit.suitableDays : 0,
        suitablePct: suit ? suit.pct : null
      };
    });
  }

  function computeMonthlyClimatology(daily) {
    var n = dailyLength(daily);
    var byMonth = {};
    for (var m = 1; m <= 12; m++) {
      byMonth[m] = { tempMax: [], tempMin: [], wind: [] };
    }
    var monthlyPrecipTotals = {}; // "year-month" -> total
    for (var i = 0; i < n; i++) {
      var month = extractMonth(daily.time[i]);
      var year = extractYear(daily.time[i]);
      if (isNum(daily.temperature_2m_max[i])) byMonth[month].tempMax.push(daily.temperature_2m_max[i]);
      if (isNum(daily.temperature_2m_min[i])) byMonth[month].tempMin.push(daily.temperature_2m_min[i]);
      if (isNum(daily.wind_speed_10m_max[i])) byMonth[month].wind.push(daily.wind_speed_10m_max[i]);
      if (isNum(daily.precipitation_sum[i])) {
        var key = year + "-" + month;
        monthlyPrecipTotals[key] = (monthlyPrecipTotals[key] || 0) + daily.precipitation_sum[i];
      }
    }
    var result = [];
    for (var mm = 1; mm <= 12; mm++) {
      var precipKeysForMonth = Object.keys(monthlyPrecipTotals).filter(function (k) {
        return parseInt(k.split("-")[1], 10) === mm;
      });
      var precipVals = precipKeysForMonth.map(function (k) {
        return monthlyPrecipTotals[k];
      });
      var avgMonthlyPrecipMm = precipVals.length
        ? precipVals.reduce(function (a, b) { return a + b; }, 0) / precipVals.length
        : null;
      var windVals = byMonth[mm].wind;
      var avgWindMax = windVals.length
        ? windVals.reduce(function (a, b) { return a + b; }, 0) / windVals.length
        : null;
      result.push({
        month: mm,
        tempMax: computePercentiles(byMonth[mm].tempMax, [10, 25, 50, 75, 90]),
        tempMin: computePercentiles(byMonth[mm].tempMin, [10, 25, 50, 75, 90]),
        avgMonthlyPrecipMm: avgMonthlyPrecipMm,
        avgWindMax: avgWindMax
      });
    }
    return result;
  }

  function filterByMonthWindow(daily, startMonth, endMonth) {
    var n = dailyLength(daily);
    var keepIdx = [];
    for (var i = 0; i < n; i++) {
      var m = extractMonth(daily.time[i]);
      var inRange =
        startMonth <= endMonth ? m >= startMonth && m <= endMonth : m >= startMonth || m <= endMonth;
      if (inRange) keepIdx.push(i);
    }
    var out = { time: [], temperature_2m_max: [], temperature_2m_min: [], precipitation_sum: [], wind_speed_10m_max: [] };
    for (var k = 0; k < keepIdx.length; k++) {
      var idx = keepIdx[k];
      out.time.push(daily.time[idx]);
      out.temperature_2m_max.push(daily.temperature_2m_max[idx]);
      out.temperature_2m_min.push(daily.temperature_2m_min[idx]);
      out.precipitation_sum.push(daily.precipitation_sum[idx]);
      out.wind_speed_10m_max.push(daily.wind_speed_10m_max[idx]);
    }
    return out;
  }

  function csvEscape(field) {
    var s = field === null || field === undefined ? "" : String(field);
    if (/[",\n\r]/.test(s)) {
      return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
  }

  function formatCSV(headers, rows) {
    var lines = [headers.map(csvEscape).join(",")];
    for (var i = 0; i < rows.length; i++) {
      lines.push(rows[i].map(csvEscape).join(","));
    }
    return lines.join("\r\n");
  }

  global.Almanac = {
    ACTIVITY_PRESETS: ACTIVITY_PRESETS,
    DEFAULT_THRESHOLDS: DEFAULT_THRESHOLDS,
    isNum: isNum,
    validNumbers: validNumbers,
    computePercentile: computePercentile,
    computePercentiles: computePercentiles,
    findRuns: findRuns,
    extractYear: extractYear,
    extractMonth: extractMonth,
    detectExtremeEvents: detectExtremeEvents,
    computeSuitability: computeSuitability,
    computeYearSummary: computeYearSummary,
    computeMonthlyClimatology: computeMonthlyClimatology,
    filterByMonthWindow: filterByMonthWindow,
    formatCSV: formatCSV
  };
})(typeof window !== "undefined" ? window : this);
