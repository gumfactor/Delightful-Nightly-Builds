const PENTATONIC_MAJOR = [0, 2, 4, 7, 9];
const PENTATONIC_MINOR = [0, 3, 5, 7, 10];
const BASE_FREQ_HZ = 110; // A2

const THUNDER_CODES = new Set([95, 96, 99]);
const RAIN_CODES = new Set([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]);
const SNOW_CODES = new Set([71, 73, 75, 77, 85, 86]);
const CLEAR_CODES = new Set([0, 1]);

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function temperatureToScaleDegree(temperatureC) {
  const t = clamp(temperatureC, -30, 40);
  const normalized = (t + 30) / 70;
  const index = Math.round(normalized * (PENTATONIC_MAJOR.length - 1));
  return clamp(index, 0, PENTATONIC_MAJOR.length - 1);
}

function isDaytimeMode(isDay) {
  return isDay ? 'major' : 'minor';
}

function droneFrequencyHz(temperatureC, isDay) {
  const degree = temperatureToScaleDegree(temperatureC);
  const scale = isDay ? PENTATONIC_MAJOR : PENTATONIC_MINOR;
  const semitones = scale[degree];
  const t = clamp(temperatureC, -30, 40);
  const octaveShift = t < 5 ? -1 : 0;
  return BASE_FREQ_HZ * Math.pow(2, (semitones + octaveShift * 12) / 12);
}

function windSpeedToTempoHz(windSpeedKmh) {
  const w = clamp(windSpeedKmh, 0, 80);
  return 0.2 + (w / 80) * 3.8;
}

function windSpeedToFilterCutoffHz(windSpeedKmh) {
  const w = clamp(windSpeedKmh, 0, 80);
  return 400 + (w / 80) * 4600;
}

function cloudCoverToReverbWetness(cloudCoverPct) {
  const c = clamp(cloudCoverPct, 0, 100);
  return c / 100;
}

function precipProbabilityToPercussionDensity(precipProbabilityPct) {
  const p = clamp(precipProbabilityPct, 0, 100);
  return p / 100;
}

function weatherCodeToTextureLayer(weatherCode) {
  if (THUNDER_CODES.has(weatherCode)) return 'thunder';
  if (SNOW_CODES.has(weatherCode)) return 'snow';
  if (RAIN_CODES.has(weatherCode)) return 'rain';
  if (CLEAR_CODES.has(weatherCode)) return 'clear';
  return null;
}

function mapWeatherToParams(snapshot) {
  const mode = isDaytimeMode(snapshot.isDay);
  return {
    scaleDegree: temperatureToScaleDegree(snapshot.temperatureC),
    mode,
    droneFreqHz: droneFrequencyHz(snapshot.temperatureC, snapshot.isDay),
    tempoHz: windSpeedToTempoHz(snapshot.windSpeedKmh),
    filterCutoffHz: windSpeedToFilterCutoffHz(snapshot.windSpeedKmh),
    reverbWetness: cloudCoverToReverbWetness(snapshot.cloudCoverPct),
    percussionDensity: precipProbabilityToPercussionDensity(snapshot.precipProbabilityPct),
    textureLayer: weatherCodeToTextureLayer(snapshot.weatherCode),
  };
}

export {
  PENTATONIC_MAJOR,
  PENTATONIC_MINOR,
  BASE_FREQ_HZ,
  clamp,
  temperatureToScaleDegree,
  isDaytimeMode,
  droneFrequencyHz,
  windSpeedToTempoHz,
  windSpeedToFilterCutoffHz,
  cloudCoverToReverbWetness,
  precipProbabilityToPercussionDensity,
  weatherCodeToTextureLayer,
  mapWeatherToParams,
};
