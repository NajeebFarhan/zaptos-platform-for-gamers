// Newer Node versions ship an experimental global `localStorage` that shadows jsdom's and (without a
// --localstorage-file) has no methods, so `localStorage.clear()` throws. Tests get a plain in-memory
// Storage instead, which behaves identically on every Node version.
class MemoryStorage {
  #items = new Map();
  get length() { return this.#items.size; }
  key(i) { return [...this.#items.keys()][i] ?? null; }
  getItem(k) { return this.#items.has(String(k)) ? this.#items.get(String(k)) : null; }
  setItem(k, v) { this.#items.set(String(k), String(v)); }
  removeItem(k) { this.#items.delete(String(k)); }
  clear() { this.#items.clear(); }
}

for (const target of new Set([globalThis, globalThis.window].filter(Boolean))) {
  Object.defineProperty(target, "localStorage", { value: new MemoryStorage(), configurable: true, writable: true });
}
