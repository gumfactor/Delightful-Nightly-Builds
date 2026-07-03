function capitalize(word) {
  return word.charAt(0).toUpperCase() + word.slice(1);
}

function describeTemperature(temperatureC) {
  if (temperatureC <= -10) return 'bitterly cold';
  if (temperatureC <= 0) return 'freezing';
  if (temperatureC <= 10) return 'cool';
  if (temperatureC <= 20) return 'mild';
  if (temperatureC <= 28) return 'warm';
  return 'sweltering';
}

function describeWind(windSpeedKmh) {
  if (windSpeedKmh < 5) return 'still air';
  if (windSpeedKmh < 20) return 'a light breeze';
  if (windSpeedKmh < 40) return 'a brisk wind';
  return 'a howling wind';
}

function describeSky(textureLayer, cloudCoverPct) {
  switch (textureLayer) {
    case 'thunder':
      return 'a rumbling, storm-lit sky';
    case 'rain':
      return 'a steady rain';
    case 'snow':
      return 'quiet falling snow';
    case 'clear':
      return cloudCoverPct < 20 ? 'a wide open sky' : 'a hazy, half-clear sky';
    default:
      return cloudCoverPct > 60 ? 'a thick overcast' : 'scattered cloud';
  }
}

function generateCaption(snapshot, params) {
  const tempWord = describeTemperature(snapshot.temperatureC);
  const windPhrase = describeWind(snapshot.windSpeedKmh);
  const skyPhrase = describeSky(params.textureLayer, snapshot.cloudCoverPct);
  const timeWord = snapshot.isDay ? 'daylight' : 'night';
  return `${capitalize(tempWord)} ${timeWord} over ${snapshot.city}, ${windPhrase} under ${skyPhrase} — a ${params.mode} drone at ${Math.round(params.droneFreqHz)} Hz.`;
}

export { generateCaption, describeTemperature, describeWind, describeSky };
