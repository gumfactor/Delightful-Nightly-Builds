/* Vizstract — localStorage-backed library of saved visual abstracts. */
(function () {
  "use strict";
  window.Vizstract = window.Vizstract || {};

  var KEY = "vizstract.library.v1";

  function uid() {
    if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID();
    return "id-" + Date.now() + "-" + Math.random().toString(16).slice(2);
  }

  function readAll() {
    var raw = window.localStorage.getItem(KEY);
    if (!raw) return [];
    try {
      var parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function writeAll(list) {
    window.localStorage.setItem(KEY, JSON.stringify(list));
  }

  function list() {
    return readAll().sort(function (a, b) {
      return String(b.updatedAt || "").localeCompare(String(a.updatedAt || ""));
    });
  }

  function get(id) {
    var all = readAll();
    for (var i = 0; i < all.length; i++) {
      if (all[i].id === id) return all[i];
    }
    return null;
  }

  function save(entry) {
    var all = readAll();
    var now = new Date().toISOString();
    var record = {};
    for (var k in entry) record[k] = entry[k];
    if (!record.id) {
      record.id = uid();
      record.createdAt = now;
    }
    record.updatedAt = now;

    var found = false;
    for (var i = 0; i < all.length; i++) {
      if (all[i].id === record.id) {
        record.createdAt = all[i].createdAt || record.createdAt || now;
        all[i] = record;
        found = true;
        break;
      }
    }
    if (!found) all.push(record);
    writeAll(all);
    return record;
  }

  function remove(id) {
    var all = readAll().filter(function (r) {
      return r.id !== id;
    });
    writeAll(all);
  }

  window.Vizstract.Library = {
    KEY: KEY,
    list: list,
    get: get,
    save: save,
    remove: remove
  };
})();
