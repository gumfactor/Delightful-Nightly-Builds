import { test, expect } from '@playwright/test';
import { saveEntry, listEntries, getEntry, removeEntry, MAX_ENTRIES } from '../src/journal.js';

class MemoryStorage {
  constructor() {
    this.store = new Map();
  }

  getItem(key) {
    return this.store.has(key) ? this.store.get(key) : null;
  }

  setItem(key, value) {
    this.store.set(key, value);
  }
}

const sampleSnapshot = {
  city: 'Toronto',
  temperatureC: 20,
  windSpeedKmh: 10,
  cloudCoverPct: 40,
  precipProbabilityPct: 10,
  weatherCode: 1,
  isDay: true,
};

const sampleParams = {
  mode: 'major',
  droneFreqHz: 220,
  tempoHz: 1,
  filterCutoffHz: 1000,
  reverbWetness: 0.4,
  percussionDensity: 0.1,
  textureLayer: 'clear',
};

test.describe('journal.js — localStorage-backed weather journal', () => {
  test('saveEntry writes an entry that listEntries returns', () => {
    const storage = new MemoryStorage();
    saveEntry({ city: 'Toronto', weatherSnapshot: sampleSnapshot, params: sampleParams, caption: 'A caption' }, storage);
    const entries = listEntries(storage);
    expect(entries).toHaveLength(1);
    expect(entries[0].city).toBe('Toronto');
    expect(entries[0].caption).toBe('A caption');
  });

  test('listEntries returns newest-first', () => {
    const storage = new MemoryStorage();
    const first = saveEntry({ city: 'Toronto', weatherSnapshot: sampleSnapshot, params: sampleParams, caption: 'first' }, storage);
    // force a distinguishable savedAt ordering without relying on real elapsed time
    const secondEntry = { ...first, id: 'later-id', savedAt: '2099-01-01T00:00:00.000Z', caption: 'second' };
    storage.setItem('weathersong.journal', JSON.stringify([...listEntries(storage), secondEntry]));

    const entries = listEntries(storage);
    expect(entries[0].caption).toBe('second');
    expect(entries[1].caption).toBe('first');
  });

  test('getEntry retrieves a specific saved entry by id', () => {
    const storage = new MemoryStorage();
    const saved = saveEntry({ city: 'Halifax', weatherSnapshot: sampleSnapshot, params: sampleParams, caption: 'east coast' }, storage);
    const found = getEntry(saved.id, storage);
    expect(found).not.toBeNull();
    expect(found.city).toBe('Halifax');
  });

  test('getEntry returns null for an unknown id', () => {
    const storage = new MemoryStorage();
    expect(getEntry('does-not-exist', storage)).toBeNull();
  });

  test('removeEntry deletes only the targeted entry', () => {
    const storage = new MemoryStorage();
    const first = saveEntry({ city: 'Toronto', weatherSnapshot: sampleSnapshot, params: sampleParams, caption: 'one' }, storage);
    const second = saveEntry({ city: 'Calgary', weatherSnapshot: sampleSnapshot, params: sampleParams, caption: 'two' }, storage);
    removeEntry(first.id, storage);
    const remaining = listEntries(storage);
    expect(remaining).toHaveLength(1);
    expect(remaining[0].id).toBe(second.id);
  });

  test('entries are capped at MAX_ENTRIES, dropping the oldest', () => {
    const storage = new MemoryStorage();
    for (let i = 0; i < MAX_ENTRIES + 5; i += 1) {
      saveEntry({ city: `City${i}`, weatherSnapshot: sampleSnapshot, params: sampleParams, caption: `caption${i}` }, storage);
    }
    const entries = listEntries(storage);
    expect(entries).toHaveLength(MAX_ENTRIES);
    // the most recently saved entry (last inserted) must still be present
    expect(entries.some((entry) => entry.caption === `caption${MAX_ENTRIES + 4}`)).toBe(true);
  });

  test('listEntries returns an empty array when storage has never been written to', () => {
    const storage = new MemoryStorage();
    expect(listEntries(storage)).toEqual([]);
  });

  test('loadEntries-backed functions tolerate corrupted JSON in storage', () => {
    const storage = new MemoryStorage();
    storage.setItem('weathersong.journal', '{not valid json');
    expect(listEntries(storage)).toEqual([]);
    expect(getEntry('anything', storage)).toBeNull();
  });
});
