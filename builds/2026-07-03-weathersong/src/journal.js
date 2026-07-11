const STORAGE_KEY = 'weathersong.journal';
const MAX_ENTRIES = 60;

function defaultStorage() {
  return window.localStorage;
}

function loadEntries(storage) {
  const activeStorage = storage || defaultStorage();
  const raw = activeStorage.getItem(STORAGE_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    return [];
  }
}

function persistEntries(entries, storage) {
  const activeStorage = storage || defaultStorage();
  activeStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

function saveEntry({ city, weatherSnapshot, params, caption }, storage) {
  const entries = loadEntries(storage);
  const entry = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    savedAt: new Date().toISOString(),
    city,
    weatherSnapshot,
    params,
    caption,
  };
  const updated = [entry, ...entries].slice(0, MAX_ENTRIES);
  persistEntries(updated, storage);
  return entry;
}

function listEntries(storage) {
  return loadEntries(storage)
    .slice()
    .sort((a, b) => (a.savedAt < b.savedAt ? 1 : -1));
}

function getEntry(id, storage) {
  return loadEntries(storage).find((entry) => entry.id === id) || null;
}

function removeEntry(id, storage) {
  const remaining = loadEntries(storage).filter((entry) => entry.id !== id);
  persistEntries(remaining, storage);
  return remaining;
}

export { saveEntry, listEntries, getEntry, removeEntry, MAX_ENTRIES, STORAGE_KEY };
