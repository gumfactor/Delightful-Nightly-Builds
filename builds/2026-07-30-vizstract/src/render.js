/* Vizstract — SVG layout engine: text measurement/fitting, theme palette,
   and the generic region interpreter that turns a template's declarative
   body regions + the current form data into a full SVG document string. */
(function () {
  "use strict";
  window.Vizstract = window.Vizstract || {};

  var FONT_FAMILY = "Arial, Helvetica, sans-serif";
  var CANVAS_W = 640;
  var CANVAS_H = 480;

  var THEMES = {
    indigo: { bg: "#ffffff", cardBg: "#eef1fd", cardBorder: "#c7d2fe", textPrimary: "#1e1b4b", textMuted: "#4c4f6b", accent: "#4338ca", accentSoft: "#e0e7ff", calloutBg: "#f5f3ff", calloutBorder: "#ddd6fe" },
    teal: { bg: "#ffffff", cardBg: "#e6f7f5", cardBorder: "#99e0d6", textPrimary: "#032e2b", textMuted: "#3f5654", accent: "#0f766e", accentSoft: "#ccfbf1", calloutBg: "#effdfa", calloutBorder: "#99e0d6" },
    amber: { bg: "#ffffff", cardBg: "#fef3e2", cardBorder: "#f3cf8a", textPrimary: "#3a2404", textMuted: "#5c4a2c", accent: "#b45309", accentSoft: "#fde8c8", calloutBg: "#fffaf0", calloutBorder: "#f3cf8a" },
    crimson: { bg: "#ffffff", cardBg: "#fdeaec", cardBorder: "#f2b7bd", textPrimary: "#450a12", textMuted: "#6b3a3f", accent: "#b91c3c", accentSoft: "#fbd0d7", calloutBg: "#fff3f4", calloutBorder: "#f2b7bd" },
    slate: { bg: "#ffffff", cardBg: "#eef1f5", cardBorder: "#c7d0dc", textPrimary: "#1c2530", textMuted: "#4a5568", accent: "#334155", accentSoft: "#dde3ea", calloutBg: "#f7f9fb", calloutBorder: "#c7d0dc" }
  };

  var DIRECTIONS = ["increase", "decrease", "none", "mixed"];

  function escapeXml(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&apos;");
  }

  var _measureCtx = null;
  function measureCtx() {
    if (!_measureCtx) {
      _measureCtx = document.createElement("canvas").getContext("2d");
    }
    return _measureCtx;
  }

  function measureWidth(text, fontSize, weight, family) {
    var ctx = measureCtx();
    ctx.font = (weight || 400) + " " + fontSize + "px " + (family || FONT_FAMILY);
    return ctx.measureText(String(text)).width;
  }

  function wrapText(text, maxWidth, fontSize, weight, family) {
    var words = String(text || "").split(/\s+/).filter(Boolean);
    if (!words.length) return [""];
    var lines = [];
    var current = "";
    for (var i = 0; i < words.length; i++) {
      var word = words[i];
      var test = current ? current + " " + word : word;
      if (measureWidth(test, fontSize, weight, family) <= maxWidth) {
        current = test;
        continue;
      }
      if (current) lines.push(current);
      if (measureWidth(word, fontSize, weight, family) > maxWidth) {
        var chunk = "";
        for (var c = 0; c < word.length; c++) {
          var testChunk = chunk + word[c];
          if (measureWidth(testChunk, fontSize, weight, family) <= maxWidth) {
            chunk = testChunk;
          } else {
            if (chunk) lines.push(chunk);
            chunk = word[c];
          }
        }
        current = chunk;
      } else {
        current = word;
      }
    }
    if (current) lines.push(current);
    return lines;
  }

  function fitText(text, boxW, boxH, opts) {
    opts = opts || {};
    var maxFont = opts.maxFontSize || 18;
    var minFont = opts.minFontSize || 10;
    var lineHeightRatio = opts.lineHeight || 1.25;
    var weight = opts.weight || 400;
    var family = opts.family || FONT_FAMILY;
    var maxLinesCap = opts.maxLines || Infinity;

    var fontSize = maxFont;
    var lines;
    while (fontSize >= minFont) {
      lines = wrapText(text, boxW, fontSize, weight, family);
      var totalH = lines.length * fontSize * lineHeightRatio;
      if (lines.length <= maxLinesCap && totalH <= boxH) {
        return { lines: lines, fontSize: fontSize, truncated: false };
      }
      fontSize -= 1;
    }

    fontSize = minFont;
    lines = wrapText(text, boxW, fontSize, weight, family);
    var maxLinesThatFit = Math.max(1, Math.min(maxLinesCap, Math.floor(boxH / (fontSize * lineHeightRatio))));
    if (lines.length > maxLinesThatFit) {
      var kept = lines.slice(0, maxLinesThatFit);
      var last = kept[maxLinesThatFit - 1];
      while (last.length > 0 && measureWidth(last + "…", fontSize, weight, family) > boxW) {
        last = last.slice(0, -1);
      }
      kept[maxLinesThatFit - 1] = last + "…";
      lines = kept;
    }
    return { lines: lines, fontSize: fontSize, truncated: true };
  }

  function textLines(x, y, lines, fontSize, opts) {
    opts = opts || {};
    var lineHeight = fontSize * (opts.lineHeight || 1.25);
    var anchor = opts.align === "center" ? "middle" : "start";
    var out = '<text x="' + x + '" y="' + y + '" font-size="' + fontSize + '" font-weight="' + (opts.weight || 400) +
      '" fill="' + opts.color + '" text-anchor="' + anchor + '" font-family="' + FONT_FAMILY + '">';
    for (var i = 0; i < lines.length; i++) {
      out += '<tspan x="' + x + '" dy="' + (i === 0 ? 0 : lineHeight) + '">' + escapeXml(lines[i]) + "</tspan>";
    }
    out += "</text>";
    return out;
  }

  function iconGroup(name, x, y, size, color) {
    return '<g transform="translate(' + x + "," + y + ") scale(" + size / 24 + ')" style="color:' + color + '">' +
      window.Vizstract.Icons.markup(name) + "</g>";
  }

  function renderTitle(data, theme) {
    var x = 24, y = 16, w = 592, h = 54;
    var fit = fitText(data.title || "Untitled Study", w, h, { maxFontSize: 24, minFontSize: 14, weight: 800, maxLines: 2 });
    return textLines(x, y + fit.fontSize, fit.lines, fit.fontSize, { weight: 800, align: "left", color: theme.textPrimary, lineHeight: 1.15 });
  }

  function renderSampleBadge(data, theme) {
    var parts = [];
    if (data.population) parts.push(data.population);
    if (data.sampleSize) parts.push("N = " + data.sampleSize);
    var text = parts.join(" · ");
    if (!text) return "";
    var x = 24, y = 76, w = 592, h = 22;
    var fit = fitText(text, w, h, { maxFontSize: 14, minFontSize: 11, weight: 600, maxLines: 1 });
    return textLines(x, y + fit.fontSize, fit.lines, fit.fontSize, { weight: 600, align: "left", color: theme.textMuted, lineHeight: 1 });
  }

  function renderIconBox(region, data, theme) {
    var icon = typeof region.icon === "function" ? region.icon(data) : region.icon;
    var pad = 14;
    var iconSize = 34;
    var out = '<rect x="' + region.x + '" y="' + region.y + '" width="' + region.w + '" height="' + region.h +
      '" rx="14" fill="' + theme.cardBg + '" stroke="' + theme.cardBorder + '" stroke-width="1.5"/>';
    var iconX = region.x + region.w / 2 - iconSize / 2;
    var iconY = region.y + 16;
    out += iconGroup(icon, iconX, iconY, iconSize, theme.accent);
    var titleY = iconY + iconSize + 18;
    out += textLines(region.x + region.w / 2, titleY, [region.title], 12, { weight: 700, align: "center", color: theme.textMuted, lineHeight: 1.1 });
    var value = region.valueKey ? (data[region.valueKey] || "—") : null;
    if (value) {
      var valBoxY = titleY + 8;
      var valBoxH = Math.max(region.y + region.h - valBoxY - 12, 20);
      var fit = fitText(value, region.w - pad * 2, valBoxH, { maxFontSize: 15, minFontSize: 10, weight: 600, maxLines: 3 });
      out += textLines(region.x + region.w / 2, valBoxY + fit.fontSize, fit.lines, fit.fontSize, { weight: 600, align: "center", color: theme.textPrimary, lineHeight: 1.25 });
    }
    return out;
  }

  function renderConnector(region, theme) {
    var stroke = theme.textMuted;
    var dash = region.dashed ? ' stroke-dasharray="6 5"' : "";
    var out = '<line x1="' + region.x1 + '" y1="' + region.y1 + '" x2="' + region.x2 + '" y2="' + region.y2 +
      '" stroke="' + stroke + '" stroke-width="2"' + dash + "/>";
    if (region.arrow) {
      var angle = Math.atan2(region.y2 - region.y1, region.x2 - region.x1);
      var size = 8;
      var p1x = region.x2, p1y = region.y2;
      var p2x = region.x2 - size * Math.cos(angle - Math.PI / 6), p2y = region.y2 - size * Math.sin(angle - Math.PI / 6);
      var p3x = region.x2 - size * Math.cos(angle + Math.PI / 6), p3y = region.y2 - size * Math.sin(angle + Math.PI / 6);
      out += '<polygon points="' + p1x + "," + p1y + " " + p2x + "," + p2y + " " + p3x + "," + p3y + '" fill="' + stroke + '"/>';
    }
    return out;
  }

  function renderIconBadge(region, data, theme) {
    var icon = typeof region.icon === "function" ? region.icon(data) : region.icon;
    var out = "";
    if (region.circleBg) {
      var cx = region.x + region.w / 2, cy = region.y + region.h / 2, r = region.w / 2;
      out += '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + theme.accentSoft + '" stroke="' + theme.accent + '" stroke-width="1.5"/>';
    }
    var pad = region.circleBg ? region.w * 0.28 : 0;
    var size = region.w - pad * 2;
    out += iconGroup(icon, region.x + pad, region.y + pad, size, theme.accent);
    return out;
  }

  function renderCallout(data, theme) {
    var x = 24, y = 372, w = 592, h = 88;
    var iconSize = 26;
    var out = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="14" fill="' + theme.calloutBg +
      '" stroke="' + theme.calloutBorder + '" stroke-width="1.5"/>';
    out += iconGroup(window.Vizstract.Templates.directionIcon(data), x + w - iconSize - 16, y + 14, iconSize, theme.accent);
    var textW = w - 32 - iconSize - 12;
    var finding = data.headlineFinding || "Add a headline finding to see it here.";
    var fit = fitText(finding, textW, h - 40, { maxFontSize: 16, minFontSize: 11, weight: 600, maxLines: 3 });
    out += textLines(x + 16, y + 22, fit.lines, fit.fontSize, { weight: 600, align: "left", color: theme.textPrimary, lineHeight: 1.3 });
    if (data.statDetail) {
      var statFit = fitText(data.statDetail, w - 32, 18, { maxFontSize: 12, minFontSize: 10, weight: 500, maxLines: 1 });
      out += textLines(x + 16, y + h - 14, statFit.lines, statFit.fontSize, { weight: 500, align: "left", color: theme.textMuted, lineHeight: 1 });
    }
    return out;
  }

  function normalizeData(d) {
    d = d || {};
    return {
      title: d.title || "",
      designType: window.Vizstract.Templates.all[d.designType] ? d.designType : "compare",
      population: d.population || "",
      ivLabel: d.ivLabel || "",
      dvLabel: d.dvLabel || "",
      sampleSize: d.sampleSize || "",
      headlineFinding: d.headlineFinding || "",
      effectDirection: DIRECTIONS.indexOf(d.effectDirection) >= 0 ? d.effectDirection : "none",
      statDetail: d.statDetail || "",
      theme: THEMES[d.theme] ? d.theme : "indigo"
    };
  }

  function renderSVG(rawData) {
    var data = normalizeData(rawData);
    var theme = THEMES[data.theme];
    var tpl = window.Vizstract.Templates.get(data.designType);
    var out = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + CANVAS_W + " " + CANVAS_H + '" width="' +
      CANVAS_W + '" height="' + CANVAS_H + '" font-family="' + FONT_FAMILY + '">';
    out += '<rect x="0" y="0" width="' + CANVAS_W + '" height="' + CANVAS_H + '" fill="' + theme.bg + '"/>';
    out += renderTitle(data, theme);
    out += renderSampleBadge(data, theme);
    for (var i = 0; i < tpl.body.length; i++) {
      var region = tpl.body[i];
      if (region.kind === "iconBox") out += renderIconBox(region, data, theme);
      else if (region.kind === "connector") out += renderConnector(region, theme);
      else if (region.kind === "iconBadge") out += renderIconBadge(region, data, theme);
    }
    out += renderCallout(data, theme);
    out += "</svg>";
    return out;
  }

  window.Vizstract.Render = {
    renderSVG: renderSVG,
    normalizeData: normalizeData,
    fitText: fitText,
    wrapText: wrapText,
    measureWidth: measureWidth,
    escapeXml: escapeXml,
    THEMES: THEMES,
    CANVAS_W: CANVAS_W,
    CANVAS_H: CANVAS_H
  };
})();
