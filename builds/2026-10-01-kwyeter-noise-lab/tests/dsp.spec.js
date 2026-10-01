const { test, expect } = require('@playwright/test');
const DSP = require('../src/dsp.js');

const SR = 44100;
const SIZE = 1 << 16; // smaller loop keeps unit tests fast

function render(overrides) {
  return DSP.synthesize(Object.assign({}, DSP.presetParams('focus'), overrides), SR, SIZE);
}

test.describe('FFT', () => {
  test('forward then inverse FFT returns the original signal', () => {
    const re = Float64Array.from({ length: 64 }, (_, i) => Math.sin(i * 0.7) + (i % 5));
    const original = Float64Array.from(re);
    const im = new Float64Array(64);
    DSP.fft(re, im, false);
    DSP.fft(re, im, true);
    for (let i = 0; i < 64; i++) expect(re[i]).toBeCloseTo(original[i], 9);
  });

  test('a pure sine lands in exactly the expected bin', () => {
    const n = 256;
    const re = Float64Array.from({ length: n }, (_, i) => Math.sin(2 * Math.PI * 10 * i / n));
    const im = new Float64Array(n);
    DSP.fft(re, im, false);
    const magnitude = (k) => Math.hypot(re[k], im[k]);
    expect(magnitude(10)).toBeCloseTo(n / 2, 6);
    expect(magnitude(11)).toBeLessThan(1e-6);
  });

  test('rejects lengths that are not a power of two', () => {
    expect(() => DSP.fft(new Float64Array(12), new Float64Array(12), false)).toThrow();
  });
});

