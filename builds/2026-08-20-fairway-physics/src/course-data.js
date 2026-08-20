/* Fairway Physics — 9-hole course definition.
   Coordinate plane per hole: X = lateral yards from the tee-to-pin
   centerline (negative = left, positive = right), Y = downrange yards
   from the tee (0). Pin sits on the centerline (x: 0) at y: yardage for
   every hole, so aim/putt math always measures against a straight target
   line even on doglegs — the dogleg is expressed by bending the fairway
   corridor's x-range across two zone entries, not by moving the pin.
   `zones` type determines lookup priority in engine.js's classifyLie
   (hazards, then the green circle, then fairway/rough) — array order only
   matters between zones of the same type (e.g. two bunkers). */
(function (global) {
  'use strict';

  var COURSE = [
    {
      id: 1,
      name: 'Cedar Opener',
      par: 4,
      yardage: 380,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 380 },
      elevationChangeFt: 10,
      greenRadius: 8,
      greenBreakYd: 0.5,
      zones: [
        { type: 'bunker', xMin: 12, xMax: 24, yMin: 355, yMax: 375 },
        { type: 'fairway', xMin: -20, xMax: 20, yMin: 0, yMax: 380 },
        { type: 'rough', xMin: -40, xMax: 40, yMin: -10, yMax: 390 }
      ]
    },
    {
      id: 2,
      name: 'Sandtrap Alley',
      par: 3,
      yardage: 165,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 165 },
      elevationChangeFt: -5,
      greenRadius: 7,
      greenBreakYd: -1,
      zones: [
        { type: 'water', xMin: -15, xMax: 15, yMin: 120, yMax: 145 },
        { type: 'bunker', xMin: -25, xMax: -15, yMin: 150, yMax: 165 },
        { type: 'fairway', xMin: -15, xMax: 15, yMin: 145, yMax: 165 },
        { type: 'rough', xMin: -35, xMax: 35, yMin: -10, yMax: 175 }
      ]
    },
    {
      id: 3,
      name: 'Fence Line',
      par: 4,
      yardage: 410,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 410 },
      elevationChangeFt: 0,
      greenRadius: 8,
      greenBreakYd: 1,
      zones: [
        { type: 'ob', xMin: -55, xMax: -40, yMin: -10, yMax: 410 },
        { type: 'bunker', xMin: 18, xMax: 30, yMin: 200, yMax: 225 },
        { type: 'fairway', xMin: -20, xMax: 25, yMin: 0, yMax: 200 },
        { type: 'fairway', xMin: 0, xMax: 35, yMin: 200, yMax: 410 },
        { type: 'rough', xMin: -40, xMax: 55, yMin: -10, yMax: 420 }
      ]
    },
    {
      id: 4,
      name: "Water's Edge",
      par: 5,
      yardage: 545,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 545 },
      elevationChangeFt: 5,
      greenRadius: 9,
      greenBreakYd: 0,
      zones: [
        { type: 'water', xMin: -10, xMax: 40, yMin: 230, yMax: 265 },
        { type: 'bunker', xMin: -25, xMax: -15, yMin: 510, yMax: 530 },
        { type: 'fairway', xMin: -22, xMax: 22, yMin: 0, yMax: 545 },
        { type: 'rough', xMin: -42, xMax: 55, yMin: -10, yMax: 555 }
      ]
    },
    {
      id: 5,
      name: 'Highlands',
      par: 3,
      yardage: 195,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 195 },
      elevationChangeFt: 25,
      greenRadius: 7,
      greenBreakYd: 1.5,
      zones: [
        { type: 'bunker', xMin: -28, xMax: -15, yMin: 170, yMax: 195 },
        { type: 'bunker', xMin: 15, xMax: 28, yMin: 175, yMax: 195 },
        { type: 'rough', xMin: -35, xMax: 35, yMin: -10, yMax: 205 }
      ]
    },
    {
      id: 6,
      name: 'Long Bend',
      par: 5,
      yardage: 560,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 560 },
      elevationChangeFt: -10,
      greenRadius: 9,
      greenBreakYd: -0.5,
      zones: [
        { type: 'water', xMin: -40, xMax: -10, yMin: 380, yMax: 410 },
        { type: 'fairway', xMin: -15, xMax: 25, yMin: 0, yMax: 250 },
        { type: 'fairway', xMin: -40, xMax: 0, yMin: 250, yMax: 560 },
        { type: 'rough', xMin: -55, xMax: 40, yMin: -10, yMax: 570 }
      ]
    },
    {
      id: 7,
      name: 'Narrow Iron',
      par: 4,
      yardage: 355,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 355 },
      elevationChangeFt: 0,
      greenRadius: 7,
      greenBreakYd: 0.5,
      zones: [
        { type: 'bunker', xMin: -20, xMax: -10, yMin: 330, yMax: 350 },
        { type: 'fairway', xMin: -14, xMax: 14, yMin: 0, yMax: 355 },
        { type: 'rough', xMin: -30, xMax: 30, yMin: -10, yMax: 365 }
      ]
    },
    {
      id: 8,
      name: 'Cape Carry',
      par: 4,
      yardage: 400,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 400 },
      elevationChangeFt: 0,
      greenRadius: 8,
      greenBreakYd: 1,
      zones: [
        { type: 'water', xMin: -30, xMax: 10, yMin: 360, yMax: 390 },
        { type: 'fairway', xMin: -20, xMax: 25, yMin: 0, yMax: 360 },
        { type: 'rough', xMin: -40, xMax: 40, yMin: -10, yMax: 400 }
      ]
    },
    {
      id: 9,
      name: 'Home Hole',
      par: 5,
      yardage: 575,
      tee: { x: 0, y: 0 },
      pin: { x: 0, y: 575 },
      elevationChangeFt: 8,
      greenRadius: 9,
      greenBreakYd: 0,
      zones: [
        { type: 'bunker', xMin: 20, xMax: 32, yMin: 250, yMax: 275 },
        { type: 'water', xMin: -30, xMax: -10, yMin: 520, yMax: 545 },
        { type: 'fairway', xMin: -22, xMax: 22, yMin: 0, yMax: 575 },
        { type: 'rough', xMin: -45, xMax: 45, yMin: -10, yMax: 585 }
      ]
    }
  ];

  global.COURSE = COURSE;
})(typeof window !== 'undefined' ? window : globalThis);
