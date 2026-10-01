/* Noise Lab DSP core — pure functions, no DOM. Works in browsers (window.NoiseDSP) and Node (require). */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.NoiseDSP = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const LOOP_SIZE = 1 << 18;
  const TARGET_RMS = 0.1; // -20 dBFS before the volume control
  const MAX_BANDS = 2;
  const MAX_MODS = 3;
  const MAX_WAV_BYTES = 120 * 1024 * 1024;

  const LIMITS = {
    slope: [-2, 3], hp: [0, 4000], lp: [200, 20000], seed: [1, 9999], level: [-60, -10],
    notchFreq: [200, 16000], notchWidth: [0.1, 3], notchDepth: [0, 60],
    bandFreq: [60, 12000], bandWidth: [0.2, 3], bandGain: [-18, 18],
    modRate: [0, 8], modDepth: [0, 1],
  };

  const DEFAULTS = Object.freeze({
    slope: 1, hp: 0, lp: 20000, seed: 1, level: -40,
    notch: { on: false, freq: 4000, width: 1, depth: 40 },
    bands: [{ freq: 500, width: 1.5, gain: 0 }, { freq: 2000, width: 1.5, gain: 0 }],
    mods: [{ rate: 0, depth: 0 }, { rate: 0, depth: 0 }, { rate: 0, depth: 0 }],
  });

  const PRESETS = {
    focus: { name: 'Focus (pink)', params: { slope: 1, lp: 14000 } },
    sleep: { name: 'Deep sleep (brown)', params: { slope: 2, lp: 1200, mods: [{ rate: 0.08, depth: 0.2 }] } },
    rain: { name: 'Steady rain', params: { slope: -0.1, hp: 500, lp: 12000, mods: [{ rate: 5, depth: 0.08 }] } },
    waves: { name: 'Ocean waves', params: { slope: 1.8, lp: 2500, mods: [{ rate: 0.1, depth: 0.7 }, { rate: 0.23, depth: 0.25 }] } },
    fan: { name: 'Fan hum', params: { slope: 1, lp: 5000, bands: [{ freq: 120, width: 0.6, gain: 9 }] } },
    restaurant: {
      name: 'Busy restaurant',
      params: {
        slope: 1.2, hp: 80, lp: 6000,
        bands: [{ freq: 500, width: 1.5, gain: 6 }, { freq: 2000, width: 1.5, gain: 3 }],
        mods: [{ rate: 0.7, depth: 0.35 }, { rate: 2.3, depth: 0.3 }, { rate: 5.1, depth: 0.2 }],
      },
    },
    tinnitus: { name: 'Tinnitus notch (4 kHz)', params: { slope: 1, lp: 16000, notch: { on: true, freq: 4000, width: 1, depth: 40 } } },
  };

  function clamp(value, range, fallback) {
    const number = Number(value);
    if (!Number.isFinite(number)) return fallback;
    return Math.min(range[1], Math.max(range[0], number));
  }

  /** Clamp and complete any partial/untrusted params object into a full valid one. */
  function sanitizeParams(input) {
    const src = input && typeof input === 'object' ? input : {};
    const notch = src.notch && typeof src.notch === 'object' ? src.notch : {};
    const bands = Array.isArray(src.bands) ? src.bands : [];
    const mods = Array.isArray(src.mods) ? src.mods : [];
    return {
      slope: clamp(src.slope, LIMITS.slope, DEFAULTS.slope),
      hp: clamp(src.hp, LIMITS.hp, DEFAULTS.hp),
      lp: clamp(src.lp, LIMITS.lp, DEFAULTS.lp),
      seed: Math.round(clamp(src.seed, LIMITS.seed, DEFAULTS.seed)),
      level: clamp(src.level, LIMITS.level, DEFAULTS.level),
      notch: {
        on: notch.on === true,
        freq: clamp(notch.freq, LIMITS.notchFreq, DEFAULTS.notch.freq),
        width: clamp(notch.width, LIMITS.notchWidth, DEFAULTS.notch.width),
        depth: clamp(notch.depth, LIMITS.notchDepth, DEFAULTS.notch.depth),
      },
      bands: DEFAULTS.bands.map((def, i) => {
        const band = bands[i] && typeof bands[i] === 'object' ? bands[i] : {};
        return {
          freq: clamp(band.freq, LIMITS.bandFreq, def.freq),
          width: clamp(band.width, LIMITS.bandWidth, def.width),
          gain: clamp(band.gain, LIMITS.bandGain, def.gain),
        };
      }),
      mods: DEFAULTS.mods.map((def, i) => {
        const mod = mods[i] && typeof mods[i] === 'object' ? mods[i] : {};
        return {
          rate: clamp(mod.rate, LIMITS.modRate, def.rate),
          depth: clamp(mod.depth, LIMITS.modDepth, def.depth),
        };
      }),
    };
  }

  function presetParams(key) {
    const preset = PRESETS[key];
    return sanitizeParams(preset ? preset.params : {});
  }

  function paramsToHash(params) {
    return '#' + encodeURIComponent(JSON.stringify(sanitizeParams(params)));
  }

  function hashToParams(hash) {
    if (typeof hash !== 'string' || hash.length < 2) return null;
    try {
      return sanitizeParams(JSON.parse(decodeURIComponent(hash.slice(1))));
    } catch (error) {
      return null;
    }
  }

  // ---- logarithmic slider mapping -------------------------------------------------
  function freqFromSlider(position, min, max) {
    return min * Math.pow(max / min, Math.min(1, Math.max(0, position)));
  }
  function sliderFromFreq(freq, min, max) {
    return Math.log(Math.min(max, Math.max(min, freq)) / min) / Math.log(max / min);
  }

  // ---- random + FFT ---------------------------------------------------------------
  function mulberry32(seed) {
    let state = seed >>> 0;
    return function () {
      state = (state + 0x6D2B79F5) >>> 0;
      let t = state;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function gaussianFill(target, rand) {
    for (let i = 0; i < target.length; i += 2) {
      const radius = Math.sqrt(-2 * Math.log(1 - rand()));
      const angle = 2 * Math.PI * rand();
      target[i] = radius * Math.cos(angle);
      if (i + 1 < target.length) target[i + 1] = radius * Math.sin(angle);
    }
  }

  const twiddleCache = new Map();
  function twiddles(n) {
    let table = twiddleCache.get(n);
    if (!table) {
      table = { cos: new Float64Array(n >> 1), sin: new Float64Array(n >> 1) };
      for (let k = 0; k < n >> 1; k++) {
        table.cos[k] = Math.cos(2 * Math.PI * k / n);
        table.sin[k] = Math.sin(2 * Math.PI * k / n);
      }
      twiddleCache.set(n, table);
    }
    return table;
  }

  /** In-place radix-2 FFT. inverse=true also divides by n. */
  function fft(re, im, inverse) {
    const n = re.length;
    if (n < 2 || (n & (n - 1)) !== 0) throw new Error('FFT length must be a power of two');
    for (let i = 1, j = 0; i < n; i++) {
      let bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) {
        let tmp = re[i]; re[i] = re[j]; re[j] = tmp;
        tmp = im[i]; im[i] = im[j]; im[j] = tmp;
      }
    }
    const table = twiddles(n);
    const sign = inverse ? 1 : -1;
    for (let len = 2; len <= n; len <<= 1) {
      const half = len >> 1;
      const step = n / len;
      for (let start = 0; start < n; start += len) {
        for (let k = 0; k < half; k++) {
          const wr = table.cos[k * step];
          const wi = sign * table.sin[k * step];
          const a = start + k;
          const b = a + half;
          const xr = re[b] * wr - im[b] * wi;
          const xi = re[b] * wi + im[b] * wr;
          re[b] = re[a] - xr; im[b] = im[a] - xi;
          re[a] += xr; im[a] += xi;
        }
      }
    }
    if (inverse) {
      for (let i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
    }
  }

  // ---- spectral shaping -----------------------------------------------------------
  /** Linear magnitude gain of the whole shaping chain at frequency f (Hz). */
  function magnitudeResponse(params, f) {
    if (f <= 0) return 0;
    let gain = Math.pow(f / 1000, -params.slope / 2);
    if (params.hp > 0) gain /= Math.sqrt(1 + Math.pow(params.hp / f, 8));
    if (params.lp < 20000) gain /= Math.sqrt(1 + Math.pow(f / params.lp, 8));
    let db = 0;
    for (const band of params.bands) {
      if (band.gain === 0) continue;
      const sigma = band.width / 2.355;
      const octaves = Math.log2(f / band.freq);
      db += band.gain * Math.exp(-0.5 * (octaves / sigma) * (octaves / sigma));
    }
    if (params.notch.on) {
      const sigma = params.notch.width / 2.355;
      const octaves = Math.log2(f / params.notch.freq);
      db -= params.notch.depth * Math.exp(-0.5 * (octaves / sigma) * (octaves / sigma));
    }
    return gain * Math.pow(10, db / 20);
  }

  /** Frequency-domain spectrum of seeded gaussian white noise; cache it, reshape it many times. */
  function whiteSpectrum(seed, size) {
    const re = new Float64Array(size);
    const im = new Float64Array(size);
    gaussianFill(re, mulberry32(seed * 7919 + 13));
    fft(re, im, false);
    return { re, im, size };
  }

  function quantizedRate(rate, sampleRate, size) {
    if (rate <= 0) return 0;
    const cycles = Math.max(1, Math.round(rate * size / sampleRate));
    return cycles * sampleRate / size;
  }

  function applyModulation(samples, params, sampleRate) {
    const size = samples.length;
    const rand = mulberry32(params.seed * 31 + 5);
    for (const mod of params.mods) {
      const phase = rand() * 2 * Math.PI;
      if (mod.rate <= 0 || mod.depth <= 0) continue;
      const cycles = Math.max(1, Math.round(mod.rate * size / sampleRate)); // whole cycles keep the loop seamless
      for (let i = 0; i < size; i++) {
        samples[i] *= 1 - mod.depth * (0.5 + 0.5 * Math.sin(2 * Math.PI * cycles * i / size + phase));
      }
    }
  }

  function rmsOf(samples) {
    let sum = 0;
    for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i];
    return Math.sqrt(sum / samples.length);
  }

  /** Transparent below the threshold, smoothly saturating above it, never exceeds 1. */
  function softLimit(x, threshold) {
    const magnitude = Math.abs(x);
    if (magnitude <= threshold) return x;
    const room = 1 - threshold;
    return Math.sign(x) * (threshold + room * Math.tanh((magnitude - threshold) / room));
  }

  /** Shape one cached white spectrum into a finished, normalised, seamless loop. */
  function renderChannel(params, sampleRate, white) {
    const size = white.size;
    const re = new Float64Array(size);
    const im = new Float64Array(size);
    const half = size >> 1;
    for (let k = 1; k < half; k++) {
      const gain = magnitudeResponse(params, k * sampleRate / size);
      re[k] = white.re[k] * gain; im[k] = white.im[k] * gain;
      re[size - k] = white.re[size - k] * gain; im[size - k] = white.im[size - k] * gain;
    }
    re[half] = white.re[half] * magnitudeResponse(params, sampleRate / 2);
    fft(re, im, true);
    const samples = new Float32Array(size);
    for (let i = 0; i < size; i++) samples[i] = re[i];
    applyModulation(samples, params, sampleRate);
    const rms = rmsOf(samples);
    const scale = rms > 0 ? TARGET_RMS / rms : 0;
    for (let i = 0; i < size; i++) samples[i] = softLimit(samples[i] * scale, 0.8);
    return samples;
  }

  /** Stereo loop (two independent noise realisations). Pass `whites` to reuse cached spectra. */
  function synthesize(rawParams, sampleRate, size, whites) {
    const params = sanitizeParams(rawParams);
    const length = size || LOOP_SIZE;
    const spectra = whites && whites.length === 2 && whites[0].size === length
      ? whites
      : [whiteSpectrum(params.seed, length), whiteSpectrum(params.seed + 10000, length)];
    return { channels: spectra.map((white) => renderChannel(params, sampleRate, white)), whites: spectra, params };
  }

  // ---- measurement ----------------------------------------------------------------
  function aWeightDb(f) {
    if (f <= 0) return -Infinity;
    const f2 = f * f;
    const ra = (12194 * 12194 * f2 * f2) /
      ((f2 + 20.6 * 20.6) * Math.sqrt((f2 + 107.7 * 107.7) * (f2 + 737.9 * 737.9)) * (f2 + 12194 * 12194));
    return 20 * Math.log10(ra) + 2.0;
  }

  /** Welch estimate: mean-square contribution per bin (sums to the signal's mean square). */
  function welchPower(samples, segment) {
    const seg = segment || 4096;
    const window = new Float64Array(seg);
    let windowEnergy = 0;
    for (let i = 0; i < seg; i++) {
      window[i] = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / seg);
      windowEnergy += window[i] * window[i];
    }
    const power = new Float64Array(seg / 2 + 1);
    const re = new Float64Array(seg);
    const im = new Float64Array(seg);
    let count = 0;
    for (let start = 0; start + seg <= samples.length; start += seg / 2) {
      for (let i = 0; i < seg; i++) { re[i] = samples[start + i] * window[i]; im[i] = 0; }
      fft(re, im, false);
      for (let k = 0; k <= seg / 2; k++) {
        const fold = k === 0 || k === seg / 2 ? 1 : 2;
        power[k] += fold * (re[k] * re[k] + im[k] * im[k]) / (seg * windowEnergy);
      }
      count++;
    }
    if (count > 0) for (let k = 0; k < power.length; k++) power[k] /= count;
    return power;
  }

  function levels(samples, sampleRate) {
    const seg = 4096;
    const power = welchPower(samples, seg);
    let aWeighted = 0;
    for (let k = 1; k < power.length; k++) aWeighted += power[k] * Math.pow(10, aWeightDb(k * sampleRate / seg) / 10);
    let peak = 0;
    for (let i = 0; i < samples.length; i++) peak = Math.max(peak, Math.abs(samples[i]));
    const rms = rmsOf(samples);
    return {
      rmsDbfs: 20 * Math.log10(Math.max(rms, 1e-12)),
      aWeightedDbfs: 10 * Math.log10(Math.max(aWeighted, 1e-24)),
      peakDbfs: 20 * Math.log10(Math.max(peak, 1e-12)),
    };
  }

  /** Smoothed spectrum on a log frequency grid, in dB (power per octave-ish window). */
  function logSpectrum(samples, sampleRate, points) {
    const seg = 4096;
    const power = welchPower(samples, seg);
    const count = points || 160;
    const freqs = new Float64Array(count);
    const db = new Float64Array(count);
    const binHz = sampleRate / seg;
    for (let i = 0; i < count; i++) {
      const f = 20 * Math.pow(Math.min(20000, sampleRate / 2 - 1) / 20, i / (count - 1));
      const lo = Math.max(1, Math.floor(f / Math.pow(2, 1 / 8) / binHz));
      const hi = Math.min(power.length - 1, Math.max(lo, Math.ceil(f * Math.pow(2, 1 / 8) / binHz)));
      let sum = 0;
      for (let k = lo; k <= hi; k++) sum += power[k];
      freqs[i] = f;
      db[i] = 10 * Math.log10(Math.max(sum, 1e-20));
    }
    return { freqs, db };
  }

  /** Mean power in [f/2^(w/2), f*2^(w/2)] in dB — used to verify notches. */
  function bandPowerDb(samples, sampleRate, centerHz, widthOctaves) {
    const seg = 4096;
    const power = welchPower(samples, seg);
    const binHz = sampleRate / seg;
    const lo = Math.max(1, Math.round(centerHz / Math.pow(2, widthOctaves / 2) / binHz));
    const hi = Math.min(power.length - 1, Math.round(centerHz * Math.pow(2, widthOctaves / 2) / binHz));
    let sum = 0;
    for (let k = lo; k <= hi; k++) sum += power[k];
    return 10 * Math.log10(Math.max(sum / Math.max(1, hi - lo + 1), 1e-20));
  }

  // ---- timer + export -------------------------------------------------------------
  /** Gain multiplier for a sleep timer: 1 until the final fade, then linear to 0. */
  function fadeGain(elapsedSec, totalSec, fadeSec) {
    if (totalSec <= 0) return 1;
    const remaining = totalSec - elapsedSec;
    if (remaining <= 0) return 0;
    if (remaining >= fadeSec) return 1;
    return remaining / fadeSec;
  }

  function wavByteLength(size, repeats, channelCount) {
    return 44 + size * repeats * channelCount * 2;
  }

  /** 16-bit PCM WAV with TPDF dither. `gainLinear` applies the chosen listening level. */
  function encodeWav(channels, sampleRate, repeats, gainLinear, seed) {
    const size = channels[0].length;
    const channelCount = channels.length;
    const total = wavByteLength(size, repeats, channelCount);
    if (total > MAX_WAV_BYTES) throw new Error('Export too large');
    const buffer = new ArrayBuffer(total);
    const view = new DataView(buffer);
    const writeText = (offset, text) => { for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i)); };
    const dataBytes = total - 44;
    writeText(0, 'RIFF'); view.setUint32(4, total - 8, true); writeText(8, 'WAVE');
    writeText(12, 'fmt '); view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, channelCount, true); view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * channelCount * 2, true); view.setUint16(32, channelCount * 2, true);
    view.setUint16(34, 16, true); writeText(36, 'data'); view.setUint32(40, dataBytes, true);
    const rand = mulberry32((seed || 1) + 99);
    let offset = 44;
    for (let rep = 0; rep < repeats; rep++) {
      for (let i = 0; i < size; i++) {
        for (let ch = 0; ch < channelCount; ch++) {
          const dither = (rand() - rand()) / 32768;
          const value = softLimit(channels[ch][i] * gainLinear, 0.95) + dither;
          view.setInt16(offset, Math.max(-32768, Math.min(32767, Math.round(value * 32767))), true);
          offset += 2;
        }
      }
    }
    return new Uint8Array(buffer);
  }

  function dbToLinear(db) { return Math.pow(10, db / 20); }

  return {
    LOOP_SIZE, TARGET_RMS, MAX_BANDS, MAX_MODS, LIMITS, DEFAULTS, PRESETS,
    sanitizeParams, presetParams, paramsToHash, hashToParams,
    freqFromSlider, sliderFromFreq, mulberry32, fft, magnitudeResponse, whiteSpectrum,
    quantizedRate, synthesize, softLimit, aWeightDb, welchPower, levels, logSpectrum,
    bandPowerDb, fadeGain, wavByteLength, encodeWav, dbToLinear,
  };
}));