test.describe('synthesis', () => {
  test('output is deterministic for a given seed and differs between seeds', () => {
    const a = render({ seed: 5 }).channels[0];
    const b = render({ seed: 5 }).channels[0];
    const c = render({ seed: 6 }).channels[0];
    expect(Array.from(a.slice(0, 50))).toEqual(Array.from(b.slice(0, 50)));
    expect(Array.from(a.slice(0, 50))).not.toEqual(Array.from(c.slice(0, 50)));
  });

  test('left and right channels are different realisations', () => {
    const { channels } = render({});
    expect(channels[0][1000]).not.toBe(channels[1][1000]);
  });

  test('every preset renders to -20 dBFS RMS with no sample above full scale', () => {
    for (const key of Object.keys(DSP.PRESETS)) {
      const { channels } = DSP.synthesize(DSP.presetParams(key), SR, SIZE);
      for (const channel of channels) {
        const lv = DSP.levels(channel, SR);
        expect(Math.abs(lv.rmsDbfs + 20)).toBeLessThan(0.5);
        expect(lv.peakDbfs).toBeLessThan(0);
      }
    }
  });

  test('pink noise falls about 3 dB per octave and brown about 6 dB per octave', () => {
    for (const [slope, expected] of [[1, -3], [2, -6], [0, 0]]) {
      const { channels } = render({ slope, lp: 20000, hp: 0 });
      const low = DSP.bandPowerDb(channels[0], SR, 500, 0.5);
      const high = DSP.bandPowerDb(channels[0], SR, 1000, 0.5);
      // per-bin power measured; one octave up should shift by `expected` dB per Hz-density
      expect(high - low).toBeGreaterThan(expected - 1.5);
      expect(high - low).toBeLessThan(expected + 1.5);
    }
  });

  test('notch removes at least 25 dB at its centre without touching distant bands', () => {
    const plain = render({ notch: { on: false } }).channels[0];
    const notched = render({ notch: { on: true, freq: 4000, width: 1, depth: 40 } }).channels[0];
    const centreDrop = DSP.bandPowerDb(plain, SR, 4000, 0.3) - DSP.bandPowerDb(notched, SR, 4000, 0.3);
    const farDrop = DSP.bandPowerDb(plain, SR, 500, 0.3) - DSP.bandPowerDb(notched, SR, 500, 0.3);
    expect(centreDrop).toBeGreaterThan(25);
    expect(Math.abs(farDrop)).toBeLessThan(1);
  });

  test('low-pass and high-pass cut the far side of the cutoff', () => {
    const lowpassed = render({ slope: 0, lp: 1000 }).channels[0];
    expect(DSP.bandPowerDb(lowpassed, SR, 500, 0.3) - DSP.bandPowerDb(lowpassed, SR, 8000, 0.3)).toBeGreaterThan(30);
    const highpassed = render({ slope: 0, hp: 2000 }).channels[0];
    expect(DSP.bandPowerDb(highpassed, SR, 8000, 0.3) - DSP.bandPowerDb(highpassed, SR, 500, 0.3)).toBeGreaterThan(30);
  });

  test('band boost raises its centre by roughly the requested gain', () => {
    const flat = render({ slope: 0 }).channels[0];
    const boosted = render({ slope: 0, bands: [{ freq: 1000, width: 1, gain: 12 }, { freq: 2000, width: 1, gain: 0 }] }).channels[0];
    const rise = DSP.bandPowerDb(boosted, SR, 1000, 0.2) - DSP.bandPowerDb(flat, SR, 1000, 0.2);
    expect(rise).toBeGreaterThan(8);
    expect(rise).toBeLessThan(13);
  });

  test('loop is seamless: the wrap-around step is no bigger than a normal step', () => {
    const { channels } = render({ slope: 2, lp: 1200, mods: [{ rate: 0.3, depth: 0.7 }, { rate: 0, depth: 0 }, { rate: 0, depth: 0 }] });
    const samples = channels[0];
    let sumSquares = 0;
    for (let i = 1; i < samples.length; i++) sumSquares += Math.pow(samples[i] - samples[i - 1], 2);
    const typicalStep = Math.sqrt(sumSquares / (samples.length - 1));
    const wrapStep = Math.abs(samples[0] - samples[samples.length - 1]);
    expect(wrapStep).toBeLessThan(5 * typicalStep);
  });

  test('modulation rates snap to whole cycles per loop', () => {
    const snapped = DSP.quantizedRate(0.5, SR, DSP.LOOP_SIZE);
    const cycles = snapped * DSP.LOOP_SIZE / SR;
    expect(Math.abs(cycles - Math.round(cycles))).toBeLessThan(1e-9);
    expect(DSP.quantizedRate(0, SR, DSP.LOOP_SIZE)).toBe(0);
    expect(DSP.quantizedRate(0.0001, SR, DSP.LOOP_SIZE)).toBeGreaterThan(0);
  });

  test('swell modulation actually varies the short-term level', () => {
    const swell = render({ mods: [{ rate: 0.5, depth: 0.8 }, { rate: 0, depth: 0 }, { rate: 0, depth: 0 }] }).channels[0];
    const steady = render({}).channels[0];
    const windowRms = (samples, start) => DSP.levels(samples.slice(start, start + 4096), SR).rmsDbfs;
    const spread = (samples) => {
      const values = [];
      for (let start = 0; start + 4096 <= samples.length; start += 4096) values.push(windowRms(samples, start));
      return Math.max(...values) - Math.min(...values);
    };
    expect(spread(swell)).toBeGreaterThan(spread(steady) + 6);
  });

  test('cached white spectra can be reshaped to a new colour without re-seeding', () => {
    const first = DSP.synthesize(DSP.presetParams('focus'), SR, SIZE);
    const second = DSP.synthesize(Object.assign({}, first.params, { slope: 2 }), SR, SIZE, first.whites);
    expect(second.whites).toBe(first.whites);
    expect(second.channels[0][100]).not.toBe(first.channels[0][100]);
  });
});

test.describe('measurement', () => {
  test('RMS of a known sine is -3 dB below its amplitude and A-weighting is 0 dB at 1 kHz', () => {
    const sine = Float32Array.from({ length: 1 << 15 }, (_, i) => 0.5 * Math.sin(2 * Math.PI * 1000 * i / SR));
    const lv = DSP.levels(sine, SR);
    expect(lv.rmsDbfs).toBeCloseTo(20 * Math.log10(0.5 / Math.SQRT2), 2);
    expect(Math.abs(DSP.aWeightDb(1000))).toBeLessThan(0.1);
    expect(Math.abs(lv.aWeightedDbfs - lv.rmsDbfs)).toBeLessThan(0.6);
  });

  test('A-weighting strongly discounts low frequencies', () => {
    expect(DSP.aWeightDb(50)).toBeLessThan(-25);
    expect(DSP.aWeightDb(2500)).toBeGreaterThan(0);
  });

  test('brown noise reads much quieter A-weighted than flat RMS; white noise does not', () => {
    const brown = DSP.levels(render({ slope: 2 }).channels[0], SR);
    const white = DSP.levels(render({ slope: 0 }).channels[0], SR);
    expect(brown.rmsDbfs - brown.aWeightedDbfs).toBeGreaterThan(white.rmsDbfs - white.aWeightedDbfs + 8);
  });
});

