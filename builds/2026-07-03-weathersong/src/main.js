import { CITY_PRESETS, fetchWeather, getDemoWeather, validateCustomCoordinates } from './weather.js';
import { mapWeatherToParams } from './mapping.js';
import { generateCaption } from './caption.js';
import { saveEntry, listEntries, getEntry, removeEntry } from './journal.js';
import { WeatherSongEngine } from './audio.js';
import { WeatherVisual } from './visual.js';

const state = {
  snapshot: null,
  params: null,
  caption: null,
  isPlaying: false,
};

const engine = new WeatherSongEngine();
let visual = null;

// Exposed only so Playwright tests can assert on real engine state; not part of the app's UI surface.
window.__weatherSongEngine = engine;

function byId(id) {
  return document.getElementById(id);
}

function showError(message) {
  const banner = byId('error-banner');
  banner.textContent = message;
  banner.hidden = false;
}

function hideError() {
  const banner = byId('error-banner');
  banner.hidden = true;
  banner.textContent = '';
}

function renderWeatherPanel(snapshot, params, caption) {
  byId('weather-city').textContent = snapshot.city;
  byId('weather-temp').textContent = `${snapshot.temperatureC.toFixed(1)} °C`;
  byId('weather-wind').textContent = `${snapshot.windSpeedKmh.toFixed(1)} km/h`;
  byId('weather-cloud').textContent = `${Math.round(snapshot.cloudCoverPct)}%`;
  byId('weather-precip').textContent = `${Math.round(snapshot.precipProbabilityPct)}%`;
  byId('weather-caption').textContent = caption;
  byId('weather-panel').hidden = false;
}

function applySnapshot(snapshot) {
  const params = mapWeatherToParams(snapshot);
  const caption = generateCaption(snapshot, params);
  state.snapshot = snapshot;
  state.params = params;
  state.caption = caption;
  renderWeatherPanel(snapshot, params, caption);
  if (visual) {
    visual.setParams(params, snapshot);
  }
  if (engine.isRunning()) {
    engine.applyParams(params);
  }
}

async function loadWeather(cityName, customCoords) {
  hideError();
  try {
    const snapshot = await fetchWeather(cityName, customCoords);
    applySnapshot(snapshot);
  } catch (error) {
    showError(`Couldn't reach Open-Meteo (${error.message}). You can use demo weather instead.`);
  }
}

function togglePlayback() {
  if (!state.params) return;
  if (state.isPlaying) {
    engine.stop();
    if (visual) visual.stop();
    state.isPlaying = false;
    byId('play-pause-button').textContent = 'Play';
  } else {
    engine.start(state.params);
    if (visual) visual.start();
    state.isPlaying = true;
    byId('play-pause-button').textContent = 'Pause';
  }
}

function renderJournalList() {
  const entries = listEntries();
  const list = byId('journal-list');
  list.innerHTML = '';
  entries.forEach((entry) => {
    const item = document.createElement('li');
    item.className = 'journal-entry';
    item.dataset.entryId = entry.id;

    const label = document.createElement('button');
    label.type = 'button';
    label.className = 'journal-entry-load';
    label.setAttribute('data-testid', 'journal-entry-load');
    label.textContent = `${entry.savedAt.slice(0, 10)} — ${entry.city}: ${entry.caption}`;
    label.addEventListener('click', () => loadJournalEntry(entry.id));

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'journal-entry-remove';
    removeButton.setAttribute('data-testid', 'journal-entry-remove');
    removeButton.textContent = 'Remove';
    removeButton.addEventListener('click', () => {
      removeEntry(entry.id);
      renderJournalList();
    });

    item.appendChild(label);
    item.appendChild(removeButton);
    list.appendChild(item);
  });
}

function loadJournalEntry(id) {
  const entry = getEntry(id);
  if (!entry) return;
  state.snapshot = entry.weatherSnapshot;
  state.params = entry.params;
  state.caption = entry.caption;
  renderWeatherPanel(entry.weatherSnapshot, entry.params, entry.caption);
  if (visual) {
    visual.setParams(entry.params, entry.weatherSnapshot);
  }
  if (engine.isRunning()) {
    engine.applyParams(entry.params);
  }
}

function saveToJournal() {
  if (!state.snapshot || !state.params) return;
  saveEntry({
    city: state.snapshot.city,
    weatherSnapshot: state.snapshot,
    params: state.params,
    caption: state.caption,
  });
  renderJournalList();
}

function populateCityOptions() {
  const select = byId('city-select');
  Object.keys(CITY_PRESETS).forEach((cityName) => {
    const option = document.createElement('option');
    option.value = cityName;
    option.textContent = cityName;
    select.appendChild(option);
  });
  const customOption = document.createElement('option');
  customOption.value = 'Custom';
  customOption.textContent = 'Custom coordinates…';
  select.appendChild(customOption);
}

function init() {
  const canvas = byId('visual-canvas');
  visual = new WeatherVisual(canvas);
  populateCityOptions();
  renderJournalList();

  byId('city-select').addEventListener('change', (event) => {
    const cityName = event.target.value;
    byId('custom-coords').hidden = cityName !== 'Custom';
    if (cityName !== 'Custom') {
      loadWeather(cityName);
    }
  });

  byId('fetch-custom-button').addEventListener('click', () => {
    const latitude = byId('custom-latitude').value;
    const longitude = byId('custom-longitude').value;
    const validation = validateCustomCoordinates(latitude, longitude);
    if (!validation.valid) {
      showError(validation.error);
      return;
    }
    loadWeather('Custom', { latitude: validation.latitude, longitude: validation.longitude });
  });

  byId('demo-weather-button').addEventListener('click', () => {
    hideError();
    applySnapshot(getDemoWeather());
  });

  byId('play-pause-button').addEventListener('click', togglePlayback);

  byId('volume-slider').addEventListener('input', (event) => {
    engine.setVolume(Number(event.target.value));
  });

  byId('save-journal-button').addEventListener('click', saveToJournal);

  loadWeather('Toronto');
}

document.addEventListener('DOMContentLoaded', init);

export { applySnapshot, togglePlayback, saveToJournal, loadJournalEntry, state };
