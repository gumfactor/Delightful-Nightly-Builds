const { test, expect } = require('@playwright/test');
const snapshot = require('../src/snapshot.js');

function makeFakeStorage(initial = {}) {
  const store = { ...initial };
  return {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, value) => {
      store[key] = value;
    },
    _store: store,
  };
}

test.describe('writeSnapshot / readSnapshot', () => {
  test('round-trips a snapshot through fake storage', () => {
    const storage = makeFakeStorage();
    const data = {
      fetchedAt: '2026-09-10T08:00:00.000Z',
      industryTotals: [{ name: 'Retail', count: 65 }],
      provinceTotals: [{ name: 'Ontario', count: 117 }],
    };
    expect(snapshot.writeSnapshot(storage, data)).toBe(true);
    expect(snapshot.readSnapshot(storage)).toEqual(data);
  });

  test('returns null when no snapshot has been saved', () => {
    const storage = makeFakeStorage();
    expect(snapshot.readSnapshot(storage)).toBeNull();
  });

  test('returns null on corrupted JSON instead of throwing', () => {
    const storage = makeFakeStorage({ [snapshot.SNAPSHOT_KEY]: '{not valid json' });
    expect(snapshot.readSnapshot(storage)).toBeNull();
  });

  test('returns null when the stored shape is missing required arrays', () => {
    const storage = makeFakeStorage({ [snapshot.SNAPSHOT_KEY]: JSON.stringify({ fetchedAt: 'x' }) });
    expect(snapshot.readSnapshot(storage)).toBeNull();
  });

  test('writeSnapshot returns false instead of throwing when storage.setItem throws (private-browsing lockout)', () => {
    const storage = {
      setItem: () => {
        throw new Error('QuotaExceededError');
      },
    };
    expect(snapshot.writeSnapshot(storage, { industryTotals: [], provinceTotals: [] })).toBe(false);
  });

  test('readSnapshot returns null instead of throwing when storage.getItem throws', () => {
    const storage = {
      getItem: () => {
        throw new Error('SecurityError');
      },
    };
    expect(snapshot.readSnapshot(storage)).toBeNull();
  });
});
