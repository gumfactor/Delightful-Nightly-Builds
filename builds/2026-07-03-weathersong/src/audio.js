function createImpulseResponseBuffer(audioContext, durationSeconds, decay) {
  const sampleRate = audioContext.sampleRate;
  const length = Math.max(1, Math.floor(sampleRate * durationSeconds));
  const impulse = audioContext.createBuffer(2, length, sampleRate);
  for (let channel = 0; channel < impulse.numberOfChannels; channel += 1) {
    const channelData = impulse.getChannelData(channel);
    for (let i = 0; i < length; i += 1) {
      channelData[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, decay);
    }
  }
  return impulse;
}

class WeatherSongEngine {
  constructor() {
    this.audioContext = null;
    this.droneOscillator = null;
    this.droneGain = null;
    this.filterNode = null;
    this.convolverNode = null;
    this.dryGain = null;
    this.wetGain = null;
    this.masterGain = null;
    this.percussionTimer = null;
    this.params = null;
  }

  start(params) {
    if (this.audioContext) return;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this.audioContext = new AudioContextClass();

    this.masterGain = this.audioContext.createGain();
    this.masterGain.gain.value = 0.6;
    this.masterGain.connect(this.audioContext.destination);

    this.filterNode = this.audioContext.createBiquadFilter();
    this.filterNode.type = 'lowpass';

    this.convolverNode = this.audioContext.createConvolver();
    this.convolverNode.buffer = createImpulseResponseBuffer(this.audioContext, 2.5, 2.0);

    this.dryGain = this.audioContext.createGain();
    this.wetGain = this.audioContext.createGain();

    this.droneOscillator = this.audioContext.createOscillator();
    this.droneOscillator.type = 'sine';
    this.droneGain = this.audioContext.createGain();
    this.droneGain.gain.value = 0.35;

    this.droneOscillator.connect(this.droneGain);
    this.droneGain.connect(this.filterNode);
    this.filterNode.connect(this.dryGain);
    this.filterNode.connect(this.convolverNode);
    this.convolverNode.connect(this.wetGain);
    this.dryGain.connect(this.masterGain);
    this.wetGain.connect(this.masterGain);

    this.droneOscillator.start();

    this.applyParams(params);
    this.scheduleNextPercussion();
  }

  applyParams(params) {
    this.params = params;
    if (!this.audioContext) return;
    const now = this.audioContext.currentTime;
    this.droneOscillator.frequency.setTargetAtTime(params.droneFreqHz, now, 0.5);
    this.filterNode.frequency.setTargetAtTime(params.filterCutoffHz, now, 0.5);
    this.wetGain.gain.setTargetAtTime(params.reverbWetness, now, 0.5);
    this.dryGain.gain.setTargetAtTime(1 - params.reverbWetness * 0.6, now, 0.5);
  }

  setVolume(volume) {
    if (this.masterGain) {
      this.masterGain.gain.value = volume;
    }
  }

  scheduleNextPercussion() {
    if (!this.audioContext) return;
    const density = this.params ? this.params.percussionDensity : 0;
    const minIntervalMs = 400;
    const maxIntervalMs = 4000;
    const intervalMs = maxIntervalMs - density * (maxIntervalMs - minIntervalMs);
    this.percussionTimer = window.setTimeout(() => {
      if (density > 0.02) {
        this.playPercussionBlip();
      }
      this.scheduleNextPercussion();
    }, intervalMs);
  }

  playPercussionBlip() {
    const osc = this.audioContext.createOscillator();
    const gain = this.audioContext.createGain();
    osc.type = 'triangle';
    osc.frequency.value = 1200 + Math.random() * 800;
    gain.gain.value = 0;
    osc.connect(gain);
    gain.connect(this.masterGain);
    const now = this.audioContext.currentTime;
    gain.gain.linearRampToValueAtTime(0.2, now + 0.005);
    gain.gain.linearRampToValueAtTime(0, now + 0.12);
    osc.start(now);
    osc.stop(now + 0.15);
  }

  stop() {
    if (this.percussionTimer) {
      window.clearTimeout(this.percussionTimer);
      this.percussionTimer = null;
    }
    if (this.droneOscillator) {
      try {
        this.droneOscillator.stop();
      } catch (error) {
        // already stopped; nothing to do
      }
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
    this.audioContext = null;
    this.droneOscillator = null;
  }

  isRunning() {
    return this.audioContext !== null && this.audioContext.state !== 'closed';
  }
}

export { WeatherSongEngine, createImpulseResponseBuffer };
