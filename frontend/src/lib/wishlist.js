import { useSyncExternalStore } from "react";

/**
 * Wishlist kept in localStorage (no accounts). Each item stores a snapshot of the product
 * group plus the price when it was saved, so the page works offline and can show price drops.
 *
 * Item: { key, query, saved_at, saved_price, group, checked_at?, status? }
 *   key    — the group id at save time; stays fixed even when the group id changes later
 *   query  — the search that found it, re-run to fetch the latest prices
 *   status — "ok" | "missing" (not found in the latest search) | "error"
 */
const STORAGE_KEY = "zaptos:wishlist:v1";
const MAX_ITEMS = 60;

function read() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const items = raw ? JSON.parse(raw) : [];
    return Array.isArray(items) ? items.filter((it) => it?.key && it?.group) : [];
  } catch {
    return [];
  }
}

let items = read();
let snapshot = build(items);
const listeners = new Set();

/** Items plus a url → key index, so a product found by another search still shows as saved. */
function build(list) {
  const byUrl = new Map();
  const byKey = new Map();
  for (const it of list) {
    byKey.set(it.key, it);
    byKey.set(it.group.id, it);
    for (const o of it.group.offers || []) byUrl.set(o.url, it.key);
  }
  return { items: list, byKey, byUrl };
}

function commit(next) {
  items = next;
  snapshot = build(items);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  } catch {
    /* storage full or blocked: the wishlist still works for this session */
  }
  listeners.forEach((l) => l());
}

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// other tabs
if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key !== STORAGE_KEY) return;
    items = read();
    snapshot = build(items);
    listeners.forEach((l) => l());
  });
}

export function useWishlist() {
  return useSyncExternalStore(subscribe, () => snapshot);
}

/** The saved item for a product group, or undefined. */
export function findSaved(snap, group) {
  if (!group) return undefined;
  const direct = snap.byKey.get(group.id);
  if (direct) return direct;
  for (const o of group.offers || []) {
    const key = snap.byUrl.get(o.url);
    if (key) return snap.byKey.get(key);
  }
  return undefined;
}

/** Keep only what the wishlist page and drawer need; deals carry extra fields. */
function slim(group) {
  const { relevance, deal_score, category, source_query, ...rest } = group;
  return rest;
}

export function addItem(group, query) {
  if (findSaved(snapshot, group)) return;
  const item = {
    key: group.id,
    query: (query || group.source_query || "").trim() || null,
    saved_at: Date.now(),
    saved_price: group.min_price,
    group: slim(group),
    checked_at: Date.now(),
    status: "ok",
  };
  commit([item, ...items].slice(0, MAX_ITEMS));
}

export function removeItem(key) {
  commit(items.filter((it) => it.key !== key));
}

export function toggleItem(group, query) {
  const saved = findSaved(snapshot, group);
  if (saved) removeItem(saved.key);
  else addItem(group, query);
  return !saved;
}

export function clearAll() {
  commit([]);
}

/** Merge results from POST /api/prices/track: { [key]: { status, group } }. */
export function applyTrackResults(results, checkedAt = Date.now()) {
  commit(
    items.map((it) => {
      const r = results[it.key];
      if (!r) return it;
      if (r.status === "ok" && r.group) return { ...it, group: slim(r.group), status: "ok", checked_at: checkedAt };
      return { ...it, status: r.status, checked_at: checkedAt };
    }),
  );
}

export function trackPayload(list = items) {
  return {
    items: list.map((it) => ({
      key: it.key,
      title: it.group.title,
      query: it.query,
      urls: (it.group.offers || []).map((o) => o.url).slice(0, 20),
    })),
  };
}