test.describe('parameters, URLs and timers', () => {
  test('sanitizeParams clamps hostile values and fills missing ones', () => {
    const clean = DSP.sanitizeParams({ slope: 99, level: 5, hp: -10, seed: 'x', notch: { on: 'yes', freq: 1 }, bands: 'nope', extra: 1 });
    expect(clean.slope).toBe(3);
    expect(clean.level).toBe(-10);
    expect(clean.hp).toBe(0);
    expect(clean.seed).toBe(1);
    expect(clean.notch.on).toBe(false);
    expect(clean.notch.freq).toBe(200);
    expect(clean.bands).toHaveLength(2);
    expect(clean.extra).toBeUndefined();
  });

  test('hash round-trips and malformed hashes return null instead of throwing', () => {
    const params = DSP.presetParams('restaurant');
    expect(DSP.hashToParams(DSP.paramsToHash(params))).toEqual(params);
    expect(DSP.hashToParams('#%7Bnot-json')).toBeNull();
    expect(DSP.hashToParams('')).toBeNull();
    expect(DSP.hashToParams('#%E0%A4%A')).toBeNull();
  });

  test('log slider mapping is invertible and hits both ends', () => {
    expect(DSP.freqFromSlider(0, 200, 16000)).toBeCloseTo(200, 6);
    expect(DSP.freqFromSlider(1, 200, 16000)).toBeCloseTo(16000, 6);
    expect(DSP.sliderFromFreq(DSP.freqFromSlider(0.37, 200, 16000), 200, 16000)).toBeCloseTo(0.37, 9);
  });

  test('sleep timer holds full volume, fades over the last seconds, then silences', () => {
    expect(DSP.fadeGain(10, 600, 30)).toBe(1);
    expect(DSP.fadeGain(585, 600, 30)).toBeCloseTo(0.5, 6);
    expect(DSP.fadeGain(600, 600, 30)).toBe(0);
    expect(DSP.fadeGain(9999, 600, 30)).toBe(0);
    expect(DSP.fadeGain(9999, 0, 30)).toBe(1);
  });
});

test.describe('WAV export', () => {
  test('writes a valid 16-bit stereo header with the right sizes', () => {
    const { channels } = render({});
    const bytes = DSP.encodeWav(channels, SR, 2, 0.5, 1);
    const view = new DataView(bytes.buffer);
    const text = (offset) => String.fromCharCode(...bytes.slice(offset, offset + 4));
    expect(text(0)).toBe('RIFF'); expect(text(8)).toBe('WAVE'); expect(text(36)).toBe('data');
    expect(view.getUint16(22, true)).toBe(2);
    expect(view.getUint32(24, true)).toBe(SR);
    expect(view.getUint16(34, true)).toBe(16);
    expect(view.getUint32(40, true)).toBe(SIZE * 2 * 2 * 2);
    expect(bytes.length).toBe(DSP.wavByteLength(SIZE, 2, 2));
  });

  test('applies the gain, never clips, and repeats the loop identically', () => {
    const { channels } = render({});
    const bytes = DSP.encodeWav(channels, SR, 2, 1, 1);
    const view = new DataView(bytes.buffer);
    const expectedFirst = Math.round(channels[0][1000] * 32767);
    expect(Math.abs(view.getInt16(44 + 1000 * 4, true) - expectedFirst)).toBeLessThanOrEqual(2);
    const repeatOffset = SIZE * 4;
    expect(Math.abs(view.getInt16(44 + 1000 * 4 + repeatOffset, true) - view.getInt16(44 + 1000 * 4, true))).toBeLessThanOrEqual(2);
    let loudest = 0;
    for (let i = 44; i < bytes.length; i += 2) loudest = Math.max(loudest, Math.abs(view.getInt16(i, true)));
    expect(loudest).toBeLessThanOrEqual(32767);
    expect(loudest).toBeGreaterThan(1000);
  });

  test('refuses an export that would exceed the size cap', () => {
    const { channels } = render({});
    expect(() => DSP.encodeWav(channels, SR, 1000, 1, 1)).toThrow('Export too large');
  });

  test('soft limiter is transparent below threshold and bounded above', () => {
    expect(DSP.softLimit(0.5, 0.8)).toBe(0.5);
    expect(DSP.softLimit(5, 0.8)).toBeLessThanOrEqual(1);
    expect(DSP.softLimit(-5, 0.8)).toBeGreaterThanOrEqual(-1);
  });
});
