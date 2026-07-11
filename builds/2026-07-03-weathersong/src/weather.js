const CITY_PRESETS = {
  Toronto: { latitude: 43.6532, longitude: -79.3832 },
  Vancouver: { latitude: 49.2827, longitude: -123.1207 },
  Halifax: { latitude: 44.6488, longitude: -63.5752 },
  Calgary: { latitude: 51.0447, longitude: -114.0719 },
  Montreal: { latitude: 45.5019, longitude: -73.5674 },
};

const OPEN_METEO_BASE_URL = 'https://api.open-meteo.com/v1/forecast';

const DEMO_WEATHER_SNAPSHOT = {
  city: 'Demo (Toronto, overcast evening)',
  latitude: 43.6532,
  longitude: -79.3832,
  temperatureC: 16,
  windSpeedKmh: 22,
  cloudCoverPct: 78,
  precipProbabilityPct: 40,
  weatherCode: 61,
  isDay: false,
  fetchedAt: '2026-07-03T00:00:00.000Z',
};

function buildForecastUrl(latitude, longitude) {
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    current: 'temperature_2m,wind_speed_10m,cloud_cover,weather_code,is_day',
    hourly: 'precipitation_probability',
    forecast_days: '1',
    timezone: 'auto',
  });
  return `${OPEN_METEO_BASE_URL}?${params.toString()}`;
}

function findHourlyIndexForCurrentTime(hourlyTimes, currentTime) {
  if (!Array.isArray(hourlyTimes) || !currentTime) return 0;
  const currentHourPrefix = currentTime.slice(0, 13);
  const index = hourlyTimes.findIndex(
    (time) => typeof time === 'string' && time.startsWith(currentHourPrefix)
  );
  return index >= 0 ? index : 0;
}

function normalizeOpenMeteoResponse(raw, cityName) {
  if (!raw || typeof raw !== 'object' || !raw.current) {
    throw new Error('Malformed Open-Meteo response: missing "current" block');
  }
  const current = raw.current;
  const hourlyTimes = raw.hourly && raw.hourly.time;
  const hourlyPrecip = raw.hourly && raw.hourly.precipitation_probability;
  const index = findHourlyIndexForCurrentTime(hourlyTimes, current.time);
  const precipProbabilityPct =
    Array.isArray(hourlyPrecip) && hourlyPrecip[index] !== undefined ? hourlyPrecip[index] : 0;

  return {
    city: cityName,
    latitude: raw.latitude,
    longitude: raw.longitude,
    temperatureC: current.temperature_2m,
    windSpeedKmh: current.wind_speed_10m,
    cloudCoverPct: current.cloud_cover,
    precipProbabilityPct,
    weatherCode: current.weather_code,
    isDay: current.is_day === 1,
    fetchedAt: new Date().toISOString(),
  };
}

async function fetchWeather(cityName, customCoords) {
  const location = customCoords || CITY_PRESETS[cityName];
  if (!location) {
    throw new Error(`Unknown city: ${cityName}`);
  }
  const url = buildForecastUrl(location.latitude, location.longitude);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Open-Meteo request failed with status ${response.status}`);
  }
  const raw = await response.json();
  return normalizeOpenMeteoResponse(raw, customCoords ? 'Custom Location' : cityName);
}

function getDemoWeather() {
  return { ...DEMO_WEATHER_SNAPSHOT, fetchedAt: new Date().toISOString() };
}

function validateCustomCoordinates(latitude, longitude) {
  const lat = Number(latitude);
  const lon = Number(longitude);
  if (latitude === '' || longitude === '' || !Number.isFinite(lat) || lat < -90 || lat > 90) {
    return { valid: false, error: 'Latitude must be a number between -90 and 90.' };
  }
  if (!Number.isFinite(lon) || lon < -180 || lon > 180) {
    return { valid: false, error: 'Longitude must be a number between -180 and 180.' };
  }
  return { valid: true, latitude: lat, longitude: lon };
}

export {
  CITY_PRESETS,
  DEMO_WEATHER_SNAPSHOT,
  buildForecastUrl,
  findHourlyIndexForCurrentTime,
  normalizeOpenMeteoResponse,
  fetchWeather,
  getDemoWeather,
  validateCustomCoordinates,
};
