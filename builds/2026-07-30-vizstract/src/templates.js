/* Vizstract — declarative layout templates, one per study-design type.
   Each template's `body` array is a generic list of regions (iconBox,
   connector, iconBadge) that render.js interprets identically regardless
   of which template produced them — the per-design-type differentiation
   lives entirely in the region data below, not in render.js. */
(function () {
  "use strict";
  window.Vizstract = window.Vizstract || {};

  var DIRECTION_ICON = {
    increase: "arrowUp",
    decrease: "arrowDown",
    none: "dash",
    mixed: "zigzag"
  };

  function directionIcon(data) {
    return DIRECTION_ICON[data.effectDirection] || "dash";
  }

  var TEMPLATES = {
    compare: {
      key: "compare",
      label: "Comparison of Groups",
      body: [
        { kind: "iconBox", x: 40, y: 128, w: 180, h: 190, icon: "group", title: "Groups", valueKey: "ivLabel" },
        { kind: "connector", x1: 220, y1: 223, x2: 420, y2: 223, arrow: false, dashed: false },
        { kind: "iconBadge", x: 293, y: 196, w: 54, h: 54, icon: "scaleBalance", circleBg: true },
        { kind: "iconBadge", x: 384, y: 200, w: 30, h: 30, icon: directionIcon, circleBg: false },
        { kind: "iconBox", x: 420, y: 128, w: 180, h: 190, icon: "barChart", title: "Measured", valueKey: "dvLabel" }
      ]
    },

    correlate: {
      key: "correlate",
      label: "Correlational / Relationship",
      body: [
        { kind: "iconBox", x: 40, y: 148, w: 170, h: 150, icon: "lineChart", title: "Variable A", valueKey: "ivLabel" },
        { kind: "connector", x1: 210, y1: 223, x2: 430, y2: 223, arrow: false, dashed: true },
        { kind: "iconBadge", x: 272, y: 175, w: 96, h: 96, icon: directionIcon, circleBg: true },
        { kind: "iconBox", x: 430, y: 148, w: 170, h: 150, icon: "lineChart", title: "Variable B", valueKey: "dvLabel" }
      ]
    },

    process: {
      key: "process",
      label: "Process / Timeline / Intervention",
      body: [
        { kind: "iconBox", x: 24, y: 168, w: 170, h: 132, icon: "clock", title: "Baseline", valueKey: null },
        { kind: "connector", x1: 194, y1: 234, x2: 218, y2: 234, arrow: true, dashed: false },
        { kind: "iconBox", x: 218, y: 168, w: 168, h: 132, icon: "lightbulb", title: "Intervention", valueKey: "ivLabel" },
        { kind: "connector", x1: 386, y1: 234, x2: 426, y2: 234, arrow: true, dashed: false },
        { kind: "iconBadge", x: 389, y: 213, w: 36, h: 36, icon: directionIcon, circleBg: true },
        { kind: "iconBox", x: 426, y: 168, w: 190, h: 132, icon: "barChart", title: "Outcome", valueKey: "dvLabel" }
      ]
    },

    survey: {
      key: "survey",
      label: "Survey / Cross-Sectional",
      body: [
        { kind: "iconBox", x: 32, y: 186, w: 156, h: 110, icon: "magnifier", title: "Predictor", valueKey: "ivLabel" },
        { kind: "connector", x1: 188, y1: 241, x2: 232, y2: 213, arrow: false, dashed: false },
        { kind: "iconBox", x: 232, y: 150, w: 176, h: 182, icon: "clipboard", title: "Sample", valueKey: null },
        { kind: "connector", x1: 408, y1: 213, x2: 452, y2: 241, arrow: false, dashed: false },
        { kind: "iconBox", x: 452, y: 186, w: 156, h: 110, icon: "barChart", title: "Outcome", valueKey: "dvLabel" },
        { kind: "iconBadge", x: 546, y: 150, w: 26, h: 26, icon: directionIcon, circleBg: true }
      ]
    },

    prepost: {
      key: "prepost",
      label: "Before-After / Pre-Post",
      body: [
        { kind: "iconBox", x: 32, y: 138, w: 216, h: 184, icon: "calendar", title: "Before", valueKey: "ivLabel" },
        { kind: "connector", x1: 248, y1: 230, x2: 392, y2: 230, arrow: false, dashed: false },
        { kind: "iconBadge", x: 264, y: 174, w: 112, h: 112, icon: directionIcon, circleBg: true },
        { kind: "iconBox", x: 392, y: 138, w: 216, h: 184, icon: "calendar", title: "After", valueKey: "dvLabel" }
      ]
    }
  };

  var ORDER = ["compare", "correlate", "process", "survey", "prepost"];

  window.Vizstract.Templates = {
    all: TEMPLATES,
    order: ORDER,
    get: function (key) {
      return TEMPLATES[key] || TEMPLATES.compare;
    },
    directionIcon: directionIcon
  };
})();
