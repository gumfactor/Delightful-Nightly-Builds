/* Vizstract — hand-authored inline icon library.
   Each icon is a string of SVG child markup in a 0..24 x 0..24 coordinate
   space, meant to be wrapped by render.js in a <g> with its own transform
   and a `style="color:..."` so `stroke="currentColor"` picks up the theme. */
(function () {
  "use strict";
  window.Vizstract = window.Vizstract || {};

  var STROKE = 'fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"';

  var ICONS = {
    person:
      '<circle cx="12" cy="7.5" r="3.6" ' + STROKE + '/>' +
      '<path d="M4.5 20.5c0-4.14 3.36-7.5 7.5-7.5s7.5 3.36 7.5 7.5" ' + STROKE + '/>',

    group:
      '<circle cx="8.5" cy="8" r="3" ' + STROKE + '/>' +
      '<circle cx="16.5" cy="9" r="2.4" ' + STROKE + '/>' +
      '<path d="M2.5 20.5c0-3.6 2.7-6.5 6-6.5s6 2.9 6 6.5" ' + STROKE + '/>' +
      '<path d="M13.8 20.5c.25-2.9 2.2-5.1 4.7-5.1s4.35 2.1 4.6 5.1" ' + STROKE + '/>',

    brain:
      '<path d="M9.2 4.2C6.6 4.2 4.6 6.2 4.6 8.7c0 .9.25 1.75.7 2.45-.55.75-.9 1.7-.9 2.75 0 2.4 1.9 4.35 4.3 4.4.3 1.35 1.5 2.35 2.9 2.35s2.6-1 2.9-2.35c2.4-.05 4.3-2 4.3-4.4 0-1.05-.35-2-.9-2.75.45-.7.7-1.55.7-2.45 0-2.5-2-4.5-4.5-4.5-.85 0-1.65.25-2.35.65-.7-.4-1.5-.65-2.35-.65z" ' + STROKE + '/>' +
      '<path d="M12 6.7v11.3M9 9.4h1.1M14 9.4h1.1M9 13.4h1.1M14 13.4h1.1" ' + STROKE + '/>',

    arrowRight:
      '<path d="M4 12h15.2M14.5 6.5 20 12l-5.5 5.5" ' + STROKE + '/>',

    arrowLeft:
      '<path d="M20 12H4.8M9.5 6.5 4 12l5.5 5.5" ' + STROKE + '/>',

    arrowUp:
      '<path d="M12 20V4.8M6.5 9.5 12 4l5.5 5.5" ' + STROKE + '/>',

    arrowDown:
      '<path d="M12 4v15.2M6.5 14.5 12 20l5.5-5.5" ' + STROKE + '/>',

    arrowUpRight:
      '<path d="M5 19 19 5M9 5h10v10" ' + STROKE + '/>',

    arrowDownRight:
      '<path d="M5 5l14 14M19 9V19H9" ' + STROKE + '/>',

    zigzag:
      '<path d="M3 12l4-5 4 8 4-8 4 8 2-3" ' + STROKE + '/>',

    dash:
      '<path d="M4 12h16" ' + STROKE + '/>',

    barChart:
      '<path d="M4 20V10M11 20V4M18 20v-7" ' + STROKE + '/>' +
      '<path d="M2.5 20.5h19" ' + STROKE + '/>',

    lineChart:
      '<path d="M3 17l5-6 4 3 6-8 3 3.5" ' + STROKE + '/>' +
      '<circle cx="8" cy="11" r="1" fill="currentColor" stroke="none"/>' +
      '<circle cx="12" cy="14" r="1" fill="currentColor" stroke="none"/>' +
      '<circle cx="18" cy="6" r="1" fill="currentColor" stroke="none"/>',

    clock:
      '<circle cx="12" cy="12" r="8.5" ' + STROKE + '/>' +
      '<path d="M12 7.2V12l3.4 2" ' + STROKE + '/>',

    calendar:
      '<rect x="3.5" y="5" width="17" height="15" rx="1.6" ' + STROKE + '/>' +
      '<path d="M3.5 9.5h17M8 3v3.6M16 3v3.6M7.5 13h2M11 13h2M14.5 13h2M7.5 16.4h2M11 16.4h2" ' + STROKE + '/>',

    clipboard:
      '<rect x="5" y="4.5" width="14" height="17" rx="1.5" ' + STROKE + '/>' +
      '<rect x="9" y="2.8" width="6" height="3.2" rx="0.8" ' + STROKE + '/>' +
      '<path d="M8 11h8M8 14.4h8M8 17.8h5" ' + STROKE + '/>',

    magnifier:
      '<circle cx="10.5" cy="10.5" r="6.2" ' + STROKE + '/>' +
      '<path d="M15.2 15.2 20.5 20.5" ' + STROKE + '/>',

    scaleBalance:
      '<path d="M12 3v16.5M8 20.5h8" ' + STROKE + '/>' +
      '<path d="M4 6.5h16" ' + STROKE + '/>' +
      '<path d="M4 6.5 1.5 12a2.5 2.5 0 0 0 5 0zM20 6.5 17.5 12a2.5 2.5 0 0 0 5 0z" ' + STROKE + '/>',

    heart:
      '<path d="M12 20.2 3.9 12.6C1.8 10.6 1.8 7.4 3.9 5.5 6 3.6 9.1 3.9 11 6l1 1 1-1c1.9-2.1 5-2.4 7.1-.5 2.1 1.9 2.1 5.1 0 7.1L12 20.2Z" ' + STROKE + '/>',

    lightbulb:
      '<path d="M9 18.5h6M9.7 21h4.6" ' + STROKE + '/>' +
      '<path d="M12 3.2a6 6 0 0 0-3.4 10.9c.6.45 1 1.15 1 1.9v.5h4.8v-.5c0-.75.4-1.45 1-1.9A6 6 0 0 0 12 3.2Z" ' + STROKE + '/>',

    database:
      '<ellipse cx="12" cy="6" rx="8" ry="3" ' + STROKE + '/>' +
      '<path d="M4 6v12c0 1.66 3.58 3 8 3s8-1.34 8-3V6" ' + STROKE + '/>' +
      '<path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3" ' + STROKE + '/>',

    check:
      '<path d="M4.5 12.5 9.5 17.5 19.5 6.5" ' + STROKE + '/>',

    xmark:
      '<path d="M5.5 5.5 18.5 18.5M18.5 5.5 5.5 18.5" ' + STROKE + '/>'
  };

  window.Vizstract.Icons = {
    names: Object.keys(ICONS),
    markup: function (name) {
      return ICONS[name] || ICONS.dash;
    }
  };
})();
