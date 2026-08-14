/**
 * Thin wrapper around getUserMedia + Web Audio AnalyserNode. Exposes a small
 * event-based interface (on/off/emit) so app.js and tests can drive it
 * without any DOM coupling. All actual dB math is delegated to
 * audio-math.js's pure functions — this module only owns the audio
 * pipeline plumbing (mic access, sampling loop, FFT peak-bin lookup).
 */

function createAudioEngine(options) {
  const opts = options || {};
  const sampleIntervalMs = opts.sampleIntervalMs || 100;

  const listeners = { reading: [], error: [], stop: [] };
  let audioContext = null;
  let analyser = null;
  let sourceNode = null;
  let mediaStream = null;
  let timeDomainBuffer = null;
  let freqDomainBuffer = null;
  let intervalHandle = null;
  let running = false;
  let startedAtMs = 0;

  function on(event, handler) {
    if (!listeners[event]) listeners[event] = [];
    listeners[event].push(handler);
  }

  function emit(event, payload) {
    (listeners[event] || []).forEach((handler) => handler(payload));
  }

  function dominantFrequencyHz() {
    analyser.getByteFrequencyData(freqDomainBuffer);
    let maxIndex = 0;
    let maxValue = -1;
    for (let i = 0; i < freqDomainBuffer.length; i++) {
      if (freqDomainBuffer[i] > maxValue) {
        maxValue = freqDomainBuffer[i];
        maxIndex = i;
      }
    }
    const nyquist = audioContext.sampleRate / 2;
    return (maxIndex / freqDomainBuffer.length) * nyquist;
  }

  async function start(calibrationOffsetDb) {
    if (running) return;
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    // eslint-disable-next-line no-undef
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioContext = new AudioContextClass();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0;
    sourceNode = audioContext.createMediaStreamSource(mediaStream);
    sourceNode.connect(analyser);

    timeDomainBuffer = new Float32Array(analyser.fftSize);
    freqDomainBuffer = new Uint8Array(analyser.frequencyBinCount);

    running = true;
    startedAtMs = Date.now();

    intervalHandle = window.setInterval(() => {
      try {
        analyser.getFloatTimeDomainData(timeDomainBuffer);
        const rms = computeRms(timeDomainBuffer);
        const rawDb = rmsToDb(rms, calibrationOffsetDb || 0);
        const dominantHz = dominantFrequencyHz();
        const weightedDb = applyAWeighting(rawDb, dominantHz);
        const zone = classifyZone(weightedDb);
        const tSec = (Date.now() - startedAtMs) / 1000;
        emit('reading', { t: tSec, db: weightedDb, zone });
      } catch (err) {
        emit('error', err);
      }
    }, sampleIntervalMs);
  }

  function stop() {
    if (!running) return;
    running = false;
    if (intervalHandle) window.clearInterval(intervalHandle);
    intervalHandle = null;
    if (mediaStream) {
      mediaStream.getTracks().forEach((track) => track.stop());
    }
    if (audioContext) {
      audioContext.close().catch(() => {});
    }
    emit('stop', {});
  }

  function isRunning() {
    return running;
  }

  return { on, start, stop, isRunning };
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { createAudioEngine };
}
